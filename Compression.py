import numpy as np
import copy
import plotly.graph_objects as go
from MeshObjects import *
from utils import *


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


def apply_collapse(v1, v2, obj):
    faces = obj.faces
    adjacency = obj.adjacency
    vertices = obj.vertices
    faces_to_remove = []
    w12 = []
    neibors_between = set()
    for f in faces:
        if v2 in [f.v1, f.v2, f.v3]:
            # on repère d’abord le 3e sommet de la face AVANT de la modifier
            other_verts = [f.v1, f.v2, f.v3]
            # sommet de la face qui n'est ni v1 ni v2
            w = [vv for vv in other_verts if vv not in (v1, v2)]
            # cas face avec v1 et v2
            if len(w) == 1:
                w12.append(w[0])
                faces_to_remove.append(f)
            # cas face avec seulement v2
            elif len(w) == 2:
                if f.v1 == v2: f.v1 = v1
                if f.v2 == v2: f.v2 = v1
                if f.v3 == v2: f.v3 = v1

                neibors_between.update(w)
                
    for f in faces_to_remove:
        obj.del_face(f)

    obj.del_vertex(v2)

    return w12, neibors_between


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
    vertices, faces, adjacency = new_obj.vertices, new_obj.faces, new_obj.adjacency
    target_vertex_count = int(len(vertices) * (1 - compression_ratio))
    nb_collapses = len(vertices) - target_vertex_count

    collapse_edges = select_edge_collapses(vertices, adjacency, nb_collapses)
    collapse_info = []

    for (v1, v2) in collapse_edges:
        v2_pos = np.array(v2.as_tuple())

        connected_faces_v2 = [f for f in faces if v2 in (f.v1, f.v2, f.v3)]
        neighbors = adjacency[v2]
        v2_est = mean_position(neighbors)
        v2_est_pos = np.array(v2_est.as_tuple())

        v_err = v2_pos - v2_est_pos        # erreur (celle qu'on stocke)
        

        w12, neighbors_between = apply_collapse(v1, v2, new_obj)
        collapse_info.append({"v_split": v1, 
                              "v_err": v_err, 
                              "w12": w12,
                              "neighbors_between": neighbors_between
                              })

    return new_obj, adjacency, collapse_info

