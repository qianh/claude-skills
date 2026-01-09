#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
化学类图例渲染器
包含：原子结构图、分子结构图、元素周期表、实验装置图
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
import numpy as np
from typing import Dict, Any, List

from .base import BaseDiagramRenderer


class AtomStructureRenderer(BaseDiagramRenderer):
    """原子结构示意图渲染器"""

    diagram_type = "atom_structure"

    def _setup_fonts(self):
        """设置中文字体"""
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染原子结构图"""
        element = spec.get('element', '?')
        nucleus_charge = spec.get('nucleus_charge', 0)
        electron_shells = spec.get('electron_shells', [])
        show_label = spec.get('show_label', True)

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(-4, 4)
        ax.set_ylim(-4, 4)
        ax.set_aspect('equal')
        ax.axis('off')

        # 绘制原子核
        nucleus = Circle((0, 0), 0.5, color='#FF6B6B', ec='#C92A2A', linewidth=2)
        ax.add_patch(nucleus)
        ax.text(0, 0, f'+{nucleus_charge}', ha='center', va='center',
                fontsize=13, fontweight='bold', color='white')

        # 绘制电子层和电子
        colors = ['#4DABF7', '#51CF66', '#FFD43B', '#FF922B', '#E599F7']
        shell_radii = [1.0, 1.8, 2.6, 3.4]

        for i, electrons in enumerate(electron_shells):
            if i >= len(shell_radii):
                break

            radius = shell_radii[i]
            color = colors[i % len(colors)]

            # 绘制电子层轨道
            orbit = Circle((0, 0), radius, fill=False, ec=color, linewidth=1.5, linestyle='--')
            ax.add_patch(orbit)

            # 绘制电子
            for j in range(electrons):
                angle = 2 * np.pi * j / electrons - np.pi/2
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                electron = Circle((x, y), 0.12, color=color)
                ax.add_patch(electron)

        # 标签
        if show_label:
            label = f'{element}（{nucleus_charge}）原子结构示意图'
            ax.text(0, -3.7, self._format_label(label), ha='center', va='center', fontsize=12)

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True


class MolecularStructureRenderer(BaseDiagramRenderer):
    """分子结构图渲染器（简化版）"""

    diagram_type = "molecular_structure"

    def _setup_fonts(self):
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染分子结构图"""
        # 简化实现：显示文本形式的结构式
        formula = spec.get('formula', '')
        structure = spec.get('structure', '')

        fig, ax = plt.subplots(figsize=(8, 3))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 3)
        ax.axis('off')

        ax.text(5, 1.5, self._format_label(structure or formula), ha='center', va='center',
                fontsize=18, fontfamily='monospace')

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True


