#!/usr/bin/env python3
"""
日料店经营分析 Skill - 主入口

Usage:
    from skill import SushiAnalysisSkill
    skill = SushiAnalysisSkill()
    skill.run()
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_loader import DataLoader, create_template_files
from src.analyzer import SalesAnalyzer
from src.visualizer import ChartGenerator
from src.report import ReportGenerator


class SushiAnalysisSkill:
    """日料店经营分析 Skill"""

    VERSION = "1.0.0"

    def __init__(self):
        self.loader = DataLoader()
        self.analyzer = None
        self.charts = {}
        self.report_gen = None
        self.data_path = None

    def _get_default_data_path(self) -> str:
        """获取默认数据路径"""
        # 优先使用用户配置的路径
        home = Path.home()
        default_path = home / "sushi-data"
        return str(default_path)

    def setup(self, custom_path: str = None) -> dict:
        """
        首次设置：创建文件夹结构和模板文件

        Args:
            custom_path: 自定义数据路径，None 则使用默认路径

        Returns:
            设置结果
        """
        if custom_path:
            self.data_path = custom_path
        else:
            self.data_path = self._get_default_data_path()

        # 创建模板文件
        result = create_template_files(self.data_path)

        # 设置加载器路径
        self.loader.set_paths(self.data_path)

        return {
            'data_path': self.data_path,
            'created_files': result['created'],
            'folder_structure': {
                'reference/': 'dishes.xlsx, tables.xlsx (菜品和桌台基础数据)',
                'YYYY-MM/': 'sales_YYYY-MM-DD.xlsx (月度销售数据)',
                'reports/': 'HTML/Markdown 报告文件 (自动生成)',
            },
            'instructions': self._get_usage_instructions(),
        }

    def _get_usage_instructions(self) -> str:
        """获取使用说明"""
        return """
📋 【使用说明】

1. 每日数据更新:
   - 将 POS 系统导出的销售数据保存为 sales_YYYY-MM-DD.xlsx
   - 放入 ~/sushi-data/YYYY-MM/ 目录

2. 数据格式要求:
   - 列名必须包含: 时间、桌台、菜品名称、分类、数量、单价、金额、支付方式
   - 支持自动识别中文或英文列名

3. 运行分析:
   - 调用 /sushi-analysis 选择分析类型
   - 支持: 今日日报、本周分析、指定日期范围

4. 报告查看:
   - 报告自动保存到 ~/sushi-data/reports/ 目录
   - 文件名格式: report_YYYY-MM-DD_HHMMSS.html

5. 基础数据维护:
   - reference/dishes.xlsx: 菜品目录（售价、成本）
   - reference/tables.xlsx: 桌台信息
   - 这两个文件只有在菜品/桌台变化时才需更新
"""

    def analyze(self, analysis_type: str = 'today', date_range: tuple = None) -> dict:
        """
        执行分析

        Args:
            analysis_type: 'today', 'week', 'range', 'all'
            date_range: (start_date, end_date) 当 analysis_type='range' 时使用

        Returns:
            分析结果
        """
        if not self.data_path:
            raise ValueError("请先调用 setup() 进行初始化设置")

        # 加载数据
        if analysis_type == 'today':
            date = datetime.now().strftime('%Y-%m-%d')
            sales_df = self.loader.load_sales(date=date)
        elif analysis_type == 'week':
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            sales_df = self.loader.load_sales(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
        elif analysis_type == 'range' and date_range:
            sales_df = self.loader.load_sales(
                start_date=date_range[0],
                end_date=date_range[1]
            )
        else:  # 'all'
            sales_df = self.loader.load_sales()

        # 加载基础数据
        dishes_df = self.loader.load_dishes()
        tables_df = self.loader.load_tables()

        # 分析
        self.analyzer = SalesAnalyzer(sales_df, dishes_df, tables_df)

        # 生成图表
        visualizer = ChartGenerator()
        self.charts = visualizer.generate_all_charts(self.analyzer.generate_full_report())

        # 生成报告
        self.report_gen = ReportGenerator(self.analyzer, self.charts)

        return {
            'summary': self.report_gen.generate_summary(),
            'has_charts': bool(self.charts),
            'chart_count': len(self.charts),
        }

    def get_charts(self) -> dict:
        """获取所有图表"""
        return self.charts

    def get_full_report(self, format: str = 'markdown') -> str:
        """
        获取完整报告

        Args:
            format: 'markdown', 'html', 'text'

        Returns:
            报告内容
        """
        if not self.report_gen:
            raise ValueError("请先调用 analyze() 执行分析")

        if format == 'markdown':
            return self.report_gen.generate_markdown()
        elif format == 'html':
            return self.report_gen.generate_html()
        else:
            return self.report_gen.generate_summary()

    def save_report(self, output_path: str, format: str = 'html') -> str:
        """
        保存报告到文件

        Args:
            output_path: 输出文件路径
            format: 'html', 'markdown'

        Returns:
            保存的文件路径
        """
        if not self.report_gen:
            raise ValueError("请先调用 analyze() 执行分析")

        if format == 'html':
            return self.report_gen.save_html_report(output_path)
        else:
            content = self.report_gen.generate_markdown()
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return output_path

    def check_data_status(self) -> dict:
        """检查数据状态"""
        if not self.data_path:
            return {'initialized': False}

        return {
            'initialized': True,
            'data_path': self.data_path,
            **self.loader.check_data_status()
        }


# 导出主要类和函数
__all__ = ['SushiAnalysisSkill', 'DataLoader', 'SalesAnalyzer', 'ChartGenerator', 'ReportGenerator']
