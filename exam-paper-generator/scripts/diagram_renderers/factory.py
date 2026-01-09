#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图例渲染器工厂
"""

from typing import Dict, Optional, Type
from .base import BaseDiagramRenderer


class DiagramRendererFactory:
    """图例渲染器工厂"""

    _renderers: Dict[str, Type[BaseDiagramRenderer]] = {}
    _instances: Dict[str, BaseDiagramRenderer] = {}

    @classmethod
    def register(cls, diagram_type: str, renderer_class: Type[BaseDiagramRenderer]):
        """
        注册渲染器

        Args:
            diagram_type: 图例类型
            renderer_class: 渲染器类
        """
        cls._renderers[diagram_type] = renderer_class

    @classmethod
    def get_renderer(cls, diagram_type: str) -> Optional[BaseDiagramRenderer]:
        """
        获取渲染器实例

        Args:
            diagram_type: 图例类型

        Returns:
            渲染器实例，如果不存在则返回 None
        """
        # 延迟导入，避免循环依赖
        cls._ensure_registered()

        if diagram_type not in cls._instances:
            renderer_class = cls._renderers.get(diagram_type)
            if renderer_class:
                cls._instances[diagram_type] = renderer_class()
            else:
                return None

        return cls._instances.get(diagram_type)

    @classmethod
    def _ensure_registered(cls):
        """确保所有渲染器已注册"""
        if cls._renderers:
            return

        # 导入并注册所有渲染器
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

        # 化学类
        cls.register('atom_structure', AtomStructureRenderer)
        cls.register('molecular_structure', MolecularStructureRenderer)
        cls.register('periodic_table', PeriodicTableRenderer)
        cls.register('experiment_setup', ExperimentSetupRenderer)

        # 图表类
        cls.register('bar_chart', BarChartRenderer)
        cls.register('line_chart', LineChartRenderer)
        cls.register('pie_chart', PieChartRenderer)

        # 数学类
        cls.register('function_graph', FunctionGraphRenderer)
        cls.register('coordinate_system', CoordinateSystemRenderer)
        cls.register('geometry', GeometryRenderer)

        # 流程图
        cls.register('flowchart', FlowchartRenderer)

    @classmethod
    def list_available(cls) -> list:
        """列出所有可用的渲染器类型"""
        cls._ensure_registered()
        return list(cls._renderers.keys())
