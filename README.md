# GramentsPay

> Garment Manufacturing Automation & Payroll Management System

GramentsPay is a backend-focused automation system designed to simplify production tracking, employee payroll, weekly salary calculation, and weekly closing operations for garment manufacturing businesses.

The system converts daily production and shift data into structured database records and automatically generates weekly salary calculations and factory-style weekly closing reports.

---

## 🎯 Problem

Garment factories often depend heavily on Excel sheets for:

- Daily production tracking
- Piece-rate calculations
- Shift worker salary calculations
- Contractor payments
- Employee deductions and bonuses
- Factory expenses
- Outsource payments
- Security payments
- Weekly salary closing

Manually consolidating these records is time-consuming and can lead to calculation errors, duplicate entries, and difficulties in retrieving historical information.

**GramentsPay aims to automate this workflow while preserving the factory's existing working structure.**

---

## 💡 Solution

GramentsPay provides two primary ways to enter production data:

```text
              ┌──────────────────┐
              │   Excel Upload   │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │                  │
              │     DATABASE     │
              │                  │
              └────────┬─────────┘
                       ▲
                       │
              ┌────────┴─────────┐
              │                  │
              │  Website / API   │
              │                  │
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Salary Engine   │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Weekly Closing   │
              │      Excel       │
              └──────────────────┘
```

Both Excel and website inputs are converted into the same database structure, allowing the rest of the system to work from a single source of truth.

---

## ✨ Key Features

### 🏭 Production Management

- Daily production record management
- Employee-wise production tracking
- Style and operation tracking
- Quantity, rate and amount calculation
- Size-wise production information
- Support for different production operations
- Historical production records

### 👨‍💼 Employee Management

- Employee codes
- Employee details
- Department assignment
- Piece-rate workers
- Shift workers
- Worker types
- Contractor relationships
- Configurable employee master data

### 💰 Payroll Automation

#### Piece-rate workers

```text
Quantity × Rate = Salary
```

#### Shift workers

```text
Shifts × Shift Rate = Salary
```

#### Final salary

```text
Gross Salary
+ Bonus
- Deduction
= Net Salary
```

Historical production records retain their recorded rates so that changes to current employee rates do not alter previous calculations.

---

## 🤝 Contractor Management

The system supports shift workers associated with contractors.

Contractor commission is maintained separately from the worker's salary.

This allows the system to distinguish between:

```text
Worker Salary
+
Contractor Commission
```

rather than treating them as the same payment.

---

## 📊 Weekly Closing

The system generates a weekly closing workbook based on the factory's existing reporting structure.

The closing process can include:

- Employee salary
- Piece-rate production
- Shift salary
- Contractor information
- Bonuses
- Deductions
- Factory expenses
- Outsource payments
- Security payments
- Bank transfer information
- Production details

The generated workbook follows the existing factory template instead of replacing it with a generic report.

---

## 📥 Excel Import

Existing factory Excel workbooks can be imported into the system.

The importer supports dynamic identification of production and shift tables using semantic headers rather than relying only on fixed table positions.

Business identifiers such as:

```text
Employee Code
Style Number
Operation Name
```

are resolved to their corresponding internal database records.

This allows identifiers such as:

```text
E016
ST-101
OP-450
```

to be handled without changing the internal relational database structure.

Both Excel input and website input ultimately use the same database model.

---

## 🗄️ Database

The system uses a relational database to maintain structured factory data.

Major entities include:

- Departments
- Employees
- Contractors
- Styles
- Operations
- Operation Aliases
- Weeks
- Production Records
- Production Sizes
- Shift Records
- Deductions
- Bonuses
- Expenses
- Outsource Payments
- Security Payments
- Bank Transfers
- Weekly Closings
- Attendance Records

Internal database IDs remain integer primary/foreign keys while business-facing identifiers remain human-readable strings.

---

## 🔐 Attendance & Biometric Verification

Attendance/biometric information is treated as a verification mechanism rather than the source for salary calculation.

The system can compare attendance information against recorded work/shift information and identify mismatches for review.

This helps identify cases such as:

- Absent employee with recorded shift
- Present employee without recorded shift
- Missing attendance
- Shift mismatch

Attendance exceptions can be reviewed without altering the original biometric source.

---

## 🧩 System Architecture

