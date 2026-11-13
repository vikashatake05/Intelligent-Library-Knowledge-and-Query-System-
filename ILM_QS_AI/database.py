"""Database module for Intelligent Library Knowledge and Query System.
Provides persistent SQLite storage, schema initialization, CRUD operations,
transaction management, and metrics queries.
"""
import sqlite3
import os
import re
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple

DEFAULT_DB_DIR = os.path.join(os.path.dirname(__file__), "database")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "library.db")

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create and return a SQLite connection with foreign keys enabled."""
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize database tables and seed sample data if empty."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                author_id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_name TEXT NOT NULL UNIQUE,
                specialization TEXT
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                department TEXT,
                publication_year INTEGER,
                isbn TEXT UNIQUE NOT NULL,
                availability_status TEXT NOT NULL DEFAULT 'Available' CHECK(availability_status IN ('Available', 'Borrowed')),
                FOREIGN KEY (author_id) REFERENCES authors (author_id) ON DELETE RESTRICT
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                student_name TEXT NOT NULL,
                department TEXT NOT NULL
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS borrowing_records (
                borrowing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                book_id INTEGER NOT NULL,
                borrow_date TEXT NOT NULL,
                return_date TEXT,
                status TEXT NOT NULL DEFAULT 'Borrowed' CHECK(status IN ('Borrowed', 'Returned')),
                FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE RESTRICT,
                FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE RESTRICT
            );
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_books_author ON books(author_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_books_subject ON books(subject);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_borrowing_student ON borrowing_records(student_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_borrowing_book ON borrowing_records(book_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_borrowing_status ON borrowing_records(status);")

        # Check if database is empty; if so, seed sample data
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM books;")
        count = cur.fetchone()["cnt"]
        if count == 0:
            seed_sample_data(conn)
    finally:
        conn.close()

def seed_sample_data(conn: sqlite3.Connection) -> None:
    """Seed initial library data migrated from original sample facts."""
    authors_data = [
        ("Russell", "Artificial_Intelligence"),
        ("Norvig", "Artificial_Intelligence"),
        ("Cormen", "Data_Structures"),
        ("Sedgewick", "Data_Structures"),
        ("Elmasri", "Database_Systems"),
        ("Kurose", "Computer_Networks"),
        ("Tanenbaum", "Operating_Systems"),
        ("Sommerville", "Software_Engineering"),
        ("Rosen", "Mathematics"),
        ("Stallings", "Cyber_Security")
    ]
    with conn:
        for name, spec in authors_data:
            conn.execute(
                "INSERT OR IGNORE INTO authors (author_name, specialization) VALUES (?, ?);",
                (name, spec)
            )

        # Map author names to IDs
        cur = conn.cursor()
        cur.execute("SELECT author_id, author_name FROM authors;")
        author_map = {row["author_name"]: row["author_id"] for row in cur.fetchall()}

        books_data = [
            ("AI_A_Modern_Approach", "Russell", "Artificial_Intelligence", "Computer_Science", 2020, "978-0136042594"),
            ("Artificial_Intelligence_Foundations", "Norvig", "Artificial_Intelligence", "Computer_Science", 2021, "978-0134685991"),
            ("Introduction_to_Algorithms", "Cormen", "Data_Structures", "Computer_Science", 2022, "978-0262033848"),
            ("Algorithms_in_C", "Sedgewick", "Data_Structures", "Information_Science", 2018, "978-0201314526"),
            ("Fundamentals_of_Database_Systems", "Elmasri", "Database_Systems", "Information_Science", 2020, "978-0133970777"),
            ("Computer_Networking", "Kurose", "Computer_Networks", "Electronics", 2021, "978-0133594140"),
            ("Modern_Operating_Systems", "Tanenbaum", "Operating_Systems", "Computer_Science", 2019, "978-0133591620"),
            ("Software_Engineering", "Sommerville", "Software_Engineering", "Information_Science", 2020, "978-0133943030"),
            ("Discrete_Mathematics", "Rosen", "Mathematics", "Mathematics", 2019, "978-0073383095"),
            ("Network_Security_Essentials", "Stallings", "Cyber_Security", "Electronics", 2021, "978-0134444284"),
            ("Deep_Learning_Basics", "Norvig", "Artificial_Intelligence", "Computer_Science", 2022, "978-0262035613"),
            ("Advanced_Data_Structures", "Cormen", "Data_Structures", "Computer_Science", 2023, "978-0262033855"),
            ("Database_Design", "Elmasri", "Database_Systems", "Information_Science", 2019, "978-0132145374"),
            ("Secure_Computer_Networks", "Stallings", "Cyber_Security", "Electronics", 2022, "978-0132350884"),
            ("Software_Project_Management", "Sommerville", "Software_Engineering", "Mechanical", 2021, "978-0137043293")
        ]

        for title, author_name, subject, dept, year, isbn in books_data:
            aid = author_map[author_name]
            conn.execute("""
            INSERT INTO books (title, author_id, subject, department, publication_year, isbn, availability_status)
            VALUES (?, ?, ?, ?, ?, ?, 'Available');
            """, (title, aid, subject, dept, year, isbn))

        cur.execute("SELECT book_id, title FROM books;")
        book_map = {row["title"]: row["book_id"] for row in cur.fetchall()}

        students_data = [
            ("STU001", "Ravi", "Computer_Science"),
            ("STU002", "Ananya", "Information_Science"),
            ("STU003", "Kiran", "Electronics"),
            ("STU004", "Meera", "Mechanical"),
            ("STU005", "Arjun", "Computer_Science"),
            ("STU006", "Divya", "Information_Science"),
            ("STU007", "Rahul", "Electronics"),
            ("STU008", "Sneha", "Mechanical"),
            ("STU009", "Vikram", "Computer_Science"),
            ("STU010", "Pooja", "Information_Science")
        ]

        for sid, sname, sdept in students_data:
            conn.execute("""
            INSERT INTO students (student_id, student_name, department)
            VALUES (?, ?, ?);
            """, (sid, sname, sdept))

        # Seed realistic borrowing transactions
        # 1. Past completed borrowings (Returned)
        past_borrowings = [
            ("STU001", "Computer_Networking", "2026-08-10", "2026-08-24"),
            ("STU002", "AI_A_Modern_Approach", "2026-08-15", "2026-08-30"),
            ("STU004", "Fundamentals_of_Database_Systems", "2026-09-01", "2026-09-18"),
            ("STU006", "Software_Engineering", "2026-09-05", "2026-09-20"),
            ("STU007", "Discrete_Mathematics", "2026-09-15", "2026-09-29"),
            ("STU008", "Network_Security_Essentials", "2026-09-20", "2026-10-04"),
            ("STU009", "Algorithms_in_C", "2026-10-01", "2026-10-15"),
            ("STU010", "Database_Design", "2026-10-05", "2026-10-19"),
            ("STU002", "Database_Design", "2026-10-10", "2026-10-25"),
            ("STU003", "Discrete_Mathematics", "2026-10-15", "2026-10-29")
        ]
        for sid, btitle, bdate, rdate in past_borrowings:
            bid = book_map[btitle]
            conn.execute("""
            INSERT INTO borrowing_records (student_id, book_id, borrow_date, return_date, status)
            VALUES (?, ?, ?, ?, 'Returned');
            """, (sid, bid, bdate, rdate))

        # 2. Currently active loans (Borrowed)
        # Note: AI_A_Modern_Approach is borrowed on 2026-10-20 (> 14 days ago, so overdue)
        active_borrowings = [
            ("STU001", "AI_A_Modern_Approach", "2026-10-20"),
            ("STU002", "Introduction_to_Algorithms", "2026-11-04"),
            ("STU003", "Computer_Networking", "2026-11-06"),
            ("STU005", "Modern_Operating_Systems", "2026-11-08")
        ]
        for sid, btitle, bdate in active_borrowings:
            bid = book_map[btitle]
            conn.execute("""
            INSERT INTO borrowing_records (student_id, book_id, borrow_date, return_date, status)
            VALUES (?, ?, ?, NULL, 'Borrowed');
            """, (sid, bid, bdate))
            conn.execute("""
            UPDATE books SET availability_status = 'Borrowed' WHERE book_id = ?;
            """, (bid,))

# -----------------
# Book CRUD Operations
# -----------------

def add_book(title: str, author_id: int, subject: str, department: str,
             publication_year: int, isbn: str, db_path: str = DEFAULT_DB_PATH) -> int:
    """Add a new book after validation."""
    title = title.strip()
    subject = subject.strip()
    department = department.strip() if department else None
    isbn = isbn.strip()

    if not title:
        raise ValueError("Book title cannot be empty.")
    if not isbn:
        raise ValueError("ISBN cannot be empty.")
    if not subject:
        raise ValueError("Subject cannot be empty.")

    conn = get_connection(db_path)
    try:
        with conn:
            # Check for duplicate ISBN
            cur = conn.cursor()
            cur.execute("SELECT book_id FROM books WHERE isbn = ?;", (isbn,))
            if cur.fetchone():
                raise ValueError(f"A book with ISBN '{isbn}' already exists.")

            # Validate author exists
            cur.execute("SELECT author_id FROM authors WHERE author_id = ?;", (author_id,))
            if not cur.fetchone():
                raise ValueError(f"Author ID {author_id} does not exist.")

            cur.execute("""
            INSERT INTO books (title, author_id, subject, department, publication_year, isbn, availability_status)
            VALUES (?, ?, ?, ?, ?, ?, 'Available');
            """, (title, author_id, subject, department, publication_year, isbn))
            return cur.lastrowid
    finally:
        conn.close()

def update_book(book_id: int, title: str, author_id: int, subject: str,
                department: str, publication_year: int, isbn: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Update an existing book's details."""
    title = title.strip()
    subject = subject.strip()
    department = department.strip() if department else None
    isbn = isbn.strip()

    if not title:
        raise ValueError("Book title cannot be empty.")
    if not isbn:
        raise ValueError("ISBN cannot be empty.")

    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            # Check duplicate ISBN for other books
            cur.execute("SELECT book_id FROM books WHERE isbn = ? AND book_id != ?;", (isbn, book_id))
            if cur.fetchone():
                raise ValueError(f"Another book already has ISBN '{isbn}'.")

            # Check author exists
            cur.execute("SELECT author_id FROM authors WHERE author_id = ?;", (author_id,))
            if not cur.fetchone():
                raise ValueError(f"Author ID {author_id} does not exist.")

            cur.execute("""
            UPDATE books
            SET title = ?, author_id = ?, subject = ?, department = ?, publication_year = ?, isbn = ?
            WHERE book_id = ?;
            """, (title, author_id, subject, department, publication_year, isbn, book_id))
            return cur.rowcount > 0
    finally:
        conn.close()

