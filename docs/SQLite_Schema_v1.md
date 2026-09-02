# SQLite Schema v1

## Purpose

This document defines the SQLite database schema for the Garments Automation System.

The schema is based on:

- Factory_Rules_v1.md
- Database_Design_v1.md
- Workflow_v1.md

The schema should support:

- Weekly Closing Generation
- Payroll Calculation
- Production Tracking
- Historical Search
- Reports
- Future AI Features

---

# Table: departments

```sql
CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'active'
);
```

Purpose:

Stores factory departments.

Examples:

- Singer
- Power Table
- Checking
- Ironing

---

# Table: contractors

```sql
CREATE TABLE contractors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    commission_rate REAL NOT NULL,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Purpose:

Stores contractor details.

---

# Table: employees

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code TEXT,
    name TEXT NOT NULL,
    pay_type TEXT NOT NULL,
    department_id INTEGER,
    contractor_id INTEGER,
    shift_rate REAL,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(department_id) REFERENCES departments(id),
    FOREIGN KEY(contractor_id) REFERENCES contractors(id)
);
```

Purpose:

Stores worker information.

Pay Types:

- piece_rate
- shift

---

# Table: operations

```sql
CREATE TABLE operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Purpose:

Stores operations.

Examples:

- O/L
- F/L
- PATTI F/L
- CHECKING

---

# Table: styles

```sql
CREATE TABLE styles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    style_no TEXT NOT NULL UNIQUE,
    style_name TEXT,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Purpose:

Stores style information.

---

# Table: style_operation_rates

```sql
CREATE TABLE style_operation_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    style_id INTEGER NOT NULL,
    operation_id INTEGER NOT NULL,
    rate REAL NOT NULL,
    effective_from DATE,
    active INTEGER DEFAULT 1,

    FOREIGN KEY(style_id) REFERENCES styles(id),
    FOREIGN KEY(operation_id) REFERENCES operations(id)
);
```

Purpose:

Stores rates for style-operation combinations.

---

# Table: weeks

```sql
CREATE TABLE weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    closing_generated INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Purpose:

Represents one weekly closing period.

---

# Table: production_records

```sql
CREATE TABLE production_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    week_id INTEGER,
    work_date DATE NOT NULL,

    employee_id INTEGER NOT NULL,
    style_id INTEGER NOT NULL,
    operation_id INTEGER,

    type TEXT,
    color TEXT,

    total_qty REAL DEFAULT 0,
    rate REAL DEFAULT 0,
    total_amount REAL DEFAULT 0,

    source_sheet TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(week_id) REFERENCES weeks(id),
    FOREIGN KEY(employee_id) REFERENCES employees(id),
    FOREIGN KEY(style_id) REFERENCES styles(id),
    FOREIGN KEY(operation_id) REFERENCES operations(id)

    workbook_name TEXT,
    source_sheet TEXT,
    source_row INTEGER
);
```

Purpose:

Stores production records imported from Excel.

---

# Table: production_sizes

```sql
CREATE TABLE production_sizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    production_record_id INTEGER NOT NULL,

    size_name TEXT NOT NULL,
    qty REAL DEFAULT 0,

    FOREIGN KEY(production_record_id)
    REFERENCES production_records(id)
);
```

Purpose:

Stores size-wise quantities.

Example:

- 0/3
- 3/6
- 6/9
- 9/12

---

# Table: shift_records

```sql
CREATE TABLE shift_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    week_id INTEGER,
    work_date DATE NOT NULL,

    employee_id INTEGER NOT NULL,

    shifts REAL DEFAULT 0,
    daily_salary REAL DEFAULT 0,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(week_id) REFERENCES weeks(id),
    FOREIGN KEY(employee_id) REFERENCES employees(id)
);
```

Purpose:

Stores shift-worker attendance.

---

# Table: deductions

```sql
CREATE TABLE deductions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    week_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,

    deduction_type TEXT NOT NULL,
    amount REAL NOT NULL,

    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(week_id) REFERENCES weeks(id),
    FOREIGN KEY(employee_id) REFERENCES employees(id)
);
```

Purpose:

Stores salary deductions.

Examples:

- Advance
- Loan
- PF
- ESI

---

# Table: bonuses

```sql
CREATE TABLE bonuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    week_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,

    bonus_type TEXT NOT NULL,
    amount REAL NOT NULL,

    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(week_id) REFERENCES weeks(id),
    FOREIGN KEY(employee_id) REFERENCES employees(id)
);
```

Purpose:

Stores employee bonuses.

---

# Table: expenses

```sql
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    week_id INTEGER NOT NULL,

    category TEXT NOT NULL,
    amount REAL NOT NULL,

    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(week_id) REFERENCES weeks(id)
);
```

Purpose:

Stores weekly expenses.

---

# Table: weekly_closings

```sql
CREATE TABLE weekly_closings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    week_id INTEGER NOT NULL,

    generated_by TEXT,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    file_path TEXT,

    FOREIGN KEY(week_id) REFERENCES weeks(id)
);
```

Purpose:

Stores generated weekly closing reports.

---

# Recommended Indexes

```sql
CREATE INDEX idx_employee_name
ON employees(name);

CREATE INDEX idx_style_no
ON styles(style_no);

CREATE INDEX idx_work_date
ON production_records(work_date);

CREATE INDEX idx_week_dates
ON weeks(week_start, week_end);

CREATE INDEX idx_shift_employee
ON shift_records(employee_id);

CREATE INDEX idx_production_employee
ON production_records(employee_id);
```

Purpose:

Improve search performance.

---

# Supported Queries

The schema should support:

- Ravi salary this week
- Ravi work on 07/07/2026
- Week 25 closing
- Production by style
- Monthly production
- Employee salary history
- Contractor earnings
- Expense analysis
- Size-wise production reports

---

# Future Expansion

This schema should support:

- Telegram Bot
- Employee Notifications
- Charts
- Analytics
- AI Search
- Multi-Factory Support

without major redesign.