```text
                         ┌──────────────────┐
                         │  Excel Workbook  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Excel Importer  │
                         └────────┬─────────┘
                                  │
                                  │
┌──────────────────┐              ▼
│  Website / API   │──────────► DATABASE
└──────────────────┘              │
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
              Production     Salary Engine   Attendance
                Records           │          Verification
                    │              │
                    └──────┬───────┘
                           ▼
                  Weekly Closing
                     Generator
                           │
                           ▼
                  Weekly Closing Excel
```

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Core backend |
| FastAPI | REST API |
| SQLite | Relational database |
| Pandas | Excel/data processing |
| OpenPyXL | Excel reading and generation |
| Pydantic | API validation |
| Git & GitHub | Version control |

---

## 📁 Project Structure

```text
garmesnts-automation/
│
├── docs/
│   └── Project documentation
│
├── samples/
│   └── Sample input files
│
├── src/
│   ├── database/
│   ├── ...
│   └── ...
│
├── tests/
│   └── Automated and integration tests
│
├── .gitignore
├── README.md
└── requirements.txt
```

> The exact modules may evolve as development continues.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/sharveshwars2025aids-cloud/GramentsPay.git
```

```bash
cd GramentsPay
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

Git Bash:

```bash
source venv/Scripts/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the database

Run the project's database initialization and seed process as documented in the project files.

### 5. Start the FastAPI application

The exact command depends on the current application entry point.

A typical development command is:

```bash
uvicorn <module>:app --reload
```

---

## 🧪 Testing

Run the project's test suite with:

```bash
pytest
```

The project includes testing for important workflows such as:

- Production records
- Shift records
- Salary calculation
- Deductions
- Bonuses
- Contractor calculations
- Excel import
- Weekly closing generation
- Attendance verification

---

## 📌 Development Status

### Completed

- [x] Database foundation
- [x] API/input contract
- [x] Week management
- [x] Website/API production input
- [x] Excel import pipeline
- [x] Salary calculation engine
- [x] Weekly closing generation
- [x] Piece-rate salary calculation
- [x] Shift salary calculation
- [x] Contractor commission handling
- [x] Deductions and bonuses
- [x] Factory expense handling
- [x] Attendance verification foundation

### In Progress / Planned

- [ ] Complete dashboard experience
- [ ] Advanced reports and analytics
- [ ] Telegram-based interaction
- [ ] AI-assisted factory queries
- [ ] Employee notifications
- [ ] Production and salary visualizations
- [ ] Further production-scale testing
- [ ] Deployment and production hardening

---

## 🔮 Future Vision

GramentsPay is intended to evolve from a payroll and production automation system into an intelligent garment factory management assistant.

The long-term workflow is:

```text
Daily Factory Data
       ↓
Automatic Processing
       ↓
Database
       ↓
Payroll + Production Analysis
       ↓
Weekly Closing
       ↓
Reports & Notifications
       ↓
AI Factory Assistant
```

The long-term goal is to allow authorized users to ask questions such as:

```text
"What did Ravi produce on 07/07/2026?"

"How much salary does E016 have this week?"

"What was the total factory expense?"

"How much was paid to contractors?"

"Show this week's production."
```

and receive answers directly from the factory's stored data.

---

## 🔒 Data & Security

Sensitive factory information should not be committed to the repository.

The project `.gitignore` excludes:

- Database files
- Environment files
- API keys and secrets
- Generated Excel files
- Virtual environments
- IDE-specific files

Production credentials and private factory data should be supplied through environment variables or secure deployment configuration.

---

## 🗺️ Development Roadmap

```text
Phase 1   → Database Foundation             ✅
Phase 2   → API / Input Contract            ✅
Phase 3   → Week Management                 ✅
Phase 4   → Website / Dashboard             ✅
Phase 5   → Excel Import Pipeline           ✅
Phase 6   → Salary Engine                   ✅
Phase 7   → Weekly Closing Generator        ✅
Phase 8   → Manual Weekend Inputs           🔜
Phase 9   → Reports & Search                🔜
Phase 10  → Attendance / Biometric          🔜
Phase 11  → Telegram + AI Agent             🔜
Phase 12  → Notifications & Integration     🔜
```

---

## 👨‍💻 Project

### GramentsPay

**Garment Manufacturing Automation & Payroll Management System**

Built with:

**Python • FastAPI • SQLite • Pandas • OpenPyXL**

---

## 📄 License

This project is currently intended for development and project evaluation purposes.


git add README.md
git commit -m "Add project README"
git push
