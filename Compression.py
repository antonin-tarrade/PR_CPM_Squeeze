import numpy as np
import copy
import plotly.graph_objects as go
from MeshObjects import *
from utils import *


def edge_length(v1, v2, obj):
    pos1 = obj.vertices[v1]
    pos2 = obj.vertices[v2]
    return np.linalg.norm(pos1 - pos2)


def is_collapse_valid(v1, v2, adjacency, collapsed_vertices):
    if v1 in collapsed_vertices or v2 in collapsed_vertices:
        return False
    common_neighbors = set(adjacency[v1]).intersection(adjacency[v2])
    if len(common_neighbors) != 2:
        return False
    if any(v in collapsed_vertices for v in (adjacency[v1] + adjacency[v2])):
        return False
    return True


def select_edge_collapses(obj, nb_collapses):
    edges = []
    
    # On parcourt les indices, pas les positions
    for v in range(len(obj.vertices)):
        for n in obj.vertex_neighbors[v]:  # adjacency[v] est une liste d'indices
            if v != n:
                # éviter doublons (v,n) / (n,v)
                if (n, v) not in edges:
                    edges.append((v, n))
    
    # Coûts : edge_length doit accepter deux indices et vertices
    edges_with_cost = [(e, edge_length(e[0], e[1], obj)) 
                       for e in edges]
    
    edges_with_cost.sort(key=lambda x: x[1])
    
    selected = []
    collapsed_vertices = set()

    # Sélection des collapses valides
    for (v1, v2), _ in edges_with_cost:
        if is_collapse_valid(v1, v2, obj.vertex_neighbors, collapsed_vertices):
            selected.append((v1, v2))
            collapsed_vertices.update([v1, v2])

        if len(selected) >= nb_collapses:
            break
    
    return selected



def apply_collapse(v1, v2, mesh):
    vertices = mesh.vertices.copy()
    faces = mesh.faces.copy()

    faces_to_remove = []
    w12 = []               # → indices !
    neighbors_between = [] # → indices !

    for fi, f in enumerate(faces):
        if v2 in f:
            vA, vB, vC = f
            other = [v for v in (vA, vB, vC) if v not in (v1, v2)]

            # CAS 1 : face avec v1 et v2 → triangle dégénéré
            if len(other) == 1:
                w12.append(other[0])
                faces_to_remove.append(fi)

            # CAS 2 : face avec seulement v2
            elif len(other) == 2:
                new_f = f.copy()
                new_f[new_f == v2] = v1
                faces[fi] = new_f
                neighbors_between.extend(other)

    # suppression et remap identiques...

    keep = np.ones(len(vertices), dtype=bool)
    keep[v2] = False
    new_vertices = vertices[keep]

    remap = np.full(len(vertices), -1, dtype=int)
    remap[np.where(keep)[0]] = np.arange(len(new_vertices))

    new_faces = remap[faces]
    mask = np.all(new_faces != -1, axis=1)
    new_faces = new_faces[mask]

    new_mesh = trimesh.Trimesh(vertices=new_vertices,
                               faces=new_faces,
                               process=True)

    # Remapper aussi w12 et neighbors_between
    v1 = remap[v1] if remap[v1] != -1 else v1
    v12 = [v1,v2]
    w12 = [remap[i] for i in w12 if remap[i] != -1]
    neighbors_between = [remap[i] for i in neighbors_between if remap[i] != -1]

    return v12, w12, neighbors_between, new_mesh





def squeeze_compression(obj: trimesh.Trimesh, compression_ratio=0.1):
    new_obj = obj.copy()

    # Nombre total de collapses à faire
    target_vertex_count = int(len(new_obj.vertices) * (1 - compression_ratio))
    nb_collapses = len(new_obj.vertices) - target_vertex_count

    # Initial edge list (on la recalculera après chaque collapse)
    collapse_edges = select_edge_collapses(new_obj, nb_collapses)

    collapse_info = []

    for _ in range(nb_collapses):

        # ---------------------------------------------------------
        # 1) Si plus de collapse planifiés → STOP
        # ---------------------------------------------------------
        if not collapse_edges:
            break

        # prendre le prochain edge
        v1, v2 = collapse_edges.pop(0)

        # ---------------------------------------------------------
        # 2) Vérifier que v1 et v2 existent encore après remappings
        # ---------------------------------------------------------
        if v1 >= len(new_obj.vertices) or v2 >= len(new_obj.vertices):
            # indices invalides → on recalcule la liste complète
            collapse_edges = select_edge_collapses(new_obj, nb_collapses)
            continue

        # ---------------------------------------------------------
        # 3) Calcule error & voisins V2
        # ---------------------------------------------------------
        v2_pos = new_obj.vertices[v2]

        neighbors = new_obj.vertex_neighbors[v2]
        if len(neighbors) == 0:
            # vertice isolé : on saute
            collapse_edges = select_edge_collapses(new_obj, nb_collapses)
            continue

        neighbors_vertices = [new_obj.vertices[n] for n in neighbors]
        v2_est_pos = np.mean(neighbors_vertices, axis=0)
        v_err_pos = v2_pos - v2_est_pos

        # ---------------------------------------------------------
        # 4) Collapse réel du mesh
        # ---------------------------------------------------------
        v12, w12, neighbors_between, new_obj = apply_collapse(v1, v2, new_obj)

        # ---------------------------------------------------------
        # 5) Mémorisation du collapse
        # ---------------------------------------------------------
        collapse_info.append({
            "v_split": v12,
            "v_err": v_err_pos,
            "w12": w12,
            "neighbors_between": neighbors_between
        })

        # ---------------------------------------------------------
        # 6) Recalcul des edges restants → EVITE TOUT BUG D’INDICE
        # ---------------------------------------------------------
        collapse_edges = select_edge_collapses(new_obj, nb_collapses)


    return new_obj, collapse_info

