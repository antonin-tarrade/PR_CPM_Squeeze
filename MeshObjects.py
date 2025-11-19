from Compression import squeeze_compression
from Decompression import squeeze_decompression
from utils import *
import trimesh
import numpy as np
import random
import copy
import plotly.graph_objects as go

# Structures de base : Vertex, Face, Object3D




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
            obj, transfo = squeeze_compression(last_lod, compression_ratio)
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

    def show_lods(self):
        for idx, lod in enumerate(self.model_lods):
            lod.Show(f'LOD {idx + 1} of {self.name}')

    def show_last_lod(self):
        self.get_last_lod().Show(f'Last LOD of {self.name}')
