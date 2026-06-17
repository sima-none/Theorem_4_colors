# models.py
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from shapely.geometry import Polygon
import numpy as np

COLORS = {
    -1: "lightgray",
    0: "yellow",
    1: "red",
    2: "blue",
    3: "black"
}

KEY_MAP = {"y": 0, "r": 1, "b": 2, "d": 3, "x": -1}


@dataclass
class Region:
    """Представляет одну область на карте"""
    id: int
    polygon: Polygon
    color_id: int = -1

    def __post_init__(self):
        if self.polygon.is_empty:
            raise ValueError(f"Region {self.id} has empty polygon")

    @property
    def color_name(self) -> str:
        return COLORS.get(self.color_id, "unknown")

    @property
    def is_colored(self) -> bool:
        return self.color_id != -1

    @property
    def centroid(self):
        return self.polygon.centroid.coords[0]


@dataclass
class ColorMap:
    """Основная модель карты"""
    regions: List[Region] = field(default_factory=list)
    graph: Dict[int, Set[int]] = field(default_factory=dict)

    def __post_init__(self):
        if not self.graph and self.regions:
            self._build_graph()

    def _build_graph(self):
        """Строит граф соседства по ребрам (не по углам)"""
        self.graph = {i: set() for i in range(len(self.regions))}
        for i in range(len(self.regions)):
            for j in range(i + 1, len(self.regions)):
                if self._shares_edge(self.regions[i].polygon, self.regions[j].polygon):
                    self.graph[i].add(j)
                    self.graph[j].add(i)

    @staticmethod
    def _shares_edge(poly1: Polygon, poly2: Polygon) -> bool:
        """Проверяет, делят ли полигоны общее ребро (не просто точку)"""
        if not poly1.touches(poly2):
            return False
        inter = poly1.intersection(poly2)
        return inter.geom_type in ['LineString', 'MultiLineString'] and inter.length > 1e-5

    @property
    def region_count(self) -> int:
        return len(self.regions)

    @property
    def colored_indices(self) -> List[int]:
        return [i for i, r in enumerate(self.regions) if r.is_colored]

    @property
    def uncolored_indices(self) -> List[int]:
        return [i for i, r in enumerate(self.regions) if not r.is_colored]

    @property
    def is_complete(self) -> bool:
        return all(r.is_colored for r in self.regions)

    def get_available_colors(self, region_idx: int) -> Set[int]:
        """Возвращает цвета, доступные для региона"""
        all_colors = {0, 1, 2, 3}
        taken_colors = {
            self.regions[n].color_id
            for n in self.graph.get(region_idx, set())
            if self.regions[n].is_colored
        }
        return all_colors - taken_colors

    def get_region(self, idx: int) -> Region:
        return self.regions[idx]

    def set_color(self, idx: int, color_id: int):
        if 0 <= idx < len(self.regions):
            self.regions[idx].color_id = color_id

    def reset_colors(self):
        for region in self.regions:
            region.color_id = -1

    def find_deadlocks(self) -> List[int]:
        """Находит регионы, у которых нет доступных цветов"""
        deadlocks = []
        for idx in self.uncolored_indices:
            if len(self.get_available_colors(idx)) == 0:
                deadlocks.append(idx)
        return deadlocks

    def get_frontier_regions(self) -> List[int]:
        """Возвращает неокрашенные регионы, граничащие с окрашенными"""
        colored_set = set(self.colored_indices)
        frontier = []
        for idx in self.uncolored_indices:
            if self.graph.get(idx, set()) & colored_set:
                frontier.append(idx)
        return frontier