import random
import numpy as np
import matplotlib.pyplot as plt
# Импортируем базовую карту и цвета из вашего файла
from theorem_4_colors_non_convex import CustomAlgorithmMap, COLORS, NUM_BASE_CELLS
class AdvancedWaveSimulation(CustomAlgorithmMap):
    def __init__(self, base_cells_count):
        super().__init__(base_cells_count)
        # Переменные для контроля автоматического режима
        self.interval_ms = 300
        self.timer_running = False
        self.timer = self.fig.canvas.new_timer(interval=self.interval_ms)
        self.timer.add_callback(self.trigger_ai_step)
        self.update_title_status("ПАУЗА. Нажмите Пробел для старта")
        # Переподключаем клавиатуру, чтобы ловить стрелки и пробел
        self.fig.canvas.mpl_connect("key_press_event", self.on_control_key)
    def update_title_status(self, text):
        """Красивое обновление заголовка"""
        self.ax.set_title(
            f"WAVE AI SIMULATION\n"
            f"← Сбросить текущую | → Новая карта | Пробел: Пауза/Старт\n"
            f"Статус: {text}",
            fontsize=10, pad=15
        )
        self.fig.canvas.draw()
    def trigger_ai_step(self):
        self.ai_step(None)
    def on_control_key(self, event):
        """Управление симуляцией через клавиатуру"""
        if not event.key:
            return
        key = event.key.lower()
        # 1. Пробел — Старт / Пауза
        if key == " ":
            if self.timer_running:
                self.timer.stop()
                self.timer_running = False
                self.update_title_status("ПАУЗА")
            else:
                # На старте, если вообще нет закрашенных клеток, красим ОДНУ случайную для запуска волны
                if np.all(self.region_colors == -1):
                    start_node = random.randint(0, len(self.regions) - 1)
                    self.region_colors[start_node] = random.randint(0, 3)
                    self.update_visuals()
                self.timer.start()
                self.timer_running = True
                self.update_title_status("АВТО-СИМУЛЯЦИЯ...")
        # 2. Стрелка Вправо — Абсолютно новая симуляция (пересоздание геометрии)
        elif event.key == "right":
            if self.timer_running:
                self.timer.stop()
                self.timer_running = False
            print("\n>>> Генерируем новую геометрию карты...")
            self._generate_mesh_by_user_algorithm()
            self.region_colors = np.full(len(self.regions), -1, dtype=int)
            self.ax.clear()
            self.patches.clear()
            self._build_plot()
            self.update_title_status("Создана новая карта. Нажмите Пробел")
        # 3. Стрелка Влево — Сбросить текущую карту до серого состояния и начать заново
        elif event.key == "left":
            if self.timer_running:
                self.timer.stop()
                self.timer_running = False
            print("\n>>> Сброс цветов текущей карты.")
            self.region_colors = np.full(len(self.regions), -1, dtype=int)
            self.update_visuals()
            self.update_title_status("Цвета сброшены. Нажмите Пробел")
    def ai_step(self, event):
        """Модифицированный ИИ по вашей теории волнового и прилежащего роста"""
        uncolored_indices = [i for i, col in enumerate(self.region_colors) if col == -1]
        colored_indices = [i for i, col in enumerate(self.region_colors) if col != -1]
        # Конец симуляции
        if not uncolored_indices:
            print("\nСимуляция завершена! Все области успешно закрашены.")
            self.update_title_status("ГОТОВО! Карта закрашена.")
            if self.timer_running:
                self.timer.stop()
                self.timer_running = False
            return
        all_possible_colors = {0, 1, 2, 3}
        # Собираем данные о незакрашенных клетках
        candidates = {}
        for idx in uncolored_indices:
            neighbors = self.graph[idx]
            taken_colors = {self.region_colors[n] for n in neighbors if self.region_colors[n] != -1}
            allowed_colors = all_possible_colors.difference(taken_colors)
            candidates[idx] = {
                'id': idx,
                'freedom': len(allowed_colors),
                'allowed_colors': list(allowed_colors),
                'taken_colors': taken_colors,
                'is_neighbor_to_colored': not neighbors.isdisjoint(colored_indices)
            }
        # --- ТУПИКОВАЯ ПРОВЕРКА ---
        deadlocks = [c for c in candidates.values() if c['freedom'] == 0]
        if deadlocks:
            dead_id = deadlocks[0]['id']
            if self.timer_running:
                self.timer.stop()
                self.timer_running = False
            self.patches[dead_id].set_facecolor("white")
            self.patches[dead_id].set_alpha(1.0)
            self.patches[dead_id].set_linewidth(3.0)
            self.update_title_status("КРИТИЧЕСКИЙ ТУПИК! Остановка.")
            print(f"🚨 [ТУПИК] Область №{dead_id} зажата всеми 4 цветами.")
            return
        target_id = None
        reason = ""
        # ПРИОРИТЕТ 1: Степень свободы = 1
        level_1 = [c for c in candidates.values() if c['freedom'] == 1]
        if level_1:
            chosen_candidate = random.choice(level_1)
            target_id = chosen_candidate['id']
            reason = "Приоритет 1 (Свобода = 1)"
        # ПРИОРИТЕТ 2: Последний выживший сосед у закрашенной клетки
        if target_id is None:
            prio_2_candidates = []
            for c_idx in colored_indices:
                c_neighbors = self.graph[c_idx]
                # Находим серых соседей этой закрашенной клетки
                gray_neighbors = [n for n in c_neighbors if self.region_colors[n] == -1]
                # Если у закрашенной клетки остался ровно ОДИН серый сосед:
                if len(gray_neighbors) == 1:
                    lonely_gray_id = gray_neighbors[0]
                    prio_2_candidates.append(candidates[lonely_gray_id])
            if prio_2_candidates:
                # Если таких важных клеток нашлось несколько — берем случайную
                chosen_candidate = random.choice(prio_2_candidates)
                target_id = chosen_candidate['id']
                reason = "Приоритет 2 (Последний неокрашенный сосед)"
        # ПРИОРИТЕТ 3: Случайная прилежащая (приграничная) клетка
        if target_id is None:
            # Отбираем только те серые клетки, которые касаются хотя бы одной цветной
            frontier_candidates = [c for c in candidates.values() if c['is_neighbor_to_colored']]
            if frontier_candidates:
                chosen_candidate = random.choice(frontier_candidates)
                target_id = chosen_candidate['id']
                reason = "Приоритет 3 (Случайный фронтовой рост)"
            else:
                # Страховка на случай, если закрашенных клеток вообще еще нет на карте
                chosen_candidate = random.choice(list(candidates.values()))
                target_id = chosen_candidate['id']
                reason = "Стартовый случайный ход"
        # --- ПОКРАСКА ---
        final_candidate = candidates[target_id]
        chosen_color = random.choice(final_candidate['allowed_colors'])
        self.region_colors[target_id] = chosen_color
        print(f"[ИИ] Область №{target_id} -> {COLORS[chosen_color].upper()} [{reason}]")
        self.update_visuals()
if __name__ == "__main__":
    simulation_app = AdvancedWaveSimulation(NUM_BASE_CELLS)
    plt.show()