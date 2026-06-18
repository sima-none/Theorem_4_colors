# ui/ai_app.py
from map_coloring.ui.base_app import BaseColoringApp
from map_coloring.core.controller import SimulationController  # ← используем оригинальный!


class AIColoringApp(BaseColoringApp):
    def __init__(self, base_cells_count: int = 1000,
                 generator_type: str = "non_convex",
                 strategy=None,
                 color_priority: bool = True):

        super().__init__(base_cells_count, generator_type)

        self._strategy = strategy
        self._color_priority = color_priority

        self.timer = self.visualizer.fig.canvas.new_timer(interval=300)

        # Используем оригинальный SimulationController
        self.controller = SimulationController(
            self.colormap,
            self.visualizer,
            self._strategy,
            self.timer
        )
        self.controller.set_color_priority(color_priority)
        self.timer.add_callback(self.controller.auto_step)

        self.visualizer.fig.canvas.mpl_connect("key_press_event", self._on_key)
        self._update_status()

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
        elif event.key == "up":
            msg = self.controller.speed_up()
            self._update_status(msg)
        elif event.key == "down":
            msg = self.controller.slow_down()
            self._update_status(msg)
        elif event.key == "enter":
            self._regenerate_map()
        elif event.key == "c":
            self._toggle_color_priority()

    def _toggle_color_priority(self):
        if not self.controller:
            return
        new_state = not self.controller.color_priority
        self.controller.set_color_priority(new_state)
        color_status = "🎨 Приоритет цветных" if new_state else "🎲 Случайный цвет"
        self._update_status(color_status)

    def _regenerate_map(self):
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

        current_color_priority = self.controller.color_priority if self.controller else True

        self.timer = self.visualizer.fig.canvas.new_timer(interval=300)
        self.controller = SimulationController(
            self.colormap,
            self.visualizer,
            self._strategy,
            self.timer
        )
        self.controller.set_color_priority(current_color_priority)
        self.timer.add_callback(self.controller.auto_step)

        generator_name = self.generator.get_name()
        color_status = "🎨 Приоритет цветных" if current_color_priority else "🎲 Случайный цвет"
        self._update_status(f"🗺️ НОВАЯ КАРТА ({generator_name}) | {color_status}")
        print(f"✅ Создано {len(self.colormap.regions)} новых регионов")

    def _update_status(self, text: str = ""):
        if not self.controller:
            return
        status = self.controller.status
        interval = self.controller.interval_ms if self.controller else 300
        self.visualizer.set_title(
            f"🧠 AI СИМУЛЯЦИЯ\n"
            f"← → шаги | ↑↓ скорость | Пробел: Авто | Enter: Новая карта | C: цвет\n"
            f"{status} | {interval}ms | {text}",
            fontsize=10, pad=15
        )