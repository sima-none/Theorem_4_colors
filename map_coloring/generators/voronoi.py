# generators/voronoi.py
import numpy as np
import random
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from typing import Dict, Set, List

from map_coloring.core.models import Region, ColorMap


class VoronoiBase:
    """Базовый класс для всех генераторов на основе Вороного"""

    def __init__(self, base_cells_count: int = 1000):
        self.base_cells_count = base_cells_count
        self.bounds = Polygon([(-1, -1), (1, -1), (1, 1), (-1, 1)])

    def generate_base_polygons(self, vor) -> Dict[int, Polygon]:
        """Генерирует базовые ячейки Вороного"""
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
        """Строит граф соседства ячеек"""
        neighbors = {i: set() for i in range(self.base_cells_count)}
        for p1, p2 in vor.ridge_points:
            neighbors[p1].add(p2)
            neighbors[p2].add(p1)
        return neighbors

    def has_shared_edge(self, poly1: Polygon, poly2: Polygon) -> bool:
        """Проверяет, делят ли полигоны общее ребро"""
        if not poly1.touches(poly2):
            return False
        inter = poly1.intersection(poly2)
        return inter.geom_type in ['LineString', 'MultiLineString'] and inter.length > 1e-5


class ConvexMapGenerator(VoronoiBase):
    """Вороного: отдельные ячейки (convex)"""

    def get_name(self) -> str:
        return "Voronoi Convex"

    def generate(self) -> ColorMap:
        points = np.random.uniform(-1, 1, (self.base_cells_count, 2))
        vor = Voronoi(points)

        base_polygons = self.generate_base_polygons(vor)
        regions = [Region(id=i, polygon=poly) for i, poly in enumerate(base_polygons.values())]

        print(f"✅ Создано {len(regions)} convex-регионов")
        return ColorMap(regions=regions)


class NonConvexMapGenerator(VoronoiBase):
    """Вороного: объединённые ячейки (non-convex) - как в single файле"""

    def get_name(self) -> str:
        return "Voronoi Non-Convex"

    def generate(self) -> ColorMap:
        print("🔄 Генерация non-convex карты...")

        # 1. Генерируем точки и диаграмму Вороного
        points = np.random.uniform(-1, 1, (self.base_cells_count, 2))
        vor = Voronoi(points)

        # 2. Создаем базовые полигоны
        base_polygons = self.generate_base_polygons(vor)
        cell_neighbors = self.build_cell_neighbors(vor)

        # 3. Объединяем ячейки (как в single файле)
        regions_dict = {i: [i] for i in base_polygons.keys()}

        # Сколько соединений сделать
        total_connections = random.randint(
            int(len(regions_dict) * 0.5),
            int(len(regions_dict) * 0.85)
        )

        connections_made = 0
        max_attempts = total_connections * 10
        attempts = 0

        print(f"🔄 Планируем {total_connections} объединений...")

        while connections_made < total_connections and attempts < max_attempts:
            attempts += 1

            if len(regions_dict) <= 1:
                break

            rand_region_id = random.choice(list(regions_dict.keys()))
            current_cells = regions_dict[rand_region_id]

            # Ищем соседей (как в single файле)
            all_external_neighbors = set()
            for cell in current_cells:
                all_external_neighbors.update(cell_neighbors[cell])
            all_external_neighbors.difference_update(current_cells)

            neighbor_regions = set()
            for neighbor_cell in all_external_neighbors:
                for r_id, r_cells in regions_dict.items():
                    if neighbor_cell in r_cells and r_id != rand_region_id:
                        # Проверяем, что есть общее ребро
                        poly_neighbor = base_polygons[neighbor_cell]
                        has_shared_edge = False
                        for current_cell in current_cells:
                            poly_current = base_polygons[current_cell]
                            if self.has_shared_edge(poly_current, poly_neighbor):
                                has_shared_edge = True
                                break
                        if has_shared_edge:
                            neighbor_regions.add(r_id)
                        break

            if neighbor_regions:
                target_region_id = random.choice(list(neighbor_regions))
                regions_dict[rand_region_id].extend(regions_dict[target_region_id])
                del regions_dict[target_region_id]
                connections_made += 1
                attempts = 0

        print(f"✅ Сделано {connections_made} объединений")

        # 4. Собираем финальные регионы
        regions = []
        for r_id, cells in regions_dict.items():
            polys_to_combine = [base_polygons[idx] for idx in cells if idx in base_polygons]
            if not polys_to_combine:
                continue

            merged = unary_union(polys_to_combine)

            if isinstance(merged, Polygon) and not merged.is_empty:
                regions.append(merged)
            elif isinstance(merged, MultiPolygon):
                for p in merged.geoms:
                    if not p.is_empty:
                        regions.append(p)

        # 5. Убираем перекрытия (как в single файле)
        if len(regions) > 1:
            print("🔄 Обрезаем перекрытия...")
            sorted_regions = sorted(regions, key=lambda p: p.area, reverse=True)
            result = []

            for i, poly in enumerate(sorted_regions):
                current_poly = poly
                for j in range(i + 1, len(sorted_regions)):
                    smaller = sorted_regions[j]
                    if current_poly.contains(smaller):
                        current_poly = current_poly.difference(smaller)
                        if current_poly.is_empty:
                            break

                if not current_poly.is_empty:
                    if current_poly.geom_type == 'MultiPolygon':
                        # Берем самый большой кусок
                        areas = [p.area for p in current_poly.geoms]
                        max_idx = areas.index(max(areas))
                        current_poly = current_poly.geoms[max_idx]
                    result.append(current_poly)

            regions = result

        # 6. Создаем Region объекты
        final_regions = [Region(id=i, polygon=poly) for i, poly in enumerate(regions) if not poly.is_empty]

        print(f"✅ Итоговое количество регионов: {len(final_regions)}")
        return ColorMap(regions=final_regions)