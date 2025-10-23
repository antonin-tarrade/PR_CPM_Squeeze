import plotly.graph_objects as go




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
        """
        Compress the mesh by collapsing edges corresponding to a compression ratio.
        Returns (compressed Object3D, transformation info)
        """
        new_obj = copy.deepcopy(Object3D)
        if len(new_obj.vertices) < 4:
            return new_obj, {"note": "Cannot simplify further"}

        target_vertex_count = max(3, int(len(new_obj.vertices) * (1 - compression_ratio)))
        faces = new_obj.faces
        vertices = new_obj.vertices
        transformations = []

        while len(new_obj.vertices) > target_vertex_count and len(new_obj.vertices) >= 4:
            face = random.choice(faces)
            v1, v2, v3 = face.v1, face.v2, face.v3
            collapse_edge = (v1, v2)

            new_v = Vertex(
                (v1.x + v2.x) / 2,
                (v1.y + v2.y) / 2,
                (v1.z + v2.z) / 2,
            )

            # Update all faces that used v1 or v2
            for f in faces:
                if f.v1 in collapse_edge:
                    f.v1 = new_v
                if f.v2 in collapse_edge:
                    f.v2 = new_v
                if f.v3 in collapse_edge:
                    f.v3 = new_v

            # Remove degenerate faces
            faces = [f for f in faces if len({f.v1, f.v2, f.v3}) == 3]

            # Update vertices
            vertices = [v for v in vertices if v not in collapse_edge]
            vertices.append(new_v)

            # Record transformation info
            transformations.append({
                "collapsed_edge": (v1.as_tuple(), v2.as_tuple()),
                "new_vertex": new_v.as_tuple(),
            })

            new_obj.vertices = vertices
            new_obj.faces = faces
            new_obj.nb_vertices = len(vertices)
            new_obj.nb_faces = len(faces)

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


