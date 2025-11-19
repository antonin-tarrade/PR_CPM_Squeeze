import numpy as np
import copy
from utils import *


def squeeze_decompression(Mi_minus_1, infos):
    Mi = copy.deepcopy(Mi_minus_1)
    for info in reversed(infos):
        apply_vertex_split(Mi, info)
        
    return Mi


def apply_vertex_split(Model, collapse_info):
    # Extraire les données nécessaires
    vertices = Model.vertices
    faces = Model.faces
    adjacency = Model.adjacency
    vsplit = get_vertex_from_array(vertices,collapse_info['v_split'])
    w12_tuples = collapse_info['w12']
    id_v2 = collapse_info['id_v2']
    
    # Look up w1 and w2 in the current mesh by their coordinates
    w1 = get_vertex_from_array(vertices, w12_tuples[0])
    w2 = get_vertex_from_array(vertices, w12_tuples[1])
    
    if w1 is None or w2 is None:
        raise ValueError(f"Could not find w1 or w2 in vertices. w12={w12_tuples}")
    
    v_err = np.array(collapse_info['v_err'])
    neighbors_between_array = collapse_info['neighbors_between']
    neighbors_between = set()
    for arr in neighbors_between_array:
        v = get_vertex_from_array(vertices, arr)
        if v is not None:
            neighbors_between.add(v)

    
    # # Trouver vsslit comme voisin de w1 et w2    
    # for v in adjacency[w1]:
    #     if v in adjacency[w2]:
    #         vsplit = v
    #         break

    # Calcul prédictif pour retrouver la position de vnew
    neighbors_list = list(neighbors_between) + [vsplit]
    bary = mean_position(neighbors_list)

    # Ajout du nouveau sommet
    new_pos = bary + v_err
    vnew = Vertex(*new_pos, id_v2)
    Model.add_vertex(vnew)

    # Recréer les 2 faces supprimées pendant la compression
    f1 = Face(vsplit, w1, vnew)
    f2 = Face(vsplit, vnew, w2)

    Model.add_face(f1)
    Model.add_face(f2)

    Model.adjacency = Model.build_adjacency()

    # Mettre a jour les faces connectant vsplit à ses voisins entre w1 et w2
    for f in faces:
        if vsplit in [f.v1, f.v2, f.v3]:
            other_vertices = [v for v in [f.v1, f.v2, f.v3] if v != vsplit]
            if all(v in neighbors_between for v in other_vertices):
                # Mettre à jour la face pour inclure vnew
                if f.v1 == vsplit:
                    f.v1 = vnew
                elif f.v2 == vsplit:
                    f.v2 = vnew
                elif f.v3 == vsplit:
                    f.v3 = vnew
            

    # Mettre à jour l'adjacency
    Model.adjacency = Model.build_adjacency()



    




