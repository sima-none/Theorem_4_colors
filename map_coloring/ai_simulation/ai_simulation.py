# ai_simulation/ai_simulation.py
from map_coloring.core.base_app import BaseColoringApp
from map_coloring.core.rules import Strategy, DefaultRule
from map_coloring.core.controller import SimulationController


class AdvancedWaveSimulation(BaseColoringApp):
    def __init__(self, base_cells_count: int = 1000, strategy: Strategy = None,
                 generator_type: str = "merged", color_priority: bool = True):
        """
        color_priority: True = приоритет цветных над чёрным, False = случайный
        """
        self._strategy = strategy

        if self._strategy is None:
            print("⚠️ Стратегия не передана! Использую стратегию по умолчанию.")
            default_rule = DefaultRule(neighbors="min", priority="dof", mode="connected")
            self._strategy = Strategy(
                priority_rules=[],
                default_rule=default_rule,
                name="Стратегия по умолчанию"
            )

        self._color_priority = color_priority

        super().__init__(base_cells_count, generator_type=generator_type)

        if not self.colormap or not self.colormap.regions:
            raise ValueError("Не удалось создать регионы для карты!")

        self.timer = self.visualizer.fig.canvas.new_timer(interval=300)

        self.controller = SimulationController(
            self.colormap,
            self.visualizer,
            self._strategy,
            self.timer
        )

        # ✅ Устанавливаем приоритет цветных
        self.controller.set_color_priority(color_priority)

        self.timer.add_callback(self.controller.auto_step)

        generator_name = self.generator.get_name()
        color_status = "🎨 Приоритет цветных" if color_priority else "🎲 Случайный цвет"
        self._update_status(f"Пробел: Авто | ← → шаги | Enter: Новая карта | C: переключить цвет | {color_status}")
        self._connect_events()

    def _connect_events(self):
        self.visualizer.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _update_status(self, text: str = ""):
        if not self.controller:
            return
        status = self.controller.status
        interval = self.controller.interval_ms if self.controller else 300
        self.visualizer.set_title(
            f"🧠 WAVE AI SIMULATION\n"
            f"← → шаги | ↑↓ скорость | Пробел: Авто | Enter: Новая карта | C: цвет\n"
            f"{status} | {interval}ms | {text}",
            fontsize=10, pad=15
        )

    def _on_key(self, event):
        if not event.key or not self.controller:
            return

        if event.key == " ":
            msg = self.controller.toggle_auto()
            self._update_status(msg)
        elif event.key == "right":
            msg = self.controller.step_forward()
            self._update_status(msg)
        elif event.key == "left":
            msg = self.controller.step_backward()
            self._update_status(msg)
        elif event.key == "up":  # ✅ ↑ увеличение скорости
            msg = self.controller.speed_up()
            self._update_status(msg)
        elif event.key == "down":  # ✅ ↓ уменьшение скорости
            msg = self.controller.slow_down()
            self._update_status(msg)
        elif event.key == "enter":
            self._regenerate_map()
        elif event.key == "c":  # ✅ Переключение приоритета цветных
            self._toggle_color_priority()

    def _toggle_color_priority(self):
        """Переключает приоритет цветных"""
        if not self.controller:
            return

        new_state = not self.controller.color_priority
        self.controller.set_color_priority(new_state)

        color_status = "🎨 Приоритет цветных" if new_state else "🎲 Случайный цвет"
        self._update_status(f"{color_status}")

    def _regenerate_map(self):
        """Пересоздает карту с сохранением стратегии"""
        print("🔄 Генерация новой карты...")

        if self.timer:
            try:
                self.timer.stop()
            except:
                pass

        self._init_new_map()

        if not self.colormap or not self.colormap.regions:
            print("❌ Ошибка: не удалось создать новую карту!")
            return

        self.timer = self.visualizer.fig.canvas.new_timer(interval=300)

        # ✅ Сохраняем текущий приоритет цветных
        current_color_priority = self.controller.color_priority if self.controller else True

        self.controller = SimulationController(
            self.colormap,
            self.visualizer,
            self._strategy,
            self.timer
        )

        # ✅ Восстанавливаем приоритет цветных
        self.controller.set_color_priority(current_color_priority)

        self.timer.add_callback(self.controller.auto_step)

        generator_name = self.generator.get_name()
        color_status = "🎨 Приоритет цветных" if current_color_priority else "🎲 Случайный цвет"
        self._update_status(f"🗺️ НОВАЯ КАРТА ({generator_name}) | {color_status}")
        print(f"✅ Создано {len(self.colormap.regions)} новых регионов")

    def _on_click(self, event):
        pass

    @property
    def strategy(self):
        return self._strategy