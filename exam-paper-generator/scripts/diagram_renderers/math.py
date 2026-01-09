#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学类图例渲染器
包含：函数图像、坐标系、几何图形
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Polygon, FancyArrowPatch
import numpy as np
from typing import Dict, Any, List, Callable

from .base import BaseDiagramRenderer


class FunctionGraphRenderer(BaseDiagramRenderer):
    """函数图像渲染器"""

    diagram_type = "function_graph"

    def _setup_fonts(self):
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染函数图像"""
        functions = spec.get('functions', [])
        x_range = spec.get('x_range', [-10, 10])
        y_range = spec.get('y_range', None)
        title = spec.get('title', '')
        show_grid = spec.get('show_grid', True)
        show_axes = spec.get('show_axes', True)
        show_legend = spec.get('show_legend', True)

        if not functions:
            return False

        fig, ax = plt.subplots(figsize=(10, 8))

        x = np.linspace(x_range[0], x_range[1], 1000)

        for func_spec in functions:
            expression = func_spec.get('expression', 'x')
            label = func_spec.get('label', expression)
            color = func_spec.get('color', None)

            try:
                # 安全评估表达式
                y = self._safe_eval(expression, x)

                # 处理 y 值中的无穷大和 NaN
                y = np.where(np.isfinite(y), y, np.nan)

                ax.plot(x, y, label=self._format_label(label), color=color, linewidth=2)
            except Exception as e:
                print(f"函数解析失败: {expression}, 错误: {e}")
                continue

        # 坐标轴
        if show_axes:
            ax.axhline(y=0, color='k', linewidth=0.8)
            ax.axvline(x=0, color='k', linewidth=0.8)

        # 网格
        if show_grid:
            ax.grid(alpha=0.3)

        # 范围
        ax.set_xlim(x_range)
        if y_range:
            ax.set_ylim(y_range)

        # 标签
        ax.set_xlabel(self._format_label('x'), fontsize=11)
        ax.set_ylabel(self._format_label('y'), fontsize=11)
        ax.set_title(self._format_label(title), fontsize=13, fontweight='bold')

        # 图例
        if show_legend and len(functions) > 0:
            ax.legend()

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True

    def _safe_eval(self, expression: str, x: np.ndarray) -> np.ndarray:
        """安全评估数学表达式"""
        # 允许的函数和常量
        safe_dict = {
            'x': x,
            'sin': np.sin,
            'cos': np.cos,
            'tan': np.tan,
            'exp': np.exp,
            'log': np.log,
            'log10': np.log10,
            'sqrt': np.sqrt,
            'abs': np.abs,
            'pi': np.pi,
            'e': np.e,
        }

        # 替换常见表示法
        expr = expression.replace('^', '**')

        return eval(expr, {"__builtins__": {}}, safe_dict)


class CoordinateSystemRenderer(BaseDiagramRenderer):
    """坐标系渲染器"""

    diagram_type = "coordinate_system"

    def _setup_fonts(self):
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染坐标系"""
        points = spec.get('points', [])
        vectors = spec.get('vectors', [])
        lines = spec.get('lines', [])
        x_range = spec.get('x_range', [-5, 5])
        y_range = spec.get('y_range', [-5, 5])
        title = spec.get('title', '')
        show_grid = spec.get('show_grid', True)

        fig, ax = plt.subplots(figsize=(8, 8))

        # 坐标轴
        ax.axhline(y=0, color='k', linewidth=1)
        ax.axvline(x=0, color='k', linewidth=1)

        # 网格
        if show_grid:
            ax.grid(alpha=0.3)

        # 绘制点
        for point in points:
            x = point.get('x', 0)
            y = point.get('y', 0)
            label = point.get('label', '')
            color = point.get('color', 'red')

            ax.plot(x, y, 'o', color=color, markersize=8)
            if label:
                ax.annotate(self._format_label(label), (x, y), xytext=(5, 5),
                           textcoords='offset points', fontsize=10)

        # 绘制向量
        for vec in vectors:
            start = vec.get('start', [0, 0])
            end = vec.get('end', [1, 1])
            label = vec.get('label', '')
            color = vec.get('color', 'blue')

            ax.annotate('', xy=end, xytext=start,
                       arrowprops=dict(arrowstyle='->', color=color, lw=2))

            if label:
                mid_x = (start[0] + end[0]) / 2
                mid_y = (start[1] + end[1]) / 2
                ax.text(mid_x, mid_y, self._format_label(label), fontsize=10, color=color)

        # 绘制直线
        for line in lines:
            if 'points' in line:
                pts = line['points']
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                ax.plot(xs, ys, color=line.get('color', 'green'),
                       linewidth=line.get('width', 1.5),
                       linestyle=line.get('style', '-'))

        ax.set_xlim(x_range)
        ax.set_ylim(y_range)
        ax.set_aspect('equal')
        ax.set_xlabel(self._format_label('x'), fontsize=11)
        ax.set_ylabel(self._format_label('y'), fontsize=11)
        ax.set_title(self._format_label(title), fontsize=13, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True


class GeometryRenderer(BaseDiagramRenderer):
    """几何图形渲染器"""

    diagram_type = "geometry"

    def _setup_fonts(self):
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染几何图形"""
        shapes = spec.get('shapes', [])
        points = spec.get('points', [])
        labels = spec.get('labels', [])
        title = spec.get('title', '')
        x_range = spec.get('x_range', [0, 10])
        y_range = spec.get('y_range', [0, 10])

        fig, ax = plt.subplots(figsize=(8, 8))

        # 绘制图形
        for shape in shapes:
            shape_type = shape.get('type', '')

            if shape_type == 'circle':
                center = shape.get('center', [5, 5])
                radius = shape.get('radius', 2)
                circle = Circle(center, radius, fill=False,
                               edgecolor=shape.get('color', 'blue'),
                               linewidth=shape.get('width', 2))
                ax.add_patch(circle)

            elif shape_type == 'polygon':
                vertices = shape.get('vertices', [])
                if vertices:
                    poly = Polygon(vertices, fill=shape.get('fill', False),
                                  facecolor=shape.get('facecolor', 'lightblue'),
                                  edgecolor=shape.get('color', 'blue'),
                                  linewidth=shape.get('width', 2),
                                  alpha=shape.get('alpha', 0.3))
                    ax.add_patch(poly)

            elif shape_type == 'line':
                start = shape.get('start', [0, 0])
                end = shape.get('end', [1, 1])
                ax.plot([start[0], end[0]], [start[1], end[1]],
                       color=shape.get('color', 'blue'),
                       linewidth=shape.get('width', 2),
                       linestyle=shape.get('style', '-'))

            elif shape_type == 'arc':
                center = shape.get('center', [5, 5])
                radius = shape.get('radius', 2)
                theta1 = shape.get('theta1', 0)
                theta2 = shape.get('theta2', 90)
                arc = patches.Arc(center, 2*radius, 2*radius,
                                 angle=0, theta1=theta1, theta2=theta2,
                                 edgecolor=shape.get('color', 'blue'),
                                 linewidth=shape.get('width', 2))
                ax.add_patch(arc)

        # 绘制点
        for point in points:
            x = point.get('x', 0)
            y = point.get('y', 0)
            label = point.get('label', '')

            ax.plot(x, y, 'o', color='red', markersize=6)
            if label:
                ax.annotate(self._format_label(label), (x, y), xytext=(5, 5),
                           textcoords='offset points', fontsize=11,
                           fontweight='bold')

        ax.set_xlim(x_range)
        ax.set_ylim(y_range)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(self._format_label(title), fontsize=13, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True
