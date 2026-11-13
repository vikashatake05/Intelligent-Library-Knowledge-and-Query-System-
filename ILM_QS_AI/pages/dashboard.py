"""Dashboard page for Intelligent Library Knowledge and Query System.
Presents persistent live statistics from SQLite, hierarchical analytical charts,
and recent operational activity following the Unslop design methodology.
"""
import streamlit as st
import pandas as pd
import altair as alt
import database
from ui_components import render_page_header, apply_altair_unslop_theme

def render_dashboard():
    # Clean academic page header (no emojis)
    render_page_header(
        title="Library Catalog & Circulation Analytics",
        subtitle="Real-time catalog distribution, active circulation loans, and longitudinal borrowing trends backed by persistent SQLite storage.",
        tag="Dashboard"
    )

    # 1. Fetch live metrics directly from SQLite
    stats = database.get_dashboard_stats()

    if stats["total_books"] == 0:
        st.info("The library database is currently empty. Use the Library Management workbench to register books, authors, and students.")
        return

    # 2. Responsive, Rhythmic Metric Grid (3 + 3 layout)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Catalog Books", value=stats["total_books"])
    with col2:
        st.metric(label="Available for Loan", value=stats["available_books"])
    with col3:
        st.metric(label="Currently Borrowed", value=stats["borrowed_books"])

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric(
            label="Overdue Loans (>14 Days)",
            value=stats["overdue_books"],
            delta=f"{stats['overdue_books']} overdue" if stats["overdue_books"] > 0 else "0 overdue",
            delta_color="inverse"
        )
    with col5:
        st.metric(label="Registered Authors", value=stats["total_authors"])
    with col6:
        st.metric(label="Enrolled Students", value=stats["total_students"])

    # 3. Data Visualizations with Clear Hierarchy
    st.markdown("### Catalog & Circulation Distribution")

    # Main Row: Dominant Chart (Monthly Borrowing Activity) + Secondary Chart (Subject Distribution)
    row1_c1, row1_c2 = st.columns([1.5, 1])

    with row1_c1:
        st.markdown("<div style='font-size: 0.9rem; font-weight: 500; color: var(--text-primary); margin-bottom: 8px;'>Monthly Circulation Volume</div>", unsafe_allow_html=True)
        monthly_data = database.get_monthly_borrowing_activity()
        if monthly_data:
            df_month = pd.DataFrame(monthly_data)
            line_chart = alt.Chart(df_month).mark_line(
                point=alt.OverlayMarkDef(color="#3b82f6", size=48, fill="#181c24"),
                color="#3b82f6",
                strokeWidth=2
            ).encode(
                x=alt.X("month:N", title="Month (YYYY-MM)", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("count:Q", title="Transactions", axis=alt.Axis(tickMinStep=1)),
                tooltip=[
                    alt.Tooltip("month:N", title="Month"),
                    alt.Tooltip("count:Q", title="Borrowing Count")
                ]
            ).properties(height=260)
            st.altair_chart(apply_altair_unslop_theme(line_chart), use_container_width=True)
        else:
            st.caption("No monthly transaction records available.")

    with row1_c2:
        st.markdown("<div style='font-size: 0.9rem; font-weight: 500; color: var(--text-primary); margin-bottom: 8px;'>Books by Academic Subject</div>", unsafe_allow_html=True)
        subject_data = database.get_books_by_subject()
        if subject_data:
            df_subj = pd.DataFrame(subject_data)
            df_subj["subject_clean"] = df_subj["subject"].str.replace("_", " ")
            subj_chart = alt.Chart(df_subj).mark_bar(
                cornerRadiusTopRight=4,
                cornerRadiusBottomRight=4,
                color="#3b82f6"
            ).encode(
                y=alt.Y("subject_clean:N", title=None, sort="-x"),
                x=alt.X("count:Q", title="Titles", axis=alt.Axis(tickMinStep=1)),
                tooltip=[
                    alt.Tooltip("subject_clean:N", title="Subject"),
                    alt.Tooltip("count:Q", title="Titles")
                ]
            ).properties(height=260)
            st.altair_chart(apply_altair_unslop_theme(subj_chart), use_container_width=True)
        else:
            st.caption("No subject data available.")

    # Secondary Visualizations Row: Top Borrowed Titles + Department Breakdown + Availability
    row2_c1, row2_c2 = st.columns([1.2, 1])

    with row2_c1:
        st.markdown("<div style='font-size: 0.9rem; font-weight: 500; color: var(--text-primary); margin-bottom: 8px;'>Most Frequently Circulated Books</div>", unsafe_allow_html=True)
        top_data = database.get_top_borrowed_books(limit=5)
        if top_data:
            df_top = pd.DataFrame(top_data)
            df_top["title_clean"] = df_top["title"].str.replace("_", " ")
            top_chart = alt.Chart(df_top).mark_bar(
                cornerRadiusTopRight=4,
                cornerRadiusBottomRight=4,
                color="#2563eb"
            ).encode(
                y=alt.Y("title_clean:N", sort="-x", title=None),
                x=alt.X("borrow_count:Q", title="Total Loans", axis=alt.Axis(tickMinStep=1)),
                tooltip=[
                    alt.Tooltip("title_clean:N", title="Title"),
                    alt.Tooltip("borrow_count:Q", title="Total Loans")
                ]
            ).properties(height=220)
            st.altair_chart(apply_altair_unslop_theme(top_chart), use_container_width=True)
        else:
            st.caption("No circulation history records.")

    with row2_c2:
        st.markdown("<div style='font-size: 0.9rem; font-weight: 500; color: var(--text-primary); margin-bottom: 8px;'>Department Classification</div>", unsafe_allow_html=True)
        dept_data = database.get_books_by_department()
        if dept_data:
            df_dept = pd.DataFrame(dept_data)
            df_dept["dept_clean"] = df_dept["department"].str.replace("_", " ")
            dept_chart = alt.Chart(df_dept).mark_bar(
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4,
                color="#475569"
            ).encode(
                x=alt.X("dept_clean:N", title=None, axis=alt.Axis(labelAngle=-25)),
                y=alt.Y("count:Q", title="Titles", axis=alt.Axis(tickMinStep=1)),
                tooltip=[
                    alt.Tooltip("dept_clean:N", title="Department"),
                    alt.Tooltip("count:Q", title="Titles")
                ]
            ).properties(height=220)
            st.altair_chart(apply_altair_unslop_theme(dept_chart), use_container_width=True)
        else:
            st.caption("No department data available.")

    # 4. Recent Circulation Activity (Clean tabs, no emojis)
    st.markdown("### Operational Activity Log")

    tab_added, tab_borrowed, tab_returned = st.tabs([
        "Recently Cataloged Books",
        "Active Circulation Loans",
        "Completed Returns"
    ])

    with tab_added:
        recent_books = database.get_recent_added_books(limit=5)
        if recent_books:
            df_rb = pd.DataFrame(recent_books)
            df_rb["title"] = df_rb["title"].str.replace("_", " ")
            df_rb["author_name"] = df_rb["author_name"].str.replace("_", " ")
            df_rb["subject"] = df_rb["subject"].str.replace("_", " ")
            df_rb = df_rb.rename(columns={
                "book_id": "Catalog ID", "title": "Title", "author_name": "Author",
                "subject": "Subject", "availability_status": "Availability"
            })
            st.dataframe(df_rb, use_container_width=True, hide_index=True)
        else:
            st.info("No books have been recorded in the catalog.")

    with tab_borrowed:
        recent_loans = database.get_recent_borrowings(limit=5)
        if recent_loans:
            df_rl = pd.DataFrame(recent_loans)
            df_rl["student_name"] = df_rl["student_name"].str.replace("_", " ")
            df_rl["book_title"] = df_rl["book_title"].str.replace("_", " ")
            df_rl = df_rl.rename(columns={
                "borrowing_id": "Loan ID", "student_name": "Student Borrower",
                "book_title": "Book Title", "borrow_date": "Borrow Date", "status": "Circulation Status"
            })
            st.dataframe(df_rl, use_container_width=True, hide_index=True)
        else:
            st.info("No active circulation loans recorded.")

    with tab_returned:
        recent_returns = database.get_recent_returns(limit=5)
        if recent_returns:
            df_rr = pd.DataFrame(recent_returns)
            df_rr["student_name"] = df_rr["student_name"].str.replace("_", " ")
            df_rr["book_title"] = df_rr["book_title"].str.replace("_", " ")
            df_rr = df_rr.rename(columns={
                "borrowing_id": "Loan ID", "student_name": "Student",
                "book_title": "Book Title", "borrow_date": "Borrow Date", "return_date": "Return Date"
            })
            st.dataframe(df_rr, use_container_width=True, hide_index=True)
        else:
            st.info("No returned loans recorded.")
