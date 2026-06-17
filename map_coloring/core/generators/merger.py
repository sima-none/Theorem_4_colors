# core/generators/merger.py
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from typing import List, Dict, Set
import random

# Используем относительный импорт от корня пакета
from ..models import Region


class Merger:
    """Логика объединения базовых ячеек в регионы"""

    @staticmethod
    def merge_cells(base_polygons: Dict[int, Polygon],
                    cell_neighbors: Dict[int, Set[int]]) -> Dict[int, List[int]]:
        """Объединяет базовые ячейки в регионы"""
        regions_dict = {i: [i] for i in base_polygons.keys()}
        cell_to_region = {i: i for i in base_polygons.keys()}

        total_connections = random.randint(
            int(len(regions_dict) * 0.5),
            int(len(regions_dict) * 0.85)
        )

        connections_made = 0
        while connections_made < total_connections:
            rand_id = random.choice(list(regions_dict.keys()))
            current_cells = set(regions_dict[rand_id])

            neighbor_regions = Merger._find_eligible_neighbors(
                rand_id, current_cells, regions_dict, base_polygons,
                cell_neighbors, cell_to_region
            )

            if neighbor_regions:
                target_id = random.choice(list(neighbor_regions))
                regions_dict[rand_id].extend(regions_dict[target_id])
                for cell in regions_dict[target_id]:
                    cell_to_region[cell] = rand_id
                del regions_dict[target_id]
                connections_made += 1

        return regions_dict

    @staticmethod
    def _find_eligible_neighbors(region_id: int, current_cells: Set[int],
                                 regions_dict: Dict[int, List[int]],
                                 base_polygons: Dict[int, Polygon],
                                 cell_neighbors: Dict[int, Set[int]],
                                 cell_to_region: Dict[int, int]) -> Set[int]:
        """Находит регионы-соседи через O(1) поиск"""
        all_external_neighbors = set()
        for cell in current_cells:
            all_external_neighbors.update(cell_neighbors[cell])
        all_external_neighbors.difference_update(current_cells)

        neighbor_regions = set()
        for neighbor_cell in all_external_neighbors:
            owner_region = cell_to_region.get(neighbor_cell)
            if owner_region is not None and owner_region != region_id:
                poly_neighbor = base_polygons[neighbor_cell]
                if Merger._has_shared_edge(current_cells, base_polygons, poly_neighbor):
                    neighbor_regions.add(owner_region)

        return neighbor_regions

    @staticmethod
    def _has_shared_edge(cells: Set[int],
                         base_polygons: Dict[int, Polygon],
                         target_poly: Polygon) -> bool:
        """Проверяет общее ребро"""
        for cell in cells:
            poly_current = base_polygons[cell]
            if poly_current.touches(target_poly):
                inter = poly_current.intersection(target_poly)
                if inter.geom_type in ['LineString', 'MultiLineString'] and inter.length > 1e-5:
                    return True
        return False

    @staticmethod
    def build_regions(regions_dict: Dict[int, List[int]],
                      base_polygons: Dict[int, Polygon]) -> List[Region]:
        """Строит регионы из объединённых полигонов"""
        regions = []
        region_id = 0
        for cells in regions_dict.values():
            polys = [base_polygons[idx] for idx in cells if idx in base_polygons]
            if not polys:
                continue

            merged = unary_union(polys)
            if isinstance(merged, Polygon) and not merged.is_empty:
                regions.append(Region(id=region_id, polygon=merged))
                region_id += 1
            elif hasattr(merged, 'geoms'):
                for p in merged.geoms:
                    if not p.is_empty:
                        regions.append(Region(id=region_id, polygon=p))
                        region_id += 1
        return regions

    @staticmethod
    def cut_overlapping_regions(regions: List[Region]) -> List[Region]:
        """Вырезает меньшие области из больших"""
        if len(regions) < 2:
            return regions

        sorted_regions = sorted(regions, key=lambda r: r.polygon.area, reverse=True)
        result = []

        for i, region in enumerate(sorted_regions):
            current_poly = region.polygon
            for j in range(i + 1, len(sorted_regions)):
                smaller = sorted_regions[j]
                if current_poly.contains(smaller.polygon):
                    current_poly = current_poly.difference(smaller.polygon)
                    if current_poly.is_empty:
                        break

            if not current_poly.is_empty:
                if current_poly.geom_type == 'MultiPolygon':
                    current_poly = max(current_poly.geoms, key=lambda p: p.area)
                result.append(Region(id=region.id, polygon=current_poly, color_id=region.color_id))

        for i, region in enumerate(result):
            region.id = i

        return result