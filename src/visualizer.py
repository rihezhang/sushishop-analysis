"""
可视化模块 - 生成图表
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from typing import List, Dict, Optional
import io
import base64
from pathlib import Path

# 设置中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class ChartGenerator:
    """图表生成器"""

    # 配色方案 - 简约专业风
    COLORS = {
        'primary': '#2563EB',      # 蓝色
        'secondary': '#3B82F6',    # 浅蓝
        'accent': '#10B981',       # 绿色
        'warning': '#F59E0B',      # 橙色
        'danger': '#EF4444',       # 红色
        'gray': '#6B7280',         # 灰色
        'light': '#F3F4F6',        # 浅灰
    }

    def __init__(self, theme: str = 'professional'):
        self.theme = theme
        self._set_style()

    def _set_style(self):
        """设置图表样式"""
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['axes.labelsize'] = 10

    def _save_to_base64(self, fig) -> str:
        """将图表保存为 base64"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_base64

    def _create_figure(self, figsize=(10, 6)):
        """创建图表"""
        fig, ax = plt.subplots(figsize=figsize)
        return fig, ax

    # ============ 营收图表 ============

    def plot_revenue_trend(self, data: List[Dict], title: str = "营收趋势") -> str:
        """
        营收趋势图

        Args:
            data: [{'hour': int, 'revenue': float, 'orders': int}, ...]
            title: 图表标题
        """
        if not data:
            return None

        df = pd.DataFrame(data)
        fig, ax = self._create_figure(figsize=(12, 5))

        # 绘制柱状图
        bars = ax.bar(df['hour'], df['revenue'], color=self.COLORS['primary'], alpha=0.8)

        # 绘制折线
        ax2 = ax.twinx()
        ax2.plot(df['hour'], df['orders'], color=self.COLORS['accent'], marker='o',
                 linewidth=2, markersize=6, label='订单数')

        # 设置标题和标签
        ax.set_xlabel('时段 (小时)')
        ax.set_ylabel('营收 (元)', color=self.COLORS['primary'])
        ax2.set_ylabel('订单数', color=self.COLORS['accent'])
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

        # 设置x轴刻度
        ax.set_xticks(df['hour'])
        ax.set_xticklabels([f'{h}:00' for h in df['hour']])

        # 添加数值标签
        for bar, val in zip(bars, df['revenue']):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                       f'¥{int(val)}', ha='center', va='bottom', fontsize=8)

        # 图例
        ax2.legend(loc='upper right')

        plt.tight_layout()
        return self._save_to_base64(fig)

    def plot_revenue_summary(self, summary: Dict) -> str:
        """
        营收汇总卡片（用文字展示）
        """
        # 返回一个简单的 HTML 格式卡片数据
        return summary

    # ============ 菜品图表 ============

    def plot_top_dishes(self, data: List[Dict], metric: str = 'revenue',
                        title: str = "热销菜品 TOP10") -> str:
        """
        热销菜品图

        Args:
            data: [{'dish_name': str, 'revenue': float}, ...]
            metric: 'revenue' 或 'quantity'
            title: 图表标题
        """
        if not data:
            return None

        df = pd.DataFrame(data)
        df = df.sort_values(metric, ascending=True)  # 升序以便横向柱状图

        fig, ax = self._create_figure(figsize=(10, max(6, len(df) * 0.5)))

        # 颜色渐变
        colors = [self.COLORS['primary'] if i < 5 else self.COLORS['secondary']
                  for i in range(len(df))]

        bars = ax.barh(df['dish_name'], df[metric], color=colors, height=0.7)

        # 设置标签
        ax.set_xlabel(f"{'销售额' if metric == 'revenue' else '销量'}")
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

        # 添加数值标签
        for bar, val in zip(bars, df[metric]):
            label = f'¥{int(val)}' if metric == 'revenue' else f'{int(val)}份'
            ax.text(bar.get_width() + max(df[metric]) * 0.01, bar.get_y() + bar.get_height()/2,
                   label, va='center', fontsize=9)

        ax.set_xlim(0, max(df[metric]) * 1.15)

        plt.tight_layout()
        return self._save_to_base64(fig)

    def plot_category_pie(self, data: List[Dict], title: str = "菜品分类占比") -> str:
        """
        分类占比饼图
        """
        if not data:
            return None

        df = pd.DataFrame(data)

        fig, ax = self._create_figure(figsize=(8, 6))

        colors = [self.COLORS['primary'], self.COLORS['secondary'],
                  self.COLORS['accent'], self.COLORS['warning'],
                  self.COLORS['danger'], self.COLORS['gray']]

        wedges, texts, autotexts = ax.pie(
            df['subtotal'], labels=df['category'],
            autopct=lambda p: f'{p:.1f}%' if p > 3 else '',
            colors=colors[:len(df)],
            startangle=90,
            explode=[0.02] * len(df)
        )

        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')

        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

        plt.tight_layout()
        return self._save_to_base64(fig)

    # ============ 时段图表 ============

    def plot_period_comparison(self, data: Dict, title: str = "午市 vs 晚市") -> str:
        """
        时段对比图
        """
        if not data:
            return None

        periods = list(data.keys())
        revenues = [data[p]['revenue'] for p in periods]
        orders = [data[p]['orders'] for p in periods]
        percentages = [data[p]['revenue_pct'] for p in periods]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # 左图：营收对比
        colors = [self.COLORS['primary'] if '午市' in p else self.COLORS['accent'] for p in periods]
        bars = ax1.bar(periods, revenues, color=colors, width=0.6)

        for bar, val, pct in zip(bars, revenues, percentages):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'¥{int(val)}\n({pct}%)', ha='center', va='bottom', fontsize=10)

        ax1.set_ylabel('营收 (元)')
        ax1.set_title('营收对比', fontsize=12, fontweight='bold')

        # 右图：订单数对比
        bars2 = ax2.bar(periods, orders, color=colors, width=0.6)

        for bar, val in zip(bars2, orders):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{int(val)}单', ha='center', va='bottom', fontsize=10)

        ax2.set_ylabel('订单数')
        ax2.set_title('订单对比', fontsize=12, fontweight='bold')

        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)

        plt.tight_layout()
        return self._save_to_base64(fig)

    def plot_hourly_distribution(self, data: List[Dict], title: str = "每小时订单分布") -> str:
        """
        每小时订单分布图
        """
        if not data:
            return None

        df = pd.DataFrame(data)
        df = df.sort_values('hour')

        fig, ax = self._create_figure(figsize=(12, 5))

        bars = ax.bar(df['hour'], df['count'], color=self.COLORS['primary'], alpha=0.8)

        # 标注高峰时段
        max_count = df['count'].max()
        for bar, row in zip(bars, df.itertuples()):
            if row.count >= max_count * 0.7:  # 高于70%最大值为高峰
                bar.set_color(self.COLORS['accent'])

        ax.set_xlabel('时段 (小时)')
        ax.set_ylabel('订单数')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

        ax.set_xticks(df['hour'])
        ax.set_xticklabels([f'{h}:00' for h in df['hour']])

        plt.tight_layout()
        return self._save_to_base64(fig)

    # ============ 桌台图表 ============

    def plot_table_efficiency(self, data: Dict, title: str = "桌台效率分析") -> str:
        """
        桌台效率分析
        """
        if not data or 'top_tables' not in data:
            return None

        df = pd.DataFrame(data['top_tables'])

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # 左图：桌台营收排行
        df_sorted = df.sort_values('revenue', ascending=True).tail(8)
        bars = ax1.barh(df_sorted['table_id'], df_sorted['revenue'],
                       color=self.COLORS['primary'], height=0.6)

        for bar, val in zip(bars, df_sorted['revenue']):
            ax1.text(bar.get_width() + max(df_sorted['revenue']) * 0.01,
                    bar.get_y() + bar.get_height()/2,
                    f'¥{int(val)}', va='center', fontsize=9)

        ax1.set_xlabel('营收 (元)')
        ax1.set_title('桌台营收 TOP', fontsize=12, fontweight='bold')

        # 右图：关键指标
        ax2.axis('off')

        metrics_text = f"""
        总桌台使用次数: {data.get('total_table_visits', 0)}
        预估翻台率: {data.get('estimated_turnover_rate', 0)}
        平均桌台营收: ¥{data.get('avg_revenue_per_table', 0)}
        """

        if data.get('vip_analysis'):
            vip = data['vip_analysis']
            metrics_text += f"""
        包间营收: ¥{vip.get('revenue', 0)} ({vip.get('revenue_pct', 0)}%)
        包间使用次数: {vip.get('visits', 0)}
            """

        ax2.text(0.5, 0.5, metrics_text, transform=ax2.transAxes,
                fontsize=12, verticalalignment='center', horizontalalignment='center',
                bbox=dict(boxstyle='round', facecolor=self.COLORS['light'], alpha=0.8))

        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)

        plt.tight_layout()
        return self._save_to_base64(fig)

    # ============ 支付方式图表 ============

    def plot_payment_breakdown(self, data: List[Dict], title: str = "支付方式分布") -> str:
        """
        支付方式分布图
        """
        if not data:
            return None

        df = pd.DataFrame(data)

        fig, ax = self._create_figure(figsize=(8, 5))

        colors = [self.COLORS['accent'], self.COLORS['primary'],
                  self.COLORS['warning'], self.COLORS['gray']]

        bars = ax.bar(df['payment'], df['revenue'], color=colors[:len(df)], width=0.6)

        for bar, row in zip(bars, df.itertuples()):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                   f'¥{int(row.revenue)}\n({row.percentage}%)',
                   ha='center', va='bottom', fontsize=9)

        ax.set_ylabel('营收 (元)')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

        plt.tight_layout()
        return self._save_to_base64(fig)

    # ============ 批量生成 ============

    def generate_all_charts(self, report: Dict) -> Dict[str, str]:
        """
        生成所有图表

        Returns:
            {'chart_name': 'base64_image_string', ...}
        """
        charts = {}

        # 营收趋势
        if report.get('revenue_trend'):
            charts['revenue_trend'] = self.plot_revenue_trend(report['revenue_trend'])

        # 热销菜品（按销售额）
        if report.get('top_dishes_revenue'):
            charts['top_dishes_revenue'] = self.plot_top_dishes(
                report['top_dishes_revenue'], 'revenue', '热销菜品 TOP10（按销售额）'
            )

        # 热销菜品（按销量）
        if report.get('top_dishes_quantity'):
            charts['top_dishes_quantity'] = self.plot_top_dishes(
                report['top_dishes_quantity'], 'quantity', '热销菜品 TOP10（按销量）'
            )

        # 分类占比
        if report.get('category_breakdown'):
            charts['category_pie'] = self.plot_category_pie(report['category_breakdown'])

        # 时段分析
        if report.get('period_analysis'):
            charts['period_comparison'] = self.plot_period_comparison(report['period_analysis'])

        # 每小时分布
        if report.get('hourly_distribution'):
            charts['hourly_distribution'] = self.plot_hourly_distribution(report['hourly_distribution'])

        # 桌台分析
        if report.get('table_analysis'):
            charts['table_efficiency'] = self.plot_table_efficiency(report['table_analysis'])

        # 支付方式
        if report.get('payment_breakdown'):
            charts['payment_breakdown'] = self.plot_payment_breakdown(report['payment_breakdown'])

        return charts
