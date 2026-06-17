# ai_simulation/ai_simulation.py
from map_coloring.core.base_app import BaseColoringApp
from map_coloring.ai_simulation.rules import Strategy, DefaultRule
from map_coloring.core.controller import SimulationController


class AdvancedWaveSimulation(BaseColoringApp):
    def __init__(self, base_cells_count: int = 1000, strategy: Strategy = None, generator_type: str = "merged"):
        # ✅ Сохраняем стратегию ДО вызова super()
        self._strategy = strategy

        # ✅ Проверяем стратегию
        if self._strategy is None:
            print("⚠️ ВНИМАНИЕ: Стратегия не передана! Использую стратегию по умолчанию.")
            default_rule = DefaultRule(neighbors="min", priority="dof", mode="connected")
            self._strategy = Strategy(
                priority_rules=[],
                default_rule=default_rule,
                name="Стратегия по умолчанию"
            )

        # ✅ Вызываем родительский конструктор
        super().__init__(base_cells_count, generator_type=generator_type)

        # ✅ Проверяем, что регионы создались
        if not self.colormap or not self.colormap.regions:
            raise ValueError("Не удалось создать регионы для карты!")

        # ✅ Создаем таймер
        self.timer = self.visualizer.fig.canvas.new_timer(interval=300)

        # ✅ Создаем контроллер С ОДНОЙ стратегией (не создаем лишние)
        self.controller = SimulationController(
            self.colormap,
            self.visualizer,
            self._strategy,  # ← передаем готовую стратегию
            self.timer
        )

        # ✅ Подключаем таймер к контроллеру
        self.timer.add_callback(self.controller.auto_step)

        # ✅ Обновляем статус
        generator_name = self.generator.get_name()
        self._update_status(f"Пробел: Авто | ← → шаги | Enter: Новая карта | Карта: {generator_name}")
        self._connect_events()

    def _connect_events(self):
        """Подключаем обработчики событий"""
        self.visualizer.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _update_status(self, text: str = ""):
        """Обновляет заголовок"""
        if not self.controller:
            return

        status = self.controller.status
        self.visualizer.set_title(
            f"🧠 WAVE AI SIMULATION\n"
            f"← → шаги | Пробел: Авто | Enter: Новая карта\n"
            f"{status} | {text}",
            fontsize=10, pad=15
        )

    def _on_key(self, event):
        """Обработка клавиш"""
        if not event.key or not self.controller:
            return

        # ✅ Обработка клавиш
        if event.key == " ":
            msg = self.controller.toggle_auto()
            self._update_status(msg)

        elif event.key == "right":
            msg = self.controller.step_forward()
            self._update_status(msg)

        elif event.key == "left":
            msg = self.controller.step_backward()
            self._update_status(msg)

        elif event.key == "enter":
            # ✅ Новая карта - ПРАВИЛЬНОЕ обновление
            self._regenerate_map()

    def _regenerate_map(self):
        """Пересоздает карту с сохранением стратегии"""
        print("🔄 Генерация новой карты...")

        # ✅ Останавливаем старый контроллер
        if self.controller and hasattr(self.controller, 'timer'):
            if self.controller.timer:
                self.controller.timer.stop()

        # ✅ Создаем новую карту
        self._init_new_map()

        # ✅ Проверяем, что карта создалась
        if not self.colormap or not self.colormap.regions:
            print("❌ Ошибка: не удалось создать новую карту!")
            return

        # ✅ Создаем НОВЫЙ таймер (старый останавливается автоматически)
        old_timer = self.timer
        self.timer = self.visualizer.fig.canvas.new_timer(interval=300)

        # ✅ Создаем НОВЫЙ контроллер с сохраненной стратегией
        self.controller = SimulationController(
            self.colormap,
            self.visualizer,
            self._strategy,  # ← сохраняем стратегию!
            self.timer
        )

        # ✅ Подключаем таймер
        self.timer.add_callback(self.controller.auto_step)

        # ✅ Останавливаем старый таймер (если был)
        if old_timer:
            try:
                old_timer.stop()
            except:
                pass

        # ✅ Обновляем статус
        generator_name = self.generator.get_name()
        self._update_status(f"🗺️ НОВАЯ КАРТА ({generator_name})")
        print(f"✅ Создано {len(self.colormap.regions)} новых регионов")

    def _on_click(self, event):
        """Обработка кликов (отключаем для AI режима)"""
        pass

    @property
    def strategy(self):
        """Доступ к стратегии"""
        return self._strategy