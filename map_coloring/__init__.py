# map_coloring/__init__.py
from .core.models import ColorMap, Region, COLORS, KEY_MAP
from .core.visualizer import MapVisualizer
from .core.base_app import BaseColoringApp
from .core.controller import SimulationController
from .core.generators import (
    ConvexMapGenerator,
    NonConvexMapGenerator
)

# ai_simulation
from .ai_simulation.history import HistoryManager
from map_coloring.core.rules import (
    Rule,
    FirstPriorityRule,
    SecondPriorityRule,
    ThirdPriorityRule,
    DescendingRule,
    AscendingRule,
    DefaultRule,
    RandomRule,
    Strategy,
    DefaultRuleSelector
)

# manual
from .manual_simulation.manual_simulation import ManualColoringApp

# ai_simulation
from .ai_simulation.ai_simulation import AdvancedWaveSimulation

__all__ = [
    # Core
    'ColorMap', 'Region', 'COLORS', 'KEY_MAP',
    'MapVisualizer', 'BaseColoringApp', 'SimulationController',
    'ConvexMapGenerator', 'NonConvexMapGenerator',

    # History
    'HistoryManager',

    # Rules
    'Rule', 'FirstPriorityRule', 'SecondPriorityRule', 'ThirdPriorityRule',
    'DescendingRule', 'AscendingRule', 'RandomRule',
    'Strategy', 'DefaultRuleSelector',

    # Apps
    'ManualColoringApp', 'AdvancedWaveSimulation'
]