# Database Design v1

## Purpose

The database must support:

- Weekly Closing Generation
- Salary Calculation
- Production Tracking
- Employee History
- Expense Tracking
- Contractor Tracking
- Employee Notifications
- Owner Reports
- Future AI Search Queries

The database should store facts and historical records so that reports can always be regenerated.

---

# Design Principles

## Internal IDs

Every table will use an internal database ID.

Example:

Employee:

- id = 1
- name = Ravi

The factory may or may not use employee codes.

The system should not depend on employee codes.

Employee codes can be added later without redesigning the database.

---

## Dynamic Configuration

The following should be user-manageable:

- Departments
- Operations
- Styles
- Expense Categories
- Deduction Types

Adding new values should not require code changes.

---

# Table: employees

Stores all workers.

## Columns

- id (PK)
- employee_code (optional)
- name
- pay_type
- department_id
- contractor_id (nullable)
- shift_rate (nullable)
- status
- created_at

## Notes

Pay Types:

- piece_rate
- shift

Piece-rate workers normally do not belong to contractors.

Shift workers may belong to contractors.

---

# Table: departments

Stores worker departments.

## Columns

- id (PK)
- name
- status

## Examples

- Singer
- Power Table
- Checking
- Ironing
- Packing

---

# Table: contractors

Stores contractor information.

## Columns

- id (PK)
- name
- commission_rate
- status
- created_at

## Notes

Contractor Salary:

Contractor Salary =
Commission Rate × Total Worker Shifts

---

# Table: operations

Stores production operations.

## Columns

- id (PK)
- name
- status
- created_at

## Examples

- O/L
- F/L
- PATTI F/L
- NECK FOLG
- CHECKING
- IRONING

Operations are dynamic.

---

# Table: styles

Stores style information.

## Columns

- id (PK)
- style_no
- style_name
- status
- created_at

## Examples

- PE097PJFS26
- PEV010S26

---

# Table: style_operation_rates

Stores rates for every style and operation combination.

## Columns

- id (PK)
- style_id
- operation_id
- rate
- effective_from
- active

## Example

Style: PE097

Operation: PATTI F/L

Rate: ₹3

---

# Table: weeks

Represents one weekly closing period.

## Columns

- id (PK)
- week_start
- week_end
- closing_generated
- created_at

## Example

Week Start:

20-06-2026

Week End:

26-06-2026

---

# Table: production_records

Stores production entries imported from workbook.

## Columns

- id (PK)
- week_id
- work_date
- employee_id
- style_id
- operation_id
- type
- color
- total_qty
- rate
- total_amount
- source_sheet
- created_at

## Notes

One production record may contain multiple sizes.

Size details are stored separately.

---

# Table: production_sizes

Stores size-wise quantity breakdown.

## Columns

- id (PK)
- production_record_id
- size_name
- qty

## Example

Production Record: 101

0/3 → 250

3/6 → 70

6/9 → 185

9/12 → 22

12/18 → 168

---

# Table: shift_records

Stores shift-worker attendance and salary information.

## Columns

- id (PK)
- week_id
- work_date
- employee_id
- shifts
- daily_salary
- created_at

## Examples

1 Shift

0.5 Shift

1.5 Shift

## Notes

Source of shift data is still to be confirmed.

Database should remain flexible.

---

# Table: deductions

Stores salary deductions.

## Columns

- id (PK)
- week_id
- employee_id
- deduction_type
- amount
- notes
- created_at

## Examples

- Advance
- Loan
- PF
- ESI

Current factory mainly uses Advance.

---

# Table: bonuses

Stores employee bonuses.

## Columns

- id (PK)
- week_id
- employee_id
- bonus_type
- amount
- notes
- created_at

## Examples

- Festival Bonus
- Special Bonus

---

# Table: expenses

Stores weekly expenses.

## Columns

- id (PK)
- week_id
- category
- amount
- notes
- created_at

## Examples

- Electricity
- Sweeping
- Cleaning
- Flowers
- Pooja
- Transport

Expense categories are dynamic.

---

# Table: weekly_closings

Stores generated closing reports.

## Columns

- id (PK)
- week_id
- generated_by
- generated_at
- file_path

## Purpose

Stores references to generated weekly closing files.

---

# Relationships

Department
|
Employees
|
+--------------------+
|                    |
Production Records   Shift Records
|
Style
|
Style Operation Rates
|
Operation

Weeks
|
+--- Expenses
|
+--- Deductions
|
+--- Bonuses
|
+--- Weekly Closings

Contractors
|
Employees

Production Records
|
Production Sizes

---

# Queries Supported

The database should support:

- What is Ravi's salary this week?
- What work did Ravi do on 07/07/2026?
- Show Week 25 Closing.
- Show all work done for Style PE097.
- Show production for June.
- Show total contractor earnings.
- Show employee salary history.
- Show total advances for Ravi.
- Show yearly electricity expenses.
- Show size-wise production reports.

---

# Future Features

This design should support:

- Telegram Bot
- Employee Salary Notifications
- Owner Dashboard
- Production Charts
- Expense Charts
- Search Queries
- AI Assistant
- Multi-Factory Support (Future)

without redesigning the database.