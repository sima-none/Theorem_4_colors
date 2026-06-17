# run.py
from map_coloring import (
    AdvancedWaveSimulation,
    Strategy,
    FirstPriorityRule,
    ChainPriorityRule,
    SecondPriorityRule,
    ThirdPriorityRule,
    DefaultRule,
)



MAP_TYPE = "non_convex"  # ← поменяй на "voronoi"


# ============================================================
#  НАСТРОЙКА ДЕФОЛТА
# ============================================================

default = DefaultRule("min", "dof", "connected")


# ============================================================
#  НАСТРОЙКА ПРИОРИТЕТОВ
# ============================================================

priority_rules = [
    FirstPriorityRule(),
]


# ============================================================
#  ЗАПУСК
# ============================================================

my_strategy = Strategy(
    priority_rules=priority_rules,
    default_rule=default,
    name="Моя стратегия"
)

if __name__ == "__main__":
    app = AdvancedWaveSimulation(100, strategy=my_strategy, generator_type=MAP_TYPE)
    app.run()