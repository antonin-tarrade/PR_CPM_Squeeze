import numpy as np
import random
import plotly.graph_objects as go
import trimesh


def update_faces_after_removal(faces, removed_index):
    # Créer une copie pour ne pas modifier l'original
    new_faces = faces.copy()
    
    # Décrémenter tous les indices supérieurs au vertex supprimé
    mask = new_faces > removed_index
    new_faces[mask] -= 1
    
    # Supprimer les faces qui contiennent le vertex supprimé
    mask_removed_vertex = np.any(new_faces == removed_index, axis=1)
    new_faces = new_faces[~mask_removed_vertex]
    
    return new_faces


def adjust_hex_color(hex_color, factor):
    hex_color = hex_color.lstrip("#")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # application du facteur
    r = min(int(r * factor), 255)
    g = min(int(g * factor), 255)
    b = min(int(b * factor), 255)

    return f"#{r:02X}{g:02X}{b:02X}"



def show_obj(mesh: trimesh.Trimesh, title=None, point=False):
    # Titre automatique si non fourni
    if title is None:
        title = f"3D Object : {mesh.metadata.get('name', 'Unnamed')}"

    # Extraction vertices
    x, y, z = mesh.vertices[:, 0], mesh.vertices[:, 1], mesh.vertices[:, 2]

    # Extraction faces
    i, j, k = mesh.faces[:, 0], mesh.faces[:, 1], mesh.faces[:, 2]

    # Couleurs pour les faces
    main_color = "#B12CFF"
    colors = [
        adjust_hex_color(main_color, 0.9),
        adjust_hex_color(main_color, 0.8),
        adjust_hex_color(main_color, 1.1),
        adjust_hex_color(main_color, 1.2),
    ]
    face_colors = [random.choice(colors) for _ in range(len(mesh.faces))]

    # Liste des traces à afficher
    traces = []

    # === Affichage des faces ===
    if point is False or point == "both":
        traces.append(
            go.Mesh3d(
                x=x, y=y, z=z,
                i=i, j=j, k=k,
                facecolor=face_colors,
                flatshading=True,
                opacity=1.0
            )
        )

    # === Affichage des points ===
    if point is True or point == "both":
        traces.append(
            go.Scatter3d(
                x=x, y=y, z=z,
                mode="markers",
                marker=dict(size=3, color="black"),
                name="Vertices"
            )
        )

    # Création figure
    fig = go.Figure(
        data=traces,
        layout=go.Layout(
            scene=dict(
                xaxis=dict(visible=True),
                yaxis=dict(visible=True),
                zaxis=dict(visible=True),
            ),
            title=title,
            annotations=[
                dict(
                    showarrow=False,
                    text=f"Vertices: {len(mesh.vertices)} | Faces: {len(mesh.faces)}",
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=0
                )
            ]
        )
    )

    fig.show()
