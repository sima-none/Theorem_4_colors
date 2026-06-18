# run_ai.py
from map_coloring.ui.ai_app import AIColoringApp
from map_coloring.solvers import Strategy, DefaultRule, FirstPriorityRule, SecondPriorityRule

CONFIG = {
    "map_type": "convex",
    "base_cells": 200,
    "color_priority": True,
    "priority_rules": "1 2",
    "order": "colors dead_min alive_max",
}

if __name__ == "__main__":
    # Создаём стратегию
    rule_map = {"1": FirstPriorityRule(), "2": SecondPriorityRule()}
    priority_rules = [rule_map[k] for k in CONFIG["priority_rules"].split() if k in rule_map]
    default_rule = DefaultRule(order=CONFIG["order"], mode="connected")
    strategy = Strategy(priority_rules=priority_rules, default_rule=default_rule)

    # Запускаем приложение
    app = AIColoringApp(
        base_cells_count=CONFIG["base_cells"],
        generator_type=CONFIG["map_type"],
        strategy=strategy,
        color_priority=CONFIG["color_priority"]
    )
    app.run()