# simulation/rules.py
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List
import random



class Rule(ABC):
    @abstractmethod
    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


# ============================================================
#  ПРИОРИТЕТНЫЕ ПРАВИЛА
# ============================================================

class FirstPriorityRule(Rule):
    @property
    def name(self) -> str:
        return "first_priority"

    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        candidates = []
        for idx in colormap.uncolored_indices:
            freedom = len(colormap.get_available_colors(idx))
            if freedom == 1:
                candidates.append(idx)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0], self.name

        return self._select_by_default(colormap, candidates)

    def _select_by_default(self, colormap, candidates: List[int]) -> Tuple[int, str]:
        default_type = DefaultRuleSelector.get_default_type()

        if default_type == "descending":
            # Сортируем по: 1) свободе (по возрастанию), 2) неокрашенным соседям (по возрастанию)
            sorted_candidates = sorted(
                candidates,
                key=lambda idx: (
                    len(colormap.get_available_colors(idx)),  # свобода
                    sum(1 for n in colormap.graph.get(idx, set()) if not colormap.regions[n].is_colored)
                # неокрашенные соседи
                )
            )
            return sorted_candidates[0], f"{self.name} → descending"

        elif default_type == "ascending":
            # Сортируем по: 1) свободе (по возрастанию), 2) неокрашенным соседям (по убыванию)
            sorted_candidates = sorted(
                candidates,
                key=lambda idx: (
                    len(colormap.get_available_colors(idx)),  # свобода
                    -sum(1 for n in colormap.graph.get(idx, set()) if not colormap.regions[n].is_colored)
                # неокрашенные соседи (от макс к мин)
                )
            )
            return sorted_candidates[0], f"{self.name} → ascending"

        else:  # random
            return random.choice(candidates), f"{self.name} → random"


class SecondPriorityRule(Rule):
    @property
    def name(self) -> str:
        return "second_priority"

    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        candidates = []
        for colored_idx in colormap.colored_indices:
            neighbors = colormap.graph.get(colored_idx, set())
            gray_neighbors = [n for n in neighbors if not colormap.regions[n].is_colored]
            if len(gray_neighbors) == 1:
                candidates.append(gray_neighbors[0])

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0], self.name

        return self._select_by_default(colormap, candidates)

    def _select_by_default(self, colormap, candidates: List[int]) -> Tuple[int, str]:
        default_type = DefaultRuleSelector.get_default_type()

        if default_type == "descending":
            sorted_candidates = sorted(
                candidates,
                key=lambda idx: (
                    len(colormap.get_available_colors(idx)),  # свобода
                    sum(1 for n in colormap.graph.get(idx, set()) if not colormap.regions[n].is_colored)
                # неокрашенные соседи
                )
            )
            return sorted_candidates[0], f"{self.name} → descending"

        elif default_type == "ascending":
            sorted_candidates = sorted(
                candidates,
                key=lambda idx: (
                    len(colormap.get_available_colors(idx)),  # свобода
                    -sum(1 for n in colormap.graph.get(idx, set()) if not colormap.regions[n].is_colored)
                # неокрашенные соседи (от макс к мин)
                )
            )
            return sorted_candidates[0], f"{self.name} → ascending"

        else:  # random
            return random.choice(candidates), f"{self.name} → random"


class ThirdPriorityRule(Rule):
    """
    Находит неокрашенные области, у которых ровно 3 соседа уже закрашены
    (то есть степень свободы = 1, но только через закрашенных соседей)
    """

    @property
    def name(self) -> str:
        return "third_priority"

    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        candidates = []
        for idx in colormap.uncolored_indices:
            neighbors = colormap.graph.get(idx, set())
            colored_neighbors = sum(1 for n in neighbors if colormap.regions[n].is_colored)
            if colored_neighbors == 3:
                candidates.append(idx)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0], self.name

        return self._select_by_default(colormap, candidates)

    def _select_by_default(self, colormap, candidates: List[int]) -> Tuple[int, str]:
        default_type = DefaultRuleSelector.get_default_type()

        if default_type == "descending":
            sorted_candidates = sorted(
                candidates,
                key=lambda idx: (
                    len(colormap.get_available_colors(idx)),
                    sum(1 for n in colormap.graph.get(idx, set()) if not colormap.regions[n].is_colored)
                )
            )
            return sorted_candidates[0], f"{self.name} → descending"

        elif default_type == "ascending":
            sorted_candidates = sorted(
                candidates,
                key=lambda idx: (
                    len(colormap.get_available_colors(idx)),
                    -sum(1 for n in colormap.graph.get(idx, set()) if not colormap.regions[n].is_colored)
                )
            )
            return sorted_candidates[0], f"{self.name} → ascending"

        else:  # random
            return random.choice(candidates), f"{self.name} → random"


