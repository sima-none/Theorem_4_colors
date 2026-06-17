# core/visualizer.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from typing import List, Optional

from .models import ColorMap, COLORS


class MapVisualizer:
    def __init__(self, colormap: ColorMap, figsize: tuple = (11, 11)):
        self.colormap = colormap
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.patches: List[MplPolygon] = []
        self.selection_patch: Optional[MplPolygon] = None
        self.centroid_scatter = None
        self.selected_idx: Optional[int] = None
        self._patch_to_region: List[int] = []
        self._build_plot()

    def _build_plot(self):
        """Строит начальный график — маленькие области рисуются последними (поверх)"""
        # Сортируем: большие → первые, маленькие → последние (поверх)
        sorted_indices = sorted(
            range(len(self.colormap.regions)),
            key=lambda i: self.colormap.regions[i].polygon.area,
            reverse=True  # большие первые
        )

        self._patch_to_region = []

        for region_idx in sorted_indices:
            region = self.colormap.regions[region_idx]
            coords = np.array(region.polygon.exterior.coords)
            patch = MplPolygon(
                coords, closed=True,
                facecolor=COLORS[-1],
                edgecolor="black",
                linewidth=1.2
            )
            patch.region_id = region.id
            self.ax.add_patch(patch)
            self.patches.append(patch)
            self._patch_to_region.append(region.id)

        # Патч для выделения
        self.selection_patch = MplPolygon(
            np.empty((0, 2)), closed=True,
            facecolor="black", alpha=0.2,
            visible=False, zorder=9999
        )
        self.ax.add_patch(self.selection_patch)

        # Скаттер для центроидов
        self.centroid_scatter = self.ax.scatter([], [], c="black", s=30, zorder=10000)

        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_aspect("equal")
        self.ax.axis("off")

    def update(self):
        """Обновляет визуализацию"""
        centroids = []
        for patch in self.patches:
            region = self.colormap.regions[patch.region_id]
            color_id = region.color_id
            patch.set_facecolor(COLORS[color_id])
            patch.set_alpha(0.65 if color_id != -1 else 1.0)
            if color_id != -1:
                centroids.append(region.centroid)

        if self.selected_idx is not None:
            polygon = self.colormap.regions[self.selected_idx].polygon
            self.selection_patch.set_xy(np.array(polygon.exterior.coords))
            self.selection_patch.set_visible(True)
        else:
            self.selection_patch.set_visible(False)

        if centroids:
            self.centroid_scatter.set_offsets(np.array(centroids))
        else:
            self.centroid_scatter.set_offsets(np.empty((0, 2)))

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def set_title(self, title: str, fontsize: int = 11, pad: int = 15):
        self.ax.set_title(title, fontsize=fontsize, pad=pad)
        self.fig.canvas.draw()

    def highlight_region(self, idx: int, color: str = "white", linewidth: float = 3.0):
        for patch in self.patches:
            if patch.region_id == idx:
                patch.set_facecolor(color)
                patch.set_linewidth(linewidth)
                self.fig.canvas.draw()
                return

    def get_region_at_point(self, x: float, y: float) -> Optional[int]:
        from shapely.geometry import Point
        point = Point(x, y)
        for region in self.colormap.regions:
            if region.polygon.contains(point):
                return region.id
        return None

    def show(self):
        plt.show()