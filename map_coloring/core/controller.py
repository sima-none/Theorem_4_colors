# core/controller.py
import random  # ✅ Импорт на уровне модуля (исправление #1)
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
        self._auto_mode_active = False  # ✅ Флаг для предотвращения двойного запуска

        # Сохраняем начальное состояние
        self._save_initial_state()

    # ============================================================
    #  ПУБЛИЧНЫЕ МЕТОДЫ
    # ============================================================

    def toggle_auto(self) -> str:
        """Переключить авто/ручной режим"""
        if not self.timer:  # ✅ Проверка существования таймера (исправление #3)
            return "❌ Таймер не инициализирован!"

        self.is_auto = not self.is_auto

        if self.is_auto:
            # ✅ Исправление #2: НЕ сбрасываем историю при старте авто
            if self.colormap.is_complete:
                self._reset_colors()  # Это теперь безопасно

            # Если история пуста, делаем первый шаг
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

        # Если есть шаги вперёд по истории
        if not self.history.is_at_end:
            idx, color = self.history.step_forward()
            self.colormap.set_color(idx, color)
            self.visualizer.update()
            return f"⏩ Шаг → {self.history.current}/{self.history.total}"

        # Если карта не завершена - делаем AI шаг
        if not self.colormap.is_complete:
            self.do_ai_step()
            return f"🤖 Новый шаг → {self.history.current}/{self.history.total}"

        return "✅ ГОТОВО! Enter для новой карты"

    def step_backward(self) -> str:
        """Шаг назад (ОПТИМИЗИРОВАННЫЙ)"""
        if self.is_auto:
            self.is_auto = False
            if self.timer:
                self.timer.stop()

        if self.history.is_at_start:
            return "🔙 ЭТО НАЧАЛО!"

        # ✅ Исправление #3: Отменяем ТОЛЬКО ПОСЛЕДНИЙ шаг
        last_step = self.history.step_back()
        if last_step:
            idx, color = last_step
            # Возвращаем цвет в -1 (неокрашенный)
            self.colormap.set_color(idx, -1)
            self.visualizer.update()
            return f"⏪ Шаг ← {self.history.current}/{self.history.total}"

        return "⚠️ Не удалось отменить шаг"

    def reset_colors(self) -> str:
        """Сброс цветов (публичный метод)"""
        self._reset_colors()
        return "🔄 ЦВЕТА СБРОШЕНЫ"

    def new_map(self) -> str:
        """Новая карта (вызывается извне)"""
        if self.is_auto:
            self.is_auto = False
            if self.timer:
                self.timer.stop()
        self.history.clear()
        return "🗺️ НОВАЯ КАРТА"

    # controller.py - добавить проверки

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

        # ✅ Проверка на None с информативным сообщением
        if target_id is None:
            print(f"⚠️ Стратегия не выбрала регион: {reason}")
            if self.colormap.uncolored_indices:
                # ✅ УБЕРИТЕ import random ОТСЮДА!
                target_id = random.choice(self.colormap.uncolored_indices)  # ← использует глобальный random
                reason = "random (emergency)"
                print(f"🔄 Использую экстренный случайный выбор региона {target_id}")
            else:
                print("✅ Все регионы раскрашены!")
                return False

        # Выбор цвета
        available = list(self.colormap.get_available_colors(target_id))
        if not available:
            print(f"⚠️ Нет доступных цветов для региона {target_id}")
            return False

        chosen = random.choice(available)  # ← теперь random определен!
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
        """Приватный метод сброса цветов (исправление #4)"""
        # Сохраняем историю ДО сброса (на случай отмены)
        old_history = self.history.steps.copy()
        old_current = self.history.current

        # Сбрасываем цвета
        self.colormap.reset_colors()
        self.history.clear()

        # ✅ Исправление #2: Не сохраняем пустую историю!
        # Вместо этого просто очищаем и сбрасываем указатель
        self.visualizer.update()

    def _go_to_step(self, step: int):
        """Переход к конкретному шагу (используется редко)"""
        # Полностью перестраиваем состояние до step
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
        return f"{mode} | Шаг {self.history.current}/{self.history.total}"