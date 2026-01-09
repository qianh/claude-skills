#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图例渲染器基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import re


class BaseDiagramRenderer(ABC):
    """图例渲染器基类"""

    # 图例类型标识
    diagram_type: str = ""

    def __init__(self):
        self.context: Dict[str, Any] = {}
        self._setup_fonts()

    def _setup_fonts(self):
        """设置字体（子类可覆盖）"""
        pass

    def set_context(self, context: Dict[str, Any]):
        """设置渲染上下文（如学科）"""
        self.context = context or {}

    @abstractmethod
    def render(self, spec: Dict[str, Any], output_path: str) -> bool:
        """
        渲染图例

        Args:
            spec: 图例规格参数
            output_path: 输出文件路径

        Returns:
            是否渲染成功
        """
        pass

    def validate_spec(self, spec: Dict[str, Any]) -> bool:
        """
        验证规格参数

        Args:
            spec: 图例规格参数

        Returns:
            是否有效
        """
        return True

    def _format_label(self, text: str) -> str:
        """根据学科格式化图例文本"""
        if not text:
            return text

        subject = str(self.context.get('subject', '') or '')
        subject_lower = subject.lower()
        is_math = '数学' in subject or 'math' in subject_lower
        is_chem = '化学' in subject or 'chem' in subject_lower

        if is_math and not is_chem:
            return self._format_math_label(text)

        return self._format_chem_label(text)

    def _format_math_label(self, text: str) -> str:
        """数学表达式的上标格式化"""
        return self._format_segments(text, mode='math')

    def _format_chem_label(self, text: str) -> str:
        """化学表达式的下标/电荷格式化"""
        return self._format_segments(text, mode='chem')

    def _format_segments(self, text: str, mode: str) -> str:
        pattern = re.compile(r'[A-Za-z][A-Za-z0-9\(\)\+\-\^]*')

        def repl(match: re.Match) -> str:
            seg = match.group(0)
            if mode == 'math':
                if '^' not in seg:
                    return seg
                return f'${self._math_tex_from_segment(seg)}$'

            if not re.search(r'[0-9\+\-\^]', seg):
                return seg
            return f'${self._chem_tex_from_segment(seg)}$'

        return pattern.sub(repl, text)

    def _math_tex_from_segment(self, seg: str) -> str:
        return re.sub(r'\^(-?[0-9]+)', r'^{\1}', seg)

    def _chem_tex_from_segment(self, seg: str) -> str:
        # 单原子离子，如 Fe2+、Na+、Cl-
        single_ion = re.fullmatch(r'([A-Z][a-z]?)(\d*)([+-])', seg)
        if single_ion:
            elem, digits, sign = single_ion.groups()
            charge = f'{digits}{sign}' if digits else sign
            return f'{elem}^{{{charge}}}'

        s = seg
        s = re.sub(r'\^([0-9]*[+-])', r'^{\1}', s)
        s = re.sub(r'\^([0-9]+)', r'^{\1}', s)
        s = re.sub(r'([0-9])([+-])$', r'\1^{\2}', s)
        s = re.sub(r'([A-Za-z\)])([+-])$', r'\1^{\2}', s)
        s = re.sub(r'(?<=[A-Za-z\)\]])(\d+)', r'_{\1}', s)
        return s
