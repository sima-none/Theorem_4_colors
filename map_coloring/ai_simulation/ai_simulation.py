# ai_simulation/ai_simulation.py
# ✅ ПРАВИЛЬНО:
from map_coloring.core.base_app import BaseColoringApp
from map_coloring.ai_simulation.rules import Strategy, DefaultRule  # ← абсолютный
from map_coloring.core.controller import SimulationController  # ← абсолютный

class AdvancedWaveSimulation(BaseColoringApp):
    def __init__(self, base_cells_count: int = 1000, strategy: Strategy = None, generator_type: str = "merged"):
        super().__init__(base_cells_count, generator_type=generator_type)

        self.strategy = strategy or Strategy([], default_rule=DefaultRule(None, None), name="Стратегия не задана")

        self.timer = self.visualizer.fig.canvas.new_timer(interval=300)
        self.controller = SimulationController(
            self.colormap, self.visualizer, self.strategy, self.timer
        )
        self.timer.add_callback(self.controller.auto_step)

        generator_name = self.generator.get_name()
        self._update_status(f"Пробел: Авто | ← → шаги | Enter: Новая карта | Карта: {generator_name}")
        self._connect_events()

    # ... остальное без изменений

    def _connect_events(self):
        self.visualizer.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _update_status(self, text: str = ""):
        status = self.controller.status
        self.visualizer.set_title(
            f"WAVE AI SIMULATION\n"
            f"← → шаги | Пробел: Авто | Enter: Новая карта\n"
            f"{status} | {text}",
            fontsize=10, pad=15
        )

    def _on_key(self, event):
        if not event.key:
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

        elif event.key == "enter":
            self.controller.new_map()
            self._init_new_map()
            self.controller = SimulationController(
                self.colormap, self.visualizer, self.strategy, self.timer
            )
            self.timer.add_callback(self.controller.auto_step)
            self._update_status("НОВАЯ КАРТА")

    def _on_click(self, event):
        pass


if __name__ == "__main__":
    import sys, os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from map_coloring import Strategy, FirstPriorityRule, SecondPriorityRule, DescendingRule, RandomRule

    app = AdvancedWaveSimulation(1000, Strategy(
        rules=[FirstPriorityRule(), SecondPriorityRule(), DescendingRule(), RandomRule()],
        name="Стратегия"
    ))
    app.run()