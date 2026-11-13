# Intelligent Library Knowledge and Query System Using First-Order Logic (FOL)

A full-stack, explainable symbolic AI library management and query system combining **First-Order Logic (FOL)** reasoning, **predicate unification**, **Horn clause forward chaining**, and a persistent **SQLite relational database** with an interactive **Streamlit** user interface.

---

## 🌟 Key Features

1. **Persistent SQLite Source of Truth (`database.py`)**
   - Normalized relational schema: `books`, `authors`, `students`, `borrowing_records`.
   - Foreign-key constraints, transactions, and parameterised SQL queries.
   - Automatic database initialization and seeding of academic catalog data on first run.

2. **Bidirectional SQLite ⟷ FOL Synchronization**
   - Ground atomic formulas (`Book`, `Author`, `Subject`, `Student`, `WrittenBy`, `BelongsTo`, `Borrowed`, `MemberOf`) dynamically generated from SQLite tables.
   - Live synchronization on every CRUD action or loan status change.
   - Strict separation between original database ground facts and derived inference facts.

3. **Symbolic AI Inference Engine (`inference_engine.py`)**
   - Semi-naive forward chaining iterating definite Horn clauses to a fixed point.
   - **Rule R1**: $\forall x, y \ (\text{Borrowed}(x, y) \rightarrow \text{LibraryUser}(x))$ (Borrower role derivation).
   - **Rule R2**: $\forall b, a, s \ ((\text{WrittenBy}(b, a) \land \text{SpecializesIn}(a, s)) \rightarrow \text{BelongsTo}(b, s))$ (Subject inheritance).
   - **Rule R3**: $\forall p, b \ (\text{Borrowed}(p, b) \rightarrow \text{HasBorrowed}(p, b))$ (Borrowing alias).
   - **Rule R4**: $\forall b \ ((\text{Book}(b) \land \neg \exists p \ \text{Borrowed}(p, b)) \rightarrow \text{Available}(b))$ (Non-monotonic availability under negation / closed-world check).

4. **Intelligent Query with Natural Language Translation (`query_engine.py`)**
   - Enter queries in **plain English** (e.g. *"Find books written by Russell"*, *"Is AI A Modern Approach available?"*, *"Which books are related to Artificial Intelligence?"*, *"Who borrowed Computer Networking?"*).
   - Enter queries in **standard FOL syntax** with variables (e.g. `WrittenBy(b, Russell)`, `Available(b)`, `Borrowed(s, AI_A_Modern_Approach)`).
   - Unification engine resolves variable substitutions with full provenance, separating ground facts from inferred rule conclusions.

5. **Library Management (CRUD & Circulation)**
   - **Books**: Register books, search & filter catalog, edit metadata (title, author, subject, department, publication year, ISBN), safe delete.
   - **Authors**: Register authors, edit names, manage research specializations, check linked catalog books.
   - **Students**: Register students, manage department memberships, check active loan counts.
   - **Borrowing & Returns**: Issue loans to students with availability checks, record returns, track active loans with overdue alerts (>14 days), view complete circulation history.

6. **Interactive Analytics Dashboard**
   - Top metrics: Total Books, Total Authors, Total Students, Currently Borrowed, Available Books, Overdue Loans.
   - Visualizations: Books by Subject (Bar chart), Books by Department (Donut chart), Borrowed vs. Available (Bar chart), Monthly Borrowing Activity (Line chart), Top Borrowed Books (Horizontal bar chart).
   - Recent activity logs: Recently added books, active borrowings, and recent returns.

---

## 📁 Project Structure

```text
intelligent_library_fol/
│
├── app.py                     # Main Streamlit web application & sidebar navigation
├── database.py                # Persistent SQLite schema, CRUD, transactions, & analytics
├── knowledge_base.py          # Fact representation, knowledge store, & DB synchronization
├── rules.py                   # Horn inference rule definitions (R1–R4)
├── unification.py             # First-order term unification with occurs check
├── inference_engine.py        # Forward-chaining deduction engine
├── query_engine.py            # Natural language to FOL translator & query answerer
├── data.py                    # Static sample fact definitions & initial catalogue mapping
├── utils.py                   # Predicate signatures & validation utilities
├── test_demo.py               # Original 5-scenario FOL validation script
├── test_suite.py              # Comprehensive automated 12-scenario integration test suite
│
├── pages/                     # Modular view components
│   ├── dashboard.py           # Real-time analytics dashboard & Altair visualizations
│   ├── intelligent_query.py   # Query input, natural language parser, and explanation view
│   └── library_management.py  # Tabbed CRUD and borrowing circulation management
│
├── database/
│   └── library.db             # Persistent SQLite database file (created automatically)
│
├── requirements.txt           # Python package dependencies
└── README.md                  # Project documentation & execution guide
```

---

## 🚀 Installation and Execution

### Prerequisites
- Python 3.10 or newer (tested on Python 3.10, 3.11, 3.12, 3.14).

### Step 1: Clone or Navigate to the Project Directory
```powershell
cd c:\Users\Vikas.S\Desktop\AI-Libary\ILM_QS_demo-1\intelligent_library_fol
```

### Step 2: (Optional) Create and Activate Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Automated Test Suite
Verify that all 12 system scenarios pass:
```powershell
python test_suite.py
```

