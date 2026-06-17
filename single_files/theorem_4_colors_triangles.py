import random
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union
from matplotlib.patches import Polygon as MplPolygon

# -------------------
# Настройки
# -------------------
SIDE_LEN = 0.12  # Длина стороны правильного треугольника (задает масштаб)
NUM_FIGURES = 18  # Количество собираемых сложных фигур
CELLS_PER_FIG = 25  # Количество треугольников в одной фигуре

COLORS = {
    -1: "lightgray",
    0: "yellow",
    1: "red",
    2: "blue",
    3: "black"
}

# -------------------
# 1. Генерация правильной треугольной сетки (60-60-60)
# -------------------
triangles = {}
cell_id = 0

dx = SIDE_LEN
dy = SIDE_LEN * np.sqrt(3) / 2  # Высота правильного треугольника

# Границы экрана для заполнения сеткой
X_MIN, X_MAX = -1.2, 1.2
Y_MIN, Y_MAX = -1.2, 1.2

# Буферная матрица для быстрого поиска соседей по индексам (row, col, orientation)
# orientation: 0 - вершиной вверх, 1 - вершиной вниз
grid_matrix = {}

# Генерируем ряды треугольников
row = 0
y = Y_MIN
while y < Y_MAX:
    # Смещение каждого четного ряда для правильной стыковки
    x_offset = 0.0 if row % 2 == 0 else -dx / 2

    col = 0
    x = X_MIN + x_offset
    while x < X_MAX:
        # 1. Треугольник вершиной ВВЕРХ
        p1 = (x, y)
        p2 = (x + dx, y)
        p3 = (x + dx / 2, y + dy)

        # Обрезаем по bounding box [-1, 1], чтобы сохранить форму экрана
        poly_up = Polygon([p1, p2, p3])
        if poly_up.centroid.x >= -1 and poly_up.centroid.x <= 1 and poly_up.centroid.y >= -1 and poly_up.centroid.y <= 1:
            grid_matrix[(row, col, 0)] = cell_id
            triangles[cell_id] = {"poly": poly_up, "neighbors": set(), "assigned": False}
            cell_id += 1

        # 2. Треугольник вершиной ВНИЗ
        p4 = (x + dx / 2, y + dy)
        p5 = (x + 3 * dx / 2, y + dy)
        p6 = (x + dx, y)

        poly_down = Polygon([p4, p5, p6])
        if poly_down.centroid.x >= -1 and poly_down.centroid.x <= 1 and poly_down.centroid.y >= -1 and poly_down.centroid.y <= 1:
            grid_matrix[(row, col, 1)] = cell_id
            triangles[cell_id] = {"poly": poly_down, "neighbors": set(), "assigned": False}
            cell_id += 1

        x += dx
        col += 1
    y += dy
    row += 1

# Заполнение графа соседей (проверка по индексам сетки)
for (r, c, o), i in grid_matrix.items():
    if o == 0:  # Вершиной вверх
        # Соседи: внизу (r, c, 1 - если сдвиг), слева-снизу, справа-снизу в зависимости от ряда
        # Проще и надежнее для правильной сетки: найти тех, у кого o==1
        if (r, c, 1) in grid_matrix: triangles[i]["neighbors"].add(grid_matrix[(r, c, 1)])
        if (r, c - 1, 1) in grid_matrix: triangles[i]["neighbors"].add(grid_matrix[(r, c - 1, 1)])
        if (r - 1, c, 1) in grid_matrix if r % 2 == 0 else (r - 1, c + 1, 1) in grid_matrix:
            neighbor_row = r - 1
            neighbor_col = c if r % 2 == 0 else c + 1
            if (neighbor_row, neighbor_col, 1) in grid_matrix:
                triangles[i]["neighbors"].add(grid_matrix[(neighbor_row, neighbor_col, 1)])
    else:  # Вершиной вниз
        if (r, c, 0) in grid_matrix: triangles[i]["neighbors"].add(grid_matrix[(r, c, 0)])
        if (r, c + 1, 0) in grid_matrix: triangles[i]["neighbors"].add(grid_matrix[(r, c + 1, 0)])
        if (r + 1, c, 0) in grid_matrix if r % 2 == 0 else (r + 1, c - 1, 0) in grid_matrix:
            neighbor_row = r + 1
            neighbor_col = c if r % 2 == 0 else c - 1
            if (neighbor_row, neighbor_col, 0) in grid_matrix:
                triangles[i]["neighbors"].add(grid_matrix[(neighbor_row, neighbor_col, 0)])

# -------------------
# 2. Пошаговое выращивание фигур
# -------------------
figures = []

for _ in range(NUM_FIGURES):
    available = [k for k, v in triangles.items() if not v["assigned"]]
    if not available:
        break

    start_cell = random.choice(available)
    current_cluster = [start_cell]
    triangles[start_cell]["assigned"] = True

    growth_front = set(triangles[start_cell]["neighbors"])

    for _ in range(CELLS_PER_FIG - 1):
        valid_front = [c for c in growth_front if c in triangles and not triangles[c]["assigned"]]
        if not valid_front:
            break

        next_cell = random.choice(valid_front)
        current_cluster.append(next_cell)
        triangles[next_cell]["assigned"] = True
        growth_front.update(triangles[next_cell]["neighbors"])

    polygons_to_union = [triangles[c]["poly"] for c in current_cluster]
    merged_poly = unary_union(polygons_to_union)

    if isinstance(merged_poly, MultiPolygon):
        for part in merged_poly.geoms:
            figures.append(part)
    elif isinstance(merged_poly, Polygon):
        figures.append(merged_poly)

# Оставшиеся одиночные треугольники добавляем как отдельные области
for k, v in triangles.items():
    if not v["assigned"]:
        figures.append(v["poly"])

# -------------------
# 3. Состояние интерактива
# -------------------
region_colors = [-1] * len(figures)  # Изначально все серые (-1)
patches = []

fig, ax = plt.subplots(figsize=(12, 12))


# -------------------
# 4. Отрисовка и Интерактивность
# -------------------
def draw_map():
    ax.clear()
    patches.clear()

    for i, poly in enumerate(figures):
        coords = np.array(poly.exterior.coords)
        color_id = region_colors[i]
        facecolor = COLORS.get(color_id, "lightgray")

        # Рисуем контуры
        patch = MplPolygon(coords, closed=True, facecolor=facecolor, edgecolor="#444444", linewidth=1.2)
        ax.add_patch(patch)
        patches.append(patch)

    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_aspect('equal')
    ax.axis('off')  # Скрываем оси для красоты
    plt.title("Идеальная сетка 60-60-60. Кликните на фигуру для перекрашивания", fontsize=14)
    fig.canvas.draw_idle()


def on_click(event):
    # Проверяем, что клик был внутри осей
    if event.inaxes != ax:
        return

    click_point = Point(event.xdata, event.ydata)

    # Ищем, в какую фигуру попал клик
    for i, poly in enumerate(figures):
        if poly.contains(click_point):
            # Циклическое переключение цветов: -1 -> 0 -> 1 -> 2 -> 3 -> -1
            current_color = region_colors[i]
            color_keys = list(COLORS.keys())
            next_index = (color_keys.index(current_color) + 1) % len(color_keys)
            region_colors[i] = color_keys[next_index]

            # Обновляем цвет патча без полной перерисовки осей (для скорости)
            patches[i].set_facecolor(COLORS[region_colors[i]])
            fig.canvas.draw_idle()
            break


# Подключаем событие клика мыши
fig.canvas.mpl_connect('button_press_event', on_click)

# Первый запуск
draw_map()
plt.show()
