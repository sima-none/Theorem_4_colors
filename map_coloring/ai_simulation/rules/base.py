# rules/base.py
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Set, Dict, Union
import random


class Rule(ABC):
    """Базовый абстрактный класс для всех правил"""

    @abstractmethod
    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class DefaultRule(Rule):
    """
    Базовое правило выбора региона с ГИБКИМИ ПРИОРИТЕТАМИ.

    Параметры:
    - neighbors: "min" или "max"
      Влияет ТОЛЬКО на сортировку по "neighbors" в приоритете.
      - "min": чем МЕНЬШЕ неокрашенных соседей, тем ВЫШЕ приоритет
      - "max": чем БОЛЬШЕ неокрашенных соседей, тем ВЫШЕ приоритет

    - priority: список приоритетов в порядке важности (пробел как разделитель).
      Доступные: "colors", "neighbors", "last", "random"

      "colors"   → область с НАИМЕНЬШИМ количеством доступных цветов
      "neighbors"→ область с НАИМЕНЬШИМ (или НАИБОЛЬШИМ, зависит от neighbors)
                   количеством неокрашенных соседей
      "last"     → область с НАИМЕНЬШИМ значением "последнего" соседа
      "random"   → может быть в любом месте:
                   - если в списке → случайный выбор среди текущих кандидатов
                   - если единственный → полностью случайный выбор
                   - если в середине → случайный выбор среди равных по предыдущим

    - mode: "connected" (только области с закрашенным соседом) или "alone" (можно любые)
    - fallback_to_alone: если mode="connected" не нашел кандидатов, использовать mode="alone"
    """

    def __init__(self,
                 neighbors: Optional[str] = None,
                 priority: Union[str, List[str]] = "colors neighbors",
                 mode: str = "connected",
                 fallback_to_alone: bool = True):

        # Преобразуем строку в список
        if isinstance(priority, str):
            self.priority_list = priority.split() if priority else []
        else:
            self.priority_list = priority.copy() if priority else []

        # Валидация
        valid_priorities = {"colors", "neighbors", "last", "random"}
        for p in self.priority_list:
            if p not in valid_priorities:
                raise ValueError(f"Неизвестный приоритет: {p}. Доступные: {valid_priorities}")

        if neighbors not in [None, "min", "max"]:
            raise ValueError(f"neighbors должен быть 'min', 'max' или None, получено: {neighbors}")

        self.neighbors = neighbors
        self.mode = mode
        self.fallback_to_alone = fallback_to_alone
        self._name = self._generate_name()

    def _generate_name(self) -> str:
        parts = []

        # Приоритеты
        priority_str = "_".join(self.priority_list) if self.priority_list else "empty"
        parts.append(priority_str)

        # Соседи (только если есть "neighbors" в приоритетах)
        if "neighbors" in self.priority_list:
            if self.neighbors == "min":
                parts.append("neighbors↑")
            elif self.neighbors == "max":
                parts.append("neighbors↓")

        # Режим
        if self.mode == "connected":
            parts.append("conn")
        elif self.mode == "alone":
            parts.append("alone")

        if self.fallback_to_alone:
            parts.append("fallback")

        return "_".join(parts)

    @property
    def name(self) -> str:
        return self._name

    def _filter_candidates(self, colormap, indices: List[int]) -> List[int]:
        """Фильтрует кандидатов по mode"""
        if self.mode == "alone":
            return indices

        filtered = []
        for idx in indices:
            neighbors = colormap.graph.get(idx, set())
            if any(colormap.regions[n].is_colored for n in neighbors):
                filtered.append(idx)

        if not filtered and self.fallback_to_alone:
            return indices

        return filtered

    def _calculate_weight(self, colormap, idx: int, priority_key: str) -> float:
        """
        ✅ Вычисляет ТОЛЬКО ОДИН вес для конкретного приоритета.
        Это позволяет вычислять веса постепенно, а не все сразу.
        """
        graph = colormap.graph
        regions = colormap.regions

        if priority_key == "colors":
            return len(colormap.get_available_colors(idx))

        elif priority_key == "neighbors":
            neighbors_set = graph.get(idx, set())
            return sum(1 for n in neighbors_set if not regions[n].is_colored)

        elif priority_key == "last":
            neighbors_set = graph.get(idx, set())
            colored_neighbors = [n for n in neighbors_set if regions[n].is_colored]

            if not colored_neighbors:
                return 0

            last_value = float('inf')
            for neighbor_idx in colored_neighbors:
                neighbor_neighbors = graph.get(neighbor_idx, set())
                uncolored_count = sum(1 for n in neighbor_neighbors if not regions[n].is_colored)
                last_value = min(last_value, uncolored_count)

            return last_value if last_value != float('inf') else 0

        elif priority_key == "random":
            return random.random()

        return 0

    def _apply_neighbors_modifier(self, value: float) -> float:
        """
        ✅ Применяет модификатор neighbors к значению.
        neighbors="min" → значение как есть (меньше = лучше)
        neighbors="max" → отрицательное значение (больше = лучше)
        """
        if self.neighbors == "min":
            return value
        elif self.neighbors == "max":
            return -value
        return value

    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        if not colormap.uncolored_indices:
            return None

        # Фильтруем кандидатов
        candidates = self._filter_candidates(colormap, colormap.uncolored_indices)
        if not candidates:
            return None

        # ✅ Если priority_list пустой → сразу DefaultRuleSelector
        if not self.priority_list:
            default_type = DefaultRuleSelector.get_default_type()
            if default_type == "descending":
                return candidates[0], "first (empty priority)"
            elif default_type == "ascending":
                return candidates[-1], "last (empty priority)"
            else:  # random
                return random.choice(candidates), "random (empty priority)"

        # ✅ Если единственный приоритет "random" → сразу случайный
        if len(self.priority_list) == 1 and self.priority_list[0] == "random":
            return random.choice(candidates), "random"

        # ✅ ПОШАГОВАЯ сортировка с постепенным вычислением весов
        current_candidates = candidates

        for priority_idx, priority_key in enumerate(self.priority_list):
            # Вычисляем вес ТОЛЬКО для этого приоритета у всех текущих кандидатов
            weighted = []
            for idx in current_candidates:
                weight = self._calculate_weight(colormap, idx, priority_key)

                # Применяем модификатор neighbors только для "neighbors"
                if priority_key == "neighbors":
                    weight = self._apply_neighbors_modifier(weight)

                weighted.append((idx, weight))

            # Сортируем по весу (по возрастанию)
            weighted.sort(key=lambda x: x[1])

            # Находим минимальный вес
            min_weight = weighted[0][1]

            # Оставляем только кандидатов с минимальным весом
            current_candidates = [idx for idx, w in weighted if w == min_weight]

            # ✅ Если остался 1 кандидат → возвращаем его
            if len(current_candidates) == 1:
                priority_names = "_".join(self.priority_list[:priority_idx + 1])
                neighbors_info = f"_{self.neighbors}" if self.neighbors and "neighbors" in self.priority_list[
                    :priority_idx + 1] else ""
                return current_candidates[0], f"{priority_names}{neighbors_info}"

            # ✅ Если осталось 0 кандидатов (не должно случиться) → страховка
            if not current_candidates:
                current_candidates = [weighted[0][0]]
                break

        # ✅ Если дошли до конца и осталось несколько кандидатов
        if len(current_candidates) > 1:
            # ✅ Используем DefaultRuleSelector для разрешения конфликта
            default_type = DefaultRuleSelector.get_default_type()

            if default_type == "descending":
                best_idx = current_candidates[0]
            elif default_type == "ascending":
                best_idx = current_candidates[-1]
            else:  # "random"
                best_idx = random.choice(current_candidates)

            priority_names = "_".join(self.priority_list)
            neighbors_info = f"_{self.neighbors}" if self.neighbors and "neighbors" in self.priority_list else ""
            return best_idx, f"{priority_names}{neighbors_info}_tie"

        # Страховка
        if current_candidates:
            return current_candidates[0], "fallback"

        return None


class DefaultRuleSelector:
    """
    ✅ Глобальный селектор для разрешения конфликтов при равных кандидатах.

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