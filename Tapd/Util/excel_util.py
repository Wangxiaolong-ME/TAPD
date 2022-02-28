import xlrd as xlrd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference


class ExcelUtil:
    class ExcelBarChart:
        def __init__(self, file):
            self.file = file

        def create_workbook(self):
            wb = Workbook(write_only=True)
            return wb

        def chart_attribute(self, title='', x_title='', y_title='', style=39, width=40, height=12):
            # 柱形图属性
            chart = BarChart()
            chart.type = 'col'      # col:纵向柱形图, bar:横向柱形图
            chart.style = style     # 样式
            chart.width = width     # 宽度
            chart.height = height   # 高度
            chart.title = title     # 标题
            chart.x_axis.title = x_title    # 横轴标题
            chart.y_axis.title = y_title    # 纵轴标题
            return chart

        def load_excel(self):
            """两列数据"""
            tables = {}
            data = xlrd.open_workbook(self.file)
            how_many_sheets = len(data.sheets())
            sheet_names = data.sheet_names()
            for sheet in range(how_many_sheets):
                table = data.sheets()[sheet]
                sheet_table = []
                for i in range(table.nrows):
                    row = table.row_values(i)
                    col1 = row[0]
                    col2 = row[1]
                    sheet_table.append([col1, col2])
                tables[sheet_names[sheet]] = sheet_table
            return tables

        def build_bar_chart(self, wb, title, rows):
            """
            rows: 所有行数据
            max_row: 展示多少个数据绘制到柱形图上
            cell: 柱形图开始单元格位置
            """

            ws = wb.create_sheet(title=title)
            for row in rows:
                ws.append(row)

            max_row = len(rows) + 1

            # total 数据图
            data = Reference(ws, min_col=2, min_row=1, max_row=max_row, max_col=2)  # y 轴数值
            cats = Reference(ws, min_col=1, min_row=2, max_row=max_row)  # x轴数据

            # 前20 数据图
            data2 = Reference(ws, min_col=2, min_row=1, max_row=max_row / 2, max_col=2)  # y 轴数值
            cats2 = Reference(ws, min_col=1, min_row=2, max_row=max_row / 2)  # x轴数据

            chart = self.chart_attribute(title='Total', y_title='TF-IDF', width=50)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            ws.add_chart(chart, "D2")

            chart2 = self.chart_attribute(width=30, height=10, title=f'Top{int(max_row / 2 -1)}', y_title='TF-IDF')
            chart2.add_data(data2, titles_from_data=True)
            chart2.set_categories(cats2)
            ws.add_chart(chart2, "D30")

            return wb


def build_bar_chart(source_file, target_file):
    bar = ExcelUtil.ExcelBarChart(source_file)  # 实例化工具类
    tables = bar.load_excel()   # 读取excel内容,返回 以工作表名称为键 行内容列表集合为值 的字典
    wb = bar.create_workbook()  # 实例化表格
    for ft_title in tables.keys():  # 根据工作表名称,分别生成柱形图
        bar.build_bar_chart(wb, ft_title, tables[ft_title])     # 生成柱形图
    wb.save(target_file)    # 保存
