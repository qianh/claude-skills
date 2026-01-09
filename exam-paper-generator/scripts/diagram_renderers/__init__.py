#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图例渲染器模块
提供多种类型图例的渲染功能
"""

from .base import BaseDiagramRenderer
from .factory import DiagramRendererFactory
from .chemistry import (
    AtomStructureRenderer,
    MolecularStructureRenderer,
    PeriodicTableRenderer,
    ExperimentSetupRenderer,
)
from .charts import (
    BarChartRenderer,
    LineChartRenderer,
    PieChartRenderer,
)
from .math import (
    FunctionGraphRenderer,
    CoordinateSystemRenderer,
    GeometryRenderer,
)
from .flowchart import FlowchartRenderer

__all__ = [
    'BaseDiagramRenderer',
    'DiagramRendererFactory',
    'AtomStructureRenderer',
    'MolecularStructureRenderer',
    'PeriodicTableRenderer',
    'ExperimentSetupRenderer',
    'BarChartRenderer',
    'LineChartRenderer',
    'PieChartRenderer',
    'FunctionGraphRenderer',
    'CoordinateSystemRenderer',
    'GeometryRenderer',
    'FlowchartRenderer',
]
