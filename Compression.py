import numpy as np
import copy
import plotly.graph_objects as go
from MeshObjects import *


def build_adjacency(obj):
    adjacency = {v: [] for v in obj.vertices}
    for f in obj.faces:
        for (a, b, c) in [(f.v1, f.v2, f.v3), (f.v2, f.v3, f.v1), (f.v3, f.v1, f.v2)]:
            if b not in adjacency[a]:
                adjacency[a].append(b)
            if c not in adjacency[a]:
                adjacency[a].append(c)
    return adjacency

def build_spanning_tree(adjacency, root):
    parent = {v: None for v in adjacency}
    visited = {root}
    stack = [root]
    while stack:
        v = stack.pop()
        for n in adjacency[v]:
            if n not in visited:
                visited.add(n)
                parent[n] = v
                stack.append(n)
    return parent


def edge_length(v1, v2):
    return np.linalg.norm(np.array(v1.as_tuple()) - np.array(v2.as_tuple()))


def is_collapse_valid(v1, v2, adjacency, collapsed_vertices):
    if v1 in collapsed_vertices or v2 in collapsed_vertices:
        return False
    common_neighbors = set(adjacency[v1]).intersection(adjacency[v2])
    if len(common_neighbors) < 1:
        return False
    #for w in common_neighbors:
    #    if len(set(adjacency[w]).intersection({v1, v2})) >= 2:
    #        return False
    return True


def select_edge_collapses(vertices, adjacency, nb_collapses):
    edges = []
    for v in vertices:
        for n in adjacency[v]:
            if v != n and (n, v) not in edges:
                edges.append((v, n))
    edges_with_cost = [(e, edge_length(*e)) for e in edges]
    edges_with_cost.sort(key=lambda x: x[1])

    selected = []
    collapsed_vertices = set()
    for (v1, v2), _ in edges_with_cost:
        if is_collapse_valid(v1, v2, adjacency, collapsed_vertices):
            selected.append((v1, v2))
            collapsed_vertices.update([v1, v2])
        if len(selected) >= nb_collapses:
            break
    return selected


def apply_collapse(v1, v2, faces, adjacency, vertices):
    faces_to_remove = []
    cut_neighbors = []
    for f in faces:
        if v2 in [f.v1, f.v2, f.v3]:
            # on repère d’abord le 3e sommet de la face AVANT de la modifier
            other_verts = [f.v1, f.v2, f.v3]
            # sommet de la face qui n'est ni v1 ni v2
            w = [vv for vv in other_verts if vv not in (v1, v2)]
            if len(w) == 1:
                cut_neighbors.append(w[0])

            # puis on remplace v2 par v1
            if f.v1 == v2: f.v1 = v1
            if f.v2 == v2: f.v2 = v1
            if f.v3 == v2: f.v3 = v1

            if len({f.v1, f.v2, f.v3}) < 3:
                faces_to_remove.append(f)

    for f in faces_to_remove:
        faces.remove(f)

    for neighbor in list(adjacency[v2]):
        if neighbor != v1:
            if v1 not in adjacency[neighbor]:
                adjacency[neighbor].append(v1)
            if neighbor not in adjacency[v1]:
                adjacency[v1].append(neighbor)
        if v2 in adjacency[neighbor]:
            adjacency[neighbor].remove(v2)
    if v2 in adjacency:
        del adjacency[v2]
    if v2 in vertices:
        vertices.remove(v2)
        
    cut_neighbors = list(dict.fromkeys(cut_neighbors))[:2]
    return cut_neighbors

def encode_cut_indices(record, adjacency, parent):
    vs = record["v_split"]
    neighbors = adjacency[vs]
    d = len(neighbors)

    # point de départ = edge (vsplit -> parent)
    if parent[vs] is not None and parent[vs] in neighbors:
        start = neighbors.index(parent[vs])
    else:
        start = 0

    cut_idxs = []
    for w in record["cut_neighbors"]:
        if w in neighbors:
            raw_index = neighbors.index(w)
            # décalage pour que le 0 corresponde à l’arête vers le parent
            rel_index = (raw_index - start) % d
            cut_idxs.append(rel_index)
    # sécurité : on complète ou on tronque
    if len(cut_idxs) < 2:
        # on met -1 pour dire "pas de deuxième arête"
        cut_idxs += [-1] * (2 - len(cut_idxs))
    else:
        cut_idxs = cut_idxs[:2]

    record["cut_indices"] = cut_idxs
    # on peut jeter la version en sommets ensuite
    # del record["cut_neighbors"]


def squeeze_compression(Object3D, compression_ratio=0.1):
    new_obj = copy.deepcopy(Object3D)
    vertices, faces = new_obj.vertices, new_obj.faces
    adjacency = build_adjacency(new_obj)
    target_vertex_count = int(len(vertices) * (1 - compression_ratio))
    nb_collapses = len(vertices) - target_vertex_count

    collapse_edges = select_edge_collapses(vertices, adjacency, nb_collapses)
    collapse_info = []

    for (v1, v2) in collapse_edges:
        connected_faces = [f for f in faces if v2 in (f.v1, f.v2, f.v3)]
        if connected_faces:
            bary = np.mean([
                np.array([(f.v1.x + f.v2.x + f.v3.x) / 3,
                        (f.v1.y + f.v2.y + f.v3.y) / 3,
                        (f.v1.z + f.v2.z + f.v3.z) / 3])
                for f in connected_faces
            ], axis=0)
        else:
            bary = np.array(v1.as_tuple())  # fallback : v1 lui-même

        v2_pos = np.array(v2.as_tuple())
        v1_pos = np.array(v1.as_tuple())

        vdisp = v2_pos - v1_pos       # déplacement brut
        v_pred = bary - v1_pos        # prédiction barycentrique
        v_est = vdisp - v_pred        # erreur (celle qu'on stocke)

        cut_neighbors = apply_collapse(v1, v2, faces, adjacency, vertices)
        collapse_info.append({"v_split": v1, 
                              "v_est": v_est, 
                              "cut_neighbors": cut_neighbors,
                              })

    new_obj.vertices = [v for v in vertices if v in adjacency]
    new_obj.nb_vertices = len(new_obj.vertices)
    new_obj.nb_faces = len(new_obj.faces)


    root = next(iter(adjacency.keys()))
    parent = build_spanning_tree(adjacency, root)

    for rec in collapse_info:
        encode_cut_indices(rec, adjacency, parent)

    for v, neighs in list(adjacency.items()):
        adjacency[v] = [n for n in neighs if n in adjacency]

    return new_obj, adjacency, collapse_info

