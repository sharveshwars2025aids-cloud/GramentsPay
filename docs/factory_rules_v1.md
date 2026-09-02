# Factory Rules v1

## 1. Employee Types

The factory has two types of workers:

### Piece Rate Workers

Workers are paid based on the quantity of work completed.

Formula:

Weekly Salary = Sum of Daily Amounts

### Shift Workers

Workers are paid based on the number of shifts worked.

Formula:

Weekly Salary = Total Shifts Worked × Shift Rate

---

## 2. Employee Master

Each employee contains:

- Employee ID
- Name
- Pay Type (Piece Rate / Shift)
- Department
- Contractor (Optional)
- Status (Active / Inactive)

---

## 3. Departments

Examples:

- Singer
- Power Table
- Checking
- Ironing
- Packing

Departments must be dynamic.

New departments can be added without code changes.

---

## 4. Contractor Rules

Contractors are associated only with shift workers.

### Worker Relationship

- One contractor can manage multiple workers.
- Shift workers may belong to a contractor.
- Piece-rate workers never belong to contractors.

### Contractor Salary Calculation

Formula:

Contractor Salary = Commission Amount × Total Shifts Worked By Workers Under Contractor

Example:

Contractor: Kapil

Workers:

Ravi = 7 shifts
Kumar = 7 shifts
Muthu = 6.5 shifts

Total Shifts = 20.5

Commission Amount = ₹100

Contractor Salary = 20.5 × 100 = ₹2050

---

## 5. Operations

The factory has approximately 20 common operations.

Examples:

- O/L
- F/L
- PATTI F/L
- NECK FOLG
- BODY TOWER
- LEG TOWER
- CROTCH FOLDG
- CHECKING
- IRONING
- PACKING

Operations are dynamic.

New operations can be created whenever required.

---

## 6. Styles

Styles arrive from:

- Buyer
- Head Office

Each style contains:

- Style Number
- Style Name

Example:

- PE097PJFS26

---

## 7. Style Activation Rule

Production cannot start until rates are finalized.

Workflow:

New Style
↓
Rate Finalized
↓
Production Starts

---

## 8. Style Structure

Most styles contain multiple operations.

Example:

Style A

- PATTI F/L
- NECK FOLG
- BODY TOWER
- LEG TOWER

Some styles may contain only one operation.

Example:

- Checking Only
- Ironing Only
- Packing Only

These usually occur when work is outsourced from head office.

---

## 9. Rate Rules

Current understanding:

Rate is determined by:

Style + Operation

Example:

Style A

PATTI F/L = ₹1
NECK FOLG = ₹0.80

Rates are finalized before production begins.

---

## 10. Sizes

Sizes are tracked for production history.

Examples:

- 0/6
- 3/6
- 6/12
- 12/18
- 2Y
- 3Y
- 4Y

The system must store size information.

This allows future queries such as:

"What work did Ravi do on 07/07/2026?"

Response:

- Style
- Operation
- Size
- Quantity

---

## 11. Daily Workbook

One workbook contains multiple daily sheets.

Example:

- Day 1
- Day 2
- Day 3
- Day 4
- Day 5
- Day 6
- Day 7

The accountant updates these sheets throughout the week.

---

## 12. Weekly Closing

The weekly closing sheet is generated from the weekly workbook.

The weekly closing consolidates:

- Piece Rate Salary
- Shift Salary
- Contractor Salary
- Expenses
- Deductions
- Bonuses

---

## 13. Weekly Closing Template

The weekly closing template is fixed.

The structure remains the same every week.

Only the data changes.

This makes automation possible.

---

## 14. Expenses

Examples:

- Electricity
- Sweeping
- Cleaning
- Flowers
- Pooja
- Transport
- Miscellaneous

Expense categories are dynamic.

The system should allow new expense categories without code changes.

---

## 15. Deductions

Current factory uses:

- Advance

Future factories may use:

- Advance
- Loan
- PF
- ESI
- Fine
- Other

Deductions must be dynamic.

---

## 16. Bonuses

Bonuses are not regular.

Examples:

- Festival Bonus
- Special Bonus

Bonuses are entered during weekly closing.

---

## 17. Piece Rate Salary Calculation

Daily Salary:

Quantity × Rate

Weekly Salary:

Sum of all daily amounts during the week

Net Salary:

Gross Salary
+ Bonus
- Deductions

---

## 18. Shift Salary Calculation

Full Shift = 1

Half Shift = 0.5

Examples:

- 7 shifts
- 7.5 shifts

Weekly Salary:

Total Shifts × Shift Rate

Verification:

Sum of Daily Shift Salary
=
Total Shifts × Shift Rate

---

## 19. Data Collected From Workbook

The system should capture:

- Date
- Employee
- Department
- Style Number
- Style Name (if available)
- Type
- Operation
- Size
- Color (if available)
- Quantity
- Rate
- Amount

---

## 20. Weekly Closing Workflow

Step 1

Upload Weekly Workbook

↓

Step 2

Extract Production Data

↓

Step 3

Ask For Deductions

Example:

Ravi 1000 Advance

↓

Step 4

Ask For Bonuses

Example:

Ravi 500 Festival Bonus

↓

Step 5

Ask For Expenses

Example:

Electricity 5000
Flowers 200

↓

Step 6

Generate Weekly Closing

↓

Step 7

Send Notifications

---

## 21. Official Notifications

Officials should receive:

- Weekly Closing Reminder
- Weekly Closing Generated Notification

---

## 22. Employee Notifications

Employees should receive:

- Work Summary
- Gross Salary
- Deductions
- Bonuses
- Net Salary

This allows employees to verify calculations.

---

## 23. Owner Summary

After weekly closing generation, the owner receives:

### Production Summary

- Total Pieces Produced
- Total Workers
- Total Styles

### Salary Summary

- Piece Rate Salary
- Shift Salary
- Contractor Salary

### Expense Summary

- Electricity
- Cleaning
- Miscellaneous
- Other Expenses

### Cost Summary

- Total Salary Cost
- Total Expense Cost
- Total Weekly Cost

---

## 24. Future Search Queries

The system should support queries such as:

- What is Ravi's salary this week?
- What work did Ravi do on 07/07/2026?
- Show Week 25 Closing.
- Show all work done for Style PE097.
- Show production for June.
- Show top workers this month.
- Show total electricity expense this year.

---

### 25. Open Question

Shift-worker source data has not yet been identified.

Possible sources:

- Daily workbook
- Separate attendance sheet
- Separate shift register

The system design should remain flexible until a sample containing shift-worker data is obtained.

## 26. System Philosophy

The system should be flexible.

Adding:

- Employee
- Contractor
- Style
- Operation
- Department
- Expense Category
- Deduction Type

must not require developer intervention.

Users should be able to manage business data through natural workflows.