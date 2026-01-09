#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表类渲染器
包含：柱状图、折线图、饼图
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List

from .base import BaseDiagramRenderer


class BarChartRenderer(BaseDiagramRenderer):
    """柱状图渲染器"""

    diagram_type = "bar_chart"

    def _setup_fonts(self):
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染柱状图"""
        data = spec.get('data', [])
        labels = spec.get('labels', [])
        title = spec.get('title', '')
        xlabel = spec.get('xlabel', '')
        ylabel = spec.get('ylabel', '')
        colors = spec.get('colors', None)

        if not data:
            return False

        fig, ax = plt.subplots(figsize=(10, 6))

        x = np.arange(len(data))
        bar_colors = colors if colors else ['steelblue'] * len(data)

        ax.bar(x, data, color=bar_colors, alpha=0.8)

        ax.set_xlabel(self._format_label(xlabel), fontsize=12)
        ax.set_ylabel(self._format_label(ylabel), fontsize=12)
        ax.set_title(self._format_label(title), fontsize=14, fontweight='bold')

        if labels:
            ax.set_xticks(x)
            ax.set_xticklabels([self._format_label(label) for label in labels], fontsize=11)

        ax.tick_params(axis='y', labelsize=11)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True


class LineChartRenderer(BaseDiagramRenderer):
    """折线图渲染器"""

    diagram_type = "line_chart"

    def _setup_fonts(self):
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染折线图"""
        data_series = spec.get('data_series', {})
        x_values = spec.get('x_values', None)
        title = spec.get('title', '')
        xlabel = spec.get('xlabel', '')
        ylabel = spec.get('ylabel', '')
        show_legend = spec.get('show_legend', True)

        if not data_series:
            return False

        fig, ax = plt.subplots(figsize=(10, 6))

        for label, data in data_series.items():
            fmt_label = self._format_label(label)
            if x_values:
                ax.plot(x_values, data, marker='o', label=fmt_label, linewidth=2)
            else:
                ax.plot(data, marker='o', label=fmt_label, linewidth=2)

        ax.set_xlabel(self._format_label(xlabel), fontsize=12)
        ax.set_ylabel(self._format_label(ylabel), fontsize=12)
        ax.set_title(self._format_label(title), fontsize=14, fontweight='bold')

        if show_legend and len(data_series) > 1:
            ax.legend(fontsize=11)

        ax.tick_params(axis='both', labelsize=11)
        ax.grid(alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True


class PieChartRenderer(BaseDiagramRenderer):
    """饼图渲染器"""

    diagram_type = "pie_chart"

    def _setup_fonts(self):
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染饼图"""
        data = spec.get('data', [])
        labels = spec.get('labels', [])
        title = spec.get('title', '')
        colors = spec.get('colors', None)
        explode = spec.get('explode', None)
        show_percentage = spec.get('show_percentage', True)

        if not data:
            return False

        fig, ax = plt.subplots(figsize=(8, 8))

        autopct = '%1.1f%%' if show_percentage else None
        chart_colors = colors if colors else plt.cm.Set3(np.linspace(0, 1, len(data)))

        ax.pie(
            data,
            labels=[self._format_label(label) for label in labels],
            autopct=autopct,
            colors=chart_colors,
            explode=explode,
            startangle=90,
            textprops={'fontsize': 11}
        )

        ax.set_title(self._format_label(title), fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True
