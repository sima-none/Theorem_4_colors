# rules/priority.py
from typing import Optional, Tuple, List
import random
from .base import Rule, DefaultRuleSelector


class PriorityRuleBase(Rule):
    """
    Базовый класс для всех приоритетных правил.
    Содержит общую логику выбора и сортировки.
    """

    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        candidates = self._find_candidates(colormap)

        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0], self.name

        return self._select_by_default(colormap, candidates)

    def _find_candidates(self, colormap) -> List[int]:
        raise NotImplementedError

    def _select_by_default(self, colormap, candidates: List[int]) -> Tuple[int, str]:
        """✅ Использует DefaultRuleSelector для разрешения конфликтов"""
        default_type = DefaultRuleSelector.get_default_type()

        if default_type == "descending":
            return candidates[0], f"{self.name} → first"
        elif default_type == "ascending":
            return candidates[-1], f"{self.name} → last"
        else:  # "random"
            return random.choice(candidates), f"{self.name} → random"


class FirstPriorityRule(PriorityRuleBase):
    """Правило №1: области со степенью свободы = 1"""

    @property
    def name(self) -> str:
        return "first_priority"

    def _find_candidates(self, colormap) -> List[int]:
        candidates = []
        for idx in colormap.uncolored_indices:
            if len(colormap.get_available_colors(idx)) == 1:
                candidates.append(idx)
        return candidates


class SecondPriorityRule(PriorityRuleBase):
    """Правило №2: области, у закрашенных соседей которых остался 1 неокрашенный сосед"""

    @property
    def name(self) -> str:
        return "second_priority"

    def _find_candidates(self, colormap) -> List[int]:
        candidates = []
        graph = colormap.graph
        regions = colormap.regions

        for colored_idx in colormap.colored_indices:
            neighbors = graph.get(colored_idx, set())
            gray_neighbors = [n for n in neighbors if not regions[n].is_colored]
            if len(gray_neighbors) == 1:
                candidates.append(gray_neighbors[0])
        return candidates


class ThirdPriorityRule(PriorityRuleBase):
    """Правило №3: области, у которых ровно 3 закрашенных соседа"""

    @property
    def name(self) -> str:
        return "third_priority"

    def _find_candidates(self, colormap) -> List[int]:
        candidates = []
        graph = colormap.graph
        regions = colormap.regions

        for idx in colormap.uncolored_indices:
            neighbors = graph.get(idx, set())
            colored_neighbors = sum(1 for n in neighbors if regions[n].is_colored)
            if colored_neighbors == 3:
                candidates.append(idx)
        return candidates