import numpy as np
from MeshObjects import *

def apply_vertex_split(collapse_info, adjacency, faces, vertices):
    vsplit = collapse_info['v_split']
    cut_indices = collapse_info['cut_indices']
    v_est = np.array(collapse_info['v_est'])

    # si on n'a pas 2 indices valides, on ne peut pas reconstruire proprement
    if len(cut_indices) == 0:
        return

    neighbors = adjacency.get(vsplit, [])
    d = len(neighbors)
    if d == 0:
        return

    i1 = cut_indices[0] % d
    w1 = neighbors[i1]
    w2 = neighbors[cut_indices[1] % d] if len(cut_indices) > 1 and cut_indices[1] >= 0 else w1


    # Retrouver les voisins autour de vsplit
    neighbors = adjacency[vsplit]
    d = len(neighbors)

    # Retrouver les deux voisins concernés
    i1 = cut_indices[0]
    i2 = cut_indices[1]
    w1 = neighbors[i1 % d]
    w2 = neighbors[i2 % d]

    # Calcul prédictif pour retrouver la position de vnew
    bary = np.mean([
        np.array([(w1.x + w2.x + vsplit.x) / 3,
                  (w1.y + w2.y + vsplit.y) / 3,
                  (w1.z + w2.z + vsplit.z) / 3])
    ], axis=0)

    v_pred = bary - np.array(vsplit.as_tuple())
    vdisp = v_est + v_pred
    new_pos = np.array(vsplit.as_tuple()) + vdisp

    vnew = Vertex(*new_pos)

    vertices.append(vnew)

    # Recréer les 2 faces supprimées pendant la compression
    f1 = Face(vsplit, w1, vnew)
    f2 = Face(vsplit, vnew, w2)
    faces.extend([f1, f2])

    # Rettre à jour adjacency
    adjacency[vsplit].extend([vnew])
    adjacency[vnew] = [vsplit, w1, w2]
    for w in (w1, w2):
        adjacency[w].append(vnew)


def dedup_vertices_from_faces(faces, eps=1e-6):
    """
    Reconstruit une liste de sommets SANS doublons géométriques.
    Si deux Vertex ont (x,y,z) très proches, on garde le premier
    et on remplace dans les faces.
    """
    pos2vert = {}   # (x,y,z) arrondi -> Vertex canonique
    unique_vertices = []

    def key_from_vertex(v):
        return (round(v.x / eps) * eps,
                round(v.y / eps) * eps,
                round(v.z / eps) * eps)

    for f in faces:
        for attr in ("v1", "v2", "v3"):
            v = getattr(f, attr)
            k = key_from_vertex(v)
            if k in pos2vert:
                # remplacer par le vertex déjà existant
                setattr(f, attr, pos2vert[k])
            else:
                # nouveau sommet canonique
                pos2vert[k] = v
                unique_vertices.append(v)

    return unique_vertices

def decompress(Mi_minus_1, adjacency, infos):
    new_obj = copy.deepcopy(Mi_minus_1)
    faces = new_obj.faces
    vertices = new_obj.vertices
    # adjacency = build_adjacency(new_obj)

    for rec in reversed(infos):
        apply_vertex_split(
            rec,
            adjacency,
            faces,
            vertices
        )

    # reconstruire la liste de sommets utilisée par les faces
    unique_vertices = dedup_vertices_from_faces(faces, eps=1e-6)
    

    new_obj.vertices = unique_vertices
    new_obj.nb_vertices = len(unique_vertices)
    new_obj.nb_faces = len(faces)


    return new_obj
