"""
template_mapper.py

Defines the structure of the weekly closing workbook.

This module DOES NOT

- execute SQL
- read Excel
- write Excel
- know about openpyxl

It only describes how a workbook is organised.

Importer
        ↓
Database
        ↓
Report Queries
        ↓
Template Mapper   <-- THIS MODULE
        ↓
Excel Generator
        ↓
Weekly Closing Workbook
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple


# ==========================================================
# SECTION TYPES
# ==========================================================

class SectionType(Enum):
    """
    Represents the logical type of a report section.
    """

    COMPANY = "company"
    CONTRACTOR = "contractor"
    SHIFT = "shift"
    PIECE_RATE = "piece_rate"
    EXPENSE = "expense"
    OUTSOURCE = "outsource"
    SALARY = "salary"
    BANK_TRANSFER = "bank_transfer"
    SUMMARY = "summary"


# ==========================================================
# QUERY NAMES
# ==========================================================

class QueryName(Enum):
    """
    Every report section receives its data
    from exactly one query.

    report_queries.py will implement these.
    """

    POWER_TABLE_CONTRACTOR = "power_table_contractor"

    POWER_TABLE_COMPANY = "power_table_company"

    HELPERS_CONTRACTOR = "helpers_contractor"

    HELPERS_COMPANY = "helpers_company"

    POWER_PC_RATE = "power_pc_rate"

    SINGER_PC_RATE = "singer_pc_rate"

    CHECKING_SHIFT = "checking_shift"

    CHECKING_PC_RATE = "checking_pc_rate"

    IRONING_PC_RATE = "ironing_pc_rate"

    SALARY = "salary"

    SALARY_DEPARTMENT_SUMMARY = "salary_department_summary"

    SALARY_OPERATIONS = "salary_operations"

    BANK_TRANSFER = "bank_transfer"

    PT_SHIFT = "pt_shift"

    EXPENSES = "expenses"

    OUTSOURCE = "outsource"

    SECURITY = "security"

    SUMMARY = "summary"


# ==========================================================
# OVERFLOW STRATEGY
# ==========================================================

class OverflowStrategy(Enum):
    """
    Defines what happens when a section
    becomes larger than expected.
    """

    EXPAND = "expand"

    NEW_SHEET = "new_sheet"

    ERROR = "error"


# ==========================================================
# RENDER RULES
# ==========================================================

@dataclass(frozen=True)
class RenderRules:
    """
    Describes HOW a section should appear.

    This class contains no coordinates.
    """

    show_title: bool = True

    show_header: bool = True

    show_total: bool = False

    blank_rows_before: int = 1

    blank_rows_after: int = 1

    overflow_strategy: OverflowStrategy = OverflowStrategy.EXPAND


# ==========================================================
# SECTION TEMPLATE
# ==========================================================

@dataclass(frozen=True)
class SectionTemplate:
    """
    Represents one logical report section.

    Examples

    - Power Table
    - Singer PC Rate
    - Security Payment
    - Salary Summary
    """

    name: str

    section_type: SectionType

    query_name: QueryName

    render_rules: RenderRules = field(default_factory=RenderRules)

    metadata: dict[str, object] = field(default_factory=dict)


    enabled: bool = True


# ==========================================================
# SHEET TEMPLATE
# ==========================================================

@dataclass(frozen=True)
class SheetTemplate:
    """
    Represents one worksheet.

    A worksheet may contain multiple sections.
    """

    name: str

    repeatable: bool = False

    enabled: bool = True

    sections: Tuple[SectionTemplate, ...] = field(
        default_factory=tuple
    )


# ==========================================================
# WORKBOOK TEMPLATE
# ==========================================================

@dataclass(frozen=True)
class WorkbookTemplate:
    """
    Represents the complete workbook.
    """

    name: str

    sheets: Tuple[SheetTemplate, ...]


# ==========================================================
# VALIDATION HELPERS
# ==========================================================

def validate_sheet(sheet: SheetTemplate) -> None:
    """
    Validates a sheet definition.
    """

    if not sheet.name.strip():
        raise ValueError("Sheet name cannot be empty.")

    if len(sheet.sections) == 0:
        raise ValueError(
            f"'{sheet.name}' contains no sections."
        )


def validate_workbook(workbook: WorkbookTemplate) -> None:
    """
    Validates the workbook definition.
    """

    if not workbook.name.strip():
        raise ValueError("Workbook name cannot be empty.")

    if len(workbook.sheets) == 0:
        raise ValueError(
            "Workbook contains no sheets."
        )

    sheet_names = set()

    for sheet in workbook.sheets:

        if sheet.name in sheet_names:
            raise ValueError(
                f"Duplicate sheet '{sheet.name}'."
            )

        sheet_names.add(sheet.name)

        validate_sheet(sheet)


# ==========================================================
# FACTORY FUNCTIONS
# ==========================================================

def create_section(
    *,
    name: str,
    section_type: SectionType,
    query_name: QueryName,
    metadata: dict[str, object] | None = None,
    enabled: bool = True,
    render_rules: RenderRules | None = None,
) -> SectionTemplate:
    """
    Convenience factory for creating sections.
    """

    return SectionTemplate(
        name=name,
        section_type=section_type,
        query_name=query_name,
        metadata=metadata or {},
        enabled=enabled,
        render_rules=render_rules or RenderRules(),
    )


def create_sheet(
    *,
    name: str,
    sections: Tuple[SectionTemplate, ...],
    repeatable: bool = False,
    enabled: bool = True,
) -> SheetTemplate:
    """
    Convenience factory for creating sheets.
    """

    return SheetTemplate(
        name=name,
        repeatable=repeatable,
        enabled=enabled,
        sections=sections,
    )
# ==========================================================
# SHEET 1
# TALRS - HELPERS
# ==========================================================

# ==========================================================
# SHEET 1
# TALRS - HELPERS
# ==========================================================

TALRS_HELPERS = create_sheet(
    name="TALRS-HELPERS",
    sections=(
        create_section(
            name="Power Table - Contractor",
            section_type=SectionType.CONTRACTOR,
            query_name=QueryName.POWER_TABLE_CONTRACTOR,
            metadata={
                "group_by": "contractor",
                "group_show_total": False,
                "columns": (
                    "employee_name",
                    "operation",
                    "item",
                    "total_shifts",
                    "shift_rate",
                    "total_salary",
                ),
            },
        ),

        create_section(
            name="Power Table - Company",
            section_type=SectionType.COMPANY,
            query_name=QueryName.POWER_TABLE_COMPANY,
            metadata={
                "columns": (
                    "employee_name",
                    "operation",
                    "item",
                    "total_shifts",
                    "shift_rate",
                    "total_salary",
                ),
            },
        ),

        create_section(
            name="Helpers - Contractor",
            section_type=SectionType.CONTRACTOR,
            query_name=QueryName.HELPERS_CONTRACTOR,
            metadata={
                "group_by": "contractor",
                "group_show_total": False,
                "columns": (
                    "employee_name",
                    "operation",
                    "item",
                    "total_shifts",
                    "shift_rate",
                    "total_salary",
                ),
            },
        ),

        create_section(
            name="Helpers - Company",
            section_type=SectionType.COMPANY,
            query_name=QueryName.HELPERS_COMPANY,
            metadata={
                "columns": (
                    "employee_name",
                    "operation",
                    "item",
                    "total_shifts",
                    "shift_rate",
                    "total_salary",
                ),
            },
        ),
    ),
)


# ==========================================================
# SHEET 2
# PC RATE - OTHERS
# ==========================================================

PC_RATE_OTHERS = create_sheet(

    name="PC RATE-OTHERS",

    sections=(

        create_section(
            name="Power Table PC Rate",
            section_type=SectionType.PIECE_RATE,
            query_name=QueryName.POWER_PC_RATE,
            metadata={
                "department": "POWER",
                "payment": "PC_RATE",
                "columns": (
                "name",
                "item",
                "salary",
            ),
        },
    ),

        create_section(
            name="Singer PC Rate",
            section_type=SectionType.PIECE_RATE,
            query_name=QueryName.SINGER_PC_RATE,
            metadata={
                "department": "SINGER",
                "payment": "PC_RATE",
                "columns": (
                    "name",
                    "item",
                    "salary",
                ),
            },
        ),

        create_section(
            name="Checking Shift",
            section_type=SectionType.SHIFT,
            query_name=QueryName.CHECKING_SHIFT,
            metadata={
                "department": "CHECKING",
                "payment": "SHIFT",
                "columns": (
                    "name",
                    "shifts",
                    "salary",
                ),
            },
        ),

        create_section(
            name="Checking PC Rate",
            section_type=SectionType.PIECE_RATE,
            query_name=QueryName.CHECKING_PC_RATE,
            metadata={
                "department": "CHECKING",
                "payment": "PC_RATE",
                "columns": (
                    "name",
                    "item",
                    "salary",
                ),
            },
        ),

        create_section(
            name="Ironing PC Rate",
            section_type=SectionType.PIECE_RATE,
            query_name=QueryName.IRONING_PC_RATE,
            metadata={
                "department": "IRONING",
                "payment": "PC_RATE",
                "columns": (
                    "name",
                    "item",
                    "salary",
                ),
            },
        ),

        create_section(
            name="General Expenses",
            section_type=SectionType.EXPENSE,
            query_name=QueryName.EXPENSES,
            metadata={
                "columns": (
                    "expense_name",
                    "amount",
                ),
                "items": [
                    "Flower",
                    "Cleaner",
                    "Sweeper",
                    "Oil",
                ],
            },
        ),

        create_section(
            name="Outsource Work Centres",
            section_type=SectionType.OUTSOURCE,
            query_name=QueryName.OUTSOURCE,
            render_rules=RenderRules(
                show_title=False,
            ),
            metadata={
                "group_by": "centre_name",
                "total_label": "TOTAL",
                "total_sum_columns": (
                    "qty",
                    "salary",
                ),
                "columns": (
                    "style",
                    "item",
                    "qty",
                    "rate",
                    "salary",
                ),
            },
        ),

        create_section(
            name="Security Payment",
            section_type=SectionType.SUMMARY,
            query_name=QueryName.SECURITY,
            metadata={
                "columns": (
                    "name",
                    "days",
                    "salary",
                ),
            },
        ),

    ),
)

# ==========================================================
# SHEET 3
# SALARY
# ==========================================================

SALARY = create_sheet(

    name="SALARY",

    sections=(

        create_section(
            name="Salary Summary",
            section_type=SectionType.SALARY,
            query_name=QueryName.SALARY_DEPARTMENT_SUMMARY,
            metadata={
                "columns": (
                    "s_no",
                    "department",
                    "salary",
                ),
            },
        ),

        create_section(
            name="Production Details",
            section_type=SectionType.SALARY,
            query_name=QueryName.SALARY_OPERATIONS,
            render_rules=RenderRules(
                show_total=True,
            ),
            metadata={
                "columns": (
                    "style",
                    "qty",
                    "rate",
                    "amt",
                ),
                "total_label": "TTL PRODUCTION QTY",
                "total_sum_columns": (
                    "qty",
                    "amt",
                ),
            },
        ),

    ),
)


# ==========================================================
# SHEET 4
# BANK TRANSFER
# ==========================================================

BANK_TRANSFER = create_sheet(

    name="BANK-TRANSFER",

    sections=(

        create_section(
            name="Bank Transfer",
            section_type=SectionType.BANK_TRANSFER,
            query_name=QueryName.BANK_TRANSFER,
            metadata={
                "columns": (
                    "s_no",
                    "name",
                    "department",
                    "amount",
                ),
            },
        ),

    ),
)


# ==========================================================
# SHEET 5
# PT SHIFT
# ==========================================================

PT_SHIFT = create_sheet(

    name="PT-SHIFT",

    repeatable=True,

    sections=(

        create_section(
            name="PT Shift Workers",
            section_type=SectionType.SHIFT,
            query_name=QueryName.PT_SHIFT,
            metadata={
                "group_by": "contractor",
                "include_company": True,
                "columns": (
                    "s_no",
                    "name",
                    "operation",
                    "item",
                    "shift",
                    "rate_per_shift",
                    "salary",
                ),
                "repeatable": True,
                "continue_when_full": True,
            },
        ),
    )
)


# ==========================================================
# WEEKLY CLOSING WORKBOOK
# ==========================================================

WEEKLY_CLOSING_TEMPLATE = WorkbookTemplate(

    name="Weekly Closing",

    sheets=(

        TALRS_HELPERS,

        PC_RATE_OTHERS,

        SALARY,

        BANK_TRANSFER,

        PT_SHIFT,

    ),
)


# ==========================================================
# VALIDATE TEMPLATE
# ==========================================================

validate_workbook(WEEKLY_CLOSING_TEMPLATE)


# ==========================================================
# PUBLIC EXPORTS
# ==========================================================

__all__ = (

    "SectionType",

    "QueryName",

    "OverflowStrategy",

    "RenderRules",

    "SectionTemplate",

    "SheetTemplate",

    "WorkbookTemplate",

    "create_section",

    "create_sheet",

    "validate_sheet",

    "validate_workbook",

    "TALRS_HELPERS",

    "PC_RATE_OTHERS",

    "SALARY",

    "BANK_TRANSFER",

    "PT_SHIFT",

    "WEEKLY_CLOSING_TEMPLATE",

)