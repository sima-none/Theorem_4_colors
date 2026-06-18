# core/base_app.py
from typing import Optional
from map_coloring.core.models import ColorMap
from map_coloring.core.visualizer import MapVisualizer
from map_coloring.core.controller import SimulationController
from map_coloring.core.generators import (
    ConvexMapGenerator,
    NonConvexMapGenerator
)


class BaseColoringApp:
    """Базовый класс для всех приложений раскраски"""

    def __init__(self, base_cells_count: int = 1000, generator_type: str = "non_convex"):
        self.base_cells_count = base_cells_count
        self.generator_type = generator_type
        self.generator = self._create_generator(generator_type)

        self.colormap: Optional[ColorMap] = None
        self.visualizer: Optional[MapVisualizer] = None
        self.selected_idx: Optional[int] = None
        self.timer = None
        self.controller: Optional[SimulationController] = None

        self._init_new_map()

        if not self.colormap or not self.colormap.regions:
            raise ValueError(f"Не удалось создать карту с типом {generator_type}")

    def _create_generator(self, generator_type: str):
        """Фабрика генераторов"""
        generators = {
            "convex": ConvexMapGenerator,
            "non_convex": NonConvexMapGenerator
        }

        if generator_type not in generators:
            raise ValueError(
                f"❌ Неизвестный тип генератора: {generator_type}. "
                f"Доступные: {list(generators.keys())}"
            )

        return generators[generator_type](self.base_cells_count)

    def _init_new_map(self):
        """Создаёт новую карту (БЕЗ создания контроллера)"""
        self.colormap = self.generator.generate()

        if not self.colormap or not self.colormap.regions:
            raise ValueError("Генератор вернул пустую карту!")

        self.visualizer = MapVisualizer(self.colormap)
        self.timer = None
        self.controller = None

    def _update_title(self, title: str):
        """Обновляет заголовок"""
        if self.visualizer:
            self.visualizer.set_title(title)

    def run(self):
        """Запускает приложение"""
        if not self.visualizer:
            raise RuntimeError("Визуализатор не инициализирован!")
        self.visualizer.show()

    def print_analysis(self):
        """Выводит анализ карты"""
        if not self.colormap:
            print("❌ Нет данных для анализа")
            return
        # Временно убираем вызов print_stats, пока не добавим его в models.py
        print(f"📊 Всего регионов: {len(self.colormap.regions)}")
        print(f"📊 Раскрашено: {len(self.colormap.colored_indices)}")
        print(f"📊 Не раскрашено: {len(self.colormap.uncolored_indices)}")