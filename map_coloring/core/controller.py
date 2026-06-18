# core/controller.py
import random  # ✅ импорт на уровне модуля
from typing import Optional, Tuple, List
from map_coloring.ai_simulation.history import HistoryManager


class SimulationController:
    """Управление симуляцией: авто/ручной режим, шаги, история"""

    def __init__(self, colormap, visualizer, strategy, timer):
        self.colormap = colormap
        self.visualizer = visualizer
        self.strategy = strategy
        self.timer = timer

        self.history = HistoryManager()
        self.is_auto = False

        # ✅ Стратегия выбора цвета: True = приоритет цветных, False = случайный
        self.color_priority = True  # по умолчанию включен

        self._save_initial_state()

        self.interval_ms = 150  # ✅ текущий интервал
        self.min_interval = 50  # ✅ минимальный интервал (быстро)
        self.max_interval = 1050  # ✅ максимальный интервал (медленно)

    def set_color_priority(self, enabled: bool):
        """Включает/выключает приоритет цветных над чёрным"""
        self.color_priority = enabled
        status = "включен" if enabled else "выключен"
        print(f"🎨 Приоритет цветных: {status}")

    def _choose_color(self, available_colors: List[int]) -> int:
        """
        Выбирает цвет из доступных.

        - color_priority = True: сначала цветные (0,1,2), потом чёрный (3)
        - color_priority = False: полностью случайный
        """
        if not available_colors:
            return -1

        if not self.color_priority:
            return random.choice(available_colors)

        # ✅ Приоритет цветных над чёрным
        colored = [c for c in available_colors if c != 3]  # все кроме чёрного
        black = [c for c in available_colors if c == 3]

        if colored:
            return random.choice(colored)
        else:
            return black[0] if black else random.choice(available_colors)

    # ============================================================
    #  ПУБЛИЧНЫЕ МЕТОДЫ
    # ============================================================

    def toggle_auto(self) -> str:
        """Переключить авто/ручной режим"""
        if not self.timer:
            return "❌ Таймер не инициализирован!"

        self.is_auto = not self.is_auto

        if self.is_auto:
            if self.colormap.is_complete:
                self._reset_colors()

            if len(self.colormap.colored_indices) == 0:
                self.do_ai_step()

            self.timer.start()
            return "🔄 АВТОМАТИЧЕСКИЙ РЕЖИМ"
        else:
            self.timer.stop()
            return "✋ РУЧНОЙ РЕЖИМ"

    def step_forward(self) -> str:
        """Шаг вперёд"""
        if self.is_auto:
            self.is_auto = False
            if self.timer:
                self.timer.stop()

        if not self.history.is_at_end:
            idx, color = self.history.step_forward()
            self.colormap.set_color(idx, color)
            self.visualizer.update()
            return f"⏩ Шаг → {self.history.current}/{self.history.total}"

        if not self.colormap.is_complete:
            self.do_ai_step()
            return f"🤖 Новый шаг → {self.history.current}/{self.history.total}"

        return "✅ ГОТОВО! Enter для новой карты"

    def step_backward(self) -> str:
        """Шаг назад (оптимизированный)"""
        if self.is_auto:
            self.is_auto = False
            if self.timer:
                self.timer.stop()

        if self.history.is_at_start:
            return "🔙 ЭТО НАЧАЛО!"

        last_step = self.history.step_back()
        if last_step:
            idx, color = last_step
            self.colormap.set_color(idx, -1)
            self.visualizer.update()
            return f"⏪ Шаг ← {self.history.current}/{self.history.total}"

        return "⚠️ Не удалось отменить шаг"

    def speed_up(self):
        """Увеличить скорость (уменьшить интервал)"""
        new_interval = max(self.min_interval, self.interval_ms - 100)
        self._set_interval(new_interval)
        return f"⚡ Скорость: {new_interval}ms"

    def slow_down(self):
        """Уменьшить скорость (увеличить интервал)"""
        new_interval = min(self.max_interval, self.interval_ms + 100)
        self._set_interval(new_interval)
        return f"🐢 Скорость: {new_interval}ms"

    def _set_interval(self, interval: int):
        """Устанавливает новый интервал таймера"""
        self.interval_ms = interval
        if self.timer:
            # Перезапускаем таймер с новым интервалом
            was_running = self.is_auto
            if was_running:
                self.timer.stop()
            self.timer = self.visualizer.fig.canvas.new_timer(interval=interval)
            self.timer.add_callback(self.auto_step)
            if was_running:
                self.timer.start()

    def reset_colors(self) -> str:
        """Сброс цветов (публичный метод)"""
        self._reset_colors()
        return "🔄 ЦВЕТА СБРОШЕНЫ"

    def new_map(self) -> str:
        """Новая карта"""
        if self.is_auto:
            self.is_auto = False
            if self.timer:
                self.timer.stop()
        self.history.clear()
        return "🗺️ НОВАЯ КАРТА"

    def do_ai_step(self) -> bool:
        """Один шаг AI (возвращает True если шаг был сделан)"""
        if self.colormap.is_complete:
            print("✅ Карта уже полностью раскрашена!")
            return False

        # Проверка на тупики
        deadlocks = self.colormap.find_deadlocks()
        if deadlocks:
            self.visualizer.highlight_region(deadlocks[0], "white", 3.0)
            if self.is_auto:
                self.is_auto = False
                if self.timer:
                    self.timer.stop()
            print(f"⚠️ ТУПИК в области {deadlocks[0]}")
            return False

        # Выбор региона по стратегии
        if self.strategy is None:
            print("⚠️ Стратегия не задана!")
            return False

        target_id, reason = self.strategy.select_region(self.colormap)

        if target_id is None:
            print(f"⚠️ Стратегия не выбрала регион: {reason}")
            if self.colormap.uncolored_indices:
                target_id = random.choice(self.colormap.uncolored_indices)
                reason = "random (emergency)"
                print(f"🔄 Использую экстренный случайный выбор региона {target_id}")
            else:
                print("✅ Все регионы раскрашены!")
                return False

        # ✅ Выбор цвета по стратегии
        available = list(self.colormap.get_available_colors(target_id))
        if not available:
            print(f"⚠️ Нет доступных цветов для региона {target_id}")
            return False

        chosen = self._choose_color(available)

        self.colormap.set_color(target_id, chosen)
        self.history.add(target_id, chosen)
        self.visualizer.update()

        if self.colormap.is_complete and self.is_auto:
            self.is_auto = False
            if self.timer:
                self.timer.stop()
            print("🎉 КАРТА ПОЛНОСТЬЮ ЗАКРАШЕНА!")

        return True

    def auto_step(self):
        """Шаг для таймера"""
        if self.is_auto and not self.colormap.is_complete:
            self.do_ai_step()
        elif self.colormap.is_complete and self.is_auto:
            self.is_auto = False
            if self.timer:
                self.timer.stop()

    # ============================================================
    #  ПРИВАТНЫЕ МЕТОДЫ
    # ============================================================

    def _save_initial_state(self):
        """Сохраняет начальное состояние карты в историю"""
        self.history.clear()
        for i, region in enumerate(self.colormap.regions):
            if region.is_colored:
                self.history.steps.append((i, region.color_id))
        self.history.current = self.history.total

    def _reset_colors(self):
        """Приватный метод сброса цветов"""
        self.colormap.reset_colors()
        self.history.clear()
        self.visualizer.update()

    def _go_to_step(self, step: int):
        """Переход к конкретному шагу"""
        self.colormap.reset_colors()
        for i in range(step):
            if i < len(self.history.steps):
                idx, color = self.history.steps[i]
                self.colormap.set_color(idx, color)
        self.history.current = step
        self.visualizer.update()

    def _go_to_end(self):
        """Переход в конец истории"""
        self._go_to_step(self.history.total)

    # ============================================================
    #  СВОЙСТВА
    # ============================================================

    @property
    def status(self) -> str:
        mode = "🤖 АВТО" if self.is_auto else "✋ РУЧНОЙ"
        color_status = "🎨 приоритет" if self.color_priority else "🎲 случайный"
        return f"{mode} | {color_status} | Шаг {self.history.current}/{self.history.total}"