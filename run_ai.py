# run_ai.py
from map_coloring import (
    AdvancedWaveSimulation,
    Strategy,
    FirstPriorityRule,
    SecondPriorityRule,
    DefaultRule,
)

MAP_TYPE = "triangles_non_convex"  # ← Убедитесь, что это "non_convex"

default = DefaultRule(neighbors="min", priority="dof", mode="connected")
priority_rules = [FirstPriorityRule(), SecondPriorityRule()]

my_strategy = Strategy(
    priority_rules=priority_rules,
    default_rule=default,
    name="Моя стратегия"
)

if __name__ == "__main__":
    print("🚀 Запуск с MAP_TYPE =", MAP_TYPE)
    print("📊 Создаем приложение...")

    app = AdvancedWaveSimulation(100, strategy=my_strategy, generator_type=MAP_TYPE)

    print(f"✅ Создано {len(app.colormap.regions)} регионов")  # ← ДОБАВЬТЕ

    if not app.colormap.regions:
        print("❌ ОШИБКА: Нет регионов!")
    else:
        print("▶️ Запускаем визуализацию...")
        app.run()