import plotly.graph_objects as go
import numpy as np



# ---------------------------------- AObject3D ---------------------------------
import random
import copy

class AObject3D:
    def __init__(self, objRef, name=None):
        self.name = name if name is not None else "Unknown"
        self.model_ref = objRef
        self.model_lods = []
        self.tranformations = []
        self.nb_lod = 0

    def get_last_lod(self):
        return self.model_ref if len(self.model_lods) == 0 else self.model_lods[-1]

    def compress(self, compression_ratio=0.1, nb_compressions=1):
        """
        Perform multiple squeeze compression passes.
        compression_ratio: fraction of vertices to remove per pass (0 < ratio < 1)
        nb_compressions: number of compression passes
        """
        for _ in range(nb_compressions):
            last_lod = self.get_last_lod()
            obj, transfo = self.squeeze_compression(last_lod, compression_ratio)
            self.tranformations.append(transfo)
            self.model_lods.append(obj)
        return self.model_lods, self.tranformations


    def squeeze_compression(self, Object3D, compression_ratio=0.1):
        new_obj = copy.deepcopy(Object3D)


        target_vertex_count = max(3, int(len(new_obj.vertices) * (1 - compression_ratio)))
        faces = new_obj.faces
        vertices = new_obj.vertices
        transformations = []

        def edge_length(edge):
            p1 = np.array(edge.v1.as_tuple())
            p2 = np.array(edge.v2.as_tuple())
            return np.linalg.norm(p1 - p2)

        def all_edges():
            edges = set()
            for f in faces:
                edges.add(Edge(f.v1, f.v2))
                edges.add(Edge(f.v2, f.v3))
                edges.add(Edge(f.v3, f.v1))
            return list(edges)
        

        edges = all_edges()
        print(edges)
        # Trier la liste
        sorted_edge = edges.sort(key=lambda e: edge_length(e))
        print(sorted_edge)

        edge_index = 0
        # boucle de collapses simples
        while len(vertices) > target_vertex_count:

            collapse_edge = sorted_edge[edge_index];
            v1, v2 = collapse_edge

            #  calculer la prédiction du sommet supprimé (par exemple barycentre local)
            connected_faces = [f for f in faces if v2 in [f.v1, f.v2, f.v3]]
            if connected_faces:
                bary = np.mean([np.array([(f.v1.x + f.v2.x + f.v3.x)/3,
                                            (f.v1.y + f.v2.y + f.v3.y)/3,
                                            (f.v1.z + f.v2.z + f.v3.z)/3])
                                for f in connected_faces], axis=0)
            else:
                bary = np.array(v1.as_tuple())

            v2_pos = np.array(v2.as_tuple())
            v_est = bary - v2_pos   # erreur prédictive (petite normalement)

            v_split = v1
            v_del = v2

            faces_to_remove = []
            for f in faces:
                # remplacer del_v par keep_v
                if f.v1 is v_del:
                    f.v1 = v_split
                if f.v2 is v_del:
                    f.v2 = v_split
                if f.v3 is v_del:
                    f.v3 = v_split

                # si la face est devenue dégénérée (2 mêmes sommets), on la vire
                if len({f.v1, f.v2, f.v3}) < 3:
                    faces_to_remove.append(f)

            # supprimer les faces dégénérées
            for f in faces_to_remove:
                faces.remove(f)

            # 4. retirer v_del de la liste des vertices
            if v_del in vertices:
                vertices.remove(v_del)

            # 5. enregistrer la transformation pour un éventuel vsplit
            transformations.append({
                "V_split" : v_split,
                "V_est" : v_est,
                "Collapse_edge" : collapse_edge
            })

            # mettre à jour les infos de l'objet
            new_obj.vertices = vertices
            new_obj.faces = faces
            new_obj.nb_vertices = len(vertices)
            new_obj.nb_faces = len(faces)
            edge_index += 1

        transfo = {
            "compression_ratio": compression_ratio,
            "transformations": transformations,
            "removed_vertices": len(Object3D.vertices) - len(new_obj.vertices),
        }
        return new_obj, transfo



    def show_lods(self):
        for idx, lod in enumerate(self.model_lods):
            lod.Show(f'LOD {idx + 1} of {self.name}')

    def show_last_lod(self):
        self.get_last_lod().Show(f'Last LOD of {self.name}')
        
  



# ---------------------------------- Object3D ----------------------------------
class Object3D :

    def __init__(self, objFile, name = None) :
        self.name = name if name is not None else "Unknown"
        vertices = []
        faces = []

        for line in objFile:
            if line.startswith('v '):  # vertex
                parts = line.strip().split()
                vertices.append(Vertex(float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith('f '):  # face
                parts = line.strip().split()

                face = Face(*[vertices[int(p) - 1] for p in parts[1:]])
                faces.append(face)
        self.vertices = vertices
        self.faces = faces
        self.nb_faces = len(faces)
        self.nb_vertices = len(vertices)

    def Show(self,title = None) :
        if title is None : title = f"3D Object : {self.name}"
        x, y, z = zip(*[v.as_tuple() for v in self.vertices])

        # Map vertices to indices for faces
        vertex_to_index = {v: idx for idx, v in enumerate(self.vertices)}
        i = [vertex_to_index[f.v1] for f in self.faces]
        j = [vertex_to_index[f.v2] for f in self.faces]
        k = [vertex_to_index[f.v3] for f in self.faces]

        fig = go.Figure(
            data=[
                go.Mesh3d(
                    x=x, y=y, z=z,
                    i=i, j=j, k=k,
                    color='#9575CD',
                    opacity=1.0,
                    flatshading=True
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

# ----------------------------------- Vertex -----------------------------------
class Vertex :
    def __init__(self,x,y,z) :
        self.x = x
        self.y = y
        self.z = z

    def as_tuple(self) :
        return (self.x,self.y,self.z)

# ------------------------------------ Face ------------------------------------
class Face :
    def __init__(self,v1,v2,v3) :
            self.v1 = v1
            self.v2 = v2
            self.v3 = v3

class Edge :
    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2
