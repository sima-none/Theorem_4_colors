# manual_simulation/manual_simulation.py
from map_coloring.core.base_app import BaseColoringApp
from map_coloring.core.models import KEY_MAP


class ManualColoringApp(BaseColoringApp):
    def __init__(self, base_cells_count: int = 1000, generator_type: str = "non_convex"):
        # ✅ Передаем generator_type в родительский класс
        super().__init__(base_cells_count, generator_type=generator_type)

        # ✅ Проверяем, что карта создалась
        if not self.colormap or not self.colormap.regions:
            raise ValueError("Не удалось создать карту!")

        self._update_title(
            "🖌️ РУЧНАЯ РАСКРАСКА\n"
            "Кликни по области → выбери цвет\n"
            "Y = Жёлтый | R = Красный | B = Синий | D = Чёрный | X = Серый"
        )
        self._connect_events()

        # ✅ Состояние выделения
        self._pending_selection = None

    def _connect_events(self):
        """Подключает обработчики событий"""
        self.visualizer.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.visualizer.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _on_click(self, event):
        """Обработка клика мыши"""
        if event.inaxes != self.visualizer.ax or event.xdata is None:
            return

        # ✅ Находим регион через STRtree (быстро!)
        idx = self.visualizer.get_region_at_point(event.xdata, event.ydata)

        if idx is not None:
            # ✅ Сохраняем выделение
            self._pending_selection = idx
            self.visualizer.select_region(idx)
            print(f"✅ Выбрана область {idx}")

    def _on_key(self, event):
        """Обработка клавиш - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ"""
        # ✅ Проверяем, есть ли выделение
        if self._pending_selection is None or not event.key:
            return

        key = event.key.lower()

        # ✅ Проверяем, что клавиша валидна
        if key not in KEY_MAP:
            return

        # ✅ Пытаемся установить цвет
        color_id = KEY_MAP[key]
        region = self.colormap.get_region(self._pending_selection)

        if region is None:
            print(f"⚠️ Ошибка: область {self._pending_selection} не найдена")
            self._pending_selection = None
            self.visualizer.deselect_region()
            return

        # ✅ Устанавливаем цвет
        self.colormap.set_color(self._pending_selection, color_id)

        # ✅ Обновляем визуализацию ОДИН РАЗ
        self.visualizer.update()

        # ✅ Выводим информацию
        color_name = "Серый" if color_id == -1 else region.color_name
        print(f"🎨 Область {self._pending_selection} → {color_name}")

        # ✅ Сбрасываем выделение ПОСЛЕ успешной покраски
        self._pending_selection = None
        self.visualizer.deselect_region()

    def _update_title(self, title: str):
        """Обновляет заголовок"""
        if self.visualizer:
            self.visualizer.set_title(title)


if __name__ == "__main__":
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    app = ManualColoringApp(200, generator_type="non_convex")
    app.run()