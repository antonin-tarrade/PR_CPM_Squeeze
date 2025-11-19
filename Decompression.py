import copy
import numpy as np
import trimesh


def squeeze_decompression(mesh, infos):
    for info in reversed(infos):
        mesh = apply_vertex_split(mesh, info)
    return mesh

def apply_vertex_split(mesh, info):
    vertices = mesh.vertices.copy()
    faces = mesh.faces.copy()

    # --- Extraction des données ---
    vsplit, v2 = info["v_split"]             # indice
    w12 = info["w12"]                        # liste d'indices
    neighbors_between = set(info["neighbors_between"])
    v_err = np.asarray(info["v_err"], float)

    # --- 1. Calcule du barycentre prédictif ---
    pts = [vertices[vsplit]]
    if len(w12) >= 1:
        pts.append(vertices[w12[0]])
    if len(w12) >= 2:
        pts.append(vertices[w12[1]])
    for n in neighbors_between:
        pts.append(vertices[n])

    bary = np.mean(np.vstack(pts), axis=0)

    # --- 2. Reconstruction du nouveau sommet ---
    vnew_pos = bary + v_err
    vnew = v2  # position où insérer le nouveau vertex

    # Insérer le nouveau vertex dans vertices à l'indice vnew
    new_vertices = np.insert(vertices, vnew, vnew_pos, axis=0)

    # --- 3. Reconstruction des deux faces supprimées ---
    added_faces = []
    for w in w12:
        added_faces.append([vsplit, w, vnew])

    # --- 4. Mise à jour des faces existantes ---
    new_faces = faces.copy()

    for i, f in enumerate(new_faces):
        if vsplit in f:
            others = [v for v in f if v != vsplit]
            
            # Cette face avait absorbé v2 → on la restaure
            if len(others) == 2 and set(others).issubset(neighbors_between):
                f2 = f.copy()
                f2[f2 == vsplit] = vnew
                new_faces[i] = f2

    # --- 5. On concatène les faces ajoutées ---
    if len(added_faces) > 0:
        new_faces = np.vstack([new_faces, np.array(added_faces, int)])

    # --- 6. On supprime les faces dégénérées ---
    mask = np.array([len(set(face)) == 3 for face in new_faces])
    new_faces = new_faces[mask]

    # --- 7. Création du mesh final ---
    return trimesh.Trimesh(
        vertices=new_vertices,
        faces=new_faces,
        process=True
    )
