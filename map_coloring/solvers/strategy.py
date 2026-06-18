# solvers/strategy.py
from typing import Optional, Tuple, List
import random
from .base_rule import Rule, DefaultRule, DefaultRuleSelector


class DescendingRule(DefaultRule):
    """Предустановка: colors > neighbors (как было раньше)"""

    def __init__(self):
        super().__init__(
            neighbors="min",
            priority="colors neighbors",
            mode="connected",
            fallback_to_alone=True
        )


class AscendingRule(DefaultRule):
    """Предустановка: neighbors > colors"""

    def __init__(self):
        super().__init__(
            neighbors="max",
            priority="neighbors colors",
            mode="connected",
            fallback_to_alone=True
        )


class RandomRule(DefaultRule):
    """Предустановка: случайный"""

    def __init__(self):
        super().__init__(
            neighbors=None,
            priority="random",
            mode="alone",
            fallback_to_alone=False
        )


class Strategy:
    """Стратегия: набор правил в порядке приоритета + default правило"""

    def __init__(self, priority_rules: List[Rule], default_rule: Rule, name: str = "Стратегия"):
        self.priority_rules = priority_rules
        self.default_rule = default_rule
        self._name = name
        self._last_result = None

    @property
    def name(self) -> str:
        return self._name

    def select_region(self, colormap) -> Tuple[Optional[int], str]:
        """Возвращает (индекс_региона, имя_правила) или (None, причина_ошибки)"""

        if not colormap.uncolored_indices:
            self._last_result = (None, "Нет неокрашенных регионов")
            return self._last_result

        # Приоритетные правила по порядку
        for rule in self.priority_rules:
            result = rule.apply(colormap)
            if result is not None:
                self._last_result = result
                return result

        # Default правило
        result = self.default_rule.apply(colormap)
        if result is not None:
            self._last_result = result
            return result

        # Страховка
        if colormap.uncolored_indices:
            print("⚠️ Стратегия не нашла кандидатов! Использую случайный выбор.")
            idx = random.choice(colormap.uncolored_indices)
            self._last_result = (idx, "random (strategy fallback)")
            return self._last_result

        self._last_result = (None, "Нет регионов для раскраски")
        return self._last_result

    def get_last_result(self):
        """Для отладки: возвращает последний результат выбора"""
        return self._last_result