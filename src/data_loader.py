"""
数据加载模块 - 读取 Excel 文件
"""

import os
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime, timedelta


class DataLoader:
    """数据加载器"""

    # Excel 列名映射
    SALES_COLUMNS = {
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

    DISH_COLUMNS = {
        'dish_name': ['菜品名', 'dish_name', 'DishName', '菜品名称'],
        'category': ['分类', 'category', 'Category', '菜品分类'],
        'cost': ['成本', 'cost', 'Cost'],
        'price': ['售价', 'price', 'Price', '价格'],
    }

    TABLE_COLUMNS = {
        'table_id': ['桌台号', 'table_id', 'TableID', '桌台'],
        'seats': ['座位数', 'seats', 'Seats', '座位'],
        'area': ['区域', 'area', 'Area'],
        'is_vip': ['是否包间', 'is_vip', 'IsVIP', 'VIP'],
    }

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else None
        self.reference_path = None
        self.sales_path = None

    def set_paths(self, base_path: str):
        """设置数据根目录"""
        self.base_path = Path(base_path)
        self.reference_path = self.base_path / "reference"
        self.sales_path = self.base_path

    def _normalize_columns(self, df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
        """标准化列名"""
        df = df.copy()
        rename_dict = {}

        for standard_name, possible_names in column_map.items():
            for col in df.columns:
                if col in possible_names:
                    rename_dict[col] = standard_name
                    break

        df = df.rename(columns=rename_dict)
        return df

    def _get_sheet_name(self, excel_file: Path) -> str:
        """获取 Excel 文件的第一个 sheet 名"""
        xl = pd.ExcelFile(excel_file)
        return xl.sheet_names[0]

    def load_sales(self, date: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> pd.DataFrame:
        """
        加载销售数据

        Args:
            date: 单日日期 YYYY-MM-DD
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD

        Returns:
            销售数据 DataFrame
        """
        if not self.sales_path:
            raise ValueError("请先设置数据路径")

        dfs = []

        if date:
            # 单日数据
            file_name = f"sales_{date.replace('-', '')}.xlsx"
            if len(date) == 10:
                file_name = f"sales_{date}.xlsx"
            file_path = self.sales_path / date[:7].replace('-', '-') / file_name
            if file_path.exists():
                df = pd.read_excel(file_path, sheet_name=self._get_sheet_name(file_path))
                df = self._normalize_columns(df, self.SALES_COLUMNS)
                dfs.append(df)

        elif start_date and end_date:
            # 日期范围
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            while start <= end:
                date_str = start.strftime('%Y-%m-%d')
                month_dir = start.strftime('%Y-%m')
                file_name = f"sales_{date_str}.xlsx"
                file_path = self.sales_path / month_dir / file_name

                if file_path.exists():
                    df = pd.read_excel(file_path, sheet_name=self._get_sheet_name(file_path))
                    df = self._normalize_columns(df, self.SALES_COLUMNS)
                    dfs.append(df)

                start += timedelta(days=1)

        else:
            # 加载所有销售数据
            for month_dir in sorted(self.sales_path.glob("????-??")):
                if month_dir.is_dir():
                    for file_path in sorted(month_dir.glob("sales_*.xlsx")):
                        df = pd.read_excel(file_path, sheet_name=self._get_sheet_name(file_path))
                        df = self._normalize_columns(df, self.SALES_COLUMNS)
                        dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        result = pd.concat(dfs, ignore_index=True)

        # 确保数值列是正确类型
        for col in ['quantity', 'unit_price', 'subtotal']:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)

        # 确保时间列是正确类型
        if 'order_time' in result.columns:
            result['order_time'] = pd.to_datetime(result['order_time'], format='%H:%M', errors='coerce').dt.time

        return result

    def load_dishes(self) -> pd.DataFrame:
        """加载菜品目录"""
        if not self.reference_path:
            raise ValueError("请先设置数据路径")

        file_path = self.reference_path / "dishes.xlsx"
        if not file_path.exists():
            return pd.DataFrame()

        df = pd.read_excel(file_path, sheet_name=self._get_sheet_name(file_path))
        df = self._normalize_columns(df, self.DISH_COLUMNS)

        for col in ['cost', 'price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def load_tables(self) -> pd.DataFrame:
        """加载桌台信息"""
        if not self.reference_path:
            raise ValueError("请先设置数据路径")

        file_path = self.reference_path / "tables.xlsx"
        if not file_path.exists():
            return pd.DataFrame()

        df = pd.read_excel(file_path, sheet_name=self._get_sheet_name(file_path))
        df = self._normalize_columns(df, self.TABLE_COLUMNS)

        for col in ['seats']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        if 'is_vip' in df.columns:
            df['is_vip'] = df['is_vip'].apply(lambda x: str(x).lower() in ['是', 'vip', 'yes', 'true', '1'])

        return df

    def check_data_status(self) -> dict:
        """检查数据状态"""
        status = {
            'base_path': str(self.base_path) if self.base_path else None,
            'reference_exists': self.reference_path.exists() if self.reference_path else False,
            'dishes_exists': (self.reference_path / "dishes.xlsx").exists() if self.reference_path else False,
            'tables_exists': (self.reference_path / "tables.xlsx").exists() if self.reference_path else False,
            'sales_files_count': 0,
            'months': [],
        }

        if self.sales_path and self.sales_path.exists():
            for month_dir in self.sales_path.glob("????-??"):
                if month_dir.is_dir():
                    status['months'].append(month_dir.name)
                    status['sales_files_count'] += len(list(month_dir.glob("sales_*.xlsx")))

        return status


def create_template_files(base_path: str) -> dict:
    """
    创建模板文件

    Args:
        base_path: 数据根目录

    Returns:
        创建结果
    """
    base = Path(base_path)
    results = {
        'created': [],
        'errors': [],
    }

    try:
        # 创建目录结构
        (base / "reference").mkdir(parents=True, exist_ok=True)
        (base / "analysis_output").mkdir(parents=True, exist_ok=True)

        # 创建菜品模板
        dishes_df = pd.DataFrame({
            '菜品名称': ['示例菜品1', '示例菜品2', '示例菜品3'],
            '分类': ['刺身', '寿司', '烧物'],
            '成本': [25.0, 15.0, 20.0],
            '售价': [68.0, 38.0, 48.0],
        })

        # 添加空行作为填充提示
        empty_rows = pd.DataFrame([{
            '菜品名称': '',
            '分类': '',
            '成本': '',
            '售价': '',
        }] * 5)

        dishes_df = pd.concat([dishes_df, empty_rows], ignore_index=True)

        dishes_path = base / "reference" / "dishes.xlsx"
        dishes_df.to_excel(dishes_path, index=False, sheet_name='菜品目录')
        results['created'].append(str(dishes_path))

        # 创建桌台模板
        tables_df = pd.DataFrame({
            '桌台号': ['A1', 'A2', 'A3', 'A4', 'VIP-1', 'VIP-2'],
            '座位数': [4, 4, 6, 6, 8, 10],
            '区域': ['大厅', '大厅', '大厅', '大厅', '包间', '包间'],
            '是否包间': ['否', '否', '否', '否', '是', '是'],
        })

        tables_path = base / "reference" / "tables.xlsx"
        tables_df.to_excel(tables_path, index=False, sheet_name='桌台信息')
        results['created'].append(str(tables_path))

        # 创建销售日报模板
        today = datetime.now().strftime('%Y-%m-%d')
        month_dir = today[:7]
        sales_df = pd.DataFrame({
            '订单号': ['SO-20260108-001', 'SO-20260108-002'],
            '时间': ['11:30', '12:00'],
            '桌台': ['A1', 'A2'],
            '菜品名称': ['三文鱼刺身', '鳗鱼寿司'],
            '分类': ['刺身', '寿司'],
            '数量': [1, 2],
            '单价': [68.0, 38.0],
            '小计': [68.0, 76.0],
            '支付方式': ['微信', '支付宝'],
        })

        empty_rows = pd.DataFrame([{
            '订单号': '',
            '时间': '',
            '桌台': '',
            '菜品名称': '',
            '分类': '',
            '数量': '',
            '单价': '',
            '小计': '',
            '支付方式': '',
        }] * 10)

        sales_df = pd.concat([sales_df, empty_rows], ignore_index=True)

        sales_dir = base / month_dir
        sales_dir.mkdir(parents=True, exist_ok=True)
        sales_path = sales_dir / f"sales_{today}.xlsx"
        sales_df.to_excel(sales_path, index=False, sheet_name='订单明细')
        results['created'].append(str(sales_path))

    except Exception as e:
        results['errors'].append(str(e))

    return results