def delete_book(book_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Delete a book if it has no active loans.
    Also cleans up historical borrowing records safely within a transaction."""
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            # Check for active loans
            cur.execute("""
            SELECT borrowing_id FROM borrowing_records
            WHERE book_id = ? AND status = 'Borrowed';
            """, (book_id,))
            if cur.fetchone():
                raise ValueError("Cannot delete book: it currently has an active borrowing loan. Return the book first.")

            # Remove past borrowing history for this book to avoid FK violation
            cur.execute("DELETE FROM borrowing_records WHERE book_id = ?;", (book_id,))
            cur.execute("DELETE FROM books WHERE book_id = ?;", (book_id,))
            return cur.rowcount > 0
    finally:
        conn.close()

def get_all_books(search: Optional[str] = None, subject: Optional[str] = None,
                  department: Optional[str] = None, availability: Optional[str] = None,
                  db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all books with author names and optional filtering."""
    conn = get_connection(db_path)
    try:
        query = """
        SELECT b.book_id, b.title, b.author_id, a.author_name, b.subject,
               b.department, b.publication_year, b.isbn, b.availability_status
        FROM books b
        JOIN authors a ON b.author_id = a.author_id
        WHERE 1=1
        """
        params: List[Any] = []
        if search:
            query += " AND (b.title LIKE ? OR b.isbn LIKE ? OR a.author_name LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term, term])
        if subject and subject != "All":
            query += " AND b.subject = ?"
            params.append(subject)
        if department and department != "All":
            query += " AND b.department = ?"
            params.append(department)
        if availability and availability != "All":
            query += " AND b.availability_status = ?"
            params.append(availability)

        query += " ORDER BY b.title ASC;"
        cur = conn.cursor()
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_book_by_id(book_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a single book by ID."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT b.book_id, b.title, b.author_id, a.author_name, b.subject,
               b.department, b.publication_year, b.isbn, b.availability_status
        FROM books b
        JOIN authors a ON b.author_id = a.author_id
        WHERE b.book_id = ?;
        """, (book_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

# -----------------
# Author CRUD Operations
# -----------------

def add_author(author_name: str, specialization: Optional[str] = None,
               db_path: str = DEFAULT_DB_PATH) -> int:
    """Add a new author."""
    name = author_name.strip()
    if not name:
        raise ValueError("Author name cannot be empty.")
    spec = specialization.strip() if specialization else None

    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT author_id FROM authors WHERE author_name = ?;", (name,))
            if cur.fetchone():
                raise ValueError(f"Author '{name}' already exists.")
            cur.execute("INSERT INTO authors (author_name, specialization) VALUES (?, ?);", (name, spec))
            return cur.lastrowid
    finally:
        conn.close()

def update_author(author_id: int, author_name: str, specialization: Optional[str] = None,
                  db_path: str = DEFAULT_DB_PATH) -> bool:
    """Update an author's name and specialization."""
    name = author_name.strip()
    if not name:
        raise ValueError("Author name cannot be empty.")
    spec = specialization.strip() if specialization else None

    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT author_id FROM authors WHERE author_name = ? AND author_id != ?;", (name, author_id))
            if cur.fetchone():
                raise ValueError(f"Another author with name '{name}' already exists.")
            cur.execute("UPDATE authors SET author_name = ?, specialization = ? WHERE author_id = ?;", (name, spec, author_id))
            return cur.rowcount > 0
    finally:
        conn.close()

def delete_author(author_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Delete an author if no books are associated with them."""
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS cnt FROM books WHERE author_id = ?;", (author_id,))
            cnt = cur.fetchone()["cnt"]
            if cnt > 0:
                raise ValueError(f"Cannot delete author: {cnt} book(s) are currently associated with this author. Reassign or delete those books first.")
            cur.execute("DELETE FROM authors WHERE author_id = ?;", (author_id,))
            return cur.rowcount > 0
    finally:
        conn.close()

def get_all_authors(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all authors with their book counts."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT a.author_id, a.author_name, a.specialization, COUNT(b.book_id) AS book_count
        FROM authors a
        LEFT JOIN books b ON a.author_id = b.author_id
        GROUP BY a.author_id
        ORDER BY a.author_name ASC;
        """)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

# -----------------
# Student CRUD Operations
# -----------------

def add_student(student_id: str, student_name: str, department: str,
                db_path: str = DEFAULT_DB_PATH) -> str:
    """Add a new student."""
    sid = student_id.strip()
    sname = student_name.strip()
    sdept = department.strip()

    if not sid:
        raise ValueError("Student ID cannot be empty.")
    if not sname:
        raise ValueError("Student name cannot be empty.")
    if not sdept:
        raise ValueError("Department cannot be empty.")

    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT student_id FROM students WHERE student_id = ?;", (sid,))
            if cur.fetchone():
                raise ValueError(f"Student with ID '{sid}' already exists.")
            cur.execute("INSERT INTO students (student_id, student_name, department) VALUES (?, ?, ?);",
                        (sid, sname, sdept))
            return sid
    finally:
        conn.close()

def update_student(student_id: str, student_name: str, department: str,
                   db_path: str = DEFAULT_DB_PATH) -> bool:
    """Update student name and department."""
    sname = student_name.strip()
    sdept = department.strip()
    if not sname:
        raise ValueError("Student name cannot be empty.")
    if not sdept:
        raise ValueError("Department cannot be empty.")

    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE students SET student_name = ?, department = ? WHERE student_id = ?;",
                        (sname, sdept, student_id))
            return cur.rowcount > 0
    finally:
        conn.close()

def delete_student(student_id: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Delete a student if they have no active loans. Historical borrowing records are safely removed."""
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT borrowing_id FROM borrowing_records
            WHERE student_id = ? AND status = 'Borrowed';
            """, (student_id,))
            if cur.fetchone():
                raise ValueError("Cannot delete student: this student currently has an active borrowed book.")

            # Remove past history safely
            cur.execute("DELETE FROM borrowing_records WHERE student_id = ?;", (student_id,))
            cur.execute("DELETE FROM students WHERE student_id = ?;", (student_id,))
            return cur.rowcount > 0
    finally:
        conn.close()

def get_all_students(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all students with their active borrowing count."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT s.student_id, s.student_name, s.department,
               COUNT(CASE WHEN br.status = 'Borrowed' THEN 1 END) AS active_loans_count
        FROM students s
        LEFT JOIN borrowing_records br ON s.student_id = br.student_id
        GROUP BY s.student_id
        ORDER BY s.student_name ASC;
        """)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

# -----------------
# Borrowing Management
# -----------------

def record_borrowing(student_id: str, book_id: int, borrow_date: Optional[str] = None,
                     db_path: str = DEFAULT_DB_PATH) -> int:
    """Record a borrowing transaction and set book status to 'Borrowed'."""
    bdate = borrow_date or date.today().isoformat()
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            # Verify student exists
            cur.execute("SELECT student_id FROM students WHERE student_id = ?;", (student_id,))
            if not cur.fetchone():
                raise ValueError(f"Student ID '{student_id}' does not exist.")

            # Verify book exists and is Available
            cur.execute("SELECT availability_status FROM books WHERE book_id = ?;", (book_id,))
            book_row = cur.fetchone()
            if not book_row:
                raise ValueError(f"Book ID {book_id} does not exist.")
            if book_row["availability_status"] != "Available":
                raise ValueError("This book is already borrowed and not currently available.")

            cur.execute("""
            INSERT INTO borrowing_records (student_id, book_id, borrow_date, return_date, status)
            VALUES (?, ?, ?, NULL, 'Borrowed');
            """, (student_id, book_id, bdate))
            rec_id = cur.lastrowid

            cur.execute("UPDATE books SET availability_status = 'Borrowed' WHERE book_id = ?;", (book_id,))
            return rec_id
    finally:
        conn.close()

def record_return(borrowing_id: int, return_date: Optional[str] = None,
                  db_path: str = DEFAULT_DB_PATH) -> bool:
    """Record a return transaction and set book status back to 'Available'."""
    rdate = return_date or date.today().isoformat()
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT book_id, status FROM borrowing_records WHERE borrowing_id = ?;", (borrowing_id,))
            rec = cur.fetchone()
            if not rec:
                raise ValueError(f"Borrowing record ID {borrowing_id} not found.")
            if rec["status"] == "Returned":
                raise ValueError("This borrowing transaction has already been marked as returned.")

            book_id = rec["book_id"]
            cur.execute("""
            UPDATE borrowing_records
            SET return_date = ?, status = 'Returned'
            WHERE borrowing_id = ?;
            """, (rdate, borrowing_id))

            cur.execute("UPDATE books SET availability_status = 'Available' WHERE book_id = ?;", (book_id,))
            return True
    finally:
        conn.close()

def update_borrowing_record(borrowing_id: int, student_id: Optional[str] = None,
                            borrow_date: Optional[str] = None, return_date: Optional[str] = None,
                            db_path: str = DEFAULT_DB_PATH) -> bool:
    """Update fields of an existing borrowing record."""
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT borrowing_id, student_id, borrow_date, return_date, status FROM borrowing_records WHERE borrowing_id = ?;",
                        (borrowing_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("Borrowing record not found.")

            new_student = student_id if student_id else row["student_id"]
            new_bdate = borrow_date if borrow_date else row["borrow_date"]
            new_rdate = return_date if return_date is not None else row["return_date"]

            cur.execute("""
            UPDATE borrowing_records
            SET student_id = ?, borrow_date = ?, return_date = ?
            WHERE borrowing_id = ?;
            """, (new_student, new_bdate, new_rdate, borrowing_id))
            return True
    finally:
        conn.close()

def get_active_loans(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all active (unreturned) borrowing loans."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT br.borrowing_id, br.student_id, s.student_name, s.department AS student_department,
               br.book_id, b.title AS book_title, b.isbn, br.borrow_date, br.status
        FROM borrowing_records br
        JOIN students s ON br.student_id = s.student_id
        JOIN books b ON br.book_id = b.book_id
        WHERE br.status = 'Borrowed'
        ORDER BY br.borrow_date ASC;
        """)
        results = []
        today = date.today()
        for row in cur.fetchall():
            d = dict(row)
            try:
                b_date = datetime.strptime(d["borrow_date"], "%Y-%m-%d").date()
                days = (today - b_date).days
                d["days_borrowed"] = days
                d["is_overdue"] = days > 14
            except (ValueError, TypeError):
                d["days_borrowed"] = 0
                d["is_overdue"] = False
            results.append(d)
        return results
    finally:
        conn.close()

def get_borrowing_history(limit: int = 100, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all borrowing records (active and returned)."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT br.borrowing_id, br.student_id, s.student_name,
               br.book_id, b.title AS book_title, b.isbn,
               br.borrow_date, br.return_date, br.status
        FROM borrowing_records br
        JOIN students s ON br.student_id = s.student_id
        JOIN books b ON br.book_id = b.book_id
        ORDER BY br.borrowing_id DESC
        LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

# -----------------
# Dashboard Analytics Queries
# -----------------

def get_dashboard_stats(db_path: str = DEFAULT_DB_PATH) -> Dict[str, int]:
    """Calculate key library statistics directly via SQL."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM books;")
        total_books = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM authors;")
        total_authors = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM students;")
        total_students = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM books WHERE availability_status = 'Borrowed';")
        borrowed_books = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM books WHERE availability_status = 'Available';")
        available_books = cur.fetchone()["cnt"]

        # Overdue: active loans borrowed more than 14 days ago
        cutoff_date = (date.today() - timedelta(days=14)).isoformat()
        cur.execute("""
        SELECT COUNT(*) AS cnt FROM borrowing_records
        WHERE status = 'Borrowed' AND borrow_date < ?;
        """, (cutoff_date,))
        overdue_books = cur.fetchone()["cnt"]

        return {
            "total_books": total_books,
            "total_authors": total_authors,
            "total_students": total_students,
            "borrowed_books": borrowed_books,
            "available_books": available_books,
            "overdue_books": overdue_books
        }
    finally:
        conn.close()

def get_books_by_subject(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Count books per subject."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT subject, COUNT(*) AS count
        FROM books
        GROUP BY subject
        ORDER BY count DESC;
        """)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_books_by_department(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Count books per department."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT COALESCE(department, 'General') AS department, COUNT(*) AS count
        FROM books
        GROUP BY department
        ORDER BY count DESC;
        """)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_monthly_borrowing_activity(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Group borrowing activity by month."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT SUBSTR(borrow_date, 1, 7) AS month, COUNT(*) AS count
        FROM borrowing_records
        GROUP BY month
        ORDER BY month ASC;
        """)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_top_borrowed_books(limit: int = 5, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve top most-borrowed books across all time."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT b.title, COUNT(br.borrowing_id) AS borrow_count
        FROM books b
        JOIN borrowing_records br ON b.book_id = br.book_id
        GROUP BY b.book_id
        ORDER BY borrow_count DESC, b.title ASC
        LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_recent_added_books(limit: int = 5, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve the most recently added books."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT b.book_id, b.title, a.author_name, b.subject, b.availability_status
        FROM books b
        JOIN authors a ON b.author_id = a.author_id
        ORDER BY b.book_id DESC
        LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_recent_borrowings(limit: int = 5, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve the most recent borrowing transactions."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT br.borrowing_id, s.student_name, b.title AS book_title, br.borrow_date, br.status
        FROM borrowing_records br
        JOIN students s ON br.student_id = s.student_id
        JOIN books b ON br.book_id = b.book_id
        WHERE br.status = 'Borrowed'
        ORDER BY br.borrowing_id DESC
        LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

def get_recent_returns(limit: int = 5, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve the most recent return transactions."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT br.borrowing_id, s.student_name, b.title AS book_title, br.borrow_date, br.return_date
        FROM borrowing_records br
        JOIN students s ON br.student_id = s.student_id
        JOIN books b ON br.book_id = b.book_id
        WHERE br.status = 'Returned'
        ORDER BY br.borrowing_id DESC
        LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

# -----------------
# FOL Fact Synchronization
# -----------------

def clean_fol_constant(value: str) -> str:
    """Normalize strings into valid First-Order Logic constants."""
    clean = re.sub(r"[^A-Za-z0-9]+", "_", str(value).strip()).strip("_")
    if not clean:
        clean = "Unknown"
    if clean[0].islower():
        clean = clean[0].upper() + clean[1:]
    return clean

def load_fol_facts_from_db(db_path: str = DEFAULT_DB_PATH):
    """
    Read persistent SQLite database records and convert them into
    ground FOL Fact instances for the KnowledgeBase.
    Only original ground facts are produced. Inferred facts are not stored here.
    """
    # Import Fact inside function to avoid circular imports
    from knowledge_base import Fact

    facts = []
    seen = set()

    def add(pred: str, *args: str):
        c_args = tuple(clean_fol_constant(a) for a in args)
        f = Fact(pred, c_args)
        if f not in seen:
            seen.add(f)
            facts.append(f)

    conn = get_connection(db_path)
    try:
        cur = conn.cursor()

        # 1. Authors and specializations
        cur.execute("SELECT author_name, specialization FROM authors;")
        for row in cur.fetchall():
            a_name = row["author_name"]
            add("Author", a_name)
            if row["specialization"]:
                add("Subject", row["specialization"])
                add("SpecializesIn", a_name, row["specialization"])

        # 2. Books, Authorship, Subjects, and Departments
        cur.execute("""
        SELECT b.title, a.author_name, b.subject, b.department
        FROM books b
        JOIN authors a ON b.author_id = a.author_id;
        """)
        for row in cur.fetchall():
            title = row["title"]
            author = row["author_name"]
            subject = row["subject"]
            dept = row["department"]

            add("Book", title)
            add("Author", author)
            add("Subject", subject)
            add("WrittenBy", title, author)
            add("BelongsTo", title, subject)
            if dept:
                add("Department", dept)

        # 3. Students and Departments
        cur.execute("SELECT student_name, department FROM students;")
        for row in cur.fetchall():
            s_name = row["student_name"]
            dept = row["department"]
            add("Student", s_name)
            add("Department", dept)
            add("MemberOf", s_name, dept)

        # 4. Active Borrowing records (Borrowed)
        cur.execute("""
        SELECT s.student_name, b.title
        FROM borrowing_records br
        JOIN students s ON br.student_id = s.student_id
        JOIN books b ON br.book_id = b.book_id
        WHERE br.status = 'Borrowed';
        """)
        for row in cur.fetchall():
            add("Borrowed", row["student_name"], row["title"])

        return facts
    finally:
        conn.close()

