# core/generators/triangles.py
import random
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from typing import Dict

from ..models import Region, ColorMap


class TrianglesBase:
    """Базовый класс для всех генераторов на основе треугольников"""

    def __init__(self, base_cells_count: int = 1000):
        self.base_cells_count = base_cells_count
        self.side_len = 0.12

    def generate_triangles(self) -> Dict[int, Dict]:
        triangles = {}
        cell_id = 0

        dx = self.side_len
        dy = self.side_len * np.sqrt(3) / 2
        X_MIN, X_MAX = -1.2, 1.2
        Y_MIN, Y_MAX = -1.2, 1.2
        grid_matrix = {}

        row = 0
        y = Y_MIN
        while y < Y_MAX:
            x_offset = 0.0 if row % 2 == 0 else -dx / 2
            col = 0
            x = X_MIN + x_offset
            while x < X_MAX:
                # Треугольник вершиной ВВЕРХ
                p1 = (x, y)
                p2 = (x + dx, y)
                p3 = (x + dx / 2, y + dy)
                poly_up = Polygon([p1, p2, p3])
                if -1 <= poly_up.centroid.x <= 1 and -1 <= poly_up.centroid.y <= 1:
                    grid_matrix[(row, col, 0)] = cell_id
                    triangles[cell_id] = {"poly": poly_up, "neighbors": set()}
                    cell_id += 1

                # Треугольник вершиной ВНИЗ
                p4 = (x + dx / 2, y + dy)
                p5 = (x + 3 * dx / 2, y + dy)
                p6 = (x + dx, y)
                poly_down = Polygon([p4, p5, p6])
                if -1 <= poly_down.centroid.x <= 1 and -1 <= poly_down.centroid.y <= 1:
                    grid_matrix[(row, col, 1)] = cell_id
                    triangles[cell_id] = {"poly": poly_down, "neighbors": set()}
                    cell_id += 1

                x += dx
                col += 1
            y += dy
            row += 1

        self._build_neighbors(triangles, grid_matrix)
        return triangles

    def _build_neighbors(self, triangles: Dict, grid_matrix: Dict):
        for (r, c, o), i in grid_matrix.items():
            if o == 0:
                if (r, c, 1) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(r, c, 1)])
                if (r, c - 1, 1) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(r, c - 1, 1)])
                neighbor_row = r - 1
                neighbor_col = c if r % 2 == 0 else c + 1
                if (neighbor_row, neighbor_col, 1) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(neighbor_row, neighbor_col, 1)])
            else:
                if (r, c, 0) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(r, c, 0)])
                if (r, c + 1, 0) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(r, c + 1, 0)])
                neighbor_row = r + 1
                neighbor_col = c if r % 2 == 0 else c - 1
                if (neighbor_row, neighbor_col, 0) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(neighbor_row, neighbor_col, 0)])


class TrianglesConvexGenerator(TrianglesBase):
    """Треугольники: отдельные треугольники (convex)"""

    def get_name(self) -> str:
        return "Triangles Convex"

    def generate(self) -> ColorMap:
        triangles = self.generate_triangles()
        regions = [Region(id=tri_id, polygon=data["poly"]) for tri_id, data in triangles.items()]
        return ColorMap(regions=regions)


class TrianglesNonConvexGenerator(TrianglesBase):
    """Треугольники: объединённые группы треугольников (non-convex)"""

    def __init__(self, base_cells_count: int = 1000):
        super().__init__(base_cells_count)
        self.num_figures = 18
        self.cells_per_fig = 25

    def get_name(self) -> str:
        return "Triangles Non-Convex"

    def generate(self) -> ColorMap:
        triangles = self.generate_triangles()
        for tri_id in triangles:
            triangles[tri_id]["assigned"] = False

        figures = self._grow_figures(triangles)
        regions = [Region(id=i, polygon=poly) for i, poly in enumerate(figures) if not poly.is_empty]
        return ColorMap(regions=regions)

    def _grow_figures(self, triangles: dict) -> list:
        figures = []

        for _ in range(self.num_figures):
            available = [k for k, v in triangles.items() if not v["assigned"]]
            if not available:
                break

            start_cell = random.choice(available)
            current_cluster = [start_cell]
            triangles[start_cell]["assigned"] = True
            growth_front = set(triangles[start_cell]["neighbors"])

            for _ in range(self.cells_per_fig - 1):
                valid_front = [c for c in growth_front if c in triangles and not triangles[c]["assigned"]]
                if not valid_front:
                    break
                next_cell = random.choice(valid_front)
                current_cluster.append(next_cell)
                triangles[next_cell]["assigned"] = True
                growth_front.update(triangles[next_cell]["neighbors"])

            polygons_to_union = [triangles[c]["poly"] for c in current_cluster]
            merged_poly = unary_union(polygons_to_union)

            if isinstance(merged_poly, MultiPolygon):
                for part in merged_poly.geoms:
                    figures.append(part)
            elif isinstance(merged_poly, Polygon):
                figures.append(merged_poly)

        for k, v in triangles.items():
            if not v["assigned"]:
                figures.append(v["poly"])

        return figures