"""
excel_generator.py

Generates the Weekly Closing workbook.

Responsibilities

Database
      ↓
Report Queries
      ↓
Template Mapper
      ↓
Excel Generator
      ↓
Weekly Closing.xlsx

This module DOES NOT

- calculate salary
- parse Excel
- execute business logic
"""

from __future__ import annotations
from template_mapper import WEEKLY_CLOSING_TEMPLATE
from dataclasses import dataclass
from pathlib import Path

import sqlite3

from openpyxl import Workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)
from openpyxl.worksheet.worksheet import Worksheet

from database import connect_database
from report_queries import run_report_query
from template_mapper import WorkbookTemplate


# ==========================================================
# PATHS
# ==========================================================

CURRENT_FILE = Path(__file__).resolve()

PROJECT_ROOT = CURRENT_FILE.parent

EXPORT_FOLDER = PROJECT_ROOT / "exports"


# ==========================================================
# DEFAULT STYLES
# ==========================================================

THIN_BORDER = Border(

    left=Side(style="thin"),

    right=Side(style="thin"),

    top=Side(style="thin"),

    bottom=Side(style="thin"),

)

TITLE_FONT = Font(

    bold=True,

    size=13,

)

HEADER_FONT = Font(

    bold=True,

)

HEADER_FILL = PatternFill(

    fill_type="solid",

    fgColor="D9D9D9",

)

CENTER = Alignment(

    horizontal="center",

    vertical="center",

)

LEFT = Alignment(

    horizontal="left",

    vertical="center",

)


# ==========================================================
# RENDER CONTEXT
# ==========================================================

@dataclass
class RenderContext:
    """
    Maintains the rendering position of
    a worksheet.

    The cursor automatically moves down
    as sections are rendered.
    """

    worksheet: Worksheet

    current_row: int = 1


# ==========================================================
# WORKBOOK HELPERS
# ==========================================================

def create_workbook() -> Workbook:
    """
    Creates a new workbook.
    """

    workbook = Workbook()

    default_sheet = workbook.active

    workbook.remove(default_sheet)

    return workbook


def create_sheet(
    workbook: Workbook,
    name: str,
) -> RenderContext:
    """
    Creates a worksheet and returns
    its render context.
    """

    worksheet = workbook.create_sheet(name)

    return RenderContext(
        worksheet=worksheet,
    )


# ==========================================================
# STYLE HELPERS
# ==========================================================

def style_title(cell) -> None:

    cell.font = TITLE_FONT

    cell.alignment = LEFT


def style_header(cell) -> None:

    cell.font = HEADER_FONT

    cell.fill = HEADER_FILL

    cell.alignment = CENTER

    cell.border = THIN_BORDER


def style_body(cell) -> None:

    cell.border = THIN_BORDER

    cell.alignment = LEFT


def style_number(cell) -> None:

    cell.border = THIN_BORDER

    cell.alignment = CENTER

    cell.number_format = "#,##0.00"


# ==========================================================
# SAVE
# ==========================================================

def save_workbook(
    workbook: Workbook,
    week_id: int,
) -> Path:
    """
    Saves the workbook.
    """

    EXPORT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = (
        EXPORT_FOLDER
        / f"Weekly_Closing_Week_{week_id}.xlsx"
    )

    try:
        workbook.save(file_path)
    except PermissionError as err:
        raise RuntimeError(
            f"Cannot write generated workbook to '{file_path}' because it is currently open in Excel or write-locked. Please close the file and try again."
        ) from err

    return file_path


# ==========================================================
# CURSOR HELPERS
# ==========================================================

def current_row(context: RenderContext) -> int:
    """
    Returns the current worksheet row.
    """

    return context.current_row


def next_row(
    context: RenderContext,
    rows: int = 1,
) -> None:
    """
    Moves the rendering cursor down.
    """

    context.current_row += rows


# ==========================================================
# WRITING HELPERS
# ==========================================================

def write_cell(
    context: RenderContext,
    column: int,
    value,
):
    """
    Writes a single cell.
    """

    cell = context.worksheet.cell(
        row=context.current_row,
        column=column,
        value=value,
    )

    return cell


def write_row(
    context: RenderContext,
    values: list,
):
    """
    Writes one row and moves
    to the next row.
    """

    for column, value in enumerate(values, start=1):

        cell = context.worksheet.cell(
            row=context.current_row,
            column=column,
            value=value,
        )

        style_body(cell)

    next_row(context)


