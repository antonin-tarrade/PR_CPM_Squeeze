import numpy as np
import copy
import plotly.graph_objects as go
from MeshObjects import *
from utils import *


def edge_length(v1, v2):
    return np.linalg.norm(v1.array - v2.array)


def is_collapse_valid(v1, v2, collapsed_vertices, vertices):
    # Condition 1
    if v1.id in collapsed_vertices or v2.id in collapsed_vertices:
        return False
    
    # Condition 2
    v1neighbors = v1.get_neighbors()
    v2neighbors = v2.get_neighbors()
    common_neighbors = set(v1neighbors).intersection(set(v2neighbors))
    if len(common_neighbors) != 2:
        return False
    
    id_w1, id_w2 = common_neighbors
    w1 = vertices[id_w1]
    w2 = vertices[id_w2]

    # Condition 2.2
    if id_w1 in w2.get_neighbors() or id_w2 in w1.get_neighbors():
        return False

    fw1 = Face(v1.id, v2.id, id_w1, -1)
    fw2 = Face(v1.id, v2.id, id_w2,-2)
    if not(fw1 in v1.faces and fw1 in v2.faces and fw2 in v1.faces and fw2 in v2.faces):
        return False
    
    # Condition 3
    if any(v in collapsed_vertices for v in (v1neighbors + v2neighbors)):
        return False

    return True


def select_edge_collapses(vertices, nb_collapses):
    seen = set()
    edges = []

    for v in vertices.values():
        for n in v.get_neighbors():
            key = tuple(sorted((v.id, n)))
            if key not in seen:
                seen.add(key)
                edges.append((v, vertices[n]))

    edges_with_cost = [(e, edge_length(*e)) for e in edges]
    edges_with_cost.sort(key=lambda x: x[1])
    
    selected = []
    collapsed_vertices = set()

    for (v1, v2), _ in edges_with_cost:
        if is_collapse_valid(v1, v2, collapsed_vertices, vertices):
            selected.append((v1, v2))
            collapsed_vertices.update([v1.id, v2.id])
        if len(selected) >= nb_collapses:
            break
    

    return selected


def apply_collapse(v1, v2, obj):
    faces_to_remove = []
    cut_ids = []

    for f in v2.faces:
        if f in v1.faces :
            # The other vertex (not v1 or v2) in the face
            w_other = [v for v in [f.v1, f.v2, f.v3] if v != v1.id and v != v2.id][0]
            cut_ids.append(w_other)
            faces_to_remove.append(f)
            obj.vertices[w_other].remove_face(f)
            v1.remove_face(f)
        else :
            if f.v1 == v2.id: f.v1 = v1.id
            if f.v2 == v2.id: f.v2 = v1.id
            if f.v3 == v2.id: f.v3 = v1.id
            v1.add_face(f)
                
    for f in faces_to_remove:
        obj.del_face(f)

    obj.del_vertex(v2.id)

    return cut_ids



def squeeze_compression(object3D, compression_ratio=0.1):
    new_obj = copy.deepcopy(object3D)
    vertices = new_obj.vertices
    target_vertex_count = int(len(vertices) * (1 - compression_ratio))
    nb_collapses = len(vertices) - target_vertex_count

    collapse_edges = select_edge_collapses(vertices, nb_collapses)
    collapse_info = []
    cut_ids = []

    #print(f"Selected {len(collapse_edges)} edges for collapse.")

    for (v1, v2) in collapse_edges:
        
        ordered_neighbors = v2.get_neighbors()

        v2_pos = v2.array

        neighbors = []

        for ind in v2.get_neighbors():
            v = vertices.get(ind, None)
            if v is not None:
                neighbors.append(vertices[ind])
            else :
                print(f"Warning: Neighbor id={ind} not found in vertices during compression.")
        v2_est = mean_position(neighbors)

        v_err = v2_pos - v2_est
        

        cut_ids = apply_collapse(v1, v2, new_obj)
        
        collapse_info.append({"v_split": v1.id,
                              "vdel_id": v2.id,
                              "v_err": v_err, 
                              "cut_ids": cut_ids,
                              "ordered_neighbors": ordered_neighbors
                              })


    return new_obj, collapse_info