class ChainPriorityRule(Rule):
    """
    Приоритет №2: Выбирает пустые области со свободой = 1,
    у которых закрашенные соседи образуют НЕРАЗРЫВНУЮ ЦЕПОЧКУ.

    Цепочка = все закрашенные соседи соединены между собой напрямую
    (между ними нет других элементов/пустот).
    """

    @property
    def name(self) -> str:
        return "chain_priority"

    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        candidates = []

        for idx in colormap.uncolored_indices:
            # 1. Сначала проверяем свободу = 1
            freedom = len(colormap.get_available_colors(idx))
            if freedom != 1:
                continue

            # 2. Проверяем цепочку
            if self._has_colored_chain(colormap, idx):
                candidates.append(idx)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0], self.name

        # Если несколько — выбираем по DEFAULT правилу
        return self._select_by_default(colormap, candidates)

    def _has_colored_chain(self, colormap, idx: int) -> bool:
        """
        Проверяет, что закрашенные соседи образуют неразрывную цепочку.
        Цепочка = все закрашенные соседи соединены между собой напрямую.
        """
        neighbors = colormap.graph.get(idx, set())
        colored_neighbors = [n for n in neighbors if colormap.regions[n].is_colored]

        # Если меньше 2 закрашенных соседей — цепочки нет
        if len(colored_neighbors) < 2:
            return False

        # Проверяем, что ВСЕ закрашенные соседи соединены между собой
        # (каждый с каждым или через других)
        for i in range(len(colored_neighbors)):
            for j in range(i + 1, len(colored_neighbors)):
                n1 = colored_neighbors[i]
                n2 = colored_neighbors[j]

                # Проверяем, есть ли прямая связь между соседями
                if n2 not in colormap.graph.get(n1, set()):
                    # Если нет прямой связи — цепочка разорвана
                    return False

        # Все закрашенные соседи соединены между собой
        return True

    def _select_by_default(self, colormap, candidates: List[int]) -> Tuple[int, str]:
        """Выбирает среди кандидатов по DEFAULT правилу"""
        default_type = DefaultRuleSelector.get_default_type()

        if default_type == "descending":
            sorted_candidates = sorted(
                candidates,
                key=lambda idx: (
                    len(colormap.get_available_colors(idx)),
                    sum(1 for n in colormap.graph.get(idx, set()) if not colormap.regions[n].is_colored)
                )
            )
            return sorted_candidates[0], f"{self.name} → descending"

        elif default_type == "ascending":
            sorted_candidates = sorted(
                candidates,
                key=lambda idx: (
                    len(colormap.get_available_colors(idx)),
                    -sum(1 for n in colormap.graph.get(idx, set()) if not colormap.regions[n].is_colored)
                )
            )
            return sorted_candidates[0], f"{self.name} → ascending"

        else:  # random
            return random.choice(candidates), f"{self.name} → random"

# ============================================================
#  БАЗОВЫЕ ПРАВИЛА (DEFAULT)
# ============================================================

# ai_simulation/rules.py

