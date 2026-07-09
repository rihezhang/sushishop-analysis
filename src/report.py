"""
报告生成模块 - 组装输出
"""

from typing import Dict, List, Optional
from datetime import datetime
from .analyzer import SalesAnalyzer
from .visualizer import ChartGenerator


class ReportGenerator:
    """报告生成器"""

    def __init__(self, analyzer: SalesAnalyzer, charts: Dict[str, str]):
        self.analyzer = analyzer
        self.charts = charts
        self.date_str = datetime.now().strftime('%Y年%m月%d日')

    def _format_currency(self, amount: float) -> str:
        """格式化货币"""
        return f"¥{amount:,.2f}"

    def _format_number(self, num: int) -> str:
        """格式化数字"""
        return f"{num:,}"

    def generate_summary(self) -> str:
        """
        生成分析摘要（纯文本）
        """
        revenue = self.analyzer.get_revenue_summary()
        if not revenue:
            return "⚠️ 暂无数据可分析"

        output = []
        output.append("=" * 50)
        output.append("       🍣 日料店经营分析报告")
        output.append(f"       📅 {self.date_str}")
        output.append("=" * 50)

        # 营收概览
        output.append("\n📊 【营收概览】")
        output.append(f"   总营收: {self._format_currency(revenue['total_revenue'])}")
        output.append(f"   订单数: {self._format_number(revenue['total_orders'])} 单")
        output.append(f"   菜品销量: {self._format_number(revenue['total_dishes'])} 份")
        output.append(f"   客单价: {self._format_currency(revenue['avg_order_value'])}")
        output.append(f"   人均点菜: {revenue['avg_dishes_per_order']:.1f} 份")

        # 菜品分析
        output.append("\n🍣 【菜品分析】")
        top_dishes = self.analyzer.get_top_dishes('revenue', 5)
        if not top_dishes.empty:
            output.append("   销售额 TOP5:")
            for i, row in enumerate(top_dishes.head(5).itertuples(), 1):
                category = row.category if 'category' in row._fields else ''
                output.append(f"   {i}. {row.dish_name} ({category}) - {self._format_currency(row.revenue)}")

        # 时段分析
        output.append("\n⏰ 【时段分析】")
        period_data = self.analyzer.get_period_analysis()
        if period_data:
            for period, stats in period_data.items():
                output.append(f"   {period}: {self._format_currency(stats['revenue'])} ({stats['revenue_pct']}%) - {stats['orders']}单")

        # 桌台分析
        output.append("\n🪑 【桌台效率】")
        table_data = self.analyzer.get_table_analysis()
        if table_data:
            output.append(f"   总使用次数: {table_data['total_table_visits']} 次")
            output.append(f"   预估翻台率: {table_data['estimated_turnover_rate']:.1f}")
            output.append(f"   平均桌台营收: {self._format_currency(table_data['avg_revenue_per_table'])}")

            if table_data.get('vip_analysis'):
                vip = table_data['vip_analysis']
                output.append(f"   包间营收: {self._format_currency(vip['revenue'])} ({vip['revenue_pct']}%)")

        # 支付方式
        payment = self.analyzer.get_payment_breakdown()
        if not payment.empty:
            output.append("\n💳 【支付方式】")
            for _, row in payment.iterrows():
                output.append(f"   {row['payment']}: {self._format_currency(row['revenue'])} ({row['percentage']}%)")

        output.append("\n" + "=" * 50)

        return "\n".join(output)

    def generate_markdown(self) -> str:
        """
        生成 Markdown 格式报告
        """
        revenue = self.analyzer.get_revenue_summary()
        if not revenue:
            return "⚠️ 暂无数据可分析"

        output = []
        output.append(f"# 🍣 日料店经营分析报告")
        output.append(f"\n**📅 日期**: {self.date_str}\n")

        # 关键指标卡片
        output.append("## 📊 关键指标\n")
        output.append("| 指标 | 数值 |")
        output.append("|------|------|")
        output.append(f"| 总营收 | {self._format_currency(revenue['total_revenue'])} |")
        output.append(f"| 订单数 | {revenue['total_orders']} 单 |")
        output.append(f"| 菜品销量 | {revenue['total_dishes']} 份 |")
        output.append(f"| 客单价 | {self._format_currency(revenue['avg_order_value'])} |")

        # 营收趋势图
        if self.charts.get('revenue_trend'):
            output.append("\n## 📈 营收趋势\n")
            output.append(f"![营收趋势](data:image/png;base64,{self.charts['revenue_trend']})\n")

        # 热销菜品
        if self.charts.get('top_dishes_revenue'):
            output.append("## 🍣 热销菜品 TOP10\n")
            output.append(f"![热销菜品](data:image/png;base64,{self.charts['top_dishes_revenue']})\n")

        # 分类占比
        if self.charts.get('category_pie'):
            output.append("## 📊 菜品分类占比\n")
            output.append(f"![分类占比](data:image/png;base64,{self.charts['category_pie']})\n")

        # 时段分析
        if self.charts.get('period_comparison'):
            output.append("## ⏰ 午市 vs 晚市\n")
            output.append(f"![时段对比](data:image/png;base64,{self.charts['period_comparison']})\n")

        # 每小时分布
        if self.charts.get('hourly_distribution'):
            output.append("## 📅 每小时订单分布\n")
            output.append(f"![时段分布](data:image/png;base64,{self.charts['hourly_distribution']})\n")

        # 桌台效率
        if self.charts.get('table_efficiency'):
            output.append("## 🪑 桌台效率\n")
            output.append(f"![桌台效率](data:image/png;base64,{self.charts['table_efficiency']})\n")

        # 支付方式
        if self.charts.get('payment_breakdown'):
            output.append("## 💳 支付方式\n")
            output.append(f"![支付方式](data:image/png;base64,{self.charts['payment_breakdown']})\n")

        return "\n".join(output)

    def generate_html(self) -> str:
        """
        生成 HTML 格式报告（可保存为网页）
        """
        revenue = self.analyzer.get_revenue_summary()
        if not revenue:
            return "<h2>⚠️ 暂无数据可分析</h2>"

        html_parts = []

        # HTML 头部
        html_parts.append("""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>日料店经营分析报告</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       background: #f5f7fa; color: #333; line-height: 1.6; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%);
                          color: white; padding: 30px; border-radius: 12px; margin-bottom: 24px; }
                .header h1 { font-size: 28px; margin-bottom: 8px; }
                .header .date { opacity: 0.9; }
                .card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
                .card h2 { color: #1e40af; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px;
                           margin-bottom: 16px; }
                .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                            gap: 16px; margin-bottom: 24px; }
                .kpi { background: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; }
                .kpi .value { font-size: 28px; font-weight: bold; color: #2563EB; }
                .kpi .label { color: #64748b; font-size: 14px; margin-top: 4px; }
                .chart { text-align: center; margin: 20px 0; }
                .chart img { max-width: 100%; border-radius: 8px; }
                .table-container { overflow-x: auto; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
                th { background: #f8fafc; font-weight: 600; color: #475569; }
                tr:hover { background: #f8fafc; }
                .period-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                               gap: 16px; }
                .period-card { background: #f8fafc; padding: 16px; border-radius: 8px;
                               border-left: 4px solid #2563EB; }
                .period-card h3 { color: #2563EB; margin-bottom: 8px; }
                .period-card .value { font-size: 24px; font-weight: bold; color: #1e40af; }
                .period-card .detail { color: #64748b; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍣 日料店经营分析报告</h1>
                    <div class="date">📅 {date}</div>
                </div>
        """.format(date=self.date_str))

        # KPI 卡片
        html_parts.append("""
                <div class="kpi-grid">
                    <div class="kpi">
                        <div class="value">{revenue}</div>
                        <div class="label">总营收</div>
                    </div>
                    <div class="kpi">
                        <div class="value">{orders}</div>
                        <div class="label">订单数</div>
                    </div>
                    <div class="kpi">
                        <div class="value">{dishes}</div>
                        <div class="label">菜品销量</div>
                    </div>
                    <div class="kpi">
                        <div class="value">{avg}</div>
                        <div class="label">客单价</div>
                    </div>
                </div>
        """.format(
            revenue=self._format_currency(revenue['total_revenue']),
            orders=revenue['total_orders'],
            dishes=revenue['total_dishes'],
            avg=self._format_currency(revenue['avg_order_value'])
        ))

        # 图表
        if self.charts.get('revenue_trend'):
            html_parts.append("""
                <div class="card">
                    <h2>📈 营收趋势</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{img}" alt="营收趋势">
                    </div>
                </div>
            """.format(img=self.charts['revenue_trend']))

        if self.charts.get('top_dishes_revenue'):
            html_parts.append("""
                <div class="card">
                    <h2>🍣 热销菜品 TOP10</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{img}" alt="热销菜品">
                    </div>
                </div>
            """.format(img=self.charts['top_dishes_revenue']))

        if self.charts.get('category_pie'):
            html_parts.append("""
                <div class="card">
                    <h2>📊 菜品分类占比</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{img}" alt="分类占比">
                    </div>
                </div>
            """.format(img=self.charts['category_pie']))

        if self.charts.get('period_comparison'):
            html_parts.append("""
                <div class="card">
                    <h2>⏰ 午市 vs 晚市</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{img}" alt="时段对比">
                    </div>
                </div>
            """.format(img=self.charts['period_comparison']))

        if self.charts.get('hourly_distribution'):
            html_parts.append("""
                <div class="card">
                    <h2>📅 每小时订单分布</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{img}" alt="时段分布">
                    </div>
                </div>
            """.format(img=self.charts['hourly_distribution']))

        if self.charts.get('table_efficiency'):
            html_parts.append("""
                <div class="card">
                    <h2>🪑 桌台效率</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{img}" alt="桌台效率">
                    </div>
                </div>
            """.format(img=self.charts['table_efficiency']))

        # HTML 尾部
        html_parts.append("""
            </div>
        </body>
        </html>
        """)

        return "\n".join(html_parts)

    def save_html_report(self, output_path: str = None, reports_dir: str = None) -> str:
        """
        保存 HTML 报告到文件

        Args:
            output_path: 直接指定输出路径
            reports_dir: 报告存储目录，会自动生成带时间戳的文件名

        Returns:
            保存的文件路径
        """
        html = self.generate_html()

        if reports_dir:
            # 自动生成文件名
            from pathlib import Path
            import time
            reports_path = Path(reports_dir)
            reports_path.mkdir(parents=True, exist_ok=True)

            # 文件名格式: report_2026-01-08_143052.html
            filename = f"report_{time.strftime('%Y-%m-%d_%H%M%S')}.html"
            output_path = reports_path / filename
        elif not output_path:
            raise ValueError("必须指定 output_path 或 reports_dir")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(output_path)

    def save_markdown_report(self, reports_dir: str = None) -> str:
        """
        保存 Markdown 报告到文件

        Args:
            reports_dir: 报告存储目录

        Returns:
            保存的文件路径
        """
        from pathlib import Path
        import time

        content = self.generate_markdown()
        reports_path = Path(reports_dir)
        reports_path.mkdir(parents=True, exist_ok=True)

        filename = f"report_{time.strftime('%Y-%m-%d_%H%M%S')}.md"
        output_path = reports_path / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_path)

    def get_report_history(self, reports_dir: str, limit: int = 10) -> list:
        """
        获取历史报告列表

        Args:
            reports_dir: 报告存储目录
            limit: 返回数量

        Returns:
            报告文件列表
        """
        from pathlib import Path

        reports_path = Path(reports_dir)
        if not reports_path.exists():
            return []

        reports = []
        for f in sorted(reports_path.glob("report_*.html"), reverse=True)[:limit]:
            reports.append({
                'filename': f.name,
                'path': str(f),
                'size': f.stat().st_size,
                'created': f.stat().st_ctime,
            })

        return reports
