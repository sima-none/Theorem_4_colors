# core/base_app.py
from typing import Optional
from map_coloring.core.models import ColorMap
from map_coloring.core.visualizer import MapVisualizer
from map_coloring.core.controller import SimulationController
from map_coloring.core.generators import (  # ← абсолютный импорт от core
    ConvexMapGenerator,
    NonConvexMapGenerator,
    TrianglesConvexGenerator,
    TrianglesNonConvexGenerator,
)

class BaseColoringApp:
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

    def _create_generator(self, generator_type: str):
        """Фабрика генераторов"""
        generators = {
            "convex": ConvexMapGenerator,
            "non_convex": NonConvexMapGenerator,
            "triangles_convex": TrianglesConvexGenerator,
            "triangles_non_convex": TrianglesNonConvexGenerator,
        }

        if generator_type not in generators:
            raise ValueError(
                f"Unknown generator type: {generator_type}. "
                f"Available: {list(generators.keys())}"
            )

        return generators[generator_type](self.base_cells_count)

    # ... остальное без изменений
    def _init_new_map(self):
        self.colormap = self.generator.generate()
        self.visualizer = MapVisualizer(self.colormap)
        self.timer = self.visualizer.fig.canvas.new_timer(interval=300)
        self.controller = SimulationController(
            self.colormap,
            self.visualizer,
            strategy=None,
            timer=self.timer
        )
    def _update_title(self, title: str):
        self.visualizer.set_title(title)

    def run(self):
        self.visualizer.show()

    def print_analysis(self):
        print("\n--- АНАЛИЗ ---")
        for region in self.colormap.regions:
            if region.is_colored:
                print(f"Фигура №{region.id} ({region.color_name}):")
                print(f"  Центр: {region.centroid}")
                print(f"  Площадь: {region.polygon.area:.4f}")