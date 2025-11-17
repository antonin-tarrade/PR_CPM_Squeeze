class Vertex:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
    def as_tuple(self):
        return (self.x, self.y, self.z)



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


