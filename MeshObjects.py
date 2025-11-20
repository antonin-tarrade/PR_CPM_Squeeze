from Compression import squeeze_compression
from Decompression import squeeze_decompression
from utils import *
import numpy as np
import random
import plotly.graph_objects as go
import os

# Structures de base : Vertex, Face, Object3D

class Object3D:

    def __init__(self, objFile, name=None):
        self.name = name or "Unknown"
        self.vertices = {}
        self.faces = []
        self.next_vertex_id = 0
        self.ParseOBJ(objFile)

    def ParseOBJ(self,objFile):
        for line in objFile:
            line = line.strip()
            if not line:
                continue
            if line.startswith('v '):
                parts = line.split()
                try:
                    coords = np.array([float(x) for x in parts[1:]], dtype=float)
                except ValueError:
                    continue
                self.add_vertex(Vertex(coords))
            elif line.startswith('f '):
                parts = line.split()
                idxs = []
                for p in parts[1:]:
                    # token may be 'v', 'v/t' or 'v/t/n' — take the vertex index before any '/'
                    try:
                        vi = int(p.split('/')[0]) - 1
                    except Exception:
                        # skip malformed token
                        continue
                    idxs.append(vi)
                if len(idxs) >= 3:
                    new_face = Face(*idxs[:3], len(self.faces))
                    self.add_face(new_face)
                    # Link face to vertices
                    for vi in idxs[:3]:
                        vertex = self.vertices.get(vi, None)
                        if vertex is not None:
                            vertex.add_face(new_face)



    def Show(self, main_color, title=None):
        if title is None:
            title = f"3D Object : {self.name}"
        # Sanity checks
        if self.nb_vertices() == 0:
            print("Warning: object has no vertices to display")
            return
        if self.nb_faces() == 0:
            print("Warning: object has no faces to display")
            return

        # Build an ordered list of vertices and coordinate arrays
        vertices_list = list(self.vertices.values())
        x = [float(v.array[0]) for v in vertices_list]
        y = [float(v.array[1]) for v in vertices_list]
        z = [float(v.array[2]) for v in vertices_list]

        # Map vertex id -> index in the x/y/z arrays
        index_map = {v.id: idx for idx, v in enumerate(vertices_list)}

        # Build face index arrays (i, j, k) referencing positions in x/y/z
        i = [index_map.get(f.v1, 0) for f in self.faces]
        j = [index_map.get(f.v2, 0) for f in self.faces]
        k = [index_map.get(f.v3, 0) for f in self.faces]



        # Liste de couleurs autorisées
        colors = [
            adjust_hex_color(main_color, 0.8),   # 10% plus sombre
            adjust_hex_color(main_color, 0.6),   # 20% plus sombre
            adjust_hex_color(main_color, 1.2),   # 10% plus claire
            adjust_hex_color(main_color, 1.4),   # 20% plus claire
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
                        text=f"Vertices: {self.nb_vertices()} | Faces: {self.nb_faces()}",
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
        vertex.set_id(self.next_vertex_id)
        self.next_vertex_id += 1
        self.vertices[vertex.id] = vertex


    def add_vertex_at(self, vertex):
        if self.vertices.get(vertex.id) is None:
            self.vertices[vertex.id] = vertex
        else :
            raise ValueError(f"Vertex with id={vertex.id} already exists in the model.")
    

    def del_vertex(self, vertexID):
        if self.vertices.get(vertexID) is not None:
           self.vertices.pop(vertexID)


    def add_face(self, face):
        self.faces.append(face)


    def del_face(self, face):
        if face in self.faces:
            self.faces.remove(face)
            # update vertices
            for v in (face.v1, face.v2, face.v3):
                vertex = self.vertices.get(v, None)
                if vertex is not None:
                    vertex.remove_face(face)


    def nb_vertices(self):
        return len(self.vertices)


    def nb_faces(self):
        return len(self.faces)

    def export_as_obj(self, obj_name):

        # Path setup
        folder = os.path.join("export", obj_name)
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(
            folder,
            f"{obj_name}_v={self.nb_vertices()}_f={self.nb_faces()}.obj"
        )

        vertices = list(self.vertices.values())
        index_map = {v.id: i + 1 for i, v in enumerate(vertices)}

        with open(filepath, "w") as f:
            # Vertices
            for v in vertices:
                f.write(f"v {v.array[0]} {v.array[1]} {v.array[2]}\n")

            # Faces
            for face in self.faces:
                f.write(f"f {index_map[face.v1]} {index_map[face.v2]} {index_map[face.v3]}\n")

        print("OBJ exported to:", filepath)






# Classe pour gérer les LODs 
class AObject3D:
    def __init__(self, objRef, name=None):
        self.name = name or "Unknown"
        self.model_ref = objRef
        self.model_lods = []
        self.collapse_info = []
    
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

    def show_lods(self, color):
        for idx, lod in enumerate(self.model_lods):
            lod.Show(color, f'LOD {idx + 1} of {self.name}')

    def show_last_lod(self, color):
        self.get_last_lod().Show(color, f'Last LOD of {self.name}')
