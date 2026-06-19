# run_manual.py
from map_coloring.ui.manual_app import ManualColoringApp

CONFIG = {
    "map_type": "non_convex",
    "base_cells": 100,
}

if __name__ == "__main__":
    app = ManualColoringApp(
        base_cells_count=CONFIG["base_cells"],
        generator_type=CONFIG["map_type"]
    )
    app.run()