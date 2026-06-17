# run_ai.py
import sys
import os

# ✅ Добавляем путь к проекту для корректных импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from map_coloring import (
    AdvancedWaveSimulation,
    Strategy,
    FirstPriorityRule,
    SecondPriorityRule,
    DefaultRule,
)

# ============================================================
#  НАСТРОЙКИ
# ============================================================

# ✅ Проверяем корректность типа карты
MAP_TYPE = "non_convex"  # или "convex", "triangles_convex", "triangles_non_convex"

# ✅ Для тестирования используем МЕНЬШЕЕ количество ячеек
# 1000 может зависнуть на non-convex, 100-200 достаточно для проверки
BASE_CELLS = 1000  # ← уменьшила с 1000 до 200

# ============================================================
#  НАСТРОЙКА СТРАТЕГИИ
# ============================================================

priority_rules = [
]

# ✅ Правильное создание DefaultRule с именованными параметрами
# ✅ НОВЫЙ СПОСОБ: приоритеты в виде строки

default_rule = DefaultRule(
    neighbors="min",
    priority="last colors random",  # ← новый формат!
    mode="connected"
)



# ✅ Создаём стратегию с именем
my_strategy = Strategy(
    priority_rules=priority_rules,
    default_rule=default_rule,
    name="Моя стратегия"
)

# ============================================================
#  ЗАПУСК С ПРОВЕРКАМИ
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ЗАПУСК run_ai.py")
    print("=" * 60)
    print(f"📊 Тип карты: {MAP_TYPE}")
    print(f"📊 Базовых ячеек: {BASE_CELLS}")
    print(f"📊 Стратегия: {my_strategy.name}")
    print("-" * 60)

    try:
        # ✅ Создаём приложение с явной передачей стратегии
        print("🔄 Создание приложения...")
        app = AdvancedWaveSimulation(
            base_cells_count=BASE_CELLS,
            strategy=my_strategy,  # ← ЯВНО ПЕРЕДАЁМ СТРАТЕГИЮ!
            generator_type=MAP_TYPE
        )

        # ✅ Проверяем, что регионы создались
        if not app.colormap or not app.colormap.regions:
            print("❌ ОШИБКА: Не удалось создать регионы!")
            sys.exit(1)

        print(f"✅ Создано {len(app.colormap.regions)} регионов")
        print(f"✅ Из них раскрашено: {len(app.colormap.colored_indices)}")

        # ✅ Проверяем, что стратегия передалась
        if app.strategy is None:
            print("⚠️ ВНИМАНИЕ: Стратегия не передана в приложение!")
        else:
            print(f"✅ Стратегия: {app.strategy.name}")

        print("-" * 60)
        print("▶️ Запуск визуализации...")
        print("🔄 Управление: Пробел - авто/ручной, → шаг вперёд, ← шаг назад")
        print("=" * 60)

        app.run()

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА:")
        print(f"   {type(e).__name__}: {e}")
        print("\n📋 Подробности:")
        import traceback

        traceback.print_exc()
        sys.exit(1)