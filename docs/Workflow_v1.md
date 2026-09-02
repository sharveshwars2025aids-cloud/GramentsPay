# Workflow v1

## Purpose

This document defines how users interact with the system and how the system processes weekly production and salary data.

The workflow is designed to:

- Minimize manual work
- Preserve existing factory processes
- Generate weekly closing reports
- Store historical data
- Enable future AI search and reporting

---

# Actors

## Official

Responsible for:

- Uploading workbook
- Entering deductions
- Entering bonuses
- Entering expenses
- Generating weekly closing

---

## Employee

Responsible for:

- Viewing salary summary
- Viewing work summary

---

## Owner

Responsible for:

- Viewing reports
- Viewing production summaries
- Asking business questions

---

# Weekly Workflow

## Step 1: Reminder Notification

At the configured closing time:

System sends notification to officials.

Example:

"Weekly closing is pending. Upload workbook to begin."

---

## Step 2: Upload Workbook

Official uploads weekly workbook.

Workbook contains:

- Day 1 Sheet
- Day 2 Sheet
- Day 3 Sheet
- Day 4 Sheet
- Day 5 Sheet
- Day 6 Sheet
- Day 7 Sheet

---

## Step 3: Workbook Validation

System checks:

- Workbook format
- Required columns
- Missing values
- Duplicate records
- Invalid rates

If issues exist:

System reports errors.

Example:

"Sheet Day 3 contains missing employee name."

Weekly closing cannot continue until validation passes.

---

## Step 4: Data Extraction

System extracts:

- Employees
- Styles
- Operations
- Sizes
- Colors
- Quantities
- Rates
- Amounts

Data is converted into structured records.

---

## Step 5: Employee Matching

System checks:

- Existing employee
- New employee

If employee does not exist:

System creates employee automatically.

Example:

New employee found:

"Karthik"

Employee created successfully.

---

## Step 6: Style Matching

System checks:

- Existing style
- New style

If style does not exist:

System creates style automatically.

---

## Step 7: Operation Matching

System checks:

- Existing operation
- New operation

If operation does not exist:

System creates operation automatically.

---

## Step 8: Save Production Records

System stores:

- Production Records
- Production Sizes

into database.

---

## Step 9: Ask For Deductions

System asks:

"Any deductions for this week?"

Example:

Ravi 1000 Advance

Kumar 500 Advance

DONE

System stores deduction records.

---

## Step 10: Ask For Bonuses

System asks:

"Any bonuses for this week?"

Example:

Ravi 500 Festival Bonus

DONE

System stores bonus records.

### Bulk Bonus Support

The system should support bulk bonus entries.

Examples:

Add bonus 500 to all employees

Add bonus 500 to all Singer workers

Add bonus 300 to all workers under Kapil

Before applying a bulk bonus, the system must display a summary and request confirmation.

---

## Step 11: Ask For Expenses

System asks:

"Any expenses for this week?"

Example:

Electricity 5000

Flowers 200

Cleaning 1000

DONE

System stores expense records.

---

## Step 12: Calculate Salaries

### Piece Rate Workers

Amount = Quantity × Rate

Weekly Salary = Sum of Daily Amounts

Net Salary = Gross Salary + Bonus - Deduction

---

### Shift Workers

Weekly Salary = Total Shifts × Shift Rate

Net Salary = Gross Salary + Bonus - Deduction

---

### Contractors

Contractor Salary =
Commission Rate × Total Worker Shifts

---

## Step 13: Generate Weekly Closing

System generates closing report matching factory format.

Closing includes:

- Piece Rate Salary
- Shift Salary
- Contractor Salary
- Expenses
- Deductions
- Bonuses

---

## Step 14: Store Weekly Closing

System:

- Saves report
- Creates week record
- Creates audit record

Historical reports remain available.

---

## Step 15: Official Notification

System sends:

"Weekly closing generated successfully."

---

## Step 16: Employee Notification

Each employee receives:

### Work Summary

- Date
- Style
- Operation
- Size
- Quantity

### Salary Summary

- Gross Salary
- Bonus
- Deduction
- Net Salary

---

## Step 17: Owner Notification

Owner receives weekly summary.

### Production Summary

- Total Pieces Produced
- Total Workers
- Total Styles

### Salary Summary

- Piece Rate Salary
- Shift Salary
- Contractor Salary

### Expense Summary

- Total Expenses

### Cost Summary

- Total Weekly Cost

---

# Search Workflow

## Owner Query

Example:

"What is Ravi's salary this week?"

System:

- Searches database
- Calculates result
- Returns answer

---

## Production Query

Example:

"What work did Ravi do on 07/07/2026?"

System returns:

- Style
- Operation
- Size
- Quantity
- Amount

---

## Style Query

Example:

"Show production for Style PE097."

System returns:

- Employees
- Operations
- Sizes
- Quantities

---

# Future Workflow

## Charts

Examples:

- Weekly Production Chart
- Monthly Production Chart
- Salary Trend Chart
- Expense Trend Chart

---

## AI Assistant

Examples:

"Who earned the most this month?"

"Show top 5 operations."

"What is the total electricity expense this year?"

"Compare this month with last month."

System generates answers from stored data.

---

# Workflow Principles

The system should:

- Minimize manual entry
- Preserve existing factory process
- Automatically detect new data
- Avoid developer intervention
- Maintain complete historical records
- Support future AI features

The factory should continue working normally while the system handles consolidation, storage, reporting, and search.