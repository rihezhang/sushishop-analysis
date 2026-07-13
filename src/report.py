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

    def _format_change(self, change: float, prefix: str = '') -> str:
        """格式化变化率"""
        if change > 0:
            return f"🔺 +{change}%{prefix}"
        elif change < 0:
            return f"🔻 {change}%{prefix}"
        return "➡️ 持平"

    def generate_summary(self) -> str:
        """生成分析摘要（纯文本）"""
        revenue = self.analyzer.get_revenue_summary()
        if not revenue:
            return "⚠️ 暂无数据可分析"

        output = []
        output.append("=" * 50)
        output.append("       🍣 日料店经营分析报告")
        output.append(f"       📅 {self.date_str}")

        # 日期范围
        if revenue.get('date_range'):
            start, end = revenue['date_range']
            output.append(f"       📆 {start} 至 {end}")

        output.append("=" * 50)

        # 营收概览
        output.append("\n📊 【营收概览】")
        output.append(f"   总营收: {self._format_currency(revenue['total_revenue'])}")
        output.append(f"   订单数: {self._format_number(revenue['total_orders'])} 单")
        output.append(f"   菜品销量: {self._format_number(revenue['total_dishes'])} 份")
        output.append(f"   客单价: {self._format_currency(revenue['avg_order_value'])}")

        # 同比/环比
        comparison = self.analyzer.get_comparison_analysis()
        if comparison.get('comparison'):
            comp = comparison['comparison']
            output.append(f"\n📈 【对比分析】")
            output.append(f"   营收变化: {self._format_change(comp['revenue_change_pct'])}")
            output.append(f"   订单变化: {self._format_change(comp['order_change_pct'])}")

        # 菜品分析
        output.append("\n🍣 【菜品分析】")
        top_dishes = self.analyzer.get_top_dishes('revenue', 5)
        if not top_dishes.empty:
            output.append("   销售额 TOP5:")
            for i, row in enumerate(top_dishes.head(5).itertuples(), 1):
                category = getattr(row, 'category', '')
                pct = getattr(row, 'pct', 0)
                output.append(f"   {i}. {row.dish_name} ({category}) - {self._format_currency(row.revenue)} ({pct}%)")

        # 滞销预警
        bottom_dishes = self.analyzer.get_bottom_dishes('quantity', 3)
        if not bottom_dishes.empty:
            output.append("\n⚠️ 【滞销预警】")
            for i, row in enumerate(bottom_dishes.itertuples(), 1):
                output.append(f"   {i}. {row.dish_name} - {int(row.quantity)}份")

        # 时段分析
        output.append("\n⏰ 【时段分析】")
        period_data = self.analyzer.get_period_analysis()
        if period_data:
            for period, stats in period_data.items():
                output.append(f"   {period}: {self._format_currency(stats['revenue'])} ({stats['revenue_pct']}%) - {stats['orders']}单")

        # 高峰时段
        peak = self.analyzer.get_peak_hours()
        if peak and peak.get('peak_hours'):
            hours = [f"{h}:00" for h in peak['peak_hours']]
            output.append(f"   高峰时段: {', '.join(hours)}")

        # 桌台分析
        output.append("\n🪑 【桌台效率】")
        table_data = self.analyzer.get_table_analysis()
        if table_data:
            output.append(f"   使用桌台: {table_data['unique_tables_used']} 个")
            output.append(f"   总使用次数: {table_data['total_table_visits']} 次")
            output.append(f"   翻台率: {table_data['estimated_turnover_rate']:.1f}")
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

    def generate_validation_report(self) -> str:
        """生成数据验证报告"""
        validation = self.analyzer.validate_data()

        output = []
        output.append("🔍 【数据验证报告】\n")

        if validation['valid']:
            output.append("✅ 数据验证通过\n")
        else:
            output.append("❌ 数据验证失败:\n")
            for err in validation['errors']:
                output.append(f"   • {err}\n")

        if validation['warnings']:
            output.append("\n⚠️ 警告:\n")
            for warn in validation['warnings']:
                output.append(f"   • {warn}\n")

        if validation['missing_columns']:
            output.append("\n📋 检测到的列:\n")
            for std_name, mapped_name in validation['column_mapping'].items():
                output.append(f"   • {std_name} → {mapped_name}\n")

        return "\n".join(output)

    def generate_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        revenue = self.analyzer.get_revenue_summary()
        if not revenue:
            return "⚠️ 暂无数据可分析"

        output = []
        date_range_text = ""
        if revenue.get('date_range'):
            start, end = revenue['date_range']
            date_range_text = f" - {start} 至 {end}"

        output.append(f"# 🍣 日料店经营分析报告")
        output.append(f"\n**📅 日期**: {self.date_str}{date_range_text}\n")

        # 关键指标卡片
        output.append("## 📊 关键指标\n")
        output.append("| 指标 | 数值 |")
        output.append("|------|------|")
        output.append(f"| 总营收 | {self._format_currency(revenue['total_revenue'])} |")
        output.append(f"| 订单数 | {revenue['total_orders']} 单 |")
        output.append(f"| 菜品销量 | {revenue['total_dishes']} 份 |")
        output.append(f"| 客单价 | {self._format_currency(revenue['avg_order_value'])} |")

        # 对比分析
        comparison = self.analyzer.get_comparison_analysis()
        if comparison.get('comparison'):
            comp = comparison['comparison']
            output.append("\n## 📈 对比分析\n")
            output.append("| 指标 | 变化 |")
            output.append("|------|------|")
            output.append(f"| 营收 | {self._format_change(comp['revenue_change_pct'])} |")
            output.append(f"| 订单 | {self._format_change(comp['order_change_pct'])} |")

        # 每日趋势图
        if self.charts.get('daily_trend'):
            output.append("\n## 📅 每日营收趋势\n")
            output.append(f"![每日趋势](data:image/png;base64,{self.charts['daily_trend']})\n")

        # 营收趋势图
        if self.charts.get('revenue_trend'):
            output.append("\n## ⏰ 营收时段分布\n")
            output.append(f"![营收趋势](data:image/png;base64,{self.charts['revenue_trend']})\n")

        # 对比图
        if self.charts.get('comparison'):
            output.append("\n## 📊 同比/环比对比\n")
            output.append(f"![对比](data:image/png;base64,{self.charts['comparison']})\n")

        # 热销菜品
        if self.charts.get('top_dishes_revenue'):
            output.append("## 🍣 热销菜品 TOP10\n")
            output.append(f"![热销菜品](data:image/png;base64,{self.charts['top_dishes_revenue']})\n")

        # 滞销预警
        if self.charts.get('bottom_dishes'):
            output.append("## ⚠️ 滞销菜品预警\n")
            output.append(f"![滞销菜品](data:image/png;base64,{self.charts['bottom_dishes']})\n")

        # 分类占比
        if self.charts.get('category_pie'):
            output.append("## 📊 菜品分类占比\n")
            output.append(f"![分类占比](data:image/png;base64,{self.charts['category_pie']})\n")

        # 分类趋势
        if self.charts.get('category_trend'):
            output.append("## 📈 分类每日趋势\n")
            output.append(f"![分类趋势](data:image/png;base64,{self.charts['category_trend']})\n")

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
        """生成 HTML 格式报告"""
        revenue = self.analyzer.get_revenue_summary()
        if not revenue:
            return "<h2>⚠️ 暂无数据可分析</h2>"

        date_range_text = ""
        if revenue.get('date_range'):
            start, end = revenue['date_range']
            date_range_text = f" - {start} 至 {end}"

        html_parts = []

        # HTML 头部
        html_parts.append(f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>日料店经营分析报告</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       background: #f5f7fa; color: #333; line-height: 1.6; }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%);
                          color: white; padding: 30px; border-radius: 12px; margin-bottom: 24px; }}
                .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
                .header .date {{ opacity: 0.9; }}
                .card {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
                .card h2 {{ color: #1e40af; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px;
                           margin-bottom: 16px; }}
                .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                            gap: 16px; margin-bottom: 24px; }}
                .kpi {{ background: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; }}
                .kpi .value {{ font-size: 28px; font-weight: bold; color: #2563EB; }}
                .kpi .label {{ color: #64748b; font-size: 14px; margin-top: 4px; }}
                .kpi .change {{ font-size: 12px; margin-top: 4px; }}
                .kpi .change.up {{ color: #10B981; }}
                .kpi .change.down {{ color: #EF4444; }}
                .chart {{ text-align: center; margin: 20px 0; }}
                .chart img {{ max-width: 100%; border-radius: 8px; }}
                .comparison {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                              gap: 16px; margin-bottom: 24px; }}
                .comparison-item {{ background: #f8fafc; padding: 16px; border-radius: 8px; text-align: center; }}
                .comparison-item .value {{ font-size: 24px; font-weight: bold; }}
                .comparison-item .change {{ font-size: 14px; }}
                .comparison-item .change.up {{ color: #10B981; }}
                .comparison-item .change.down {{ color: #EF4444; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍣 日料店经营分析报告</h1>
                    <div class="date">📅 {self.date_str}{date_range_text}</div>
                </div>
        """)

        # KPI 卡片
        html_parts.append("""
                <div class="kpi-grid">
                    <div class="kpi">
                        <div class="value">{}</div>
                        <div class="label">总营收</div>
                    </div>
                    <div class="kpi">
                        <div class="value">{}</div>
                        <div class="label">订单数</div>
                    </div>
                    <div class="kpi">
                        <div class="value">{}</div>
                        <div class="label">菜品销量</div>
                    </div>
                    <div class="kpi">
                        <div class="value">{}</div>
                        <div class="label">客单价</div>
                    </div>
                </div>
        """.format(
            self._format_currency(revenue['total_revenue']),
            revenue['total_orders'],
            revenue['total_dishes'],
            self._format_currency(revenue['avg_order_value'])
        ))

        # 对比分析
        comparison = self.analyzer.get_comparison_analysis()
        if comparison.get('comparison'):
            comp = comparison['comparison']
            rev_change = comp['revenue_change_pct']
            rev_class = 'up' if rev_change >= 0 else 'down'
            rev_arrow = '🔺' if rev_change >= 0 else '🔻'
            html_parts.append(f"""
                <div class="comparison">
                    <div class="comparison-item">
                        <div class="label">营收变化</div>
                        <div class="value">{rev_arrow} {abs(rev_change)}%</div>
                    </div>
                    <div class="comparison-item">
                        <div class="label">订单变化</div>
                        <div class="value">{rev_arrow} {abs(comp['order_change_pct'])}%</div>
                    </div>
                </div>
            """)

        # 每日趋势图
        if self.charts.get('daily_trend'):
            html_parts.append(f"""
                <div class="card">
                    <h2>📅 每日营收趋势</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['daily_trend']}" alt="每日趋势">
                    </div>
                </div>
            """)

        # 营收趋势图
        if self.charts.get('revenue_trend'):
            html_parts.append(f"""
                <div class="card">
                    <h2>⏰ 营收时段分布</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['revenue_trend']}" alt="营收趋势">
                    </div>
                </div>
            """)

        # 对比图
        if self.charts.get('comparison'):
            html_parts.append(f"""
                <div class="card">
                    <h2>📊 同比/环比对比</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['comparison']}" alt="对比">
                    </div>
                </div>
            """)

        # 热销菜品
        if self.charts.get('top_dishes_revenue'):
            html_parts.append(f"""
                <div class="card">
                    <h2>🍣 热销菜品 TOP10</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['top_dishes_revenue']}" alt="热销菜品">
                    </div>
                </div>
            """)

        # 滞销预警
        if self.charts.get('bottom_dishes'):
            html_parts.append(f"""
                <div class="card">
                    <h2>⚠️ 滞销菜品预警</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['bottom_dishes']}" alt="滞销菜品">
                    </div>
                </div>
            """)

        # 分类占比
        if self.charts.get('category_pie'):
            html_parts.append(f"""
                <div class="card">
                    <h2>📊 菜品分类占比</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['category_pie']}" alt="分类占比">
                    </div>
                </div>
            """)

        # 分类趋势
        if self.charts.get('category_trend'):
            html_parts.append(f"""
                <div class="card">
                    <h2>📈 分类每日趋势</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['category_trend']}" alt="分类趋势">
                    </div>
                </div>
            """)

        # 时段对比
        if self.charts.get('period_comparison'):
            html_parts.append(f"""
                <div class="card">
                    <h2>⏰ 午市 vs 晚市</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['period_comparison']}" alt="时段对比">
                    </div>
                </div>
            """)

        # 每小时分布
        if self.charts.get('hourly_distribution'):
            html_parts.append(f"""
                <div class="card">
                    <h2>📅 每小时订单分布</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['hourly_distribution']}" alt="时段分布">
                    </div>
                </div>
            """)

        # 桌台效率
        if self.charts.get('table_efficiency'):
            html_parts.append(f"""
                <div class="card">
                    <h2>🪑 桌台效率</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['table_efficiency']}" alt="桌台效率">
                    </div>
                </div>
            """)

        # 支付方式
        if self.charts.get('payment_breakdown'):
            html_parts.append(f"""
                <div class="card">
                    <h2>💳 支付方式</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{self.charts['payment_breakdown']}" alt="支付方式">
                    </div>
                </div>
            """)

        # HTML 尾部
        html_parts.append("""
            </div>
        </body>
        </html>
        """)

        return "\n".join(html_parts)

    def save_html_report(self, output_path: str = None, reports_dir: str = None) -> str:
        """保存 HTML 报告到文件"""
        html = self.generate_html()

        if reports_dir:
            from pathlib import Path
            import time
            reports_path = Path(reports_dir)
            reports_path.mkdir(parents=True, exist_ok=True)
            filename = f"report_{time.strftime('%Y-%m-%d_%H%M%S')}.html"
            output_path = reports_path / filename
        elif not output_path:
            raise ValueError("必须指定 output_path 或 reports_dir")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(output_path)

    def save_markdown_report(self, reports_dir: str = None) -> str:
        """保存 Markdown 报告到文件"""
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
