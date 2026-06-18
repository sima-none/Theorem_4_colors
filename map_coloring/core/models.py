# core/models.py
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Tuple
from shapely.geometry import Polygon
from shapely.strtree import STRtree
import numpy as np

# ============================================================
#  КОНСТАНТЫ
# ============================================================

COLORS = {
    -1: "lightgray",
    0: "yellow",
    1: "red",
    2: "blue",
    3: "black"
}

KEY_MAP = {"y": 0, "r": 1, "b": 2, "d": 3, "x": -1}

# ✅ Теперь количество цветов можно менять
DEFAULT_COLORS = {0, 1, 2, 3}  # ← можно расширить до {0,1,2,3,4,5}


# ============================================================
#  КЛАСС REGION
# ============================================================

@dataclass
class Region:
    """Представляет одну область на карте"""
    id: int
    polygon: Polygon
    color_id: int = -1

    def __post_init__(self):
        """Проверка валидности полигона"""
        if self.polygon.is_empty:
            raise ValueError(f"Region {self.id} has empty polygon")
        if not self.polygon.is_valid:
            # Пытаемся исправить невалидный полигон
            self.polygon = self.polygon.buffer(0)

    @property
    def color_name(self) -> str:
        return COLORS.get(self.color_id, "unknown")

    @property
    def is_colored(self) -> bool:
        return self.color_id != -1

    @property
    def centroid(self):
        return self.polygon.centroid.coords[0]

    @property
    def area(self) -> float:
        return self.polygon.area


# ============================================================
#  КЛАСС COLORMAP (ОПТИМИЗИРОВАННЫЙ)
# ============================================================

