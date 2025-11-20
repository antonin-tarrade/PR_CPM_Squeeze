import numpy as np


class Vertex:
    def __init__(self, array):
        self.array = array 
        self.id = None
        self.faces = []

    def set_id(self, id):
        self.id = id

    def add_face(self, face):
        if face not in self.faces:
            self.faces.append(face)
            
    def remove_face(self, face):
        if face in self.faces:
            self.faces.remove(face)

    def get_neighbors(self):
        vid = self.id

        next_of = {}
        prev_of = {}

        for face in self.faces:
            ids = [face.v1, face.v2, face.v3]
            if vid not in ids:
                continue
            i = ids.index(vid)
            u = ids[(i + 1) % 3]
            w = ids[(i + 2) % 3]
            next_of[u] = w
            prev_of[w] = u

        if not next_of:
            return []

        # -------- try CLOSED ring first --------
        start = next(iter(next_of.keys()))
        ordered = []
        cur = start
        visited = set()

        while True:
            ordered.append(cur)
            visited.add(cur)
            cur = next_of.get(cur, None)

            if cur is None:
                break                     # open boundary
            if cur == start:
                return ordered            # closed ring
            if cur in visited:
                break                     # corrupted but closed attempt failed

        # -------- open boundary fallback --------
        boundary_starts = [u for u in next_of.keys() if u not in prev_of]
        if boundary_starts:
            start = boundary_starts[0]

        ordered = []
        cur = start
        visited = set()
        while cur is not None and cur not in visited:
            ordered.append(cur)
            visited.add(cur)
            cur = next_of.get(cur, None)

        return ordered



class Face:
    def __init__(self,id1,id2,id3,face_id):
        self.v1 = id1
        self.v2 = id2
        self.v3 = id3
        self.id = face_id


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
    coords = [np.array(v.array) for v in vertices]
    mean_coords = np.mean(coords, axis=0)
    return mean_coords
