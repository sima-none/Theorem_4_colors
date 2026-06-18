# run_manual.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from map_coloring import ManualColoringApp

# ============================================================
#  ⚙️ НАСТРОЙКИ
# ============================================================

CONFIG = {
    "map_type": "non_convex",              # convex, non_convex, triangles_convex, triangles_non_convex
    "base_cells": 1000,                 # количество базовых ячеек
}

# ============================================================
#  ЗАПУСК
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print(f"🖌️ РУЧНАЯ РАСКРАСКА")
    print(f"🚀 {CONFIG['map_type']} | {CONFIG['base_cells']} ячеек")
    print("📌 Кликни область → Y(жёлтый) R(красный) B(синий) D(чёрный) X(серый)")
    print("=" * 50)

    app = ManualColoringApp(
        base_cells_count=CONFIG["base_cells"],
        generator_type=CONFIG["map_type"]
    )

    app.run()