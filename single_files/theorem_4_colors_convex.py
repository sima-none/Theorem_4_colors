import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiPoint, box
from shapely.ops import voronoi_diagram
from shapely.strtree import STRtree
from matplotlib.patches import Polygon as MplPolygon

# Константы

NUM_REGIONS = 64
COLORS = {
    -1: "lightgray",
    0: "yellow",
    1: "red",
    2: "blue",
    3: "black"
}
KEY_MAP = {"y": 0, "r": 1, "b": 2, "d": 3, "x": -1}

class InteractiveVoronoiMap:
    def __init__(self, num_regions):
        self.num_regions = num_regions
        self.selected_idx = None

        self._generate_mesh()
        self.region_colors = np.full(len(self.regions), -1, dtype=int)

        self.fig, self.ax = plt.subplots(figsize=(12, 12))
        self.patches = []
        self.centroid_scatter = None

        # Новый объект для красивого затемнения
        self.selection_patch = None

        self._build_plot()

        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)

    def _build_plot(self):
        """Однократная инициализация всех графических элементов"""
        for i, poly in enumerate(self.regions):
            coords = np.array(poly.exterior.coords)

            patch = MplPolygon(
                coords,
                closed=True,
                facecolor=COLORS[-1],
                edgecolor="black",
                linewidth=0.8,
                zorder=1
            )
            self.ax.add_patch(patch)
            self.patches.append(patch)

        # Создаем невидимый патч-затемнитель с высоким zorder (поверх остальных)
        self.selection_patch = MplPolygon(
            [[0, 0], [0, 0]],
            closed=True,
            facecolor="black",
            alpha=0.2,
            visible=False,
            zorder=2
        )
        self.ax.add_patch(self.selection_patch)

        self.centroid_scatter = self.ax.scatter([], [], c="black", s=12, zorder=3)

        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_aspect("equal")
        self.ax.set_title(
            "Click region → choose color\n"
            "Y = Yellow | R = Red | B = Blue | D = Black | X = Clear",
            fontsize=12
        )

    def update_visuals(self):
        """Моментальное обновление цветов и положения затемнения"""
        centroids = []

        for i, patch in enumerate(self.patches):
            color_id = self.region_colors[i]
            patch.set_facecolor(COLORS[color_id])

            # Чистый цвет без изменения alpha самого полигона
            patch.set_alpha(0.65 if color_id != -1 else 1.0)

            if color_id != -1:
                centroids.append(self.regions[i].centroid.coords[0])

        # Управление красивым эффектом затемнения
        if self.selected_idx is not None:
            # Берем координаты выбранного полигона и перемещаем туда слой затемнения
            selected_poly = self.regions[self.selected_idx]
            self.selection_patch.set_xy(np.array(selected_poly.exterior.coords))
            self.selection_patch.set_visible(True)
        else:
            self.selection_patch.set_visible(False)

        if centroids:
            self.centroid_scatter.set_offsets(centroids)
        else:
            self.centroid_scatter.set_offsets(np.empty((0, 2)))

        self.fig.canvas.draw_idle()

    def _generate_mesh(self):
        """Быстрая генерация сетки Вороного"""
        # Генерация точек через NumPy
        points = np.random.uniform(-1, 1, (self.num_regions, 2))

        # Оптимизировано: мгновенное объединение точек через MultiPoint
        multipoint = MultiPoint(points)
        bounds = box(-1, -1, 1, 1)

        vor = voronoi_diagram(multipoint, envelope=bounds)

        self.regions = []
        for cell in vor.geoms:
            clipped = cell.intersection(bounds)
            if not clipped.is_empty:
                self.regions.append(clipped)

        # Оптимизировано: STRtree для моментального поиска полигона по клику
        self.search_tree = STRtree(self.regions)

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        # Оптимизировано: STRtree находит полигон за O(log N) вместо O(N)
        click_point = Point(event.xdata, event.ydata)
        nearest_idx = self.search_tree.nearest(click_point)

        # Проверяем, попали ли точно внутрь полигона
        if self.regions[nearest_idx].contains(click_point):
            self.selected_idx = nearest_idx
            self.update_visuals()

    def on_key(self, event):
        if self.selected_idx is None or not event.key:
            return

        key = event.key.lower()
        if key in KEY_MAP:
            self.region_colors[self.selected_idx] = KEY_MAP[key]
            self.selected_idx = None  # Сбрасываем фокус после покраски
            self.update_visuals()

    def print_colored_centroids(self):
        """Вывод центроидов закрашенных регионов"""
        colored_indices = np.where(self.region_colors != -1)[0]
        if len(colored_indices) == 0:
            print("\nNo colored regions.")
            return

        print("\nCentroids (colored regions):")
        for idx in colored_indices:
            print(f"Region {idx}: {self.regions[idx].centroid.coords[0]}")

# Запуск приложения

if __name__ == "__main__":
    app = InteractiveVoronoiMap(NUM_REGIONS)
    plt.show()

    # Печать результатов после закрытия окна окна
    app.print_colored_centroids()