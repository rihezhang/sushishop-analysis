"""
数据分析模块 - 计算各项指标
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class DataValidator:
    """数据验证器"""

    # 必需的列及其别名
    REQUIRED_COLUMNS = {
        'order_id': ['订单号', 'order_id', 'OrderID'],
        'order_time': ['时间', 'order_time', 'Time', '下单时间'],
        'table_id': ['桌台', 'table_id', 'TableID', '桌台号'],
        'dish_name': ['菜品名', 'dish_name', 'DishName', '菜品名称'],
        'category': ['分类', 'category', 'Category', '菜品分类'],
        'quantity': ['数量', 'quantity', 'Quantity', '销售数量'],
        'unit_price': ['单价', 'unit_price', 'Price', '价格'],
        'subtotal': ['金额', 'subtotal', 'Subtotal', '小计'],
        'payment': ['支付方式', 'payment', 'Payment', '支付'],
    }

    @classmethod
    def validate(cls, df: pd.DataFrame) -> Dict:
        """
        验证数据并返回验证报告

        Returns:
            {
                'valid': bool,
                'errors': [],
                'warnings': [],
                'column_mapping': {}
            }
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'column_mapping': {},
            'missing_columns': [],
        }

        if df.empty:
            result['valid'] = False
            result['errors'].append('数据为空')
            return result

        # 检查列名映射
        for standard_name, aliases in cls.REQUIRED_COLUMNS.items():
            found = False
            for col in df.columns:
                if col in aliases:
                    result['column_mapping'][standard_name] = col
                    found = True
                    break
            if not found:
                result['missing_columns'].append(standard_name)

        # 必需列检查
        essential_cols = ['dish_name', 'subtotal']
        for col in essential_cols:
            if col not in result['column_mapping']:
                result['valid'] = False
                result['errors'].append(f'缺少必需列: {col}')

        # 警告检查
        if 'quantity' in result['column_mapping']:
            qty_col = result['column_mapping']['quantity']
            if (df[qty_col] <= 0).any():
                result['warnings'].append('部分数据数量<=0')

        if 'subtotal' in result['column_mapping']:
            sub_col = result['column_mapping']['subtotal']
            if (df[sub_col] <= 0).any():
                result['warnings'].append('部分数据金额<=0')

        # 检查空行
        if 'dish_name' in result['column_mapping']:
            name_col = result['column_mapping']['dish_name']
            empty_rows = df[name_col].isna() | (df[name_col] == '')
            if empty_rows.any():
                result['warnings'].append(f'发现 {empty_rows.sum()} 行空数据')

        return result

    @classmethod
    def get_validation_report(cls, validation: Dict) -> str:
        """生成验证报告文本"""
        lines = []

        if validation['valid']:
            lines.append("✅ 数据验证通过")
        else:
            lines.append("❌ 数据验证失败:")
            for err in validation['errors']:
                lines.append(f"   - {err}")

        if validation['warnings']:
            lines.append("\n⚠️ 警告:")
            for warn in validation['warnings']:
                lines.append(f"   - {warn}")

        return "\n".join(lines)


