import numpy as np
import matplotlib.pyplot as plt
import random
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from matplotlib.patches import Polygon as MplPolygon

# -------------------
# Настройки
# -------------------
NUM_BASE_CELLS = 1000

COLORS = {
    -1: "lightgray",
    0: "yellow",
    1: "red",
    2: "blue",
    3: "black"
}
KEY_MAP = {"y": 0, "r": 1, "b": 2, "d": 3, "x": -1}


class CustomAlgorithmMap:
    def __init__(self, base_cells_count):
        self.base_cells_count = base_cells_count
        self.selected_idx = None
        self._generate_mesh_by_user_algorithm()
        self.region_colors = np.full(len(self.regions), -1, dtype=int)
        self.fig, self.ax = plt.subplots(figsize=(11, 11))
        self.patches = []
        self.centroid_scatter = None
        self.selection_patch = None
        self._build_plot()
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
    def _generate_mesh_by_user_algorithm(self):
        points = np.random.uniform(-1, 1, (self.base_cells_count, 2))
        vor = Voronoi(points)
        cell_neighbors = {i: set() for i in range(self.base_cells_count)}
        for p1, p2 in vor.ridge_points:
            cell_neighbors[p1].add(p2)
            cell_neighbors[p2].add(p1)
        base_polygons = {}
        for i, reg_idx in enumerate(vor.point_region):
            region = vor.regions[reg_idx]
            if not region or -1 in region:
                continue
            poly_coords = [vor.vertices[v] for v in region]
            poly = Polygon(poly_coords)
            clipped = poly.intersection(
                Polygon([(-1, -1), (1, -1), (1, 1), (-1, 1)])
            )
            if not clipped.is_empty and isinstance(clipped, Polygon):
                base_polygons[i] = clipped
        regions_dict = {i: [i] for i in base_polygons.keys()}
        total_connections = random.randint(
            int(len(regions_dict) * 0.5),
            int(len(regions_dict) * 0.85)
        )
        connections_made = 0
        while connections_made < total_connections:
            rand_region_id = random.choice(list(regions_dict.keys()))
            current_cells = regions_dict[rand_region_id]
            all_external_neighbors = set()
            for cell in current_cells:
                all_external_neighbors.update(cell_neighbors[cell])
            all_external_neighbors.difference_update(current_cells)
            neighbor_regions = set()
            for neighbor_cell in all_external_neighbors:
                for r_id, r_cells in regions_dict.items():
                    if neighbor_cell in r_cells and r_id != rand_region_id:
                        # 🔥 ИСПРАВЛЕНИЕ 1: Защита от червей при генерации.
                        # Проверяем, что базовая ячейка касается региона именно РЕБРОМ (линией), а не уголком.
                        poly_neighbor = base_polygons[neighbor_cell]
                        has_shared_edge = False
                        for current_cell in current_cells:
                            poly_current = base_polygons[current_cell]
                            if poly_current.touches(poly_neighbor):
                                inter = poly_current.intersection(poly_neighbor)
                                # Если пересечение - линия, значит это полноценное ребро
                                if inter.geom_type in ['LineString', 'MultiLineString'] and inter.length > 1e-5:
                                    has_shared_edge = True
                                    break
                        if has_shared_edge:
                            neighbor_regions.add(r_id)
                        break
            if neighbor_regions:
                target_region_id = random.choice(list(neighbor_regions))
                regions_dict[rand_region_id].extend(regions_dict[target_region_id])
                del regions_dict[target_region_id]
                connections_made += 1
            else:
                continue
        self.regions = []
        for r_id, cells in regions_dict.items():
            polys_to_combine = [
                base_polygons[idx] for idx in cells if idx in base_polygons
            ]
            if not polys_to_combine:
                continue
            merged = unary_union(polys_to_combine)
            if isinstance(merged, Polygon) and not merged.is_empty:
                self.regions.append(merged)
            elif merged.geom_type == "MultiPolygon":
                for p in merged.geoms:
                    if not p.is_empty:
                        self.regions.append(p)

        self.search_tree = STRtree(self.regions)
        # 🔥 ИСПРАВЛЕНИЕ 2: Защита от червей в графе симуляции.
        # Строим карту связей финальных областей. Они соседи, только если делят линию границы.
        self.graph = {i: set() for i in range(len(self.regions))}
        for i in range(len(self.regions)):
            for j in range(i + 1, len(self.regions)):
                if self.regions[i].touches(self.regions[j]):
                    inter = self.regions[i].intersection(self.regions[j])
                    # Точки соприкасания углами отбрасываются, остаются только линии-ребра
                    if inter.geom_type in ['LineString', 'MultiLineString'] and inter.length > 1e-5:
                        self.graph[i].add(j)
                        self.graph[j].add(i)
    def _build_plot(self):
        for i, poly in enumerate(self.regions):
            coords = np.array(poly.exterior.coords)
            patch = MplPolygon(
                coords,
                closed=True,
                facecolor=COLORS[-1],
                edgecolor="black",
                linewidth=1.2,
                zorder=1
            )
            self.ax.add_patch(patch)
            self.patches.append(patch)
        self.selection_patch = MplPolygon(
            np.empty((0, 2)),
            closed=True,
            facecolor="black",
            alpha=0.2,
            visible=False,
            zorder=2
        )
        self.ax.add_patch(self.selection_patch)
        self.centroid_scatter = self.ax.scatter([], [], c="black", s=30, zorder=3)
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.ax.set_title(
            "YOUR CUSTOM ALGORITHM MAP\n"
            "Click region → choose color\n"
            "Y = Yellow | R = Red | B = Blue | D = Black | X = Clear",
            fontsize=11,
            pad=15
        )
    def update_visuals(self):
        centroids = []
        for i, patch in enumerate(self.patches):
            color_id = self.region_colors[i]
            patch.set_facecolor(COLORS[color_id])
            patch.set_alpha(0.65 if color_id != -1 else 1.0)
            if color_id != -1:
                centroids.append(self.regions[i].centroid.coords[0])
        if self.selected_idx is not None:
            self.selection_patch.set_xy(
                np.array(self.regions[self.selected_idx].exterior.coords)
            )
            self.selection_patch.set_visible(True)
        else:
            self.selection_patch.set_visible(False)
        if centroids:
            self.centroid_scatter.set_offsets(np.array(centroids))
        else:
            self.centroid_scatter.set_offsets(np.empty((0, 2)))
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.01)
    def on_click(self, event):
        if event.inaxes != self.ax or event.xdata is None:
            return
        click_point = Point(event.xdata, event.ydata)
        nearest_idx = self.search_tree.nearest(click_point)
        if self.regions[nearest_idx].contains(click_point):
            self.selected_idx = nearest_idx
            self.update_visuals()
    def on_key(self, event):
        if self.selected_idx is None or not event.key:
            return
        key = event.key.lower()
        if key in KEY_MAP:
            self.region_colors[self.selected_idx] = KEY_MAP[key]
            self.update_visuals()
            self.selected_idx = None
            self.selection_patch.set_visible(False)
            self.fig.canvas.draw()

            try:
                self.fig.canvas.manager.window.focus_force()
            except Exception:
                pass
    def print_analysis(self):
        print("\n--- АНАЛИЗ ---")
        for i, color_id in enumerate(self.region_colors):
            if color_id != -1:
                poly = self.regions[i]
                print(f"Фигура №{i} ({COLORS[color_id]}):")
                print(f"  Центр: {poly.centroid.coords[0]}")
                print(f"  Площадь: {poly.area:.4f}")
if __name__ == "__main__":
    app = CustomAlgorithmMap(NUM_BASE_CELLS)
    plt.show()
    app.print_analysis()