# ==========================================================
# TITLE
# ==========================================================

def render_title(
    context: RenderContext,
    title: str,
    column_count: int = 4,
):
    """
    Writes the section title.
    """

    cell = write_cell(
        context,
        1,
        title,
    )

    style_title(cell)

    context.worksheet.merge_cells(
        start_row=context.current_row,
        start_column=1,
        end_row=context.current_row,
        end_column=column_count,
    )

    next_row(context)


# ==========================================================
# HEADER
# ==========================================================

def render_header(
    context: RenderContext,
    columns: list[str],
):
    """
    Writes column headers.
    """

    for column, name in enumerate(columns, start=1):

        cell = context.worksheet.cell(
            row=context.current_row,
            column=column,
            value=name,
        )

        style_header(cell)

    next_row(context)


# ==========================================================
# TABLE
# ==========================================================

def render_table(
    context: RenderContext,
    rows: list[dict],
    columns: tuple[str, ...] | None = None,
):
    """
    Writes all table rows.

    If columns are provided by the template mapper,
    only those columns are rendered and in that order.
    """

    if not rows:

        write_row(
            context,
            ["No Data"],
        )

        return

    if columns is None:

        columns = tuple(rows[0].keys())

    headers = {
        "employee_name": "Name",
        "name": "Name",
        "contractor": "Contractor",
        "item": "Item",
        "total_qty": "Qty",
        "rate": "Rate",
        "total_amount": "Salary",
        "salary": "Salary",
        "total_shifts": "Shift",
        "total_salary": "Salary",
        "expense_name": "Expense Name",
        "amount": "Amount",
        "style": "Style",
        "days": "Days",
        "s_no": "S.No",
        "department": "Department",
        "particular": "Particular / Operations",
        "qty": "Qty",
        "amt": "Amt",
        "operation": "Operation",
        "item": "Item",
        "shift": "Shift",
        "rate_per_shift": "Shift Rate",
    }

    render_header(
        context,
        [
            headers.get(column, column.replace("_", " ").title())
            for column in columns
        ],
    )

    for index, row in enumerate(rows, start=1):

        values = []

        for column in columns:

            if column == "s_no":
                values.append(index)

            else:
                values.append(row.get(column))

        write_row(
            context,
            values,
        )



# ==========================================================
# TOTALS
# ==========================================================

def render_total(
    context: RenderContext,
    label: str,
    amount,
):
    """
    Writes a simple total row.
    """

    cell = context.worksheet.cell(
        row=context.current_row,
        column=1,
        value=label,
    )

    style_header(cell)

    value = context.worksheet.cell(
        row=context.current_row,
        column=2,
        value=amount,
    )

    style_number(value)

    next_row(context)


def render_section_total(
    context: RenderContext,
    rows: list[dict],
    columns: tuple[str, ...],
    metadata: dict,
):
    """
    Writes a total row under a table, summing whichever
    columns are listed in metadata["total_sum_columns"].

    Driven entirely by metadata so any section can opt in
    via render_rules.show_total without generator changes.
    """

    if not rows or not columns:
        return

    label = metadata.get("total_label", "Total")

    sum_columns = metadata.get("total_sum_columns", ())

    for index, column in enumerate(columns, start=1):

        if index == 1:
            value = label

        elif column in sum_columns:
            value = sum(
                (row.get(column) or 0)
                for row in rows
            )

        else:
            value = None

        cell = context.worksheet.cell(
            row=context.current_row,
            column=index,
            value=value,
        )

        if index == 1:
            style_header(cell)
        else:
            style_number(cell)

    next_row(context)

# ==========================================================
# SECTION RENDERER
# ==========================================================

# ==========================================================
# GROUPED SECTIONS (e.g. one table per contractor, per
# outsource work centre, etc.)
# ==========================================================

