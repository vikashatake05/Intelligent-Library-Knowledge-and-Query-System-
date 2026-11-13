"""Library Management workbench for Intelligent Library FOL System.
Provides persistent CRUD operations for Books, Authors, Students, and Circulation Loans
with automated First-Order Logic synchronization, following the Unslop methodology.
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime
import database
from ui_components import render_page_header

def sync_kb(kb):
    """Synchronize the FOL knowledge base with the persistent SQLite database."""
    kb.reload_from_db()
    st.session_state["kb_version"] = st.session_state.get("kb_version", 0) + 1

def render_library_management(kb):
    render_page_header(
        title="Library Catalog & Circulation Workbench",
        subtitle="Manage persistent relational records for books, authors, students, and circulation transactions. Modifications immediately update SQLite and synchronize First-Order Logic ground facts.",
        tag="Catalog Management"
    )

    tab_books, tab_authors, tab_students, tab_loans = st.tabs([
        "Books Catalog",
        "Authors Directory",
        "Students Directory",
        "Circulation & Loans"
    ])

    # ---------------------------------------------------------
    # TAB 1: BOOKS
    # ---------------------------------------------------------
    with tab_books:
        b_subtab_view, b_subtab_add, b_subtab_edit, b_subtab_del = st.tabs([
            "Catalog Search & Filter",
            "Register Book",
            "Update Book Details",
            "Remove Book"
        ])

        with b_subtab_view:
            f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 1, 1])

            authors_list = database.get_all_authors()
            all_subjects = sorted(list({b["subject"] for b in database.get_all_books()}))
            all_depts = sorted(list({b["department"] for b in database.get_all_books() if b["department"]}))

            with f_col1:
                search_term = st.text_input("Search catalog", placeholder="Filter by Title, Author, or ISBN...", key="book_search_input")
            with f_col2:
                sel_subject = st.selectbox("Subject", ["All"] + all_subjects, key="book_filter_subject")
            with f_col3:
                sel_dept = st.selectbox("Department", ["All"] + all_depts, key="book_filter_dept")
            with f_col4:
                sel_avail = st.selectbox("Status", ["All", "Available", "Borrowed"], key="book_filter_avail")

            books = database.get_all_books(
                search=search_term,
                subject=sel_subject,
                department=sel_dept,
                availability=sel_avail
            )

            if books:
                df_books = pd.DataFrame(books)
                df_books["title"] = df_books["title"].str.replace("_", " ")
                df_books["author_name"] = df_books["author_name"].str.replace("_", " ")
                df_books["subject"] = df_books["subject"].str.replace("_", " ")
                df_books["department"] = df_books["department"].fillna("General").str.replace("_", " ")

                df_display = df_books.rename(columns={
                    "book_id": "Catalog ID", "title": "Title", "author_name": "Author",
                    "subject": "Subject", "department": "Department",
                    "publication_year": "Year", "isbn": "ISBN",
                    "availability_status": "Status"
                })[["Catalog ID", "Title", "Author", "Subject", "Department", "Year", "ISBN", "Status"]]

                st.dataframe(df_display, use_container_width=True, hide_index=True)
                st.caption(f"Displaying {len(books)} catalog record(s).")
            else:
                st.info("No books match the specified search parameters.")

        with b_subtab_add:
            if not authors_list:
                st.warning("Please register at least one author before creating a book.")
            else:
                with st.form("form_add_book"):
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        new_title = st.text_input("Book Title *")
                        author_options = {a["author_name"]: a["author_id"] for a in authors_list}
                        sel_author_name = st.selectbox("Author *", list(author_options.keys()))
                        new_subject = st.text_input("Subject *", value="Artificial_Intelligence")
                    with col_b2:
                        new_dept = st.text_input("Department", value="Computer_Science")
                        new_year = st.number_input("Publication Year", min_value=1900, max_value=2030, value=2023, step=1)
                        new_isbn = st.text_input("ISBN (Unique) *", placeholder="e.g. 978-0131103627")

                    submit_add_book = st.form_submit_button("Add Book to Catalog", type="primary")

                if submit_add_book:
                    try:
                        aid = author_options[sel_author_name]
                        clean_title = new_title.strip().replace(" ", "_")
                        clean_subj = new_subject.strip().replace(" ", "_")
                        clean_dep = new_dept.strip().replace(" ", "_") if new_dept.strip() else None

                        new_id = database.add_book(
                            title=clean_title,
                            author_id=aid,
                            subject=clean_subj,
                            department=clean_dep,
                            publication_year=int(new_year),
                            isbn=new_isbn.strip()
                        )
                        sync_kb(kb)
                        st.success(f"Successfully cataloged '{new_title}' (ID: {new_id}). First-Order Logic facts synchronized.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to add book: {exc}")

        with b_subtab_edit:
            all_b = database.get_all_books()
            if not all_b:
                st.info("No books in catalog to edit.")
            else:
                book_choices = {f"{b['title'].replace('_', ' ')} (ISBN: {b['isbn']})": b for b in all_b}
                sel_b_label = st.selectbox("Select Book to Update", list(book_choices.keys()), key="edit_book_selector")
                target_book = book_choices[sel_b_label]

                with st.form("form_edit_book"):
                    col_eb1, col_eb2 = st.columns(2)
                    with col_eb1:
                        edit_title = st.text_input("Title", value=target_book["title"].replace("_", " "))
                        author_names = [a["author_name"] for a in authors_list]
                        current_auth_idx = author_names.index(target_book["author_name"]) if target_book["author_name"] in author_names else 0
                        edit_author_name = st.selectbox("Author", author_names, index=current_auth_idx)
                        edit_subject = st.text_input("Subject", value=target_book["subject"].replace("_", " "))
                    with col_eb2:
                        edit_dept = st.text_input("Department", value=(target_book["department"] or "General").replace("_", " "))
                        edit_year = st.number_input("Publication Year", min_value=1900, max_value=2030,
                                                    value=int(target_book["publication_year"] or 2022), step=1)
                        edit_isbn = st.text_input("ISBN", value=target_book["isbn"])

                    submit_edit_book = st.form_submit_button("Save Changes", type="primary")

                if submit_edit_book:
                    try:
                        author_map = {a["author_name"]: a["author_id"] for a in authors_list}
                        aid = author_map[edit_author_name]
                        clean_t = edit_title.strip().replace(" ", "_")
                        clean_s = edit_subject.strip().replace(" ", "_")
                        clean_d = edit_dept.strip().replace(" ", "_") if edit_dept.strip() else None

                        database.update_book(
                            book_id=target_book["book_id"],
                            title=clean_t,
                            author_id=aid,
                            subject=clean_s,
                            department=clean_d,
                            publication_year=int(edit_year),
                            isbn=edit_isbn.strip()
                        )
                        sync_kb(kb)
                        st.success(f"Book '{edit_title}' successfully updated. Knowledge base facts recalculated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to update book: {exc}")

        with b_subtab_del:
            all_b_del = database.get_all_books()
            if not all_b_del:
                st.info("No books available to delete.")
            else:
                del_choices = {f"{b['title'].replace('_', ' ')} (Status: {b['availability_status']})": b for b in all_b_del}
                sel_del_label = st.selectbox("Select Book to Remove", list(del_choices.keys()), key="del_book_selector")
                book_to_del = del_choices[sel_del_label]

                if book_to_del["availability_status"] == "Borrowed":
                    st.warning("Integrity restriction: This book is currently borrowed. Complete the active return before removing.")
                else:
                    st.write(f"Confirm removal of **{book_to_del['title'].replace('_', ' ')}** (ISBN: {book_to_del['isbn']}).")
                    if st.button("Confirm Removal", type="secondary"):
                        try:
                            database.delete_book(book_to_del["book_id"])
                            sync_kb(kb)
                            st.success(f"Book '{book_to_del['title'].replace('_', ' ')}' removed. Related knowledge base facts cleared.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Cannot remove book: {exc}")

    # ---------------------------------------------------------
    # TAB 2: AUTHORS
    # ---------------------------------------------------------
    with tab_authors:
        a_tab_view, a_tab_add, a_tab_edit, a_tab_del = st.tabs([
            "Author Directory",
            "Register Author",
            "Update Author Details",
            "Remove Author"
        ])

        with a_tab_view:
            authors = database.get_all_authors()
            if authors:
                df_a = pd.DataFrame(authors)
                df_a["author_name"] = df_a["author_name"].str.replace("_", " ")
                df_a["specialization"] = df_a["specialization"].fillna("-").str.replace("_", " ")
                df_a = df_a.rename(columns={
                    "author_id": "Author ID", "author_name": "Author Name",
                    "specialization": "Specialization", "book_count": "Catalog Titles"
                })
                st.dataframe(df_a, use_container_width=True, hide_index=True)
            else:
                st.info("No authors registered in directory.")

        with a_tab_add:
            with st.form("form_add_author"):
                a_name = st.text_input("Author Name *")
                a_spec = st.text_input("Research Specialization (optional)", placeholder="e.g. Artificial_Intelligence")
                submit_add_author = st.form_submit_button("Register Author", type="primary")

            if submit_add_author:
                try:
                    clean_a_name = a_name.strip().replace(" ", "_")
                    clean_a_spec = a_spec.strip().replace(" ", "_") if a_spec.strip() else None
                    new_aid = database.add_author(clean_a_name, clean_a_spec)
                    sync_kb(kb)
                    st.success(f"Author '{a_name}' registered successfully (ID: {new_aid}).")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to register author: {exc}")

        with a_tab_edit:
            authors_for_edit = database.get_all_authors()
            if authors_for_edit:
                a_choices = {a["author_name"].replace("_", " "): a for a in authors_for_edit}
                sel_a_label = st.selectbox("Select Author to Edit", list(a_choices.keys()), key="edit_author_selector")
                target_a = a_choices[sel_a_label]

                with st.form("form_edit_author"):
                    edit_a_name = st.text_input("Author Name", value=target_a["author_name"].replace("_", " "))
                    edit_a_spec = st.text_input("Specialization", value=(target_a["specialization"] or "").replace("_", " "))
                    submit_edit_author = st.form_submit_button("Save Author Changes", type="primary")

                if submit_edit_author:
                    try:
                        clean_an = edit_a_name.strip().replace(" ", "_")
                        clean_as = edit_a_spec.strip().replace(" ", "_") if edit_a_spec.strip() else None
                        database.update_author(target_a["author_id"], clean_an, clean_as)
                        sync_kb(kb)
                        st.success(f"Author '{edit_a_name}' updated successfully.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to update author: {exc}")
            else:
                st.info("No authors available to update.")

        with a_tab_del:
            authors_for_del = database.get_all_authors()
            if authors_for_del:
                a_del_choices = {f"{a['author_name'].replace('_', ' ')} ({a['book_count']} books)": a for a in authors_for_del}
                sel_del_a = st.selectbox("Select Author to Remove", list(a_del_choices.keys()), key="del_author_selector")
                target_del_a = a_del_choices[sel_del_a]

                if target_del_a["book_count"] > 0:
                    st.warning(f"Integrity restriction: Cannot remove '{target_del_a['author_name']}'. There are {target_del_a['book_count']} catalog book(s) associated with this author.")
                else:
                    st.write(f"Confirm removal of author **{target_del_a['author_name']}**.")
                    if st.button("Confirm Author Removal", type="secondary"):
                        try:
                            database.delete_author(target_del_a["author_id"])
                            sync_kb(kb)
                            st.success(f"Author '{target_del_a['author_name']}' removed.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Error removing author: {exc}")

    # ---------------------------------------------------------
    # TAB 3: STUDENTS
    # ---------------------------------------------------------
    with tab_students:
        s_tab_view, s_tab_add, s_tab_edit, s_tab_del = st.tabs([
            "Student Directory",
            "Register Student",
            "Update Student Details",
            "Remove Student"
        ])

        with s_tab_view:
            students = database.get_all_students()
            if students:
                df_s = pd.DataFrame(students)
                df_s["student_name"] = df_s["student_name"].str.replace("_", " ")
                df_s["department"] = df_s["department"].str.replace("_", " ")
                df_s = df_s.rename(columns={
                    "student_id": "Student ID", "student_name": "Full Name",
                    "department": "Department", "active_loans_count": "Active Loans"
                })
                st.dataframe(df_s, use_container_width=True, hide_index=True)
            else:
                st.info("No students enrolled in directory.")

        with s_tab_add:
            with st.form("form_add_student"):
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    new_sid = st.text_input("Student ID (Unique) *", placeholder="e.g. STU011")
                    new_sname = st.text_input("Full Name *")
                with col_s2:
                    new_sdept = st.text_input("Department *", value="Computer_Science")
                submit_add_s = st.form_submit_button("Register Student", type="primary")

            if submit_add_s:
                try:
                    clean_sid = new_sid.strip().upper()
                    clean_sname = new_sname.strip().replace(" ", "_")
                    clean_sdept = new_sdept.strip().replace(" ", "_")
                    database.add_student(clean_sid, clean_sname, clean_sdept)
                    sync_kb(kb)
                    st.success(f"Student '{new_sname}' ({clean_sid}) registered.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to register student: {exc}")

        with s_tab_edit:
            students_list = database.get_all_students()
            if students_list:
                s_choices = {f"{s['student_name'].replace('_', ' ')} ({s['student_id']})": s for s in students_list}
                sel_s_label = st.selectbox("Select Student to Update", list(s_choices.keys()), key="edit_student_selector")
                target_s = s_choices[sel_s_label]

                with st.form("form_edit_student"):
                    edit_sname = st.text_input("Full Name", value=target_s["student_name"].replace("_", " "))
                    edit_sdept = st.text_input("Department", value=target_s["department"].replace("_", " "))
                    submit_edit_s = st.form_submit_button("Save Student Details", type="primary")

                if submit_edit_s:
                    try:
                        clean_sn = edit_sname.strip().replace(" ", "_")
                        clean_sd = edit_sdept.strip().replace(" ", "_")
                        database.update_student(target_s["student_id"], clean_sn, clean_sd)
                        sync_kb(kb)
                        st.success(f"Student {target_s['student_id']} updated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to update student: {exc}")
            else:
                st.info("No students available to update.")

        with s_tab_del:
            if students_list:
                s_del_choices = {f"{s['student_name'].replace('_', ' ')} ({s['student_id']}) - {s['active_loans_count']} active loans": s for s in students_list}
                sel_del_s = st.selectbox("Select Student to Remove", list(s_del_choices.keys()), key="del_student_selector")
                target_del_s = s_del_choices[sel_del_s]

                if target_del_s["active_loans_count"] > 0:
                    st.warning(f"Integrity restriction: Cannot remove '{target_del_s['student_name']}'. This student currently has {target_del_s['active_loans_count']} active loan(s).")
                else:
                    st.write(f"Confirm removal of student **{target_del_s['student_name']}** ({target_del_s['student_id']}).")
                    if st.button("Confirm Student Removal", type="secondary"):
                        try:
                            database.delete_student(target_del_s["student_id"])
                            sync_kb(kb)
                            st.success(f"Student {target_del_s['student_name']} removed.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Failed to remove student: {exc}")

    # ---------------------------------------------------------
    # TAB 4: CIRCULATION & LOANS
    # ---------------------------------------------------------
    with tab_loans:
        l_tab_borrow, l_tab_return, l_tab_active, l_tab_history, l_tab_edit = st.tabs([
            "Issue Loan",
            "Process Return",
            "Active Circulation",
            "Circulation History",
            "Edit Loan Record"
        ])

        with l_tab_borrow:
            students_pool = database.get_all_students()
            available_books = database.get_all_books(availability="Available")

            if not students_pool:
                st.warning("No enrolled students found. Register a student before issuing a loan.")
            elif not available_books:
                st.warning("No catalog books are currently available for circulation.")
            else:
                with st.form("form_record_borrow"):
                    s_options = {f"{s['student_name'].replace('_', ' ')} ({s['student_id']})": s["student_id"] for s in students_pool}
                    b_options = {f"{b['title'].replace('_', ' ')} (ISBN: {b['isbn']})": b["book_id"] for b in available_books}

                    sel_s = st.selectbox("Student Borrower *", list(s_options.keys()))
                    sel_b = st.selectbox("Available Book *", list(b_options.keys()))
                    b_date = st.date_input("Circulation Date *", value=date.today())

                    submit_loan = st.form_submit_button("Issue Loan", type="primary")

                if submit_loan:
                    try:
                        chosen_sid = s_options[sel_s]
                        chosen_bid = b_options[sel_b]
                        rec_id = database.record_borrowing(
                            student_id=chosen_sid,
                            book_id=chosen_bid,
                            borrow_date=b_date.isoformat()
                        )
                        sync_kb(kb)
                        st.success(f"Loan #{rec_id} issued successfully. Book status updated to 'Borrowed' and asserted in First-Order Logic.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to record loan: {exc}")

        with l_tab_return:
            active_loans = database.get_active_loans()
            if not active_loans:
                st.info("No active circulation loans. All registered books are available.")
            else:
                with st.form("form_record_return"):
                    loan_options = {
                        f"Loan #{l['borrowing_id']} · {l['student_name'].replace('_', ' ')} borrowed '{l['book_title'].replace('_', ' ')}' on {l['borrow_date']}": l["borrowing_id"]
                        for l in active_loans
                    }
                    sel_loan = st.selectbox("Active Loan *", list(loan_options.keys()))
                    ret_date = st.date_input("Return Date *", value=date.today())
                    submit_return = st.form_submit_button("Record Return", type="primary")

                if submit_return:
                    try:
                        chosen_lid = loan_options[sel_loan]
                        database.record_return(chosen_lid, return_date=ret_date.isoformat())
                        sync_kb(kb)
                        st.success("Book returned. Availability restored and derived via Rule R4 (Closed-World Negation).")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to record return: {exc}")

        with l_tab_active:
            active_loans = database.get_active_loans()
            if active_loans:
                df_act = pd.DataFrame(active_loans)
                df_act["student_name"] = df_act["student_name"].str.replace("_", " ")
                df_act["book_title"] = df_act["book_title"].str.replace("_", " ")
                df_act["status_label"] = df_act["is_overdue"].map({True: "Overdue (>14d)", False: "Active"})

                df_act_display = df_act.rename(columns={
                    "borrowing_id": "Loan ID", "student_name": "Borrower",
                    "student_id": "Student ID", "book_title": "Book Title",
                    "isbn": "ISBN", "borrow_date": "Borrow Date",
                    "days_borrowed": "Days Out", "status_label": "Loan Status"
                })[["Loan ID", "Student ID", "Borrower", "Book Title", "ISBN", "Borrow Date", "Days Out", "Loan Status"]]

                st.dataframe(df_act_display, use_container_width=True, hide_index=True)
            else:
                st.info("No active circulation loans at this time.")

        with l_tab_history:
            history = database.get_borrowing_history(limit=100)
            if history:
                df_hist = pd.DataFrame(history)
                df_hist["student_name"] = df_hist["student_name"].str.replace("_", " ")
                df_hist["book_title"] = df_hist["book_title"].str.replace("_", " ")
                df_hist["return_date"] = df_hist["return_date"].fillna("-")

                df_hist_display = df_hist.rename(columns={
                    "borrowing_id": "Loan ID", "student_id": "Student ID",
                    "student_name": "Borrower", "book_title": "Book Title",
                    "isbn": "ISBN", "borrow_date": "Borrow Date",
                    "return_date": "Return Date", "status": "Circulation Status"
                })[["Loan ID", "Student ID", "Borrower", "Book Title", "ISBN", "Borrow Date", "Return Date", "Circulation Status"]]

                st.dataframe(df_hist_display, use_container_width=True, hide_index=True)
            else:
                st.info("No historical circulation records found.")

        with l_tab_edit:
            history_for_edit = database.get_borrowing_history(limit=50)
            if history_for_edit:
                loan_edit_choices = {
                    f"Loan #{l['borrowing_id']} · {l['student_name'].replace('_', ' ')} - '{l['book_title'].replace('_', ' ')}' ({l['status']})": l
                    for l in history_for_edit
                }
                sel_edit_l_label = st.selectbox("Select Loan Record to Edit", list(loan_edit_choices.keys()), key="modify_loan_selector")
                target_l = loan_edit_choices[sel_edit_l_label]

                with st.form("form_edit_loan"):
                    students_pool = database.get_all_students()
                    s_id_list = [s["student_id"] for s in students_pool]
                    curr_s_idx = s_id_list.index(target_l["student_id"]) if target_l["student_id"] in s_id_list else 0
                    edit_lid_student = st.selectbox(
                        "Borrower Student",
                        s_id_list,
                        format_func=lambda sid: f"{next((s['student_name'].replace('_', ' ') for s in students_pool if s['student_id'] == sid), sid)} ({sid})",
                        index=curr_s_idx
                    )

                    try:
                        curr_bdate = datetime.strptime(target_l["borrow_date"], "%Y-%m-%d").date()
                    except Exception:
                        curr_bdate = date.today()
                    edit_bdate = st.date_input("Borrow Date", value=curr_bdate)

                    has_rdate = bool(target_l["return_date"])
                    if has_rdate:
                        try:
                            curr_rdate = datetime.strptime(target_l["return_date"], "%Y-%m-%d").date()
                        except Exception:
                            curr_rdate = date.today()
                        edit_rdate = st.date_input("Return Date", value=curr_rdate)
                        final_rdate = edit_rdate.isoformat()
                    else:
                        st.caption("Active loan: Return date is unrecorded.")
                        final_rdate = None

                    submit_edit_loan = st.form_submit_button("Save Loan Changes", type="primary")

                if submit_edit_loan:
                    try:
                        database.update_borrowing_record(
                            borrowing_id=target_l["borrowing_id"],
                            student_id=edit_lid_student,
                            borrow_date=edit_bdate.isoformat(),
                            return_date=final_rdate
                        )
                        sync_kb(kb)
                        st.success(f"Loan record #{target_l['borrowing_id']} updated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to update loan record: {exc}")
