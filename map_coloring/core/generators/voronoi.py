# core/generators/voronoi.py
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon
from typing import Dict, Set

from .merger import Merger
from ..models import Region, ColorMap



class VoronoiBase:
    """Базовый класс для всех генераторов на основе Вороного"""

    def __init__(self, base_cells_count: int = 1000):
        self.base_cells_count = base_cells_count
        self.bounds = Polygon([(-1, -1), (1, -1), (1, 1), (-1, 1)])

    def generate_base_polygons(self) -> Dict[int, Polygon]:
        points = np.random.uniform(-1, 1, (self.base_cells_count, 2))
        vor = Voronoi(points)

        base_polygons = {}
        for i, reg_idx in enumerate(vor.point_region):
            region = vor.regions[reg_idx]
            if not region or -1 in region:
                continue
            coords = [vor.vertices[v] for v in region]
            poly = Polygon(coords)
            clipped = poly.intersection(self.bounds)
            if not clipped.is_empty and isinstance(clipped, Polygon):
                base_polygons[i] = clipped
        return base_polygons

    def build_cell_neighbors(self, vor) -> Dict[int, Set[int]]:
        neighbors = {i: set() for i in range(self.base_cells_count)}
        for p1, p2 in vor.ridge_points:
            neighbors[p1].add(p2)
            neighbors[p2].add(p1)
        return neighbors


class ConvexMapGenerator(VoronoiBase):
    """Вороного: отдельные ячейки (convex)"""

    def get_name(self) -> str:
        return "Voronoi Convex"

    def generate(self) -> ColorMap:
        base_polygons = self.generate_base_polygons()
        regions = [Region(id=i, polygon=poly) for i, poly in enumerate(base_polygons.values())]
        return ColorMap(regions=regions)


class NonConvexMapGenerator(VoronoiBase):
    """Вороного: объединённые ячейки (non-convex)"""

    def get_name(self) -> str:
        return "Voronoi Non-Convex"

    def generate(self) -> ColorMap:
        points = np.random.uniform(-1, 1, (self.base_cells_count, 2))
        vor = Voronoi(points)
        base_polygons = self.generate_base_polygons()
        cell_neighbors = self.build_cell_neighbors(vor)

        regions_dict = Merger.merge_cells(base_polygons, cell_neighbors)
        regions = Merger.build_regions(regions_dict, base_polygons)
        regions = Merger.cut_overlapping_regions(regions)

        return ColorMap(regions=regions)