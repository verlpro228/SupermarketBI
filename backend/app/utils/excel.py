from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def _display_width(value: Any) -> int:
    text = str(value)
    return sum(2 if ord(char) > 127 else 1 for char in text)


def build_workbook(sheet_title: str, headers: list[str], rows: list[list[Any]]) -> BytesIO:
    """生成带表头样式的 Excel 工作簿，返回内存字节流。"""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_title

    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)

    header_fill = PatternFill("solid", fgColor="2C4A6E")
    header_font = Font(bold=True, color="FFFFFF")
    thin_side = Side(style="thin", color="D9D9D9")
    border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.border = border

    for index, column in enumerate(worksheet.columns, start=1):
        max_width = 0
        for cell in column:
            if cell.value is None:
                continue
            max_width = max(max_width, _display_width(cell.value))
        worksheet.column_dimensions[get_column_letter(index)].width = min(
            max(max_width + 4, 10), 50
        )

    worksheet.freeze_panes = "A2"

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer
