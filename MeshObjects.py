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
    
    def decompress(self, nb_decompressions=None):
        # Si rien à décompresser
        if len(self.model_lods) == 0:
            return self.model_ref

        # Combien d'étapes ?
        if nb_decompressions is None:
            nb_decompressions = self.get_nb_of_lods()

        # On part du modèle le plus compressé M_min (dernier LOD stocké)
        new_mesh = self.get_last_lod()

        # Récupération des infos de collapses correspondantes
        collapse_info = self.collapse_info[-nb_decompressions:]

        # On applique les décompressions dans l’ordre inverse
        for infos in reversed(collapse_info):
            new_mesh = squeeze_decompression(new_mesh, infos)

        return new_mesh

    def show_lods(self):
        for idx, lod in enumerate(self.model_lods):
            lod.Show(f'LOD {idx + 1} of {self.name}')

    def show_last_lod(self):
        self.get_last_lod().Show(f'Last LOD of {self.name}')
