"""
数据分析模块 - 计算各项指标
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class SalesAnalyzer:
    """销售数据分析器"""

    def __init__(self, sales_df: pd.DataFrame, dishes_df: Optional[pd.DataFrame] = None,
                 tables_df: Optional[pd.DataFrame] = None):
        self.sales = sales_df.copy() if not sales_df.empty else pd.DataFrame()
        self.dishes = dishes_df.copy() if dishes_df is not None and not dishes_df.empty else None
        self.tables = tables_df.copy() if tables_df is not None and not tables_df.empty else None

        self._prepare_data()

    def _prepare_data(self):
        """数据预处理"""
        if self.sales.empty:
            return

        # 提取日期
        if 'order_time' in self.sales.columns:
            # 假设 order_time 包含日期和时间信息，或者从 order_id 中提取
            # 这里假设 order_time 已经是正确的时间格式
            pass

        # 计算小时
        if 'order_time' in self.sales.columns:
            self.sales['hour'] = self.sales['order_time'].apply(
                lambda x: x.hour if x else 0
            )

        # 添加时段分类
        def get_period(hour):
            if 11 <= hour < 14:
                return '午市'
            elif 17 <= hour < 21:
                return '晚市'
            elif hour >= 21 or hour < 6:
                return '宵夜'
            else:
                return '其他'

        if 'hour' in self.sales.columns:
            self.sales['period'] = self.sales['hour'].apply(get_period)

        # 计算毛利（如果有成本数据）
        if self.dishes is not None and 'cost' in self.dishes.columns:
            dish_cost_map = dict(zip(self.dishes['dish_name'], self.dishes['cost']))
            if 'dish_name' in self.sales.columns and 'subtotal' in self.sales.columns:
                self.sales['cost'] = self.sales['dish_name'].map(dish_cost_map).fillna(0)
                self.sales['profit'] = self.sales['subtotal'] - (self.sales['cost'] * self.sales.get('quantity', 1))

    # ============ 营收分析 ============

    def get_revenue_summary(self) -> Dict:
        """获取营收汇总"""
        if self.sales.empty:
            return {}

        total_revenue = self.sales['subtotal'].sum()
        total_orders = len(self.sales['order_id'].unique()) if 'order_id' in self.sales.columns else len(self.sales)
        total_dishes = self.sales['quantity'].sum()
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        avg_dishes_per_order = total_dishes / total_orders if total_orders > 0 else 0

        return {
            'total_revenue': round(total_revenue, 2),
            'total_orders': int(total_orders),
            'total_dishes': int(total_dishes),
            'avg_order_value': round(avg_order_value, 2),
            'avg_dishes_per_order': round(avg_dishes_per_order, 2),
        }

    def get_revenue_trend(self, group_by: str = 'hour') -> pd.DataFrame:
        """
        获取营收趋势

        Args:
            group_by: 'hour' 按小时, 'date' 按日期
        """
        if self.sales.empty:
            return pd.DataFrame()

        if group_by == 'hour':
            trend = self.sales.groupby('hour').agg({
                'subtotal': 'sum',
                'order_id': 'nunique' if 'order_id' in self.sales.columns else 'count'
            }).reset_index()
            trend.columns = ['hour', 'revenue', 'orders']
            return trend
        else:
            # 按日期分组（如果有日期信息的话）
            return pd.DataFrame()

    # ============ 菜品分析 ============

    def get_top_dishes(self, metric: str = 'revenue', top_n: int = 10) -> pd.DataFrame:
        """
        获取热销菜品

        Args:
            metric: 'revenue' 按销售额, 'quantity' 按销量
            top_n: 返回前 N 个
        """
        if self.sales.empty or 'dish_name' not in self.sales.columns:
            return pd.DataFrame()

        if metric == 'revenue':
            agg_col = 'subtotal'
        else:
            agg_col = 'quantity'

        top = self.sales.groupby('dish_name').agg({
            agg_col: 'sum',
            'category': 'first' if 'category' in self.sales.columns else None,
        }).reset_index()

        top.columns = ['dish_name', metric, 'category'] if 'category' in top.columns else ['dish_name', metric]
        top = top.sort_values(metric, ascending=False).head(top_n)

        return top

    def get_category_breakdown(self) -> pd.DataFrame:
        """获取分类占比"""
        if self.sales.empty or 'category' not in self.sales.columns:
            return pd.DataFrame()

        breakdown = self.sales.groupby('category').agg({
            'subtotal': 'sum',
            'quantity': 'sum',
        }).reset_index()

        total = breakdown['subtotal'].sum()
        breakdown['percentage'] = (breakdown['subtotal'] / total * 100).round(1)

        return breakdown.sort_values('subtotal', ascending=False)

    # ============ 时段分析 ============

    def get_period_analysis(self) -> Dict:
        """获取时段分析"""
        if self.sales.empty or 'period' not in self.sales.columns:
            return {}

        period_stats = self.sales.groupby('period').agg({
            'subtotal': 'sum',
            'order_id': 'nunique' if 'order_id' in self.sales.columns else 'count',
        }).reset_index()

        period_stats.columns = ['period', 'revenue', 'orders']
        total_revenue = period_stats['revenue'].sum()

        result = {}
        for _, row in period_stats.iterrows():
            result[row['period']] = {
                'revenue': round(row['revenue'], 2),
                'orders': int(row['orders']),
                'revenue_pct': round(row['revenue'] / total_revenue * 100, 1) if total_revenue > 0 else 0,
            }

        return result

    def get_hourly_distribution(self) -> List[Dict]:
        """获取每小时订单分布"""
        if self.sales.empty or 'hour' not in self.sales.columns:
            return []

        hourly = self.sales.groupby('hour').size().reset_index(name='count')
        total = hourly['count'].sum()

        return [
            {'hour': int(row['hour']), 'count': int(row['count']), 'percentage': round(row['count'] / total * 100, 1)}
            for _, row in hourly.iterrows()
        ]

    # ============ 桌台分析 ============

    def get_table_analysis(self) -> Dict:
        """获取桌台分析"""
        if self.sales.empty or 'table_id' not in self.sales.columns:
            return {}

        # 桌台使用情况
        table_usage = self.sales.groupby('table_id').agg({
            'order_id': 'nunique' if 'order_id' in self.sales.columns else 'count',
            'subtotal': 'sum',
            'quantity': 'sum',
        }).reset_index()

        table_usage.columns = ['table_id', 'visits', 'revenue', 'dishes']

        # 计算翻台率（估算）
        if self.tables is not None and 'seats' in self.tables.columns:
            total_seats = self.tables['seats'].sum()
            total_visits = table_usage['visits'].sum()
            estimated_turnover = total_visits / (total_seats / 4) if total_seats > 0 else 0  # 假设每桌4人
        else:
            total_visits = table_usage['visits'].sum()
            estimated_turnover = total_visits / 35  # 35个座位作为默认值

        # VIP 包间分析
        vip_tables = []
        if self.tables is not None and 'is_vip' in self.tables.columns:
            vip_table_ids = self.tables[self.tables['is_vip']]['table_id'].tolist()
            vip_data = table_usage[table_usage['table_id'].isin(vip_table_ids)]
            vip_revenue = vip_data['revenue'].sum()
            vip_visits = vip_data['visits'].sum()
            vip_pct = vip_revenue / self.sales['subtotal'].sum() * 100 if self.sales['subtotal'].sum() > 0 else 0
            vip_tables = vip_table_ids

            vip_info = {
                'revenue': round(vip_revenue, 2),
                'visits': int(vip_visits),
                'revenue_pct': round(vip_pct, 1),
                'table_count': len(vip_table_ids),
            }
        else:
            vip_info = None

        return {
            'total_table_visits': int(total_visits),
            'estimated_turnover_rate': round(estimated_turnover, 2),
            'avg_revenue_per_table': round(table_usage['revenue'].mean(), 2),
            'top_tables': table_usage.sort_values('revenue', ascending=False).head(5).to_dict('records'),
            'vip_analysis': vip_info,
        }

    # ============ 支付方式分析 ============

    def get_payment_breakdown(self) -> pd.DataFrame:
        """获取支付方式分布"""
        if self.sales.empty or 'payment' not in self.sales.columns:
            return pd.DataFrame()

        payment = self.sales.groupby('payment').agg({
            'subtotal': 'sum',
            'order_id': 'nunique' if 'order_id' in self.sales.columns else 'count',
        }).reset_index()

        payment.columns = ['payment', 'revenue', 'orders']
        total = payment['revenue'].sum()
        payment['percentage'] = (payment['revenue'] / total * 100).round(1)

        return payment.sort_values('revenue', ascending=False)

    # ============ 综合报告 ============

    def generate_full_report(self) -> Dict:
        """生成完整分析报告"""
        return {
            'revenue': self.get_revenue_summary(),
            'revenue_trend': self.get_revenue_trend().to_dict('records') if not self.get_revenue_trend().empty else [],
            'top_dishes_revenue': self.get_top_dishes('revenue').to_dict('records'),
            'top_dishes_quantity': self.get_top_dishes('quantity').to_dict('records'),
            'category_breakdown': self.get_category_breakdown().to_dict('records'),
            'period_analysis': self.get_period_analysis(),
            'hourly_distribution': self.get_hourly_distribution(),
            'table_analysis': self.get_table_analysis(),
            'payment_breakdown': self.get_payment_breakdown().to_dict('records'),
        }