class SalesAnalyzer:
    """销售数据分析器"""

    def __init__(self, sales_df: pd.DataFrame, dishes_df: Optional[pd.DataFrame] = None,
                 tables_df: Optional[pd.DataFrame] = None):
        self.sales = sales_df.copy() if not sales_df.empty else pd.DataFrame()
        self.dishes = dishes_df.copy() if dishes_df is not None and not dishes_df.empty else None
        self.tables = tables_df.copy() if tables_df is not None and not tables_df.empty else None
        self._date_range = None

        self._prepare_data()

    def _prepare_data(self):
        """数据预处理"""
        if self.sales.empty:
            return

        # 计算小时
        if 'order_time' in self.sales.columns:
            try:
                self.sales['hour'] = pd.to_datetime(self.sales['order_time'], format='%H:%M', errors='coerce').dt.hour
                self.sales['hour'] = self.sales['hour'].fillna(0).astype(int)
            except:
                self.sales['hour'] = self.sales['order_time'].apply(
                    lambda x: int(str(x).split(':')[0]) if pd.notna(x) and ':' in str(x) else 0
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
                quantity_col = self.sales.get('quantity', 1)
                if quantity_col is None:
                    quantity_col = 1
                self.sales['profit'] = self.sales['subtotal'] - (self.sales['cost'] * quantity_col)

    def set_date_range(self, start_date: str, end_date: str):
        """设置分析的日期范围"""
        self._date_range = (start_date, end_date)

    # ============ 数据验证 ============

    def validate_data(self) -> Dict:
        """验证当前数据"""
        return DataValidator.validate(self.sales)

    def get_validation_report(self) -> str:
        """获取数据验证报告"""
        return DataValidator.get_validation_report(self.validate_data())

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
            'date_range': self._date_range,
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
            # 按日期分组 - 从文件名或 order_id 提取日期
            return pd.DataFrame()

    def get_daily_trend(self) -> pd.DataFrame:
        """
        获取每日趋势（从文件名提取日期）
        """
        if self.sales.empty:
            return pd.DataFrame()

        # 尝试从 order_id 提取日期
        if 'order_id' in self.sales.columns:
            # order_id 格式: SO-20260709-001
            self.sales['date'] = self.sales['order_id'].str.extract(r'(\d{8})')
            if self.sales['date'].notna().any():
                # 转换为日期格式
                self.sales['date'] = pd.to_datetime(self.sales['date'], format='%Y%m%d', errors='coerce')

                trend = self.sales.groupby('date').agg({
                    'subtotal': 'sum',
                    'order_id': 'nunique',
                    'quantity': 'sum',
                }).reset_index()
                trend.columns = ['date', 'revenue', 'orders', 'dishes']
                trend['date'] = trend['date'].dt.strftime('%Y-%m-%d')
                return trend.sort_values('date')

        return pd.DataFrame()

    # ============ 同比/环比分析 ============

    def get_comparison_analysis(self, current_data: 'SalesAnalyzer' = None) -> Dict:
        """
        获取同比/环比分析

        Args:
            current_data: 当前期间的分析器实例
        """
        if self.sales.empty:
            return {}

        current_summary = self.get_revenue_summary()

        result = {
            'current': current_summary,
            'comparison': None,
        }

        if current_data and not current_data.sales.empty:
            previous_summary = current_data.get_revenue_summary()

            # 计算变化
            curr_rev = current_summary.get('total_revenue', 0)
            prev_rev = previous_summary.get('total_revenue', 0)

            curr_orders = current_summary.get('total_orders', 0)
            prev_orders = previous_summary.get('total_orders', 0)

            rev_change = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
            order_change = ((curr_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0

            result['comparison'] = {
                'previous_period': previous_summary,
                'revenue_change_pct': round(rev_change, 1),
                'order_change_pct': round(order_change, 1),
                'revenue_change_abs': round(curr_rev - prev_rev, 2),
                'trend': 'up' if rev_change > 0 else ('down' if rev_change < 0 else 'flat'),
            }

        return result

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

        agg_dict = {agg_col: 'sum'}
        if 'category' in self.sales.columns:
            agg_dict['category'] = 'first'

        top = self.sales.groupby('dish_name').agg(agg_dict).reset_index()

        if 'category' in top.columns:
            top = top[['dish_name', agg_col, 'category']]
            top.columns = ['dish_name', metric, 'category']
        else:
            top = top[['dish_name', agg_col]]
            top.columns = ['dish_name', metric]

        top = top.sort_values(metric, ascending=False).head(top_n)

        # 计算占比
        total = top[metric].sum()
        top['pct'] = (top[metric] / total * 100).round(1)

        return top

    def get_bottom_dishes(self, metric: str = 'revenue', bottom_n: int = 10) -> pd.DataFrame:
        """获取滞销菜品"""
        if self.sales.empty or 'dish_name' not in self.sales.columns:
            return pd.DataFrame()

        if metric == 'revenue':
            agg_col = 'subtotal'
        else:
            agg_col = 'quantity'

        agg_dict = {agg_col: 'sum'}
        if 'category' in self.sales.columns:
            agg_dict['category'] = 'first'

        bottom = self.sales.groupby('dish_name').agg(agg_dict).reset_index()

        if 'category' in bottom.columns:
            bottom = bottom[['dish_name', agg_col, 'category']]
            bottom.columns = ['dish_name', metric, 'category']
        else:
            bottom = bottom[['dish_name', agg_col]]
            bottom.columns = ['dish_name', metric]

        # 过滤掉销量为0的
        bottom = bottom[bottom[metric] > 0]
        bottom = bottom.sort_values(metric, ascending=True).head(bottom_n)

        return bottom

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
        breakdown['profit'] = 0  # 需要成本数据才能计算

        return breakdown.sort_values('subtotal', ascending=False)

    def get_category_trend(self) -> pd.DataFrame:
        """获取各分类的每日趋势"""
        if self.sales.empty or 'category' not in self.sales.columns:
            return pd.DataFrame()

        if 'order_id' in self.sales.columns:
            self.sales['date'] = self.sales['order_id'].str.extract(r'(\d{8})')
            if self.sales['date'].notna().any():
                self.sales['date'] = pd.to_datetime(self.sales['date'], format='%Y%m%d', errors='coerce')

                trend = self.sales.pivot_table(
                    index='date',
                    columns='category',
                    values='subtotal',
                    aggfunc='sum',
                    fill_value=0
                ).reset_index()

                trend['date'] = pd.to_datetime(trend['date']).dt.strftime('%Y-%m-%d')
                return trend.sort_values('date')

        return pd.DataFrame()

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

        # 同时计算营收
        revenue_by_hour = self.sales.groupby('hour')['subtotal'].sum().reset_index()
        revenue_by_hour.columns = ['hour', 'revenue']

        result = []
        for _, row in hourly.iterrows():
            rev = revenue_by_hour[revenue_by_hour['hour'] == row['hour']]['revenue'].values
            result.append({
                'hour': int(row['hour']),
                'count': int(row['count']),
                'percentage': round(row['count'] / total * 100, 1),
                'revenue': round(float(rev[0]) if len(rev) > 0 else 0, 2),
            })

        return result

    def get_peak_hours(self) -> Dict:
        """识别高峰时段"""
        hourly = self.get_hourly_distribution()
        if not hourly:
            return {}

        max_count = max(h['count'] for h in hourly)
        peak_threshold = max_count * 0.7

        peaks = [h for h in hourly if h['count'] >= peak_threshold]

        return {
            'peak_hours': [h['hour'] for h in peaks],
            'peak_details': peaks,
            'max_hour': max(hourly, key=lambda x: x['count']),
        }

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
            estimated_turnover = total_visits / (total_seats / 4) if total_seats > 0 else 0
        else:
            total_visits = table_usage['visits'].sum()
            estimated_turnover = total_visits / 35

        # 计算上座率（基于总座位数和订单数估算）
        if self.tables is not None:
            total_seats = self.tables['seats'].sum()
            unique_tables_used = table_usage['table_id'].nunique()
            total_table_capacity = self.tables['seats'].sum()
            # 简化上座率估算
            avg_occupancy_rate = min(100, (total_visits / unique_tables_used) * 25)  # 假设翻台3次/天
        else:
            avg_occupancy_rate = 0

        # VIP 包间分析
        vip_info = None
        if self.tables is not None and 'is_vip' in self.tables.columns:
            vip_table_ids = self.tables[self.tables['is_vip']]['table_id'].tolist()
            vip_data = table_usage[table_usage['table_id'].isin(vip_table_ids)]
            vip_revenue = vip_data['revenue'].sum()
            vip_visits = vip_data['visits'].sum()
            total_revenue = self.sales['subtotal'].sum()
            vip_pct = vip_revenue / total_revenue * 100 if total_revenue > 0 else 0

            vip_info = {
                'revenue': round(vip_revenue, 2),
                'visits': int(vip_visits),
                'revenue_pct': round(vip_pct, 1),
                'table_count': len(vip_table_ids),
            }

        return {
            'total_table_visits': int(total_visits),
            'unique_tables_used': int(unique_tables_used),
            'estimated_turnover_rate': round(estimated_turnover, 2),
            'avg_revenue_per_table': round(table_usage['revenue'].mean(), 2),
            'occupancy_rate': round(avg_occupancy_rate, 1),
            'top_tables': table_usage.sort_values('revenue', ascending=False).head(5).to_dict('records'),
            'bottom_tables': table_usage.sort_values('revenue', ascending=True).head(3).to_dict('records'),
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
            'daily_trend': self.get_daily_trend().to_dict('records') if not self.get_daily_trend().empty else [],
            'top_dishes_revenue': self.get_top_dishes('revenue').to_dict('records'),
            'top_dishes_quantity': self.get_top_dishes('quantity').to_dict('records'),
            'bottom_dishes': self.get_bottom_dishes('quantity').to_dict('records'),
            'category_breakdown': self.get_category_breakdown().to_dict('records'),
            'category_trend': self.get_category_trend().to_dict('records') if not self.get_category_trend().empty else [],
            'period_analysis': self.get_period_analysis(),
            'hourly_distribution': self.get_hourly_distribution(),
            'peak_hours': self.get_peak_hours(),
            'table_analysis': self.get_table_analysis(),
            'payment_breakdown': self.get_payment_breakdown().to_dict('records'),
            'validation': self.validate_data(),
        }
