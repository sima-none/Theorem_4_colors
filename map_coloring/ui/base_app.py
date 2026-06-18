# ui/base_app.py
from typing import Optional
from map_coloring.core.models import ColorMap
from map_coloring.ui.visualizer import MapVisualizer
from map_coloring.generators import (
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

        self._init_new_map()

        if not self.colormap or not self.colormap.regions:
            raise ValueError(f"Не удалось создать карту с типом {generator_type}")

    def _create_generator(self, generator_type: str):
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
        self.colormap = self.generator.generate()
        if not self.colormap or not self.colormap.regions:
            raise ValueError("Генератор вернул пустую карту!")
        self.visualizer = MapVisualizer(self.colormap)

    def run(self):
        if not self.visualizer:
            raise RuntimeError("Визуализатор не инициализирован!")
        self.visualizer.show()