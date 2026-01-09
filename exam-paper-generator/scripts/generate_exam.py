#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用试卷渲染引擎
从 JSON 数据文件生成 PDF 或 Word 格式的试卷

使用方法:
    python generate_exam.py input.json -o output.pdf
    python generate_exam.py input.json -o output.pdf --with-answers
    python generate_exam.py input.json -o output.docx --format word
"""

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# PDF 生成相关
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, ListFlowable, ListItem
)
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 图例渲染器
from diagram_renderers import DiagramRendererFactory


class FontManager:
    """字体管理器，处理中文字体注册"""

    _initialized = False
    font_name = 'Helvetica'
    font_bold = 'Helvetica-Bold'

    @classmethod
    def initialize(cls):
        """初始化字体"""
        if cls._initialized:
            return

        # macOS 字体路径
        font_paths = {
            'song': [
                '/System/Library/Fonts/Supplemental/Songti.ttc',
                '/System/Library/Fonts/STSong.ttc',
            ],
            'hei': [
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/System/Library/Fonts/STHeiti Medium.ttc',
            ]
        }

        # Windows 字体路径
        if sys.platform == 'win32':
            font_paths = {
                'song': ['C:/Windows/Fonts/simsun.ttc', 'C:/Windows/Fonts/simsun.ttf'],
                'hei': ['C:/Windows/Fonts/simhei.ttf', 'C:/Windows/Fonts/msyh.ttc'],
            }

        # Linux 字体路径
        elif sys.platform.startswith('linux'):
            font_paths = {
                'song': ['/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'],
                'hei': ['/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc'],
            }

        # 尝试注册字体
        for font_type, paths in font_paths.items():
            for path in paths:
                if os.path.exists(path):
                    try:
                        font_name = 'ChineseSong' if font_type == 'song' else 'ChineseHei'
                        pdfmetrics.registerFont(TTFont(font_name, path, subfontIndex=0))
                        if font_type == 'song':
                            cls.font_name = font_name
                        else:
                            cls.font_bold = font_name
                        print(f"✓ 注册字体: {font_name} <- {path}")
                        break
                    except Exception as e:
                        print(f"× 字体注册失败 {path}: {e}")

        cls._initialized = True


class StyleManager:
    """样式管理器"""

    def __init__(self):
        FontManager.initialize()
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """创建自定义样式"""
        font = FontManager.font_name
        font_bold = FontManager.font_bold

        # 试卷标题
        self.styles.add(ParagraphStyle(
            name='ExamTitle',
            fontName=font_bold,
            fontSize=18,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=6
        ))

        # 副标题（科目）
        self.styles.add(ParagraphStyle(
            name='ExamSubtitle',
            fontName=font_bold,
            fontSize=16,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=12
        ))

        # 考试信息
        self.styles.add(ParagraphStyle(
            name='ExamInfo',
            fontName=font,
            fontSize=10,
            leading=16,
            alignment=TA_CENTER
        ))

        # 考生须知
        self.styles.add(ParagraphStyle(
            name='ExamNotes',
            fontName=font,
            fontSize=9,
            leading=14,
            leftIndent=20
        ))

        # 大题标题
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            fontName=font_bold,
            fontSize=12,
            leading=18,
            spaceBefore=12,
            spaceAfter=8
        ))

        # 题目内容
        self.styles.add(ParagraphStyle(
            name='Question',
            fontName=font,
            fontSize=10.5,
            leading=16,
            spaceAfter=4
        ))

        # 选项
        self.styles.add(ParagraphStyle(
            name='Option',
            fontName=font,
            fontSize=10,
            leading=14,
            leftIndent=24
        ))

        # 小问
        self.styles.add(ParagraphStyle(
            name='SubQuestion',
            fontName=font,
            fontSize=10,
            leading=15,
            leftIndent=12,
            spaceAfter=3
        ))

        # 答案标题
        self.styles.add(ParagraphStyle(
            name='AnswerTitle',
            fontName=font_bold,
            fontSize=14,
            leading=20,
            alignment=TA_CENTER,
            spaceBefore=12,
            spaceAfter=12
        ))

        # 答案内容
        self.styles.add(ParagraphStyle(
            name='Answer',
            fontName=font,
            fontSize=10,
            leading=15,
            leftIndent=12
        ))

        # 解析
        self.styles.add(ParagraphStyle(
            name='Explanation',
            fontName=font,
            fontSize=9,
            leading=13,
            leftIndent=24,
            textColor=colors.HexColor('#666666')
        ))

    def get(self, name: str) -> ParagraphStyle:
        """获取样式"""
        return self.styles[name]


class ExamRenderer:
    """试卷渲染器"""

    def __init__(self, data: Dict[str, Any], output_path: str, include_answers: bool = False):
        self.data = data
        self.output_path = output_path
        self.include_answers = include_answers
        self.style_manager = StyleManager()
        self.diagram_factory = DiagramRendererFactory()
        self.temp_files: List[str] = []  # 临时图片文件

    def render(self):
        """渲染试卷"""
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        story = []

        # 渲染头部
        story.extend(self._render_header())

        # 渲染各部分
        for section in self.data.get('sections', []):
            story.extend(self._render_section(section))

        # 如果需要答案，添加答案页
        if self.include_answers:
            story.append(PageBreak())
            story.extend(self._render_answers())

        # 生成 PDF
        doc.build(story)
        print(f"✓ 试卷已生成: {self.output_path}")

        # 清理临时文件
        self._cleanup_temp_files()

    def _render_header(self) -> List:
        """渲染试卷头部"""
        story = []
        meta = self.data.get('meta', {})
        styles = self.style_manager

        # 标题
        if meta.get('title'):
            story.append(Paragraph(meta['title'], styles.get('ExamTitle')))

        # 科目
        if meta.get('subject'):
            story.append(Paragraph(f"{meta['subject']}试题", styles.get('ExamSubtitle')))

        story.append(Spacer(1, 0.3*cm))

        # 考试信息
        info_parts = []
        if meta.get('duration'):
            info_parts.append(f"考试时间：{meta['duration']}分钟")
        if meta.get('total_score'):
            info_parts.append(f"满分：{meta['total_score']}分")
        if info_parts:
            story.append(Paragraph("    ".join(info_parts), styles.get('ExamInfo')))

        story.append(Spacer(1, 0.3*cm))

        # 考生信息栏
        story.append(Paragraph(
            "姓名：__________    学号：__________    班级：__________",
            styles.get('ExamInfo')
        ))

        story.append(Spacer(1, 0.3*cm))

        # 考生须知
        notes = meta.get('notes', [])
        if notes:
            story.append(Paragraph("考生须知：", styles.get('Question')))
            for i, note in enumerate(notes, 1):
                story.append(Paragraph(f"{i}. {note}", styles.get('ExamNotes')))
            story.append(Spacer(1, 0.3*cm))

        # 常量表
        constants = meta.get('constants', {})
        if constants:
            const_str = "可能用到的相对原子质量：" + "  ".join(
                f"{k}-{v}" for k, v in constants.items()
            )
            story.append(Paragraph(const_str, styles.get('ExamNotes')))
            story.append(Spacer(1, 0.5*cm))

        # 分隔线
        story.append(Paragraph("_" * 80, styles.get('ExamInfo')))
        story.append(Spacer(1, 0.5*cm))

        return story

    def _render_section(self, section: Dict) -> List:
        """渲染一个大题部分"""
        story = []
        styles = self.style_manager

        # 大题标题
        title = section.get('title', '')
        if section.get('instructions'):
            title += f"（{section['instructions']}）"
        story.append(Paragraph(self._format_chem_text(title), styles.get('SectionTitle')))

        # 渲染题目
        for question in section.get('questions', []):
            story.extend(self._render_question(question, section.get('points_per_question')))

        story.append(Spacer(1, 0.5*cm))
        return story

    def _render_question(self, question: Dict, default_points: Optional[float] = None) -> List:
        """渲染单个题目"""
        story = []
        styles = self.style_manager

        # 题号和分值
        number = question.get('number', '')
        points = question.get('points', default_points)
        points_str = f"（{points}分）" if points else ""

        # 题干
        content = question.get('content', '')
        content_continued = question.get('content_continued', '')

        # 图例题标记
        if question.get('is_diagram_question'):
            points_str = f"（{points}分，图例题）" if points else "（图例题）"

        # 渲染题干
        q_text = f"{number}. {points_str}{content}"
        story.append(Paragraph(self._format_chem_text(q_text), styles.get('Question')))

        if content_continued:
            story.append(Paragraph(
                self._format_chem_text(f"    {content_continued}"),
                styles.get('Question')
            ))

        # 渲染图例（位置在题干后）
        diagram = question.get('diagram')
        if diagram and diagram.get('position', 'after_content') == 'after_content':
            story.extend(self._render_diagram(diagram))

        # 渲染选项
        options = question.get('options', [])
        if options:
            for opt in options:
                if isinstance(opt, dict):
                    opt_text = f"{opt.get('label', '')}. {opt.get('content', '')}"
                else:
                    opt_text = opt
                story.append(Paragraph(self._format_chem_text(opt_text), styles.get('Option')))

        # 渲染小问
        sub_questions = question.get('sub_questions', [])
        for sub_q in sub_questions:
            story.extend(self._render_sub_question(sub_q))

        # 答题空间
        answer_space = question.get('answer_space', {})
        if answer_space:
            lines = answer_space.get('lines', 3)
            for _ in range(lines):
                story.append(Paragraph("_" * 70, styles.get('SubQuestion')))

        story.append(Spacer(1, 0.3*cm))
        return story

    def _render_sub_question(self, sub_q: Dict) -> List:
        """渲染小问"""
        story = []
        styles = self.style_manager

        number = sub_q.get('number', '')
        content = sub_q.get('content', '')
        points = sub_q.get('points')
        points_str = f"（{points}分）" if points else ""

        # 图例题标记
        if sub_q.get('is_diagram_question'):
            points_str = f"（{points}分，图例题）" if points else "（图例题）"

        story.append(Paragraph(
            self._format_chem_text(f"{number} {points_str}{content}"),
            styles.get('SubQuestion')
        ))

        # 渲染图例
        diagram = sub_q.get('diagram')
        if diagram:
            story.extend(self._render_diagram(diagram))

        # 渲染选项
        options = sub_q.get('options', [])
        for opt in options:
            story.append(Paragraph(
                self._format_chem_text(f"    {opt}"),
                styles.get('Option')
            ))

        return story

    def _render_diagram(self, diagram: Dict) -> List:
        """渲染图例"""
        story = []
        styles = self.style_manager

        diagram_type = diagram.get('type')
        spec = diagram.get('spec', {})
        width_cm = diagram.get('width_cm', 10)
        title = diagram.get('title', '')

        try:
            # 使用图例渲染器工厂生成图例
            renderer = self.diagram_factory.get_renderer(diagram_type)
            if renderer:
                renderer.set_context({'subject': self.data.get('meta', {}).get('subject', '')})
                # 生成临时图片
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                self.temp_files.append(temp_path)

                renderer.render(spec, temp_path)

                # 插入图片
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    width_pt = width_cm * cm
                    img_reader = ImageReader(temp_path)
                    img_w, img_h = img_reader.getSize()
                    height_pt = width_pt * (img_h / img_w) if img_w else width_pt
                    img = Image(temp_path, width=width_pt, height=height_pt)
                    story.append(Spacer(1, 0.2*cm))
                    story.append(img)
                    if title:
                        story.append(Paragraph(
                            self._format_chem_text(f"图：{title}"),
                            styles.get('ExamNotes')
                        ))
                    story.append(Spacer(1, 0.2*cm))
                else:
                    # 图例生成失败，显示占位符
                    story.append(Paragraph(
                        f"【图例：{title or diagram_type}】",
                        styles.get('Question')
                    ))
            else:
                # 没有对应的渲染器
                story.append(Paragraph(
                    f"【图例：{title or diagram_type}】",
                    styles.get('Question')
                ))
        except Exception as e:
            print(f"× 图例渲染失败 ({diagram_type}): {e}")
            story.append(Paragraph(
                f"【图例：{title or diagram_type}（渲染失败）】",
                styles.get('Question')
            ))

        return story

    def _render_answers(self) -> List:
        """渲染答案页"""
        story = []
        styles = self.style_manager

        story.append(Paragraph("参考答案及评分标准", styles.get('AnswerTitle')))
        story.append(Spacer(1, 0.5*cm))

        for section in self.data.get('sections', []):
            # 大题标题
            story.append(Paragraph(
                self._format_chem_text(section.get('title', '')),
                styles.get('SectionTitle')
            ))

            # 遍历题目提取答案
            for question in section.get('questions', []):
                story.extend(self._render_question_answer(question))

            story.append(Spacer(1, 0.3*cm))

        return story

    def _render_question_answer(self, question: Dict) -> List:
        """渲染单个题目的答案"""
        story = []
        styles = self.style_manager

        number = question.get('number', '')
        answer = question.get('answer', {})

        if answer:
            ans_content = answer.get('content', '')
            explanation = answer.get('explanation', '')
            scoring = answer.get('scoring_criteria', [])

            story.append(Paragraph(
                self._format_chem_text(f"{number}. {ans_content}"),
                styles.get('Answer')
            ))

            if explanation:
                story.append(Paragraph(
                    self._format_chem_text(f"解析：{explanation}"),
                    styles.get('Explanation')
                ))

            if scoring:
                scoring_str = "；".join(
                    self._format_chem_text(f"{s['point']}得{s['score']}分") for s in scoring
                )
                story.append(Paragraph(
                    self._format_chem_text(f"评分标准：{scoring_str}"),
                    styles.get('Explanation')
                ))

        # 处理小问
        for sub_q in question.get('sub_questions', []):
            sub_number = sub_q.get('number', '')
            sub_answer = sub_q.get('answer', {})

            if sub_answer:
                ans_content = sub_answer.get('content', '')
                explanation = sub_answer.get('explanation', '')
                scoring = sub_answer.get('scoring_criteria', [])

                story.append(Paragraph(
                    self._format_chem_text(f"  {sub_number} {ans_content}"),
                    styles.get('Answer')
                ))

                if explanation:
                    story.append(Paragraph(
                        self._format_chem_text(f"    解析：{explanation}"),
                        styles.get('Explanation')
                    ))

                if scoring:
                    scoring_str = "；".join(
                        self._format_chem_text(f"{s['point']}得{s['score']}分") for s in scoring
                    )
                    story.append(Paragraph(
                        self._format_chem_text(f"    评分标准：{scoring_str}"),
                        styles.get('Explanation')
                    ))

        return story

    def _format_chem_text(self, text: str) -> str:
        """根据学科将表达式中的数字与指数转换为上下标"""
        if not text:
            return text

        subject = str(self.data.get('meta', {}).get('subject', '') or '')
        subject_lower = subject.lower()
        is_math = '数学' in subject or 'math' in subject_lower
        is_chem = '化学' in subject or 'chem' in subject_lower

        if is_math and not is_chem:
            return self._format_math_text(text)

        return self._format_chemistry_text(text)

    def _format_math_text(self, text: str) -> str:
        """数学表达式：处理 ^n 的上标"""
        safe_text = html.escape(text, quote=False)
        safe_text = re.sub(r'\^(-?[0-9]+)', r'<super>\1</super>', safe_text)
        return safe_text

    def _format_chemistry_text(self, text: str) -> str:
        """化学表达式：处理下标与电荷"""
        safe_text = html.escape(text, quote=False)

        def sub_tag(value: str) -> str:
            return f'<sub rise="2" size="80%">{value}</sub>'

        # 先处理电荷（显式 ^ 形式）
        safe_text = re.sub(r'\^([0-9]*[+-])', r'<super>\1</super>', safe_text)
        safe_text = re.sub(r'\^([0-9]+)', r'<super>\1</super>', safe_text)

        # 普通下标
        safe_text = self._apply_outside_tags(
            safe_text,
            lambda s: re.sub(r'(?<=[A-Za-z\)\]])(\d+)', lambda m: sub_tag(m.group(1)), s),
        )

        # 单原子离子（如 Fe2+、Na+）
        safe_text = re.sub(
            r'(?<![A-Za-z\)\]])([A-Z][a-z]?)(?:<sub rise=\"2\" size=\"80%\">(\d+)</sub>)([+-])',
            r'\1<super>\2\3</super>',
            safe_text,
        )
        safe_text = re.sub(
            r'(?<![A-Za-z\)\]])([A-Z][a-z]?)([+-])',
            r'\1<super>\2</super>',
            safe_text,
        )

        # 多原子离子电荷
        safe_text = re.sub(
            r'(<sub rise=\"2\" size=\"80%\">\d+</sub>)([+-])',
            r'\1<super>\2</super>',
            safe_text,
        )
        return safe_text

    def _apply_outside_tags(self, text: str, func) -> str:
        """仅对标签外的文本进行转换"""
        parts = re.split(r'(<[^>]+>)', text)
        for idx, part in enumerate(parts):
            if part.startswith('<') and part.endswith('>'):
                continue
            parts[idx] = func(part)
        return ''.join(parts)

    def _cleanup_temp_files(self):
        """清理临时文件"""
        for f in self.temp_files:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except Exception:
                pass


def load_exam_data(input_path: str) -> Dict[str, Any]:
    """加载试卷数据"""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description='试卷渲染引擎 - 从 JSON 数据生成 PDF/Word 试卷'
    )
    parser.add_argument('input', help='输入的 JSON 数据文件')
    parser.add_argument('-o', '--output', help='输出文件路径', default='exam.pdf')
    parser.add_argument('--with-answers', action='store_true', help='包含答案页')
    parser.add_argument('--format', choices=['pdf', 'word'], default='pdf', help='输出格式')
    parser.add_argument('--answers-only', action='store_true', help='仅生成答案')

    args = parser.parse_args()

    # 加载数据
    print(f"正在加载数据: {args.input}")
    data = load_exam_data(args.input)

    # 确定输出路径
    output_path = args.output
    if not output_path.endswith(('.pdf', '.docx')):
        output_path += '.pdf' if args.format == 'pdf' else '.docx'

    # 渲染
    if args.format == 'pdf':
        renderer = ExamRenderer(data, output_path, include_answers=args.with_answers)
        renderer.render()
    else:
        # TODO: Word 格式渲染
        print("Word 格式暂未实现，请使用 PDF 格式")
        sys.exit(1)


if __name__ == '__main__':
    main()
