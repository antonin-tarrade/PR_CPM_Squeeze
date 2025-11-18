from Compression import squeeze_compression
from Decompression import squeeze_decompression
from utils import *
import numpy as np
import random
import copy
import plotly.graph_objects as go

# Structures de base : Vertex, Face, Object3D

class Object3D:
    def __init__(self, objFile, name=None):
        self.name = name or "Unknown"
        vertices, faces = [], []
        for line in objFile:
            if line.startswith('v '):
                parts = line.strip().split()
                vertices.append(Vertex(float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith('f '):
                parts = line.strip().split()
                face = Face(*[vertices[int(p) - 1] for p in parts[1:]])
                faces.append(face)
        self.vertices = vertices
        self.faces = faces
        self.nb_vertices = len(vertices)
        self.nb_faces = len(faces)

    def Show(self, title=None):
        if title is None:
            title = f"3D Object : {self.name}"

        x, y, z = zip(*[v.as_tuple() for v in self.vertices])

        # Map vertices to indices for faces
        vertex_to_index = {v: idx for idx, v in enumerate(self.vertices)}
        i = [vertex_to_index[f.v1] for f in self.faces]
        j = [vertex_to_index[f.v2] for f in self.faces]
        k = [vertex_to_index[f.v3] for f in self.faces]

        # Liste de couleurs autorisées
        main_color = "#B12CFF"
        colors = [
            adjust_hex_color(main_color, 0.9),   # 10% plus sombre
            adjust_hex_color(main_color, 0.8),   # 20% plus sombre
            adjust_hex_color(main_color, 1.1),   # 10% plus claire
            adjust_hex_color(main_color, 1.2),   # 20% plus claire
        ]

        # Couleur aléatoire pour chaque face
        face_colors = [random.choice(colors) for _ in self.faces]

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
                        text=f"Vertices: {self.nb_vertices} | Faces: {self.nb_faces}",
                        xref="paper",
                        yref="paper",
                        x=0,
                        y=0
                    )
                ]
            )
        )
        fig.show()


# Classe pour gérer les LODs 
class AObject3D:
    def __init__(self, objRef, name=None):
        self.name = name or "Unknown"
        self.model_ref = objRef
        self.model_lods = []
        self.collapse_info = []
        self.adjacency_ref = []
    
    def get_nb_of_lods(self):
        return len(self.model_lods)

    def get_last_lod(self):
        return self.model_ref if len(self.model_lods) == 0 else self.model_lods[-1]

    def compress(self, compression_ratio=0.1, nb_compressions=1):
        for _ in range(nb_compressions):
            last_lod = self.get_last_lod()
            obj, adjacency, transfo = squeeze_compression(last_lod, compression_ratio)
            self.collapse_info.append(transfo)
            self.model_lods.append(obj)
            self.adjacency_ref.append(adjacency)
        return self.model_lods, self.collapse_info
    
    def decompress(self, nb_decompressions = None):
        if len(self.model_lods) == 0:
            return self.model_ref
        if nb_decompressions is None:
            nb_decompressions = self.get_nb_of_lods()

        M_n = self.get_last_lod()

        for n in np.arange(nb_decompressions):
            adjacency = self.adjacency_ref[-(n+1)]
            info = self.collapse_info[-(n+1)]
            M_n = squeeze_decompression(M_n, adjacency, info)
        return M_n

    def show_lods(self):
        for idx, lod in enumerate(self.model_lods):
            lod.Show(f'LOD {idx + 1} of {self.name}')

    def show_last_lod(self):
        self.get_last_lod().Show(f'Last LOD of {self.name}')
