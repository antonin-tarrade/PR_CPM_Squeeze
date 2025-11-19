import numpy as np


class Vertex:
    def __init__(self, x, y, z, id):
        self.x, self.y, self.z = x, y, z
        self.id = id

    def as_tuple(self):
        return (self.x, self.y, self.z)
    
    def as_array(self):
        return np.array(self.as_tuple())
    
    # hash and eq to use Vertex as dict keys
    def __hash__(self):
        return hash((self.x, self.y, self.z))
    
    # def __str__(self):
    #     return f"Vertex({self.x}, {self.y}, {self.z})"
    
    def __eq__(self, other):
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)



class Face:
    def __init__(self, id_v1, id_v2, id_v3):
        if not isinstance(id_v1, int) or not isinstance(id_v2, int) or not isinstance(id_v3, int):
            raise ValueError("Face vertices must be identified by integer IDs.")
        self.id_v1, self.id_v2, self.id_v3 = id_v1, id_v2, id_v3



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
    return np.mean(coords, axis=0)


def get_vertex_from_array(vertices, arr):
    for v in vertices:
        if np.allclose(v.as_array(), arr, atol=1e-7):
            return v
    return None