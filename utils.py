import numpy as np


class Vertex:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
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
    def __init__(self, v1, v2, v3):
        self.v1, self.v2, self.v3 = v1, v2, v3



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