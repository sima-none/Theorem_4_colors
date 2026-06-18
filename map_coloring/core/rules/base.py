# rules/base.py
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Union
import random


class Rule(ABC):
    @abstractmethod
    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class DefaultRule(Rule):
    """
    order: "colors dead_min alive_max last" и т.д.
    Доступные: colors, dead_min, dead_max, alive_min, alive_max, last, random
    """

    def __init__(self,
                 order: Union[str, List[str]] = "colors dead_min alive_max",
                 mode: str = "connected",
                 fallback_to_alone: bool = True):

        if isinstance(order, str):
            self.order_list = order.split() if order else []
        else:
            self.order_list = order.copy() if order else []

        # ✅ ДОБАВЛЯЕМ "last" В СПИСОК ДОСТУПНЫХ!
        valid = {"colors", "dead_min", "dead_max", "alive_min", "alive_max", "last", "random"}
        for p in self.order_list:
            if p not in valid:
                raise ValueError(f"wtf: {p}. Можно: {valid}")

        self.mode = mode
        self.fallback_to_alone = fallback_to_alone
        self._name = "_".join(self.order_list) if self.order_list else "empty"

    @property
    def name(self) -> str:
        return self._name

    def _filter(self, colormap, indices):
        if self.mode == "alone":
            return indices
        filtered = []
        for idx in indices:
            if any(colormap.regions[n].is_colored for n in colormap.graph.get(idx, set())):
                filtered.append(idx)
        return filtered if filtered or not self.fallback_to_alone else indices

    def _weight(self, colormap, idx, key):
        n = colormap.graph.get(idx, set())
        if key == "colors":
            return len(colormap.get_available_colors(idx))
        elif key == "dead_min":
            return sum(1 for x in n if not colormap.regions[x].is_colored)
        elif key == "dead_max":
            return -sum(1 for x in n if not colormap.regions[x].is_colored)
        elif key == "alive_min":
            return sum(1 for x in n if colormap.regions[x].is_colored)
        elif key == "alive_max":
            return -sum(1 for x in n if colormap.regions[x].is_colored)
        elif key == "last":
            # ✅ ВОЗВРАЩАЕМ LOGIC ДЛЯ "last"!
            colored_neighbors = [x for x in n if colormap.regions[x].is_colored]
            if not colored_neighbors:
                return 0
            last_value = float('inf')
            for neighbor_idx in colored_neighbors:
                neighbor_neighbors = colormap.graph.get(neighbor_idx, set())
                uncolored_count = sum(1 for x in neighbor_neighbors if not colormap.regions[x].is_colored)
                last_value = min(last_value, uncolored_count)
            return last_value if last_value != float('inf') else 0
        elif key == "random":
            return random.random()
        return 0

    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        if not colormap.uncolored_indices:
            return None

        candidates = self._filter(colormap, colormap.uncolored_indices)
        if not candidates:
            return None

        if not self.order_list:
            return candidates[0], "first"
        if len(self.order_list) == 1 and self.order_list[0] == "random":
            return random.choice(candidates), "random"

        current = candidates
        for i, key in enumerate(self.order_list):
            w = [(idx, self._weight(colormap, idx, key)) for idx in current]
            w.sort(key=lambda x: x[1])
            min_w = w[0][1]
            current = [idx for idx, val in w if val == min_w]
            if len(current) == 1:
                return current[0], "_".join(self.order_list[:i + 1])

        return current[0], "_".join(self.order_list) + "_tie"


class DefaultRuleSelector:
    """
    Глобальный селектор для разрешения конфликтов при равных кандидатах.

    Режимы:
    - "descending": всегда выбирать ПЕРВОГО в списке (детерминированно)
    - "ascending": всегда выбирать ПОСЛЕДНЕГО в списке (детерминированно)
    - "random": выбирать СЛУЧАЙНОГО из равных
    """
    _default_type: str = "descending"

    @classmethod
    def set_default(cls, rule_type: str):
        if rule_type in ["descending", "ascending", "random"]:
            cls._default_type = rule_type
        else:
            raise ValueError(f"Неизвестный тип: {rule_type}. Доступные: descending, ascending, random")

    @classmethod
    def get_default_type(cls) -> str:
        return cls._default_type