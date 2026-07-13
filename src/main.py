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
from src.analyzer import SalesAnalyzer, DataValidator
from src.visualizer import ChartGenerator
from src.report import ReportGenerator


class SushiAnalysisSkill:
    """日料店经营分析 Skill"""

    VERSION = "1.1.0"

    def __init__(self):
        self.loader = DataLoader()
        self.analyzer = None
        self.charts = {}
        self.report_gen = None
        self.data_path = None
        self.current_date_range = None

    def _get_default_data_path(self) -> str:
        """获取默认数据路径"""
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
   - 支持: 今日日报、本周分析、指定日期范围
   - 示例: 分析 7月1日到7月5日的数据

4. 报告查看:
   - 报告自动保存到 ~/sushi-data/reports/ 目录
   - 文件名格式: report_YYYY-MM-DD_HHMMSS.html

5. 基础数据维护:
   - reference/dishes.xlsx: 菜品目录（售价、成本）
   - reference/tables.xlsx: 桌台信息
   - 这两个文件只有在菜品/桌台变化时才需更新
"""

    def _load_and_analyze(self, analysis_type: str, date_range: tuple = None,
                          compare_with_previous: bool = False) -> SalesAnalyzer:
        """加载数据并创建分析器"""
        if not self.data_path:
            raise ValueError("请先调用 setup() 进行初始化设置")

        # 加载数据
        if analysis_type == 'today':
            date = datetime.now().strftime('%Y-%m-%d')
            sales_df = self.loader.load_sales(date=date)
            self.current_date_range = (date, date)
        elif analysis_type == 'week':
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            sales_df = self.loader.load_sales(start_date=start_str, end_date=end_str)
            self.current_date_range = (start_str, end_str)
        elif analysis_type == 'range' and date_range:
            sales_df = self.loader.load_sales(
                start_date=date_range[0],
                end_date=date_range[1]
            )
            self.current_date_range = (date_range[0], date_range[1])
        else:  # 'all'
            sales_df = self.loader.load_sales()
            self.current_date_range = None

        # 加载基础数据
        dishes_df = self.loader.load_dishes()
        tables_df = self.loader.load_tables()

        # 创建分析器
        analyzer = SalesAnalyzer(sales_df, dishes_df, tables_df)

        # 设置日期范围
        if self.current_date_range:
            analyzer.set_date_range(self.current_date_range[0], self.current_date_range[1])

        return analyzer

    def validate_data(self, analysis_type: str = 'today', date_range: tuple = None) -> dict:
        """验证数据"""
        analyzer = self._load_and_analyze(analysis_type, date_range)
        validation = analyzer.validate_data()
        report = DataValidator.get_validation_report(validation)

        return {
            'validation': validation,
            'report': report,
        }

    def analyze(self, analysis_type: str = 'today', date_range: tuple = None,
                compare: bool = True) -> dict:
        """
        执行分析

        Args:
            analysis_type: 'today', 'week', 'range', 'all'
            date_range: (start_date, end_date) 当 analysis_type='range' 时使用
            compare: 是否进行同比/环比对比

        Returns:
            分析结果
        """
        # 加载数据
        self.analyzer = self._load_and_analyze(analysis_type, date_range)

        # 生成报告数据
        full_report = self.analyzer.generate_full_report()

        # 如果需要对比分析且是日期范围
        if compare and self.current_date_range and analysis_type in ['week', 'range']:
            # 计算上一期数据
            start, end = self.current_date_range
            start_dt = datetime.strptime(start, '%Y-%m-%d')
            end_dt = datetime.strptime(end, '%Y-%m-%d')
            days = (end_dt - start_dt).days + 1

            # 上一期
            prev_end = start_dt - timedelta(days=1)
            prev_start = prev_end - timedelta(days=days)

            prev_analyzer = self._load_and_analyze(
                'range',
                (prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d'))
            )

            # 添加对比数据到报告
            comparison = self.analyzer.get_comparison_analysis(prev_analyzer)
            full_report['comparison'] = comparison
            full_report['comparison']['current'] = self.analyzer.get_revenue_summary()

        # 生成图表
        visualizer = ChartGenerator()
        self.charts = visualizer.generate_all_charts(full_report)

        # 生成报告
        self.report_gen = ReportGenerator(self.analyzer, self.charts)

        return {
            'summary': self.report_gen.generate_summary(),
            'has_charts': bool(self.charts),
            'chart_count': len(self.charts),
            'date_range': self.current_date_range,
            'validation': full_report.get('validation'),
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

    def get_validation_report(self) -> str:
        """获取数据验证报告"""
        if not self.analyzer:
            raise ValueError("请先调用 analyze() 执行分析")
        return self.report_gen.generate_validation_report()

    def save_report(self, output_path: str = None, format: str = 'html') -> str:
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

        # 默认保存到 reports 目录
        if not output_path and self.data_path:
            reports_dir = str(Path(self.data_path) / "reports")
        else:
            reports_dir = None

        if format == 'html':
            return self.report_gen.save_html_report(output_path=output_path, reports_dir=reports_dir)
        else:
            return self.report_gen.save_markdown_report(reports_dir=reports_dir or output_path)

    def check_data_status(self) -> dict:
        """检查数据状态"""
        if not self.data_path:
            return {'initialized': False}

        return {
            'initialized': True,
            'data_path': self.data_path,
            **self.loader.check_data_status()
        }

    def get_report_history(self, limit: int = 10) -> list:
        """获取历史报告列表"""
        if not self.data_path:
            return []

        reports_dir = Path(self.data_path) / "reports"
        if not reports_dir.exists():
            return []

        reports = []
        for f in sorted(reports_dir.glob("report_*.html"), reverse=True)[:limit]:
            reports.append({
                'filename': f.name,
                'path': str(f),
                'size': f.stat().st_size,
                'created': f.stat().st_ctime,
            })

        return reports


# 导出主要类和函数
__all__ = ['SushiAnalysisSkill', 'DataLoader', 'SalesAnalyzer', 'ChartGenerator', 'ReportGenerator', 'DataValidator']
