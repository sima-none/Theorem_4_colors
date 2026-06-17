# core/generators/triangles.py
import random
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from typing import Dict, List

from map_coloring.core.models import Region, ColorMap


class TrianglesBase:
    """Базовый класс для всех генераторов на основе треугольников"""

    def __init__(self, base_cells_count: int = 1000):
        self.base_cells_count = base_cells_count
        self.side_len = 0.12

    def generate_triangles(self) -> Dict[int, Dict]:
        """Генерирует треугольную сетку 60-60-60"""
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
                    triangles[cell_id] = {"poly": poly_up, "neighbors": set(), "assigned": False}
                    cell_id += 1

                # Треугольник вершиной ВНИЗ
                p4 = (x + dx / 2, y + dy)
                p5 = (x + 3 * dx / 2, y + dy)
                p6 = (x + dx, y)
                poly_down = Polygon([p4, p5, p6])
                if -1 <= poly_down.centroid.x <= 1 and -1 <= poly_down.centroid.y <= 1:
                    grid_matrix[(row, col, 1)] = cell_id
                    triangles[cell_id] = {"poly": poly_down, "neighbors": set(), "assigned": False}
                    cell_id += 1

                x += dx
                col += 1
            y += dy
            row += 1

        # Строим граф соседей
        for (r, c, o), i in grid_matrix.items():
            if o == 0:  # Вершиной вверх
                if (r, c, 1) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(r, c, 1)])
                if (r, c - 1, 1) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(r, c - 1, 1)])
                neighbor_row = r - 1
                neighbor_col = c if r % 2 == 0 else c + 1
                if (neighbor_row, neighbor_col, 1) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(neighbor_row, neighbor_col, 1)])
            else:  # Вершиной вниз
                if (r, c, 0) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(r, c, 0)])
                if (r, c + 1, 0) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(r, c + 1, 0)])
                neighbor_row = r + 1
                neighbor_col = c if r % 2 == 0 else c - 1
                if (neighbor_row, neighbor_col, 0) in grid_matrix:
                    triangles[i]["neighbors"].add(grid_matrix[(neighbor_row, neighbor_col, 0)])

        return triangles


class TrianglesConvexGenerator(TrianglesBase):
    """Треугольники: отдельные треугольники (convex)"""

    def get_name(self) -> str:
        return "Triangles Convex"

    def generate(self) -> ColorMap:
        triangles = self.generate_triangles()
        regions = [Region(id=tri_id, polygon=data["poly"]) for tri_id, data in triangles.items()]
        return ColorMap(regions=regions)


class TrianglesNonConvexGenerator(TrianglesBase):
    """Треугольники: объединённые группы треугольников (non-convex) - как в single файле"""

    def __init__(self, base_cells_count: int = 1000):
        super().__init__(base_cells_count)
        self.num_figures = 18
        self.cells_per_fig = 25

    def get_name(self) -> str:
        return "Triangles Non-Convex"

    def generate(self) -> ColorMap:
        print("🔄 Генерация triangles non-convex карты...")

        triangles = self.generate_triangles()

        # Пошаговое выращивание фигур (как в single файле)
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

        # Добавляем оставшиеся одиночные треугольники
        for k, v in triangles.items():
            if not v["assigned"]:
                figures.append(v["poly"])

        regions = [Region(id=i, polygon=poly) for i, poly in enumerate(figures) if not poly.is_empty]

        print(f"✅ Итоговое количество регионов: {len(regions)}")
        return ColorMap(regions=regions)