#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程图渲染器
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from typing import Dict, Any, List, Tuple

from .base import BaseDiagramRenderer


class FlowchartRenderer(BaseDiagramRenderer):
    """流程图渲染器"""

    diagram_type = "flowchart"

    # 形状参数
    SHAPE_STYLES = {
        'box': {'boxstyle': 'round,pad=0.1', 'facecolor': '#3498db', 'edgecolor': '#2c3e50'},
        'diamond': {'boxstyle': 'round,pad=0.1', 'facecolor': '#e74c3c', 'edgecolor': '#c0392b'},
        'ellipse': {'boxstyle': 'round,pad=0.2', 'facecolor': '#2ecc71', 'edgecolor': '#27ae60'},
        'parallelogram': {'boxstyle': 'round,pad=0.1', 'facecolor': '#9b59b6', 'edgecolor': '#8e44ad'},
    }

    def _setup_fonts(self):
        plt.rcParams['font.sans-serif'] = ['STHeiti', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """渲染流程图"""
        nodes = spec.get('nodes', [])
        edges = spec.get('edges', [])
        direction = spec.get('direction', 'LR')  # LR: 从左到右, TB: 从上到下
        title = spec.get('title', '')
        node_width = spec.get('node_width', 2.6)
        node_height = spec.get('node_height', 1.3)
        font_size = spec.get('font_size', 14)
        edge_font_size = spec.get('edge_font_size', 12)
        box_alpha = spec.get('box_alpha', 1.0)
        h_spacing = spec.get('h_spacing', node_width + 0.8)
        v_spacing = spec.get('v_spacing', node_height + 0.8)

        if not nodes:
            return False

        # 计算布局
        positions = self._calculate_layout(nodes, edges, direction, h_spacing, v_spacing)

        # 确定图像大小
        if direction == 'LR':
            fig_width = max(14, len(nodes) * h_spacing + 2)
            fig_height = 5
        else:
            fig_width = 8
            fig_height = max(8, len(nodes) * v_spacing + 2)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.axis('off')

        # 绘制边（先画边，再画节点，确保节点在上面）
        self._draw_edges(
            ax,
            nodes,
            edges,
            positions,
            direction,
            node_width,
            node_height,
            edge_font_size,
        )

        # 绘制节点
        self._draw_nodes(ax, nodes, positions, node_width, node_height, font_size, box_alpha)

        # 标题
        if title:
            ax.set_title(self._format_label(title), fontsize=13, fontweight='bold', pad=20)

        # 自动调整范围
        all_x = [p[0] for p in positions.values()]
        all_y = [p[1] for p in positions.values()]
        margin = max(node_width, node_height) + 0.6
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        return True

    def _calculate_layout(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        direction: str,
        h_spacing: float,
        v_spacing: float,
    ) -> Dict[str, Tuple[float, float]]:
        """计算节点位置"""
        positions = {}
        n = len(nodes)

        # 简单的线性布局
        for i, node in enumerate(nodes):
            node_id = node.get('id', f'node_{i}')

            if direction == 'LR':
                x = i * h_spacing
                y = 2
            else:  # TB
                x = 4
                y = (n - i - 1) * v_spacing

            positions[node_id] = (x, y)

        return positions

    def _draw_nodes(
        self,
        ax,
        nodes: List[Dict],
        positions: Dict[str, Tuple[float, float]],
        node_width: float,
        node_height: float,
        font_size: int,
        box_alpha: float,
    ):
        """绘制节点"""
        half_width = node_width / 2
        half_height = node_height / 2

        for node in nodes:
            node_id = node.get('id', '')
            label = node.get('label', node_id)
            shape = node.get('shape', 'box')

            if node_id not in positions:
                continue

            x, y = positions[node_id]

            # 获取形状样式
            style = self.SHAPE_STYLES.get(shape, self.SHAPE_STYLES['box'])

            # 绘制节点框
            box = FancyBboxPatch(
                (x - half_width, y - half_height), node_width, node_height,
                boxstyle=style['boxstyle'],
                facecolor=style['facecolor'],
                edgecolor=style['edgecolor'],
                linewidth=2,
                alpha=box_alpha,
                zorder=2
            )
            ax.add_patch(box)

            # 绘制文字
            ax.text(x, y, self._format_label(label), ha='center', va='center',
                   fontsize=font_size, fontweight='bold', color='white',
                   wrap=True, zorder=3)

    def _draw_edges(
        self,
        ax,
        nodes: List[Dict],
        edges: List[Dict],
        positions: Dict[str, Tuple[float, float]],
        direction: str,
        node_width: float,
        node_height: float,
        edge_font_size: int,
    ):
        """绘制边"""
        # 创建节点ID到索引的映射
        node_ids = {node.get('id', f'node_{i}'): i for i, node in enumerate(nodes)}

        for edge in edges:
            from_id = edge.get('from', '')
            to_id = edge.get('to', '')
            label = edge.get('label', '')

            if from_id not in positions or to_id not in positions:
                continue

            x1, y1 = positions[from_id]
            x2, y2 = positions[to_id]

            # 检查是否是回路（循环边）
            from_idx = node_ids.get(from_id, -1)
            to_idx = node_ids.get(to_id, -1)
            is_back_edge = from_idx > to_idx

            if is_back_edge:
                # 回路边：画曲线
                self._draw_back_edge(
                    ax,
                    x1,
                    y1,
                    x2,
                    y2,
                    label,
                    direction,
                    node_width,
                    node_height,
                    edge_font_size,
                )
            else:
                # 正常边：直线箭头
                self._draw_normal_edge(
                    ax,
                    x1,
                    y1,
                    x2,
                    y2,
                    label,
                    direction,
                    node_width,
                    node_height,
                    edge_font_size,
                )

    def _draw_normal_edge(
        self,
        ax,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str,
        direction: str,
        node_width: float,
        node_height: float,
        edge_font_size: int,
    ):
        """绘制正常边"""
        if direction == 'LR':
            start = (x1 + node_width / 2, y1)
            end = (x2 - node_width / 2, y2)
        else:
            start = (x1, y1 - node_height / 2)
            end = (x2, y2 + node_height / 2)

        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2),
                   zorder=1)

        if label:
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2 + (node_height * 0.35)
            ax.text(mid_x, mid_y, self._format_label(label), ha='center', va='center',
                   fontsize=edge_font_size, color='#666', zorder=3)

    def _draw_back_edge(
        self,
        ax,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str,
        direction: str,
        node_width: float,
        node_height: float,
        edge_font_size: int,
    ):
        """绘制回路边（曲线）"""
        if direction == 'LR':
            # 从右侧绕到下方再到左侧
            offset = -(node_height + 0.6)
            right_x = x1 + node_width / 2
            left_x = x2 - node_width / 2
            path_x = [
                right_x,
                right_x + 0.6,
                right_x + 0.6,
                left_x - 0.6,
                left_x - 0.6,
                left_x,
            ]
            path_y = [y1, y1 + offset, offset, offset, y2, y2]

            ax.plot(path_x, path_y, color='#e74c3c', linewidth=2, zorder=1)
            ax.annotate('', xy=(left_x, y2), xytext=(left_x - 0.6, offset),
                       arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2),
                       zorder=1)
        else:
            # 从下方绕到右侧再到上方
            offset = 6
            path_x = [x1, offset, offset, x2]
            path_y = [y1 - node_height / 2, y1 - node_height / 2, y2 + node_height / 2, y2 + node_height / 2]

            ax.plot(path_x, path_y, color='#e74c3c', linewidth=2, zorder=1)
            ax.annotate('', xy=(x2, y2 + node_height / 2), xytext=(offset, y2 + node_height / 2),
                       arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2),
                       zorder=1)

        if label:
            if direction == 'LR':
                ax.text((x1 + x2) / 2, offset - 0.3, self._format_label(label),
                       ha='center', va='center', fontsize=edge_font_size, color='#e74c3c', zorder=3)
            else:
                ax.text(offset + 0.3, (y1 + y2) / 2, self._format_label(label),
                       ha='left', va='center', fontsize=edge_font_size, color='#e74c3c', zorder=3)
