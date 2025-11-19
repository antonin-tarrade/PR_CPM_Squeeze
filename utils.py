import numpy as np
import random
import plotly.graph_objects as go
import trimesh

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


def get_values_between(values, id_min, id_max):
    if id_max == id_min:
        return []

    if id_min < id_max:
        return values[id_min + 1:id_max]

    # Cas circulaire
    return values[id_min + 1:] + values[:id_max]



def mean_position(vertices):
    coords = np.array([v.as_tuple() for v in vertices])
    mean_coords = np.mean(coords, axis=0)
    return Vertex(*mean_coords)


def get_vertex_from_array(vertices, arr):
    for v in vertices:
        if np.allclose(v.as_array(), arr, atol=1e-7):
            return v
    return None



import plotly.graph_objects as go
import random

def show_obj(mesh: trimesh.Trimesh, title=None):
    # Titre
    if title is None:
        title = f"3D Object : {mesh.metadata.get('name', 'Unnamed')}"

    # Extraction des vertices
    x, y, z = mesh.vertices[:, 0], mesh.vertices[:, 1], mesh.vertices[:, 2]

    # Extraction des faces (déjà des indices)
    i = mesh.faces[:, 0]
    j = mesh.faces[:, 1]
    k = mesh.faces[:, 2]

    # Couleurs
    main_color = "#B12CFF"
    colors = [
        adjust_hex_color(main_color, 0.9),
        adjust_hex_color(main_color, 0.8),
        adjust_hex_color(main_color, 1.1),
        adjust_hex_color(main_color, 1.2),
    ]

    face_colors = [random.choice(colors) for _ in range(len(mesh.faces))]

    # Création figure plotly
    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=x, y=y, z=z,
                i=i, j=j, k=k,
                facecolor=face_colors,
                flatshading=True,
                opacity=1.0
            )
        ],
        layout=go.Layout(
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False)
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
