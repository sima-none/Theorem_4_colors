# history.py
from typing import List, Tuple, Optional


class HistoryManager:
    """Управляет историей шагов раскраски"""

    def __init__(self):
        self.steps: List[Tuple[int, int]] = []  # (индекс_области, цвет)
        self.current: int = 0  # текущая позиция в истории

    @property
    def total(self) -> int:
        return len(self.steps)

    @property
    def is_at_end(self) -> bool:
        return self.current >= self.total

    @property
    def is_at_start(self) -> bool:
        return self.current <= 0

    def add(self, region_idx: int, color: int):
        """Добавляет шаг в историю (обрезает будущее)"""
        # Если мы не в конце, обрезаем историю
        if not self.is_at_end:
            self.steps = self.steps[:self.current]
        self.steps.append((region_idx, color))
        self.current = self.total

    def step_back(self) -> Optional[Tuple[int, int]]:
        """Возвращает шаг назад"""
        if self.is_at_start:
            return None
        self.current -= 1
        return self.steps[self.current]

    def step_forward(self) -> Optional[Tuple[int, int]]:
        """Возвращает шаг вперёд"""
        if self.is_at_end:
            return None
        step = self.steps[self.current]
        self.current += 1
        return step

    def go_to_start(self):
        """Переходит в начало истории"""
        self.current = 0

    def go_to_end(self):
        """Переходит в конец истории"""
        self.current = self.total

    def clear(self):
        """Очищает историю"""
        self.steps = []
        self.current = 0

    def get_current_step(self) -> int:
        return self.current

    def get_total_steps(self) -> int:
        return self.total