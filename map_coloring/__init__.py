# map_coloring/__init__.py
from .core.models import ColorMap, Region, COLORS, KEY_MAP, DEFAULT_COLORS
from .core.controller import SimulationController
from .core.history import HistoryManager

from .generators import ConvexMapGenerator, NonConvexMapGenerator

from .solvers import (
    Rule, DefaultRule, DefaultRuleSelector,
    FirstPriorityRule, SecondPriorityRule, ThirdPriorityRule,
    Strategy, DescendingRule, AscendingRule, RandomRule
)

from .ui.visualizer import MapVisualizer
from .ui.base_app import BaseColoringApp
from .ui.ai_app import AIColoringApp
from .ui.manual_app import ManualColoringApp

__all__ = [
    # Core
    'ColorMap', 'Region', 'COLORS', 'KEY_MAP', 'DEFAULT_COLORS',
    'SimulationController', 'HistoryManager',

    # Generators
    'ConvexMapGenerator', 'NonConvexMapGenerator',

    # Solvers
    'Rule', 'DefaultRule', 'DefaultRuleSelector',
    'FirstPriorityRule', 'SecondPriorityRule', 'ThirdPriorityRule',
    'Strategy', 'DescendingRule', 'AscendingRule', 'RandomRule',

    # UI
    'MapVisualizer', 'BaseColoringApp', 'AIColoringApp', 'ManualColoringApp',
]