# manual_simulation.py
from map_coloring.core.base_app import BaseColoringApp  # ← абсолютный
from map_coloring.core.models import KEY_MAP  # ← абсолютный


class ManualColoringApp(BaseColoringApp):
    def __init__(self, base_cells_count: int = 1000):
        super().__init__(base_cells_count)
        self._update_title(
            "РУЧНАЯ РАСКРАСКА\n"
            "Кликни по области → выбери цвет\n"
            "Y = Жёлтый | R = Красный | B = Синий | D = Чёрный | X = Серый"
        )
        self._connect_events()

    def _connect_events(self):
        self.visualizer.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.visualizer.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _on_click(self, event):
        if event.inaxes != self.visualizer.ax or event.xdata is None:
            return
        idx = self.visualizer.get_region_at_point(event.xdata, event.ydata)
        if idx is not None:
            self.selected_idx = idx
            self.visualizer.selected_idx = idx
            self.visualizer.update()

    def _on_key(self, event):
        if self.selected_idx is None or not event.key:
            return
        key = event.key.lower()
        if key in KEY_MAP:
            self.colormap.set_color(self.selected_idx, KEY_MAP[key])
            self.visualizer.update()
            self.selected_idx = None
            self.visualizer.selected_idx = None
            self.visualizer.update()


if __name__ == "__main__":
    app = ManualColoringApp(1000)
    app.run()