class DefaultRule(Rule):
    """
    Параметры:
    - neighbors: "min" (сначала мин. неокрашенных соседей) или "max" (сначала макс.)
    - priority: "dof" (сначала степень свободы) или "non" (сначала неокрашенные соседи)
    - mode: "connected" (только области с закрашенным соседом) или "alone" (можно любые)
    - Если neighbors и priority None → random
    """

    def __init__(self,
                 neighbors: Optional[str] = None,
                 priority: Optional[str] = None,
                 mode: str = "connected"):
        """
        neighbors: "min" или "max" (None = игнорировать)
        priority: "dof" или "non" (None = только соседи, без dof)
        mode: "connected" (только с закрашенным соседом) или "alone" (можно любые)
        """
        self.neighbors = neighbors
        self.priority = priority
        self.mode = mode
        self._name = self._generate_name()

    def _generate_name(self) -> str:
        if self.neighbors is None and self.priority is None:
            return "random"
        parts = []
        if self.neighbors == "min":
            parts.append("neighbors↑")
        elif self.neighbors == "max":
            parts.append("neighbors↓")
        if self.priority == "dof":
            parts.append("dof")
        elif self.priority == "non":
            parts.append("non")
        if self.mode == "connected":
            parts.append("conn")
        elif self.mode == "alone":
            parts.append("alone")
        return "_".join(parts)

    @property
    def name(self) -> str:
        return self._name

    def apply(self, colormap) -> Optional[Tuple[int, str]]:
        if not colormap.uncolored_indices:
            return None

        # Фильтруем по mode
        candidates = colormap.uncolored_indices

        if self.mode == "connected":
            # Только области с закрашенным соседом
            filtered = []
            for idx in candidates:
                neighbors = colormap.graph.get(idx, set())
                has_colored = any(colormap.regions[n].is_colored for n in neighbors)
                if has_colored:
                    filtered.append(idx)
            candidates = filtered

            # Если нет connected и mode == "connected" → ничего не делаем
            if not candidates:
                return None

        # Если всё None → Random (уже отфильтровано по mode)
        if self.neighbors is None and self.priority is None:
            return random.choice(candidates), "random"

        # Сортируем
        def get_key(idx: int):
            freedom = len(colormap.get_available_colors(idx))
            uncolored_neighbors = sum(
                1 for n in colormap.graph.get(idx, set())
                if not colormap.regions[n].is_colored
            )

            n_mult = 1 if self.neighbors == "min" else -1 if self.neighbors == "max" else 0

            if self.priority == "dof":
                return (freedom, n_mult * uncolored_neighbors)
            else:  # "non" или None → сначала соседи
                return (n_mult * uncolored_neighbors, freedom)

        sorted_candidates = sorted(candidates, key=get_key)
        return sorted_candidates[0], self._name
# ============================================================
#  ПРЕДУСТАНОВЛЕННЫЕ ДЕФОЛТЫ ДЛЯ УДОБСТВА
# ============================================================

# ✅ ПРАВИЛЬНО:
class DescendingRule(DefaultRule):
    def __init__(self):
        super().__init__(neighbors="min", priority="dof", mode="connected")

class AscendingRule(DefaultRule):
    def __init__(self):
        super().__init__(neighbors="max", priority="dof", mode="connected")

class RandomRule(DefaultRule):
    def __init__(self):
        super().__init__(neighbors=None, priority=None, mode="alone")
# ============================================================
#  СЕЛЕКТОР DEFAULT ПРАВИЛА
# ============================================================

# В rules.py добавьте:
class DefaultRuleSelector:
    _default_type: str = "descending"

    @classmethod
    def set_default(cls, rule_type: str):
        cls._default_type = rule_type

    @classmethod
    def get_default_type(cls) -> str:
        return cls._default_type


# ============================================================
#  СТРАТЕГИЯ
# ============================================================

# ============================================================
#  СТРАТЕГИЯ
# ============================================================

class Strategy:
    def __init__(self, priority_rules: List[Rule], default_rule: Rule, name: str = "Стратегия"):
        """
        priority_rules: список приоритетных правил (проверяются по порядку)
        default_rule: объект DefaultRule (используется, если приоритетные не сработали)
        name: имя стратегии
        """
        self.priority_rules = priority_rules
        self.default_rule = default_rule
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def select_region(self, colormap) -> Tuple[Optional[int], str]:
        # 1. Приоритетные правила ПО ПОРЯДКУ
        for rule in self.priority_rules:
            result = rule.apply(colormap)
            if result is not None:
                return result

        # 2. DEFAULT правило
        result = self.default_rule.apply(colormap)
        if result is not None:
            return result

        # 3. Страховка
        if colormap.uncolored_indices:
            return random.choice(colormap.uncolored_indices), "random (страховка)"
        return None, "Нет регионов"