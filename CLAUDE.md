# 日料店经营分析助手 (sushi-analysis)

日料店日常经营数据分析诊断工具，支持营收分析、菜品分析、时段分析、桌台效率分析。

## 首次使用流程

用户首次调用 `/sushi-analysis` 时：

```
1. 询问用户数据存储路径
   - 推荐 ~/sushi-data/
   - 或用户指定路径

2. 自动创建文件夹结构:
   ~/sushi-data/
   ├── reference/
   │   ├── dishes.xlsx          # 菜品模板
   │   └── tables.xlsx          # 桌台模板
   ├── 2026-01/                # 按月存放
   └── analysis_output/

3. 创建示例模板文件:
   - sales_YYYY-MM-DD.xlsx (今日销售示例)
   - dishes.xlsx (菜品目录)
   - tables.xlsx (桌台信息)

4. 告知用户文件结构和使用方法
```

## 数据要求

### 必需数据
| 文件 | 频率 | 说明 |
|------|------|------|
| sales_YYYY-MM-DD.xlsx | 每日 | 销售订单 |
| dishes.xlsx | 变动时 | 菜品目录 |
| tables.xlsx | 变动时 | 桌台信息 |

### 字段要求

**销售订单** (`sales_YYYY-MM-DD.xlsx`):
- 订单号、时间、桌台、菜品名称、分类、数量、单价、金额、支付方式

**菜品目录** (`dishes.xlsx`):
- 菜品名称、分类、成本、售价

**桌台信息** (`tables.xlsx`):
- 桌台号、座位数、区域、是否包间

## 交互选项

- [1] 今日日报
- [2] 本周分析
- [3] 指定日期范围
- [4] 全部汇总
- [5] 设置/更新数据路径

## 输出内容

1. **关键指标卡片** - 营收、订单数、客单价
2. **可视化图表** - 营收趋势、热销菜品、时段分布等
3. **分析摘要** - 亮点、关注点、改进建议
4. **报告导出** - Markdown/HTML 格式

## 技术实现

- Python 3.8+
- pandas - 数据处理
- matplotlib - 图表生成
- openpyxl - Excel 读取

## 文件结构

```
sushi-analysis/
├── CLAUDE.md           # 本文件
├── src/
│   ├── main.py         # 主入口 (SushiAnalysisSkill 类)
│   ├── data_loader.py  # DataLoader 类
│   ├── analyzer.py     # SalesAnalyzer 类
│   ├── visualizer.py   # ChartGenerator 类
│   └── report.py       # ReportGenerator 类
├── prompts/
│   ├── summary.md      # 分析摘要提示词
│   └── detailed.md     # 详细分析提示词
└── README.md
```