### Step 5: Start the Streamlit Application
```powershell
streamlit run app.py
```
Streamlit will print the local URL (usually `http://localhost:8501`). Open this address in your web browser.

---

## 🔍 First-Order Logic Predicate Signatures

| Predicate | Arity | Semantic Meaning | Example Ground Fact |
|---|:---:|---|---|
| `Book(x)` | 1 | `x` is a registered book in the library | `Book(AI_A_Modern_Approach)` |
| `Author(x)` | 1 | `x` is a recognized author | `Author(Russell)` |
| `Student(x)` | 1 | `x` is an enrolled student | `Student(Ravi)` |
| `Faculty(x)` | 1 | `x` is a faculty member | `Faculty(Dr_Sharma)` |
| `LibraryUser(x)` | 1 | `x` is an active library user (*inferred via R1*) | `LibraryUser(Ravi)` |
| `Subject(x)` | 1 | `x` is an academic subject | `Subject(Artificial_Intelligence)` |
| `Department(x)` | 1 | `x` is a college department | `Department(Computer_Science)` |
| `WrittenBy(b, a)` | 2 | Book `b` was written by author `a` | `WrittenBy(AI_A_Modern_Approach, Russell)` |
| `BelongsTo(b, s)` | 2 | Book `b` is classified under subject `s` | `BelongsTo(AI_A_Modern_Approach, Artificial_Intelligence)` |
| `SpecializesIn(a, s)` | 2 | Author `a` specializes in academic field `s` | `SpecializesIn(Russell, Artificial_Intelligence)` |
| `Borrowed(p, b)` | 2 | Person `p` currently has book `b` checked out | `Borrowed(Ravi, AI_A_Modern_Approach)` |
| `HasBorrowed(p, b)` | 2 | Historical or active borrowing relation (*inferred via R3*) | `HasBorrowed(Ravi, AI_A_Modern_Approach)` |
| `Available(b)` | 1 | Book `b` has no active borrowing loan (*inferred via R4*) | `Available(Introduction_to_Algorithms)` |
| `MemberOf(p, d)` | 2 | Person `p` belongs to department `d` | `MemberOf(Ravi, Computer_Science)` |

---

## ⚡ Inference Rules

- **Rule R1: Borrower is a Library User**  
  $$\forall x, y \ (\text{Borrowed}(x, y) \rightarrow \text{LibraryUser}(x))$$  
  *English:* Anyone who currently borrows a book is inferred to be a library user.

- **Rule R2: Author Specialization Determines Book Subject**  
  $$\forall b, a, s \ ((\text{WrittenBy}(b, a) \land \text{SpecializesIn}(a, s)) \rightarrow \text{BelongsTo}(b, s))$$  
  *English:* A book inherits a subject classification associated with its author's specialization.

- **Rule R3: Borrowing Relationship Alias**  
  $$\forall p, b \ (\text{Borrowed}(p, b) \rightarrow \text{HasBorrowed}(p, b))$$  
  *English:* Every active borrowing establishes a general loan association.

- **Rule R4: Availability Under Negation (Closed-World Assumption)**  
  $$\forall b \ ((\text{Book}(b) \land \neg \exists p \ \text{Borrowed}(p, b)) \rightarrow \text{Available}(b))$$  
  *English:* A known book is available when no active borrowing record exists for it.

---

## 💡 Example Queries in Intelligent Query

You can enter queries in either natural English or FOL syntax:

1. **Find books written by an author**
   - Natural Language: `Find books written by Russell` or `Books by Norvig`
   - FOL Syntax: `WrittenBy(b, Russell)`
2. **Find author of a book**
   - Natural Language: `Who wrote AI A Modern Approach?`
   - FOL Syntax: `WrittenBy(AI_A_Modern_Approach, a)`
3. **Find books belonging to a subject**
   - Natural Language: `Find books related to Artificial Intelligence`
   - FOL Syntax: `BelongsTo(b, Artificial_Intelligence)`
4. **Check whether a book is available**
   - Natural Language: `Is AI A Modern Approach available?`
   - FOL Syntax: `Available(AI_A_Modern_Approach)`
5. **List all available books**
   - Natural Language: `Which books are available?`
   - FOL Syntax: `Available(b)`
6. **Find who borrowed a book**
   - Natural Language: `Who borrowed AI A Modern Approach?`
   - FOL Syntax: `Borrowed(s, AI_A_Modern_Approach)`
7. **Find books borrowed by a student**
   - Natural Language: `Find books borrowed by Ravi`
   - FOL Syntax: `Borrowed(Ravi, b)`
8. **List all library users**
   - Natural Language: `Who is a library user?`
   - FOL Syntax: `LibraryUser(u)`

---

## 🧪 Automated Testing

Run the test suite at any time:
```powershell
python test_suite.py
```
The test suite validates:
1. Book creation and simultaneous SQLite + FOL assertion.
2. Book editing with immediate removal of outdated facts and addition of updated facts.
3. Author creation and book association.
4. Student registration and department membership.
5. Borrowing transactions with R1 (`LibraryUser`) and R3 (`HasBorrowed`) derivations.
6. Book unavailability verification under loan.
7. Return processing.
8. Availability restoration derived via Rule R4.
9. Book deletion with safe cascade handling.
10. Intelligent Query resolution against real knowledge base facts.
11. Dynamic recalculation of dashboard metrics.
12. Data persistence across application restarts.
