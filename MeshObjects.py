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
        vertices, faces = dict(), []
        id = 1
        for line in objFile:
            if line.startswith('v '):
                parts = line.strip().split()
                vertices[id] = Vertex(float(parts[1]), float(parts[2]), float(parts[3]), id)
                id += 1
            elif line.startswith('f '):
                parts = line.strip().split()
                face = Face(*[int(p) for p in parts[1:]]) ############## problèmes d'indices ici ?
                faces.append(face)
        self.vertices = vertices
        self.faces = faces
        self.adjacency = self.build_adjacency()
        self.nb_vertices = len(vertices)
        self.nb_faces = len(faces)
    
    def build_adjacency(self):
        adjacency = {id: [] for id in self.vertices.keys()}
        print (adjacency)
        for f in self.faces:
            for (a, b, c) in [(f.id_v1, f.id_v2, f.id_v3), (f.id_v2, f.id_v3, f.id_v1), (f.id_v3, f.id_v1, f.id_v2)]:
                if a not in adjacency:
                    raise ValueError(f"Vertex ID {a} in face not found in vertices.")
                if b not in adjacency[a]:
                    adjacency[a].append(b)
                if c not in adjacency[a]:
                    adjacency[a].append(c)
        return adjacency

    def Show(self, title=None):
        if title is None:
            title = f"3D Object : {self.name}"

        x, y, z = zip(*[v.as_tuple() for v in self.vertices.values()])

        # Map vertex id -> index in the x/y/z arrays
        vertices_list = list(self.vertices.values())
        index_map = {v.id: idx for idx, v in enumerate(vertices_list)}

        # Build face index arrays (i, j, k) referencing positions in x/y/z
        i = [index_map.get(f.id_v1, 0) for f in self.faces]
        j = [index_map.get(f.id_v2, 0) for f in self.faces]
        k = [index_map.get(f.id_v3, 0) for f in self.faces]

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
                        text=f"Vertices: {len(self.vertices)} | Faces: {len(self.faces)}",
                        xref="paper",
                        yref="paper",
                        x=0,
                        y=0
                    )
                ]
            )
        )
        fig.show()
    
    def add_vertex(self, vertex):
        self.vertices.append(vertex)
        self.nb_vertices += 1

    def del_vertex(self, vertex):
        if vertex in self.vertices:
            self.vertices.remove(vertex)
            self.nb_vertices -= 1
    
    def add_face(self, face):
        self.faces.append(face)
        self.nb_faces += 1
        # # Actualiser l'adjacency
        # self.adjacency = self.build_adjacency()
    
    def del_face(self, face):
        if face in self.faces:
            self.faces.remove(face)
            self.nb_faces -= 1
            # # Actualiser l'adjacency
            # self.adjacency = self.build_adjacency()


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
            obj,transfo = squeeze_compression(last_lod, compression_ratio)
            self.collapse_info.append(transfo)
            self.model_lods.append(obj)
            self.adjacency_ref.append(obj.build_adjacency())
        return self.model_lods, self.collapse_info
    
    def decompress(self, nb_decompressions = None):
        if len(self.model_lods) == 0:
            return self.model_ref
        if nb_decompressions is None:
            nb_decompressions = self.get_nb_of_lods()

        M_n = self.get_last_lod()

        for n in range(nb_decompressions):
            info = self.collapse_info[-(n+1)]
            M_n = squeeze_decompression(M_n, info)
        return M_n

    def show_lods(self):
        for idx, lod in enumerate(self.model_lods):
            lod.Show(f'LOD {idx + 1} of {self.name}')

    def show_last_lod(self):
        self.get_last_lod().Show(f'Last LOD of {self.name}')
