# controller.py
from map_coloring.ai_simulation.history import HistoryManager  # ← абсолютный



class SimulationController:
    """Управление симуляцией: авто/ручной режим, шаги, история"""

    def __init__(self, colormap, visualizer, strategy, timer):
        self.colormap = colormap
        self.visualizer = visualizer
        self.strategy = strategy
        self.timer = timer

        self.history = HistoryManager()
        self.is_auto = False

        self._save_state()

    def toggle_auto(self):
        """Переключить авто/ручной режим"""
        self.is_auto = not self.is_auto
        if self.is_auto:
            if self.colormap.is_complete:
                self._reset_colors()
            if not self.history.is_at_end:
                self._go_to_end()
            if len(self.colormap.colored_indices) == 0:
                self.do_ai_step()
            self.timer.start()
            return "АВТОМАТИЧЕСКИЙ РЕЖИМ"
        else:
            self.timer.stop()
            return "РУЧНОЙ РЕЖИМ"

    def step_forward(self) -> str:
        """Шаг вперёд"""
        if self.is_auto:
            self.is_auto = False
            self.timer.stop()

        if not self.history.is_at_end:
            idx, color = self.history.step_forward()
            self.colormap.set_color(idx, color)
            self.visualizer.update()
            return f"Шаг → {self.history.current}/{self.history.total}"

        if not self.colormap.is_complete:
            self.do_ai_step()
            return f"Новый шаг → {self.history.current}/{self.history.total}"

        return "ГОТОВО! Enter для новой карты"

    def step_backward(self) -> str:
        """Шаг назад"""
        if self.is_auto:
            self.is_auto = False
            self.timer.stop()

        if self.history.is_at_start:
            return "ЭТО НАЧАЛО!"

        self.history.step_back()
        self._go_to_step(self.history.current)
        return f"Шаг ← {self.history.current}/{self.history.total}"

    def new_map(self):
        """Новая карта"""
        if self.is_auto:
            self.is_auto = False
            self.timer.stop()
        self.history.clear()
        return "НОВАЯ КАРТА"

    def reset_colors(self):
        """Сброс цветов"""
        self.history.clear()
        self.colormap.reset_colors()
        self.visualizer.update()
        self._save_state()
        return "ЦВЕТА СБРОШЕНЫ"

    def do_ai_step(self):
        """Один шаг AI"""
        if self.colormap.is_complete:
            return

        deadlocks = self.colormap.find_deadlocks()
        if deadlocks:
            self.visualizer.highlight_region(deadlocks[0], "white", 3.0)
            if self.is_auto:
                self.is_auto = False
                self.timer.stop()
            return

        import random
        target_id, reason = self.strategy.select_region(self.colormap)
        if target_id is None:
            return

        available = list(self.colormap.get_available_colors(target_id))
        if available:
            chosen = random.choice(available)
            self.colormap.set_color(target_id, chosen)
            self.history.add(target_id, chosen)
            self.visualizer.update()

            if self.colormap.is_complete and self.is_auto:
                self.is_auto = False
                self.timer.stop()

    def auto_step(self):
        """Шаг для таймера"""
        if self.is_auto and not self.colormap.is_complete:
            self.do_ai_step()
        elif self.colormap.is_complete and self.is_auto:
            self.is_auto = False
            self.timer.stop()

    def _save_state(self):
        self.history.clear()
        for i, region in enumerate(self.colormap.regions):
            if region.is_colored:
                self.history.steps.append((i, region.color_id))
        self.history.current = self.history.total

    def _go_to_step(self, step: int):
        self.colormap.reset_colors()
        for i in range(step):
            idx, color = self.history.steps[i]
            self.colormap.set_color(idx, color)
        self.history.current = step
        self.visualizer.update()

    def _go_to_end(self):
        self._go_to_step(self.history.total)

    def _reset_colors(self):
        self.history.clear()
        self.colormap.reset_colors()
        self.visualizer.update()
        self._save_state()

    @property
    def status(self) -> str:
        mode = "АВТО" if self.is_auto else "РУЧНОЙ"
        return f"{mode} | Шаг {self.history.current}/{self.history.total}"