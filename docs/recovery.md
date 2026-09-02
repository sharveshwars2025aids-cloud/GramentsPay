We are building a Garments Factory Automation System for a real manufacturing company. The goal is not to build a generic ERP, but to replicate and improve the factory's existing weekly workflow while minimizing manual Excel work.

Core Principle

Always prioritize the real factory workflow over generic software patterns. If you're unsure about a business process, ask instead of assuming.

Weekly Workflow (Must Follow)
Upload Daily Workbook
Parse all sheets.
Validate the workbook.
Preview
Detect missing Employees.
Detect missing Styles.
Detect missing Operations (using Operation Aliases).
Detect validation errors.
Do not write anything to the database.
Resolve Missing Master Data
Missing Employees → Employee CRUD.
Missing Styles → Style CRUD (manual creation with required business details; never auto-create).
Missing Operations → Operation CRUD or Operation Alias CRUD.
Additional Weekly Information
After validation succeeds, collect information that is not present in the workbook:
General Expenses (Electricity, Flower, Pooja, Sweeping, Other, etc.)
Security Payments
Outsource Payments
Employee Bonuses
Employee Deductions
Commit Import
Import production records.
Save weekly expenses.
Save bonuses.
Save deductions.
Save security payments.
Save outsource payments.
Create/update the week.
Business Processing
Salary calculation.
Weekly closing generation.
Excel generation.
Dashboard & Analytics
Production reports.
Salary reports.
Expense reports.
Charts.
AI Assistant
Answer questions using the database.
Understand operation aliases (e.g., O/L, F/L, S/N).
Generate summaries and insights.
Master Data (CRUD)

These are maintained independently of the weekly workflow:

Employees
Departments
Contractors
Styles
Operations
Operation Aliases

Do not classify Expenses, Bonuses, Deductions, Security Payments, or Outsource Payments as Master Data.

Backend Architecture

Always keep business logic separated:

Router
    ↓
Service
    ↓
Core Business Logic
    ↓
Database

Avoid putting business logic inside routers.

Existing Features

Before suggesting new implementations, remember that the project already includes or partially includes:

Excel Parser
Workbook Validator
Importer
Salary Engine
Weekly Closing
Excel Generator
Operation Alias system
CRUD APIs for master data
Normalization utilities

Reuse existing modules whenever possible instead of rewriting them.

Recovery Checklist (Important)

Before suggesting a new architecture or implementation, first ask yourself:

Am I reusing the existing parser/importer?
Am I respecting the agreed weekly workflow?
Am I avoiding duplicate logic?
Am I keeping business logic out of routers?
Am I integrating with aliases, salary, and weekly closing instead of bypassing them?

If any answer is No, stop and ask for clarification before continuing.

If You're Unsure

Before making assumptions, ask:

"Would you like me to review the important project files before proceeding so I stay aligned with the existing implementation?"

Important files to review when needed
parser_v3.py
validator.py
importer.py
salary_engine.py
weekly_closing.py
excel_generator.py
database.py
Database_Design_v1.md
Workflow_v1.md
factory_rules_v1.md