@dataclass
class ColorMap:
    """Основная модель карты с оптимизированной производительностью"""

    regions: List[Region] = field(default_factory=list)
    graph: Dict[int, Set[int]] = field(default_factory=dict)

    # ✅ Добавляем кэшированные значения для производительности
    _uncolored_count: int = field(default=0, init=False)
    _colored_count: int = field(default=0, init=False)
    _region_index: Optional[STRtree] = field(default=None, init=False)
    _region_id_to_idx: Dict[int, int] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Инициализация с оптимизациями"""
        if not self.graph and self.regions:
            self._build_graph_optimized()

        # ✅ Строим индекс для быстрого поиска
        self._build_spatial_index()

        # ✅ Инициализируем счетчики
        self._update_counts()

    # ============================================================
    #  ОПТИМИЗИРОВАННОЕ ПОСТРОЕНИЕ ГРАФА (O(N log N))
    # ============================================================

    def _build_graph_optimized(self):
        """
        Строит граф соседства по ребрам используя STRtree.
        Сложность: O(N log N) вместо O(N²)
        """
        if len(self.regions) < 2:
            self.graph = {i: set() for i in range(len(self.regions))}
            return

        print(f"🔄 Построение графа для {len(self.regions)} регионов...")

        # ✅ Строим пространственный индекс
        polygons = [r.polygon for r in self.regions]
        tree = STRtree(polygons)

        # ✅ Инициализируем граф
        self.graph = {i: set() for i in range(len(self.regions))}

        # ✅ Для каждого полигона ищем возможных соседей через индекс
        checked_pairs = set()

        for i, poly in enumerate(polygons):
            # Находим кандидатов через STRtree (быстро!)
            candidates = tree.query(poly)

            for j in candidates:
                if i == j:
                    continue

                # ✅ Избегаем повторных проверок
                pair_key = tuple(sorted((i, j)))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                # ✅ Проверяем наличие ОБЩЕГО РЕБРА (не точки!)
                if self._shares_edge(poly, polygons[j]):
                    self.graph[i].add(j)
                    self.graph[j].add(i)

        print(f"✅ Граф построен: {sum(len(v) for v in self.graph.values()) // 2} ребер")

    @staticmethod
    def _shares_edge(poly1: Polygon, poly2: Polygon) -> bool:
        """Проверяет, делят ли полигоны общее ребро (не просто точку)"""
        if not poly1.touches(poly2):
            return False
        inter = poly1.intersection(poly2)
        return inter.geom_type in ['LineString', 'MultiLineString'] and inter.length > 1e-5

    # ============================================================
    #  ПРОСТРАНСТВЕННЫЙ ИНДЕКС ДЛЯ БЫСТРОГО ПОИСКА
    # ============================================================

    def _build_spatial_index(self):
        """Строит STRtree для быстрого поиска региона по точке"""
        if not self.regions:
            self._region_index = None
            self._region_id_to_idx = {}
            return

        polygons = [r.polygon for r in self.regions]
        self._region_index = STRtree(polygons)
        self._region_id_to_idx = {r.id: i for i, r in enumerate(self.regions)}

    def get_region_by_point(self, x: float, y: float) -> Optional[int]:
        """Находит регион по координатам точки (O(log N))"""
        from shapely.geometry import Point

        if self._region_index is None or not self.regions:
            return None

        point = Point(x, y)
        # Находим ближайший полигон через STRtree
        nearest_idx = self._region_index.nearest(point)

        # Проверяем, что точка действительно внутри
        if nearest_idx < len(self.regions) and self.regions[nearest_idx].polygon.contains(point):
            return self.regions[nearest_idx].id

        # Если не попали, проверяем все кандидаты (страховка)
        candidates = self._region_index.query(point)
        for idx in candidates:
            if idx < len(self.regions) and self.regions[idx].polygon.contains(point):
                return self.regions[idx].id

        return None

    # ============================================================
    #  УПРАВЛЕНИЕ СЧЕТЧИКАМИ (ОПТИМИЗИРОВАННО)
    # ============================================================

    def _update_counts(self):
        """Обновляет счетчики раскрашенных/не раскрашенных регионов"""
        colored = 0
        for region in self.regions:
            if region.is_colored:
                colored += 1
        self._colored_count = colored
        self._uncolored_count = len(self.regions) - colored

    @property
    def colored_count(self) -> int:
        """Быстрый доступ к количеству раскрашенных регионов"""
        return self._colored_count

    @property
    def uncolored_count(self) -> int:
        """Быстрый доступ к количеству не раскрашенных регионов"""
        return self._uncolored_count

    @property
    def is_complete(self) -> bool:
        """Быстрая проверка (O(1) вместо O(N))"""
        return self._uncolored_count == 0

    @property
    def region_count(self) -> int:
        return len(self.regions)

    @property
    def colored_indices(self) -> List[int]:
        """Возвращает индексы раскрашенных регионов (с кэшированием)"""
        return [i for i, r in enumerate(self.regions) if r.is_colored]

    @property
    def uncolored_indices(self) -> List[int]:
        """Возвращает индексы не раскрашенных регионов (с кэшированием)"""
        return [i for i, r in enumerate(self.regions) if not r.is_colored]

    # ============================================================
    #  БЕЗОПАСНЫЙ ДОСТУП К РЕГИОНАМ
    # ============================================================

    def get_region(self, idx: int) -> Optional[Region]:
        """Безопасное получение региона по индексу"""
        if 0 <= idx < len(self.regions):
            return self.regions[idx]
        return None

    def get_region_by_id(self, region_id: int) -> Optional[Region]:
        """Получение региона по его ID (не по индексу)"""
        idx = self._region_id_to_idx.get(region_id)
        if idx is not None and 0 <= idx < len(self.regions):
            return self.regions[idx]
        return None

    # ============================================================
    #  УПРАВЛЕНИЕ ЦВЕТАМИ (С ОБНОВЛЕНИЕМ СЧЕТЧИКОВ)
    # ============================================================

    def set_color(self, idx: int, color_id: int):
        """Устанавливает цвет региона с обновлением счетчиков"""
        region = self.get_region(idx)
        if region is None:
            return

        old_colored = region.is_colored
        region.color_id = color_id
        new_colored = region.is_colored

        # ✅ Обновляем счетчики
        if old_colored and not new_colored:
            self._colored_count -= 1
            self._uncolored_count += 1
        elif not old_colored and new_colored:
            self._colored_count += 1
            self._uncolored_count -= 1

    def reset_colors(self):
        """Сбрасывает все цвета (O(N))"""
        for region in self.regions:
            region.color_id = -1
        self._colored_count = 0
        self._uncolored_count = len(self.regions)

    # ============================================================
    #  РАБОТА С ЦВЕТАМИ (ГИБКОЕ КОЛИЧЕСТВО)
    # ============================================================

    def get_available_colors(self, region_idx: int, color_set: Set[int] = None) -> Set[int]:
        """
        Возвращает цвета, доступные для региона.
        color_set: множество доступных цветов (по умолчанию DEFAULT_COLORS)
        """
        if color_set is None:
            color_set = DEFAULT_COLORS

        region = self.get_region(region_idx)
        if region is None:
            return set()

        # Собираем цвета соседей
        taken_colors = set()
        for neighbor_idx in self.graph.get(region_idx, set()):
            neighbor = self.get_region(neighbor_idx)
            if neighbor and neighbor.is_colored:
                taken_colors.add(neighbor.color_id)

        return color_set - taken_colors

    def get_available_colors_by_id(self, region_id: int, color_set: Set[int] = None) -> Set[int]:
        """Версия get_available_colors, принимающая region_id вместо индекса"""
        idx = self._region_id_to_idx.get(region_id)
        if idx is None:
            return set()
        return self.get_available_colors(idx, color_set)

    # ============================================================
    #  ПОИСК ПРОБЛЕМ
    # ============================================================

    def find_deadlocks(self, color_set: Set[int] = None) -> List[int]:
        """Находит регионы, у которых нет доступных цветов"""
        if color_set is None:
            color_set = DEFAULT_COLORS

        deadlocks = []
        for idx in self.uncolored_indices:
            if len(self.get_available_colors(idx, color_set)) == 0:
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

    # ============================================================
    #  СТАТИСТИКА
    # ============================================================

    def get_color_stats(self) -> Dict[int, int]:
        """Возвращает статистику использования цветов"""
        stats = {color: 0 for color in DEFAULT_COLORS}
        for region in self.regions:
            if region.is_colored and region.color_id in stats:
                stats[region.color_id] += 1
        return stats

    def get_region_stats(self) -> Dict[str, int]:
        """Возвращает общую статистику по карте"""
        return {
            "total": self.region_count,
            "colored": self._colored_count,
            "uncolored": self._uncolored_count,
            "edges": sum(len(v) for v in self.graph.values()) // 2,
        }

    def print_stats(self):
        """Выводит статистику карты"""
        stats = self.get_region_stats()
        color_stats = self.get_color_stats()

        print("\n" + "=" * 60)
        print("📊 СТАТИСТИКА КАРТЫ")
        print("=" * 60)
        print(f"Всего регионов: {stats['total']}")
        print(f"Раскрашено: {stats['colored']} ({stats['colored'] / stats['total'] * 100:.1f}%)")
        print(f"Не раскрашено: {stats['uncolored']}")
        print(f"Ребер в графе: {stats['edges']}")
        print("-" * 60)
        print("Использование цветов:")
        for color_id, count in color_stats.items():
            if count > 0:
                print(f"  {COLORS.get(color_id, 'unknown')}: {count}")
        print("=" * 60 + "\n")