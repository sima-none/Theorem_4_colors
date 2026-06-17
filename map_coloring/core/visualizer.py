# core/visualizer.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from typing import List, Optional, Dict, Tuple
from shapely.geometry import Point

from map_coloring.core.models import ColorMap, COLORS


class MapVisualizer:
    """Оптимизированная визуализация карты с быстрым доступом к регионам"""

    def __init__(self, colormap: ColorMap, figsize: Tuple[int, int] = (11, 11)):
        self.colormap = colormap
        self.fig, self.ax = plt.subplots(figsize=figsize)

        # ✅ Словарь для быстрого доступа к патчам по region_id
        self.patches: Dict[int, MplPolygon] = {}
        self.patch_list: List[MplPolygon] = []  # Для обратной совместимости

        # ✅ Кэш для центроидов
        self._centroid_offsets = None
        self._centroid_colors = None

        # ✅ Состояние выделения
        self.selected_idx: Optional[int] = None
        self.selection_patch: Optional[MplPolygon] = None

        # ✅ Кэш для быстрого поиска
        self._bounds_set = False

        # ✅ Строим визуализацию
        self._build_plot()
        self._setup_interactivity()

    # ============================================================
    #  ПОСТРОЕНИЕ ГРАФИКА
    # ============================================================

    def _build_plot(self):
        """Строит начальный график с оптимизациями"""
        self.ax.clear()
        self.patches.clear()
        self.patch_list.clear()

        if not self.colormap.regions:
            return

        # ✅ Сортируем регионы: большие рисуем первыми (они ниже)
        sorted_indices = sorted(
            range(len(self.colormap.regions)),
            key=lambda i: self.colormap.regions[i].polygon.area,
            reverse=True  # большие первые → они будут под маленькими
        )

        # ✅ Создаем патчи для всех регионов
        for region_idx in sorted_indices:
            region = self.colormap.regions[region_idx]
            if region.polygon.is_empty:
                continue

            coords = np.array(region.polygon.exterior.coords)

            # Определяем цвет
            color_id = region.color_id
            facecolor = COLORS.get(color_id, COLORS[-1])
            alpha = 0.65 if color_id != -1 else 1.0

            patch = MplPolygon(
                coords,
                closed=True,
                facecolor=facecolor,
                edgecolor="black",
                linewidth=1.2,
                alpha=alpha,
                zorder=1
            )

            # ✅ Храним region_id для быстрого доступа
            patch.region_id = region.id
            patch._region_idx = region_idx  # Индекс в списке

            self.ax.add_patch(patch)
            self.patches[region.id] = patch
            self.patch_list.append(patch)

        # ✅ Патч для выделения (с высоким zorder)
        self.selection_patch = MplPolygon(
            np.empty((0, 2)),
            closed=True,
            facecolor="black",
            alpha=0.25,
            visible=False,
            zorder=9999  # Всегда поверх
        )
        self.ax.add_patch(self.selection_patch)

        # ✅ Скаттер для центроидов
        self.centroid_scatter = self.ax.scatter(
            [], [],
            c="black",
            s=30,
            zorder=10000,
            picker=False
        )

        # ✅ Автонастройка границ
        self._auto_set_bounds()

        # ✅ Отключаем оси для красоты
        self.ax.set_aspect("equal")
        self.ax.axis("off")

    def _auto_set_bounds(self, margin: float = 0.05):
        """Автоматически устанавливает границы осей"""
        if not self.colormap.regions:
            self.ax.set_xlim(-1.1, 1.1)
            self.ax.set_ylim(-1.1, 1.1)
            return

        # ✅ Находим экстенты всех полигонов
        all_coords = []
        for region in self.colormap.regions:
            if not region.polygon.is_empty:
                coords = np.array(region.polygon.exterior.coords)
                all_coords.extend(coords)

        if all_coords:
            all_coords = np.array(all_coords)
            x_min, x_max = all_coords[:, 0].min(), all_coords[:, 0].max()
            y_min, y_max = all_coords[:, 1].min(), all_coords[:, 1].max()

            # ✅ Добавляем отступ
            x_range = x_max - x_min
            y_range = y_max - y_min
            x_margin = x_range * margin if x_range > 0 else 0.1
            y_margin = y_range * margin if y_range > 0 else 0.1

            self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
            self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
        else:
            self.ax.set_xlim(-1.1, 1.1)
            self.ax.set_ylim(-1.1, 1.1)

        self._bounds_set = True

    # ============================================================
    #  ОБНОВЛЕНИЕ ВИЗУАЛИЗАЦИИ (ОПТИМИЗИРОВАННОЕ)
    # ============================================================

    def update(self):
        """Обновляет визуализацию - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ"""
        if not self.colormap.regions:
            return

        # ✅ Обновляем только то, что изменилось
        centroids = []
        need_update = False

        for region in self.colormap.regions:
            patch = self.patches.get(region.id)
            if patch is None:
                continue

            # ✅ Обновляем цвет только если он изменился
            color_id = region.color_id
            new_facecolor = COLORS.get(color_id, COLORS[-1])
            new_alpha = 0.65 if color_id != -1 else 1.0

            if patch.get_facecolor() != new_facecolor or patch.get_alpha() != new_alpha:
                patch.set_facecolor(new_facecolor)
                patch.set_alpha(new_alpha)
                need_update = True

            # ✅ Собираем центроиды для закрашенных регионов
            if color_id != -1:
                centroids.append(region.centroid)

        # ✅ Обновляем выделение
        if self.selected_idx is not None:
            region = self.colormap.get_region(self.selected_idx)
            if region and not region.polygon.is_empty:
                coords = np.array(region.polygon.exterior.coords)
                self.selection_patch.set_xy(coords)
                self.selection_patch.set_visible(True)
                need_update = True
        else:
            if self.selection_patch.get_visible():
                self.selection_patch.set_visible(False)
                need_update = True

        # ✅ Обновляем центроиды
        if centroids:
            offsets = np.array(centroids)
            if len(offsets) > 0:
                self.centroid_scatter.set_offsets(offsets)
                need_update = True
        else:
            if len(self.centroid_scatter.get_offsets()) > 0:
                self.centroid_scatter.set_offsets(np.empty((0, 2)))
                need_update = True

        # ✅ Перерисовываем только если были изменения
        if need_update:
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()

    # ============================================================
    #  БЫСТРЫЙ ПОИСК РЕГИОНА ПО КЛИКУ
    # ============================================================

    def get_region_at_point(self, x: float, y: float) -> Optional[int]:
        """Находит регион по координатам клика (использует STRtree)"""
        if not self.colormap or not self.colormap.regions:
            return None

        # ✅ Используем встроенный STRtree из ColorMap
        return self.colormap.get_region_by_point(x, y)

    # ============================================================
    #  УПРАВЛЕНИЕ ВЫДЕЛЕНИЕМ
    # ============================================================

    def select_region(self, region_id: int):
        """Выделяет регион"""
        self.selected_idx = region_id
        self.update()

    def deselect_region(self):
        """Снимает выделение"""
        self.selected_idx = None
        self.update()

    # ============================================================
    #  ПОДСВЕТКА
    # ============================================================

    def highlight_region(self, idx: int, color: str = "white", linewidth: float = 3.0):
        """Подсвечивает регион (для тупиков)"""
        patch = self.patches.get(idx)
        if patch is not None:
            original_color = patch.get_facecolor()
            patch.set_facecolor(color)
            patch.set_linewidth(linewidth)
            self.fig.canvas.draw_idle()
            # ✅ Возвращаем цвет через небольшую задержку
            self.fig.canvas.start_event_loop(0.5)
            patch.set_facecolor(original_color)
            patch.set_linewidth(1.2)
            self.fig.canvas.draw_idle()

    # ============================================================
    #  УПРАВЛЕНИЕ ЗАГОЛОВКОМ
    # ============================================================

    def set_title(self, title: str, fontsize: int = 11, pad: int = 15):
        """Устанавливает заголовок"""
        self.ax.set_title(title, fontsize=fontsize, pad=pad)
        self.fig.canvas.draw_idle()

    # ============================================================
    #  ИНТЕРАКТИВНОСТЬ
    # ============================================================

    def _setup_interactivity(self):
        """Настраивает интерактивность"""
        # ✅ Подключаем события
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

        # ✅ Подписываемся на обновление размера окна
        self.fig.canvas.mpl_connect("resize_event", self._on_resize)

    def _on_click(self, event):
        """Обработка клика мыши (может быть переопределена)"""
        pass

    def _on_key(self, event):
        """Обработка клавиш (может быть переопределена)"""
        pass

    def _on_resize(self, event):
        """Обработка изменения размера окна"""
        # ✅ Перерисовываем при изменении размера
        self.fig.canvas.draw_idle()

    # ============================================================
    #  ПОКАЗ ОКНА
    # ============================================================

    def show(self):
        """Показывает окно с графиком"""
        plt.show()

    # ============================================================
    #  СВОЙСТВА
    # ============================================================

    @property
    def region_patches(self) -> List[MplPolygon]:
        """Возвращает список всех патчей (для обратной совместимости)"""
        return self.patch_list

    @property
    def selected_patch(self) -> Optional[MplPolygon]:
        """Возвращает патч выбранного региона"""
        if self.selected_idx is not None:
            return self.patches.get(self.selected_idx)
        return None