class PeriodicTableRenderer(BaseDiagramRenderer):
    """元素周期表（局部）渲染器"""

    diagram_type = "periodic_table"

    # 元素数据
    ELEMENTS = {
        1: ('H', '氢'), 2: ('He', '氦'),
        3: ('Li', '锂'), 4: ('Be', '铍'), 5: ('B', '硼'), 6: ('C', '碳'),
        7: ('N', '氮'), 8: ('O', '氧'), 9: ('F', '氟'), 10: ('Ne', '氖'),
        11: ('Na', '钠'), 12: ('Mg', '镁'), 13: ('Al', '铝'), 14: ('Si', '硅'),
        15: ('P', '磷'), 16: ('S', '硫'), 17: ('Cl', '氯'), 18: ('Ar', '氩'),
    }

    # 元素在周期表中的位置 (周期, 族)
    POSITIONS = {
        1: (1, 1), 2: (1, 18),
        3: (2, 1), 4: (2, 2), 5: (2, 13), 6: (2, 14), 7: (2, 15), 8: (2, 16), 9: (2, 17), 10: (2, 18),
        11: (3, 1), 12: (3, 2), 13: (3, 13), 14: (3, 14), 15: (3, 15), 16: (3, 16), 17: (3, 17), 18: (3, 18),
    }

    def _setup_fonts(self):
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染元素周期表（局部）"""
        highlight_elements = spec.get('highlight_elements', [])
        show_periods = spec.get('show_periods', [1, 2, 3])
        show_groups = spec.get('show_groups', list(range(1, 19)))

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.set_xlim(0, 19)
        ax.set_ylim(0, 4.5)
        ax.axis('off')

        # 标题
        ax.text(9.5, 4.2, self._format_label('元素周期表（短周期）'), ha='center', va='center',
                fontsize=13, fontweight='bold')

        # 绘制元素格子
        for atomic_num, (symbol, name) in self.ELEMENTS.items():
            if atomic_num not in self.POSITIONS:
                continue

            period, group = self.POSITIONS[atomic_num]
            if period not in show_periods:
                continue

            x = group
            y = 4 - period

            # 颜色
            if symbol in highlight_elements:
                color = '#FFE066'
            elif group in [1, 2]:  # 金属
                color = '#FFE5D0'
            elif group >= 13:  # 非金属
                color = '#D3F9D8'
            else:
                color = '#E8E8E8'

            # 绘制格子
            rect = FancyBboxPatch((x-0.45, y-0.35), 0.9, 0.7,
                                   boxstyle="round,pad=0.02",
                                   facecolor=color, edgecolor='#333', linewidth=1)
            ax.add_patch(rect)

            # 原子序数
            ax.text(x-0.35, y+0.2, str(atomic_num), fontsize=8, color='#666')
            # 元素符号
            ax.text(x, y-0.05, symbol, ha='center', va='center',
                    fontsize=12, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True


class ExperimentSetupRenderer(BaseDiagramRenderer):
    """实验装置图渲染器"""

    diagram_type = "experiment_setup"

    def _setup_fonts(self):
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染实验装置图"""
        apparatus = spec.get('apparatus', [])
        connections = spec.get('connections', [])
        layout = spec.get('layout', 'horizontal')

        n = len(apparatus)
        if n == 0:
            return False

        fig_width = max(12, n * 3)
        fig, ax = plt.subplots(figsize=(fig_width, 4))

        if layout == 'horizontal':
            ax.set_xlim(0, n * 3 + 1)
            ax.set_ylim(0, 4)
        else:
            ax.set_xlim(0, 6)
            ax.set_ylim(0, n * 2 + 1)

        ax.axis('off')

        # 存储位置用于连接
        positions = {}

        for i, app in enumerate(apparatus):
            name = app.get('name', f'装置{i+1}')
            content = app.get('content', '')

            if layout == 'horizontal':
                x = i * 3 + 1.5
                y = 2
            else:
                x = 3
                y = n * 2 - i * 2

            positions[name] = (x, y)

            # 绘制装置（简化为方框）
            rect = FancyBboxPatch((x-1, y-0.6), 2, 1.2,
                                   boxstyle="round,pad=0.05",
                                   facecolor='#E3F2FD', edgecolor='#1976D2',
                                   linewidth=2)
            ax.add_patch(rect)

            # 装置名称
            ax.text(x, y+0.2, self._format_label(name), ha='center', va='center',
                    fontsize=11, fontweight='bold')
            # 内容物
            if content:
                ax.text(x, y-0.2, self._format_label(content), ha='center', va='center',
                        fontsize=10, color='#666')

        # 绘制连接
        for conn in connections:
            from_name = conn.get('from', '')
            to_name = conn.get('to', '')
            label = conn.get('label', '')

            if from_name in positions and to_name in positions:
                x1, y1 = positions[from_name]
                x2, y2 = positions[to_name]

                if layout == 'horizontal':
                    ax.annotate('', xy=(x2-1, y2), xytext=(x1+1, y1),
                               arrowprops=dict(arrowstyle='->', color='#333', lw=2))
                    if label:
                        ax.text((x1+x2)/2, y1+0.8, self._format_label(label), ha='center', fontsize=10)
                else:
                    ax.annotate('', xy=(x2, y2+0.6), xytext=(x1, y1-0.6),
                               arrowprops=dict(arrowstyle='->', color='#333', lw=2))
                    if label:
                        ax.text(x1+1, (y1+y2)/2, self._format_label(label), ha='left', fontsize=10)

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True
