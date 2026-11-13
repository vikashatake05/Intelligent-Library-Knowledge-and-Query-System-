"""Automated test suite verifying all 12 scenarios required by the project specification.
Uses an isolated temporary SQLite database to test database CRUD, FOL synchronization,
unification, inference rules, and persistence across restarts.
"""
import os
import tempfile
import database
from knowledge_base import KnowledgeBase, Fact
from query_engine import process_query, answer_query
from inference_engine import run_forward_chaining

def run_all_tests():
    print("=" * 70)
    print("RUNNING COMPREHENSIVE INTELLIGENT LIBRARY FOL TEST SUITE")
    print("=" * 70)

    # Use a temporary database path for isolated end-to-end testing
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "test_library.db")

    try:
        # Step 0: Initialize database and seed sample data
        print("\n[Setup] Initializing database at:", test_db_path)
        database.init_db(db_path=test_db_path)

        kb = KnowledgeBase()
        kb.reload_from_db(db_path=test_db_path)

        initial_stats = database.get_dashboard_stats(db_path=test_db_path)
        print(f"Initial Stats: {initial_stats}")
        assert initial_stats["total_books"] == 15
        assert initial_stats["total_authors"] == 10
        assert initial_stats["total_students"] == 10
        assert initial_stats["borrowed_books"] == 4
        assert initial_stats["available_books"] == 11
        assert kb.count("Book") == 15
        assert kb.count("Available") == 11
        print("✓ Initial setup and seeding verified.")

        # Scenario 1: Add a new book and verify that it appears in SQLite and FOL KB
        print("\n[Scenario 1] Add a new book and verify in SQLite & FOL KB...")
        new_bid = database.add_book(
            title="Deep_Reinforcement_Learning",
            author_id=1,  # Russell
            subject="Artificial_Intelligence",
            department="Computer_Science",
            publication_year=2024,
            isbn="978-0999999901",
            db_path=test_db_path
        )
        assert new_bid is not None
        # Verify in SQLite
        b_row = database.get_book_by_id(new_bid, db_path=test_db_path)
        assert b_row["title"] == "Deep_Reinforcement_Learning"
        assert b_row["availability_status"] == "Available"

        # Resync KB
        kb.reload_from_db(db_path=test_db_path)
        assert kb.contains(Fact("Book", ("Deep_Reinforcement_Learning",)))
        assert kb.contains(Fact("WrittenBy", ("Deep_Reinforcement_Learning", "Russell")))
        assert kb.contains(Fact("BelongsTo", ("Deep_Reinforcement_Learning", "Artificial_Intelligence")))
        # It should be available via R4
        assert kb.contains(Fact("Available", ("Deep_Reinforcement_Learning",)))
        print("✓ Scenario 1 passed: New book added to SQLite and FOL KB.")

        # Scenario 2: Edit a book title and verify that old facts are removed and new facts are created
        print("\n[Scenario 2] Edit a book title and verify fact update...")
        database.update_book(
            book_id=new_bid,
            title="Advanced_Reinforcement_Learning",
            author_id=1,
            subject="Artificial_Intelligence",
            department="Computer_Science",
            publication_year=2025,
            isbn="978-0999999901",
            db_path=test_db_path
        )
        kb.reload_from_db(db_path=test_db_path)
        assert not kb.contains(Fact("Book", ("Deep_Reinforcement_Learning",)))
        assert kb.contains(Fact("Book", ("Advanced_Reinforcement_Learning",)))
        assert not kb.contains(Fact("WrittenBy", ("Deep_Reinforcement_Learning", "Russell")))
        assert kb.contains(Fact("WrittenBy", ("Advanced_Reinforcement_Learning", "Russell")))
        print("✓ Scenario 2 passed: Old facts removed, updated facts created.")

        # Scenario 3: Add an author and associate that author with a book
        print("\n[Scenario 3] Add an author and associate with a book...")
        new_aid = database.add_author("Sutton", "Artificial_Intelligence", db_path=test_db_path)
        assert new_aid is not None
        sutton_bid = database.add_book(
            title="Reinforcement_Learning_An_Introduction",
            author_id=new_aid,
            subject="Artificial_Intelligence",
            department="Computer_Science",
            publication_year=2020,
            isbn="978-0262039246",
            db_path=test_db_path
        )
        kb.reload_from_db(db_path=test_db_path)
        assert kb.contains(Fact("Author", ("Sutton",)))
        assert kb.contains(Fact("SpecializesIn", ("Sutton", "Artificial_Intelligence")))
        assert kb.contains(Fact("WrittenBy", ("Reinforcement_Learning_An_Introduction", "Sutton")))
        print("✓ Scenario 3 passed: Author added and associated with book in SQLite & KB.")

        # Scenario 4: Add a student
        print("\n[Scenario 4] Add a student...")
        new_sid = database.add_student("STU099", "Aditi", "Computer_Science", db_path=test_db_path)
        assert new_sid == "STU099"
        kb.reload_from_db(db_path=test_db_path)
        assert kb.contains(Fact("Student", ("Aditi",)))
        assert kb.contains(Fact("MemberOf", ("Aditi", "Computer_Science")))
        print("✓ Scenario 4 passed: Student added and asserted in KB.")

        # Scenario 5: Record a borrowing transaction
        print("\n[Scenario 5] Record a borrowing transaction...")
        loan_id = database.record_borrowing(
            student_id="STU099",
            book_id=sutton_bid,
            borrow_date="2026-11-13",
            db_path=test_db_path
        )
        assert loan_id is not None
        kb.reload_from_db(db_path=test_db_path)
        assert kb.contains(Fact("Borrowed", ("Aditi", "Reinforcement_Learning_An_Introduction")))
        assert kb.contains(Fact("LibraryUser", ("Aditi",)))  # Inferred via Rule R1!
        assert kb.contains(Fact("HasBorrowed", ("Aditi", "Reinforcement_Learning_An_Introduction")))  # Inferred via Rule R3!
        print("✓ Scenario 5 passed: Borrowing transaction recorded; R1 & R3 derived.")

        # Scenario 6: Verify that the book becomes unavailable
        print("\n[Scenario 6] Verify book becomes unavailable...")
        b_after_borrow = database.get_book_by_id(sutton_bid, db_path=test_db_path)
        assert b_after_borrow["availability_status"] == "Borrowed"
        # In FOL KB, Available(Reinforcement_Learning_An_Introduction) must NOT be present (Rule R4)
        assert not kb.contains(Fact("Available", ("Reinforcement_Learning_An_Introduction",)))
        avail_q = process_query("Available(Reinforcement_Learning_An_Introduction)", kb)
        assert avail_q["truth"] is False
        print("✓ Scenario 6 passed: Book is unavailable in DB and FOL negated availability holds.")

        # Scenario 7: Return the book
        print("\n[Scenario 7] Return the book...")
        ret_ok = database.record_return(loan_id, return_date="2026-11-13", db_path=test_db_path)
        assert ret_ok is True
        print("✓ Scenario 7 passed: Return transaction recorded.")

        # Scenario 8: Verify that the book becomes available
        print("\n[Scenario 8] Verify book becomes available...")
        b_after_return = database.get_book_by_id(sutton_bid, db_path=test_db_path)
        assert b_after_return["availability_status"] == "Available"
        kb.reload_from_db(db_path=test_db_path)
        assert not kb.contains(Fact("Borrowed", ("Aditi", "Reinforcement_Learning_An_Introduction")))
        assert kb.contains(Fact("Available", ("Reinforcement_Learning_An_Introduction",)))
        avail_q2 = process_query("Available(Reinforcement_Learning_An_Introduction)", kb)
        assert avail_q2["truth"] is True
        print("✓ Scenario 8 passed: Book availability restored in DB and derived via R4.")

        # Scenario 9: Delete a book and verify that related facts are handled safely
        print("\n[Scenario 9] Delete a book and verify fact cleanup...")
        del_ok = database.delete_book(new_bid, db_path=test_db_path)
        assert del_ok is True
        kb.reload_from_db(db_path=test_db_path)
        assert not kb.contains(Fact("Book", ("Advanced_Reinforcement_Learning",)))
        assert not kb.contains(Fact("WrittenBy", ("Advanced_Reinforcement_Learning", "Russell")))
        assert not kb.contains(Fact("BelongsTo", ("Advanced_Reinforcement_Learning", "Artificial_Intelligence")))
        print("✓ Scenario 9 passed: Book deleted safely; all related facts cleanly removed.")

        # Scenario 10: Enter query in Intelligent Query and verify result from actual KB
        print("\n[Scenario 10] Intelligent Query execution against real KB...")
        # 10.1: Natural language query by author
        q1 = process_query("Find books written by Sutton", kb)
        assert q1["success"] is True
        assert q1["truth"] is True
        assert any("Reinforcement_Learning_An_Introduction" in m.get("b", "") for m in q1["matches"])

        # 10.2: Natural language query by subject
        q2 = process_query("Find books related to Artificial Intelligence", kb)
        assert q2["success"] is True
        assert q2["truth"] is True
        assert len(q2["matches"]) >= 3

        # 10.3: Ground check
        q3 = process_query("Available(Reinforcement_Learning_An_Introduction)", kb)
        assert q3["success"] is True
        assert q3["truth"] is True
        assert len(q3["inferred_facts"]) > 0  # Derived via R4!
        print("✓ Scenario 10 passed: Intelligent Query executes against genuine KB.")

        # Scenario 11: Verify dashboard statistics change after changes
        print("\n[Scenario 11] Verify dashboard statistics dynamically reflect changes...")
        mid_stats = database.get_dashboard_stats(db_path=test_db_path)
        # We added 1 author (Sutton), 1 book (Sutton's book kept, other deleted), etc.
        assert mid_stats["total_books"] == 16
        assert mid_stats["total_authors"] == 11
        assert mid_stats["total_students"] == 11
        assert mid_stats["borrowed_books"] == 4
        assert mid_stats["available_books"] == 12

        # Borrow another book
        cur_loan = database.record_borrowing("STU099", sutton_bid, "2026-11-13", db_path=test_db_path)
        stats_after_borrow = database.get_dashboard_stats(db_path=test_db_path)
        assert stats_after_borrow["borrowed_books"] == 5
        assert stats_after_borrow["available_books"] == 11

        database.record_return(cur_loan, "2026-11-13", db_path=test_db_path)
        stats_after_ret = database.get_dashboard_stats(db_path=test_db_path)
        assert stats_after_ret["borrowed_books"] == 4
        assert stats_after_ret["available_books"] == 12
        print("✓ Scenario 11 passed: Dashboard statistics are 100% dynamic from SQL.")

        # Scenario 12: Restart application simulation and verify persistence
        print("\n[Scenario 12] Restart simulation: verify SQLite data persists...")
        # Simulate restart by instantiating completely fresh KnowledgeBase from the database file
        fresh_kb = KnowledgeBase()
        fresh_kb.reload_from_db(db_path=test_db_path)
        persisted_stats = database.get_dashboard_stats(db_path=test_db_path)

        assert persisted_stats["total_books"] == 16
        assert persisted_stats["total_authors"] == 11
        assert persisted_stats["total_students"] == 11
        assert fresh_kb.contains(Fact("Author", ("Sutton",)))
        assert fresh_kb.contains(Fact("Book", ("Reinforcement_Learning_An_Introduction",)))
        assert fresh_kb.contains(Fact("Student", ("Aditi",)))
        print("✓ Scenario 12 passed: All changes persist in SQLite across fresh sessions.")

        print("\n" + "=" * 70)
        print("ALL 12 TESTING SCENARIOS PASSED WITH ZERO ERRORS!")
        print("=" * 70)

    finally:
        # Cleanup temp directory
        try:
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
            os.rmdir(temp_dir)
        except Exception:
            pass

if __name__ == "__main__":
    run_all_tests()

