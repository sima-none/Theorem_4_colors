# ui/manual_app.py
import numpy as np
from shapely.geometry import Point, LineString
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
        region = self.colormap.get_region(region_idx)
        if region is None:
            return False

        if region.is_colored and region.color_id == color_id:
            return True

        old_color = region.color_id
        self.colormap.set_color(region_idx, color_id)

        if old_color == -1:
            self.history.add(region_idx, color_id)
        else:
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
    """UI для ручной раскраски с навигацией по рёбрам"""

    def __init__(self, base_cells_count: int = 1000, generator_type: str = "non_convex"):
        super().__init__(base_cells_count, generator_type)

        self.controller = SimpleController(self.colormap, self.visualizer)
        self._selected_region = None
        self._pending_selection = None

        self.visualizer.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.visualizer.fig.canvas.mpl_connect("key_press_event", self._on_key)

        self._update_status()

    def _on_click(self, event):
        """Клик мышкой — выбрать область с затемнением"""
        if event.inaxes != self.visualizer.ax or event.xdata is None:
            return

        region_id = self.visualizer.get_region_at_point(event.xdata, event.ydata)
        if region_id is not None:
            if self._pending_selection is not None:
                self.visualizer.deselect_region()

            self._pending_selection = region_id
            self._selected_region = region_id
            self.visualizer.select_region(region_id)

            print(f"✅ Выбрана область {region_id} (ждёт цвета)")
            self._update_status()

    def _get_centroid(self, region_id: int):
        """Возвращает центр масс области"""
        region = self.controller.colormap.get_region(region_id)
        if region is None:
            return None
        return region.centroid

    def _get_edges(self, region_id: int):
        """Возвращает список рёбер полигона области"""
        region = self.controller.colormap.get_region(region_id)
        if region is None:
            return []

        coords = list(region.polygon.exterior.coords)
        edges = []
        for i in range(len(coords) - 1):
            edges.append((coords[i], coords[i + 1]))
        return edges

    def _find_edge_in_direction(self, edges, cx: float, cy: float, direction: str):
        """
        Находит подходящее ребро в заданном направлении.
        """
        best_edge = None
        best_value = None

        for edge in edges:
            p1, p2 = edge
            x1, y1 = p1
            x2, y2 = p2

            if direction in ['up', 'down']:
                if not (min(x1, x2) <= cx <= max(x1, x2)):
                    continue

                if abs(x2 - x1) < 1e-10:
                    y_on_edge = (y1 + y2) / 2
                else:
                    t = (cx - x1) / (x2 - x1)
                    y_on_edge = y1 + t * (y2 - y1)

                if direction == 'down':
                    if best_value is None or y_on_edge < best_value:
                        best_value = y_on_edge
                        best_edge = edge
                else:  # 'up'
                    if best_value is None or y_on_edge > best_value:
                        best_value = y_on_edge
                        best_edge = edge

            else:  # 'right' or 'left'
                if not (min(y1, y2) <= cy <= max(y1, y2)):
                    continue

                if abs(y2 - y1) < 1e-10:
                    x_on_edge = (x1 + x2) / 2
                else:
                    t = (cy - y1) / (y2 - y1)
                    x_on_edge = x1 + t * (x2 - x1)

                if direction == 'right':
                    if best_value is None or x_on_edge > best_value:
                        best_value = x_on_edge
                        best_edge = edge
                else:  # 'left'
                    if best_value is None or x_on_edge < best_value:
                        best_value = x_on_edge
                        best_edge = edge

        return best_edge

    def _find_neighbor_by_edge(self, region_id: int, direction: str):
        """Находит соседнюю область через подходящее ребро"""
        centroid = self._get_centroid(region_id)
        if centroid is None:
            return None

        cx, cy = centroid
        edges = self._get_edges(region_id)

        if not edges:
            return None

        best_edge = self._find_edge_in_direction(edges, cx, cy, direction)

        if best_edge is None:
            print(f"⚠️ Нет подходящего ребра в направлении {direction}")
            return None

        p1, p2 = best_edge

        # Находим СЕРЕДИНУ ребра
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2

        # Смещаемся от середины ребра НАРУЖУ (в сторону от центра)
        dx = cx - mid_x
        dy = cy - mid_y
        dist = np.sqrt(dx * dx + dy * dy)
        if dist > 1e-10:
            # Смещаемся на 1% от ребра ОТ центра (наружу)
            check_x = mid_x - (dx / dist) * 0.01
            check_y = mid_y - (dy / dist) * 0.01
        else:
            check_x, check_y = mid_x, mid_y

        # Проверяем ВСЕ области
        best_neighbor = None
        best_distance = float('inf')

        for other_id, region in enumerate(self.controller.colormap.regions):
            if other_id == region_id:
                continue

            # Проверяем, содержит ли область смещённую точку
            if region.polygon.contains(Point(check_x, check_y)):
                return other_id

            # Если не содержит — проверяем расстояние до полигона
            distance = region.polygon.distance(Point(mid_x, mid_y))
            if distance < best_distance and distance < 0.1:
                best_distance = distance
                best_neighbor = other_id

        if best_neighbor is not None:
            return best_neighbor

        # Запасной вариант: ищем через граф
        edge_line = LineString([p1, p2])
        for neighbor_id in self.controller.colormap.graph.get(region_id, set()):
            neighbor = self.controller.colormap.get_region(neighbor_id)
            if neighbor is None:
                continue

            neighbor_edges = self._get_edges(neighbor_id)
            for n_edge in neighbor_edges:
                n_line = LineString(n_edge)
                if edge_line.distance(n_line) < 1e-6:
                    return neighbor_id

        return None

    def _move_direction(self, direction: str):
        """Движение в направлении"""
        if self._selected_region is None:
            print("⚠️ Сначала выберите область (кликните по ней)")
            return

        if self._pending_selection is not None:
            self.visualizer.deselect_region()
            self._pending_selection = None

        new_region = self._find_neighbor_by_edge(self._selected_region, direction)

        if new_region is not None:
            self._selected_region = new_region
            self._pending_selection = new_region
            self.visualizer.select_region(new_region)
            print(f"➡️ Перешли к области {self._selected_region} (ждёт цвета)")
            self._update_status()
        else:
            print(f"⚠️ Не удалось найти область в направлении {direction}")

    def _on_key(self, event):
        """Обработка клавиш"""
        if not event.key:
            return

        # === УПРАВЛЕНИЕ ЦВЕТАМИ ===
        key = event.key.lower()
        if key in KEY_MAP:
            if self._pending_selection is not None:
                color_id = KEY_MAP[key]
                # ✅ БЕЗ ВСЯКИХ ПРОВЕРОК — просто красим!
                self.controller.paint_region(self._pending_selection, color_id)
                region = self.controller.colormap.get_region(self._pending_selection)
                color_name = "Серый" if color_id == -1 else region.color_name
                print(f"🎨 Область {self._pending_selection} → {color_name}")
                self._update_status()
            else:
                print("⚠️ Сначала выберите область (кликните по ней)")
            return

        # === НАВИГАЦИЯ ПО КАРТЕ (ПО РЁБРАМ) ===
        if event.key == "right":
            self._move_direction('right')
        elif event.key == "left":
            self._move_direction('left')
        elif event.key == "up":
            self._move_direction('up')
        elif event.key == "down":
            self._move_direction('down')

    def _update_status(self):
        """Обновляет статус в заголовке"""
        if self.controller is None:
            return

        progress = self.controller.progress
        pending = self._pending_selection if self._pending_selection is not None else "❌"
        selected = self._selected_region if self._selected_region is not None else "❌"

        status = f"Выбрана: {selected} | Ожидает цвета: {pending} | Шаг {progress}"
        status += " | Стрелки: навигация | Y/R/B/D/X: цвет"
        self.visualizer.set_title(f"🖌️ РУЧНАЯ РАСКРАСКА\n{status}")