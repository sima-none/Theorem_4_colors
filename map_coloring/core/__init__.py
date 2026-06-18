# map_coloring/core/__init__.py
from .models import ColorMap, Region, COLORS, KEY_MAP, DEFAULT_COLORS
from .controller import SimulationController  # ← исправлено!
from .history import HistoryManager

__all__ = [
    'ColorMap', 'Region', 'COLORS', 'KEY_MAP', 'DEFAULT_COLORS',
    'SimulationController', 'HistoryManager',  # ← исправлено!
]