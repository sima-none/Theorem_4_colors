# run_ai.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from map_coloring import (
    AdvancedWaveSimulation,
    Strategy,
    FirstPriorityRule,
    SecondPriorityRule,
    ThirdPriorityRule,
    DefaultRule,
)

# ============================================================
#  ⚙️ НАСТРОЙКИ
# ============================================================

CONFIG = {
    "map_type": "non_convex",              # convex, non_convex, triangles_convex, triangles_non_convex
    "base_cells": 200,                 # количество базовых ячеек
    "color_priority": True,            # True = приоритет цветных, False = случайный
    "priority_rules": "1 2",         # какие приоритетные правила использовать (1, 2, 3 через пробел)
    "order": "random",     # порядок сортировки в DefaultRule
    "mode": "alone",               # connected или alone
}

# ============================================================
#  РАЗБОР ПРИОРИТЕТОВ (НЕ ТРОГАТЬ!)
# ============================================================

rule_map = {
    "1": FirstPriorityRule(),
    "2": SecondPriorityRule(),
    "3": ThirdPriorityRule(),
}

priority_rules = []
if CONFIG["priority_rules"].strip():
    for key in CONFIG["priority_rules"].split():
        if key in rule_map:
            priority_rules.append(rule_map[key])

# ============================================================
#  ЗАПУСК
# ============================================================

default_rule = DefaultRule(order=CONFIG["order"], mode=CONFIG["mode"])

strategy = Strategy(
    priority_rules=priority_rules,
    default_rule=default_rule,
    name="Стратегия"
)

if __name__ == "__main__":
    print("=" * 50)
    print(f"🚀 {CONFIG['map_type']} | {CONFIG['base_cells']} ячеек")
    print(f"🎯 priority_rules: {CONFIG['priority_rules'] or 'НЕТ'}")
    print(f"📋 order: {CONFIG['order']}")
    print(f"🎨 {'ЦВЕТНЫЕ' if CONFIG['color_priority'] else 'РАНДОМ'}")
    print("=" * 50)

    app = AdvancedWaveSimulation(
        base_cells_count=CONFIG["base_cells"],
        strategy=strategy,
        generator_type=CONFIG["map_type"],
        color_priority=CONFIG["color_priority"]
    )

    app.run()