import numpy as np
import copy
from utils import *


def squeeze_decompression(Mi_minus_1, infos):
    print("Decompression started...")
    Mi = copy.deepcopy(Mi_minus_1)
    i = 0
    for info in reversed(infos):
        i += 1
        print(i)
        apply_vertex_split(Mi, info)
        
    return Mi


def apply_vertex_split(Model, collapse_info):
    # Extraire les données nécessaires
    vertices = Model.vertices
    faces = Model.faces
    adjacency = Model.adjacency
    vsplit = collapse_info['v_split']
    w1, w2 = collapse_info['w12']
    v_err = np.array(collapse_info['v_err'])
    neighbors_between = collapse_info['neighbors_between']


    # Retirer les faces connectant vsplit à ses voisins entre w1 et w2
    faces_to_remove = []
    for f in faces:
        if vsplit in (f.v1, f.v2, f.v3):
            # Dans les facede v1
            other_vertices = [v for v in (f.v1, f.v2, f.v3) if v != vsplit]
            if all(v in neighbors_between for v in other_vertices):
                faces_to_remove.append(f)
    for f in faces_to_remove:
        Model.del_face(f)

    # Calcul prédictif pour retrouver la position de vnew
    bary = mean_position(list(neighbors_between) + [vsplit])
    bary = np.array(bary.as_tuple())

    # Ajout du nouveau sommet
    new_pos = bary + v_err
    vnew = Vertex(*new_pos)
    Model.add_vertex(vnew)

    # Recréer les 2 faces supprimées pendant la compression
    f1 = Face(vsplit, w1, vnew)
    f2 = Face(vsplit, vnew, w2)
    Model.add_face(f1)
    Model.add_face(f2)

    # Ordonner neighbors_between de w1 à w2
    ordered_neighbors_between = [w1]
    for _ in range(len(neighbors_between)):
        voisins_last = Model.adjacency[ordered_neighbors_between[-1]]
        next_neighbors = [v for v in voisins_last if v in neighbors_between and v not in ordered_neighbors_between]
        ordered_neighbors_between.append(next_neighbors[0])

    # trouver les paires de voisins dans neighbors_between_ordered
    neighbor_pairs = []
    nb_list = list(ordered_neighbors_between)
    for idx in range(len(nb_list) - 1):
        neighbor_pairs.append((nb_list[idx], nb_list[idx + 1]))

    # Ajouter les faces entre vnew et les paires de points
    for v_a, v_b in neighbor_pairs:
        Model.add_face(Face(vnew, v_a, v_b))






    # p1 = vnew
    # p2 = w1
    # print(neighbors_between)
    # print(len(neighbors_between))
    # for _ in range(len(neighbors_between)-1):
    #     print(adjacency[p2])
    #     print(neighbors_between)
    #     p3 = [v for v in neighbors_between if v in adjacency[p2]][0]
    #     neighbors_between.remove(p3)
    #     f = Face(p1, p2, p3)
    #     Model.add_face(f)
    #     p2 = p3



    




