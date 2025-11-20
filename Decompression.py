import numpy as np
import copy
from utils import *

from obja.obja import Output
from obja.obja import Face as ObjaFace

def squeeze_decompression(Mi_minus_1, infos, out):
    Mi = copy.deepcopy(Mi_minus_1)
    #print(f"Starting decompression: there will be {len(infos)} vertex splits to apply.")
    for info in reversed(infos):
        apply_vertex_split(Mi, info, out)
    return Mi


def extract_vdel_neighbors(ordered_neighbors, w1, w2): 
    idx1 = ordered_neighbors.index(w1.id) 
    idx2 = ordered_neighbors.index(w2.id) 
    if idx1 < idx2: 
        neighbors_between = ordered_neighbors[idx1 + 1 : idx2] 
    else: # handle wrap-around (cyclic) 
        neighbors_between = ordered_neighbors[idx1 + 1 :] + ordered_neighbors[:idx2] 
    return neighbors_between


def apply_vertex_split(Model, collapse_info, out):
    # Extraire les données nécessaires
    vertices = Model.vertices
    faces = Model.faces
    vsplit = vertices.get(collapse_info['v_split'], None)
    vdel_id = collapse_info['vdel_id']

    if vsplit is None:
        raise ValueError(f"Could not find vsplit in vertices. vsplit id={collapse_info['v_split']}")
    
    cut_ids = collapse_info['cut_ids']
    w1 = vertices.get(cut_ids[0], None)
    w2 = vertices.get(cut_ids[1], None)

    if w1 is None or w2 is None:
        raise ValueError(f"Could not find w1 or w2 in vertices")
    
    v_err = collapse_info['v_err']

    ordered_neighbors = collapse_info['ordered_neighbors']


    # The new vertex vdel is estimated as the average of its immediate neighbors a1, ...ak,which are known from connectivity decoding
    # We now that vdel_neighbors are contained in the neighbors of vsplit
    # v_split_neighbors = ordered_neighbors
    
    # vdel_neighbors = extract_vdel_neighbors(v_split_neighbors, w1, w2)

    # Calcul prédictif pour retrouver la position de vnew
    vdel_neighbors_vertices = [vertices[nid] for nid in ordered_neighbors]
    bary = mean_position(vdel_neighbors_vertices)

    # Ajout du nouveau sommet
    new_pos = bary + v_err
    vnew = Vertex(new_pos)
    vnew.set_id(vdel_id)
    Model.add_vertex_at(vnew)

    # Ajout dans le obja
    out.add_vertex(vnew.id, vnew.array)
    
    
    # Recréer les 2 faces supprimées pendant la compression
    f1 = Face(vsplit.id, w1.id, vnew.id, Model.nb_faces())
    Model.add_face(f1)
    Model.vertices[vsplit.id].add_face(f1)
    Model.vertices[w1.id].add_face(f1)
    Model.vertices[vnew.id].add_face(f1)

    f2 = Face(vsplit.id, vnew.id, w2.id,Model.nb_faces())
    Model.add_face(f2)
    Model.vertices[vsplit.id].add_face(f2)
    Model.vertices[w2.id].add_face(f2)
    Model.vertices[vnew.id].add_face(f2)
    
    # Ajout dans le obja
    out.add_face(f1.id, ObjaFace(f1.v1, f1.v2, f1.v3))
    out.add_face(f2.id, ObjaFace(f2.v1, f2.v2, f2.v3))


    # Mettre a jour les faces connectant vsplit à ses voisins entre w1 et w2
    for fi,f in enumerate(faces):
        if vsplit.id in [f.v1, f.v2, f.v3]:
            other_vertices = [v for v in [f.v1, f.v2, f.v3] if v != vsplit.id]
            if all(v in ordered_neighbors for v in other_vertices):
                # Mettre à jour la face pour inclure vnew
                if f.v1 == vsplit.id:
                    f.v1 = vnew.id
                elif f.v2 == vsplit.id:
                    f.v2 = vnew.id
                elif f.v3 == vsplit.id:
                    f.v3 = vnew.id

                vnew.add_face(f)
                out.edit_face(fi, ObjaFace(f.v1, f.v2, f.v3))

