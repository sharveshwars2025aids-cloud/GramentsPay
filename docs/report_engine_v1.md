# Report Engine Design v1

## Purpose

The Report Engine is responsible for generating the factory's weekly closing workbook from the database.

Instead of manually copying data into Excel every week, the engine recreates the workbook using production records, salary calculations, expenses, deductions, bonuses and employee information stored in the database.

The engine must produce an Excel workbook that matches the factory's existing format.

---

# Overall Architecture

```
Importer
        ↓
Database
        ↓
Report Queries
        ↓
Template Mapper
        ↓
Excel Generator
        ↓
Weekly Closing Workbook
```

---

# Responsibilities

## Importer

Reads the daily workbook.

- Parses Excel
- Validates data
- Imports into database

The importer never generates reports.

---

## Report Queries

Collects all information required for reports.

Examples:

- Shift workers
- Piece rate workers
- Contractors
- Expenses
- Salary summary
- Bank transfer
- Production summary

This module contains SQL only.

---

## Template Mapper

Describes the structure of every report.

It never reads Excel.

It never executes SQL.

It simply describes

- workbook
- sheets
- sections
- layout

---

## Excel Generator

Creates the workbook.

The generator

- loads the template
- requests data
- fills sections
- applies formatting
- saves workbook

The generator never contains business logic.

---

# Workbook Structure

A workbook contains multiple sheets.

Each sheet contains multiple sections.

Each section has its own layout and query.

```
Workbook

├── Sheet
│      ├── Section
│      ├── Section
│      └── Section
│
├── Sheet
│      ├── Section
│      ├── Section
│      └── Section
│
└── ...
```

---

# Section Types

The report engine supports multiple section types.

Examples

- Company Workers
- Contractor Workers
- Shift Workers
- Piece Rate Workers
- Salary Summary
- Production Summary
- Expense Table
- Bank Transfer
- Outsource Centre
- Security Payment

---

# Dynamic Sections

Some sections are generated dynamically.

Examples

- Contractor tables
- Outsource centres
- Future departments

The generator must never hardcode contractor names.

Instead it creates one section for every contractor found in the database.

Example

Today

Power Table

- Tamil
- Kapil

Tomorrow

Power Table

- Tamil
- Kapil
- Vijay

No code changes required.

---

# Configuration

Styles are configured before importing.

Operations are configurable.

Departments are configurable.

Contractors are configurable.

Employees are configurable.

The importer consumes these configurations.

It does not create them automatically.

---

# Future Expansion

The report engine must support

- new departments
- new contractors
- new templates
- additional sheets

without redesigning the architecture.

Only configuration should change.

---

# Design Principles

The report engine follows these principles.

1. No hardcoded contractor names.

2. No hardcoded department names.

3. No business logic inside Excel generation.

4. SQL belongs inside Report Queries.

5. Layout belongs inside Template Mapper.

6. Excel Generator only renders.

7. Reports must reproduce the factory workbook.

8. New factories should require configuration instead of code changes.

---

# Factory Adaptability

The system is designed to support multiple garment factories.

Factory-specific differences such as:

- Weekly closing templates
- Department structure
- Contractor list
- Employee list
- Report layouts

should be handled through configuration whenever possible instead of modifying the application code.

The reporting engine should remain generic while allowing each factory to use its own workbook template.

# End of Version 1