def render_grouped_section(
    context: RenderContext,
    rows: list[dict],
    columns: tuple[str, ...],
    metadata: dict,
):
    """
    Renders one sub-table per distinct value of
    metadata["group_by"], each with its own title row,
    its own headers, its own data rows, and (if
    show_total is set) its own total row.

    This is what makes sections like "Outsource Work
    Centres" or "Power Table - Contractor" dynamically
    grow a new table whenever a new group (a new work
    centre, a new contractor) shows up in the data --
    the generator never needs to know the group names
    in advance.
    """

    group_column = metadata.get("group_by")

    if not rows:
        write_row(context, ["No Data"])
        next_row(context)
        return

    # Preserve first-seen order of group values rather
    # than sorting, so the sheet order follows whatever
    # order the underlying query already returned.
    group_values = []

    for row in rows:

        value = row.get(group_column) or "COMPANY"

        if value not in group_values:
            group_values.append(value)

    show_group_total = metadata.get(
        "group_show_total",
        True,
    )

    for group_value in group_values:

        group_rows = [
            row
            for row in rows
            if (row.get(group_column) or "COMPANY") == group_value
        ]

        render_title(
            context,
            str(group_value),
            column_count=len(columns) if columns else 4,
        )

        render_table(
            context,
            group_rows,
            columns=columns,
        )

        if show_group_total:
            render_section_total(
                context,
                group_rows,
                columns,
                metadata,
            )

        next_row(context)


def render_section(
    connection: sqlite3.Connection,
    context: RenderContext,
    week_id: int,
    section,
):
    """
    Renders one report section.
    """

    dataset = run_report_query(
        connection,
        section.query_name,
        week_id,
    )

    columns = section.metadata.get("columns")

    if section.render_rules.show_title:
        render_title(
            context,
            section.name,
            column_count=len(columns) if columns else 4,
        )

    if section.metadata.get("group_by"):

        render_grouped_section(
            context,
            dataset,
            columns,
            section.metadata,
        )

    else:

        render_table(
            context,
            dataset,
            columns=columns,
        )

        if section.render_rules.show_total:
            render_section_total(
                context,
                dataset,
                columns,
                section.metadata,
            )

    if section.render_rules.blank_rows_after > 0:
        next_row(
            context,
            section.render_rules.blank_rows_after,
        )


# ==========================================================
# SHEET RENDERER
# ==========================================================

def render_sheet(
    connection: sqlite3.Connection,
    workbook: Workbook,
    sheet_template,
    week_id: int,
):
    """
    Renders one worksheet.
    """

    context = create_sheet(
        workbook,
        sheet_template.name,
    )

    for section in sheet_template.sections:

        if not section.enabled:

            continue

        render_section(
            connection,
            context,
            week_id,
            section,
        )

    auto_fit_columns(
        context.worksheet,
    )


# ==========================================================
# COLUMN AUTO SIZE
# ==========================================================

def auto_fit_columns(
    worksheet: Worksheet,
):
    """
    Adjust column widths.
    """

    for column in worksheet.iter_cols():
        first_cell = column[0]

        if isinstance(first_cell, MergedCell):
            continue

        column_letter = first_cell.column_letter

        max_length = 0

        for cell in column:
            if isinstance(cell, MergedCell):
                continue

            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        worksheet.column_dimensions[column_letter].width = max_length + 2


# ==========================================================
# WORKBOOK RENDERER
# ========================= =================================

def render_workbook(
    connection: sqlite3.Connection,
    workbook: Workbook,
    template: WorkbookTemplate,
    week_id: int,
):
    """
    Renders the complete workbook.
    """

    for sheet in template.sheets:

        if not sheet.enabled:

            continue

        render_sheet(
            connection,
            workbook,
            sheet,
            week_id,
        )

# ==========================================================
# WEEKLY CLOSING GENERATOR
# ==========================================================

def generate_weekly_closing(
    week_id: int,
    template: WorkbookTemplate,
):
    """
    Generates the complete weekly closing workbook.

    Returns
    -------
    Path
        Saved workbook path.
    """

    connection = connect_database()

    try:

        workbook = create_workbook()

        render_workbook(
            connection=connection,
            workbook=workbook,
            template=template,
            week_id=week_id,
        )

        file_path = save_workbook(
            workbook,
            week_id,
        )

        return file_path

    finally:

        connection.close()


# ==========================================================
# MAIN
# ==========================================================

def main():

    week_id = int(
        input(
            "Enter Week ID : "
        )
    )

    file_path = generate_weekly_closing(
        week_id=week_id,
        template=WEEKLY_CLOSING_TEMPLATE,
    )

    print()

    print("=" * 50)

    print("Weekly Closing Generated")

    print(file_path)

    print("=" * 50)


if __name__ == "__main__":

    main()