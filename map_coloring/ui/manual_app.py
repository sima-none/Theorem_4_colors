# ui/manual_app.py
from map_coloring.ui.base_app import BaseColoringApp
from map_coloring.core.models import KEY_MAP
from map_coloring.core.history import HistoryManager


class SimpleController:
    """Простой контроллер для ручного режима (с перекрашиванием)"""

    def __init__(self, colormap, visualizer):
        self.colormap = colormap
        self.visualizer = visualizer
        self.history = HistoryManager()
        self._save_initial_state()

    def paint_region(self, region_idx: int, color_id: int) -> bool:
        """Закрасить регион (разрешаем перекрашивать)"""
        region = self.colormap.get_region(region_idx)
        if region is None:
            return False

        # Если регион уже закрашен и цвет не меняется — ничего не делаем
        if region.is_colored and region.color_id == color_id:
            return True

        # ✅ РАЗРЕШАЕМ перекрашивать даже если цвет занят соседом!
        # Просто запоминаем старый цвет для истории
        old_color = region.color_id

        # Меняем цвет
        self.colormap.set_color(region_idx, color_id)

        # Если регион был не закрашен — добавляем в историю
        if old_color == -1:
            self.history.add(region_idx, color_id)
        else:
            # Если перекрашиваем — записываем как отдельный шаг
            # или можно просто обновить последний шаг
            self.history.add(region_idx, color_id)

        self.visualizer.update()
        return True

    def _save_initial_state(self):
        self.history.clear()
        for i, region in enumerate(self.colormap.regions):
            if region.is_colored:
                self.history.steps.append((i, region.color_id))
        self.history.current = self.history.total

    @property
    def progress(self) -> str:
        return f"{self.history.current}/{self.history.total}"


class ManualColoringApp(BaseColoringApp):
    """UI для ручной раскраски"""

    def __init__(self, base_cells_count: int = 1000, generator_type: str = "non_convex"):
        super().__init__(base_cells_count, generator_type)

        self.controller = SimpleController(self.colormap, self.visualizer)
        self._pending_selection = None

        self.visualizer.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.visualizer.fig.canvas.mpl_connect("key_press_event", self._on_key)
        self._update_status()

    def _on_click(self, event):
        if event.inaxes != self.visualizer.ax or event.xdata is None:
            return

        region_id = self.visualizer.get_region_at_point(event.xdata, event.ydata)
        if region_id is not None:
            self._pending_selection = region_id
            self.visualizer.select_region(region_id)
            print(f"✅ Выбрана область {region_id}")

    def _on_key(self, event):
        if self._pending_selection is None or not event.key:
            return

        key = event.key.lower()
        if key not in KEY_MAP:
            return

        color_id = KEY_MAP[key]

        # Проверяем только существование региона
        region = self.controller.colormap.get_region(self._pending_selection)
        if region is None:
            print("⚠️ Область не найдена")
            self._pending_selection = None
            self.visualizer.deselect_region()
            return

        # Покраска (разрешаем любой цвет, даже если сосед такой же)
        self.controller.paint_region(self._pending_selection, color_id)

        color_name = "Серый" if color_id == -1 else region.color_name
        print(f"🎨 Область {self._pending_selection} → {color_name}")

        self._pending_selection = None
        self.visualizer.deselect_region()
        self._update_status()

    def _update_status(self):
        if self.controller is None:
            return
        progress = self.controller.progress
        status = f"Шаг {progress} | Кликни область → Y(жёлтый) R(красный) B(синий) D(чёрный) X(серый)"
        self.visualizer.set_title(f"🖌️ РУЧНАЯ РАСКРАСКА\n{status}")