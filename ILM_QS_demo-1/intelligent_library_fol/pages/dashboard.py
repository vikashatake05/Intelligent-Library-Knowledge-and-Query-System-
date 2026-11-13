"""Dashboard page for Intelligent Library Knowledge and Query System.
Presents persistent live statistics from SQLite, interactive analytical charts,
and recent operational activity.
"""
import streamlit as st
import pandas as pd
import altair as alt
import database

def render_dashboard():
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #f1f5f9;">
            📚 Library Analytics Dashboard
        </h1>
        <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 1.05rem;">
            Real-time library metrics, borrowing trends, and catalog distribution powered by SQLite & First-Order Logic
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Fetch live metrics from SQLite
    stats = database.get_dashboard_stats()

    # 2. Top Statistics Cards
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.metric(label="Total Books", value=stats["total_books"])
    with m2:
        st.metric(label="Total Authors", value=stats["total_authors"])
    with m3:
        st.metric(label="Total Students", value=stats["total_students"])
    with m4:
        st.metric(label="Borrowed Books", value=stats["borrowed_books"])
    with m5:
        st.metric(label="Available Books", value=stats["available_books"])
    with m6:
        st.metric(label="Overdue Loans", value=stats["overdue_books"],
                  delta=f"{stats['overdue_books']} overdue" if stats["overdue_books"] > 0 else "0 overdue",
                  delta_color="inverse")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Handle empty database gracefully
    if stats["total_books"] == 0:
        st.info("The library database is currently empty. Use the **Library Management** page to add books, authors, and students.")
        return

    # 3. Charts and Visualizations
    st.markdown("<h3 style='color: #e2e8f0; margin-top: 25px; margin-bottom: 15px;'>📊 Catalog & Borrowing Analytics</h3>", unsafe_allow_html=True)

    row1_c1, row1_c2 = st.columns([1, 1])

    # Chart 1: Books by Subject
    with row1_c1:
        st.markdown("<h5 style='color: #cbd5e1;'>Books by Subject</h5>", unsafe_allow_html=True)
        subject_data = database.get_books_by_subject()
        if subject_data:
            df_subj = pd.DataFrame(subject_data)
            df_subj["subject_clean"] = df_subj["subject"].str.replace("_", " ")
            subj_chart = alt.Chart(df_subj).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X("subject_clean:N", title="Subject", sort="-y", axis=alt.Axis(labelAngle=-30)),
                y=alt.Y("count:Q", title="Number of Books"),
                color=alt.value("#3b82f6"),
                tooltip=[alt.Tooltip("subject_clean:N", title="Subject"), alt.Tooltip("count:Q", title="Books")]
            ).properties(height=280)
            st.altair_chart(subj_chart, use_container_width=True)
        else:
            st.caption("No subject data available.")

    # Chart 2: Books by Department
    with row1_c2:
        st.markdown("<h5 style='color: #cbd5e1;'>Books by Department</h5>", unsafe_allow_html=True)
        dept_data = database.get_books_by_department()
        if dept_data:
            df_dept = pd.DataFrame(dept_data)
            df_dept["dept_clean"] = df_dept["department"].str.replace("_", " ")
            dept_chart = alt.Chart(df_dept).mark_arc(innerRadius=45, outerRadius=95).encode(
                theta=alt.Theta(field="count", type="quantitative"),
                color=alt.Color("dept_clean:N", title="Department", scale=alt.Scale(scheme="category10")),
                tooltip=[alt.Tooltip("dept_clean:N", title="Department"), alt.Tooltip("count:Q", title="Books")]
            ).properties(height=280)
            st.altair_chart(dept_chart, use_container_width=True)
        else:
            st.caption("No department data available.")

    row2_c1, row2_c2, row2_c3 = st.columns([1, 1.2, 1.2])

    # Chart 3: Borrowed vs Available Books
    with row2_c1:
        st.markdown("<h5 style='color: #cbd5e1;'>Borrowed vs Available</h5>", unsafe_allow_html=True)
        avail_data = [
            {"Status": "Available", "Count": stats["available_books"]},
            {"Status": "Borrowed", "Count": stats["borrowed_books"]}
        ]
        df_avail = pd.DataFrame(avail_data)
        avail_chart = alt.Chart(df_avail).mark_bar(size=35, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Status:N", title=None),
            y=alt.Y("Count:Q", title="Count"),
            color=alt.Color("Status:N", scale=alt.Scale(
                domain=["Available", "Borrowed"],
                range=["#10b981", "#f59e0b"]
            ), legend=None),
            tooltip=[alt.Tooltip("Status:N"), alt.Tooltip("Count:Q")]
        ).properties(height=260)
        st.altair_chart(avail_chart, use_container_width=True)

    # Chart 4: Monthly Borrowing Activity
    with row2_c2:
        st.markdown("<h5 style='color: #cbd5e1;'>Monthly Borrowing Activity</h5>", unsafe_allow_html=True)
        monthly_data = database.get_monthly_borrowing_activity()
        if monthly_data:
            df_month = pd.DataFrame(monthly_data)
            line_chart = alt.Chart(df_month).mark_line(
                point=alt.OverlayMarkDef(color="#38bdf8", size=60),
                color="#0284c7",
                strokeWidth=3
            ).encode(
                x=alt.X("month:N", title="Month (YYYY-MM)", axis=alt.Axis(labelAngle=-25)),
                y=alt.Y("count:Q", title="Transactions"),
                tooltip=[alt.Tooltip("month:N", title="Month"), alt.Tooltip("count:Q", title="Borrowings")]
            ).properties(height=260)
            st.altair_chart(line_chart, use_container_width=True)
        else:
            st.caption("No monthly transaction history yet.")

    # Chart 5: Top Borrowed Books
    with row2_c3:
        st.markdown("<h5 style='color: #cbd5e1;'>Top Borrowed Books</h5>", unsafe_allow_html=True)
        top_data = database.get_top_borrowed_books(limit=5)
        if top_data:
            df_top = pd.DataFrame(top_data)
            df_top["title_clean"] = df_top["title"].str.replace("_", " ")
            top_chart = alt.Chart(df_top).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                y=alt.Y("title_clean:N", sort="-x", title=None),
                x=alt.X("borrow_count:Q", title="Times Borrowed"),
                color=alt.value("#8b5cf6"),
                tooltip=[alt.Tooltip("title_clean:N", title="Book Title"), alt.Tooltip("borrow_count:Q", title="Borrowed Count")]
            ).properties(height=260)
            st.altair_chart(top_chart, use_container_width=True)
        else:
            st.caption("No borrowing history records.")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 4. Recent Activity Section
    st.markdown("<h3 style='color: #e2e8f0; margin-top: 15px; margin-bottom: 15px;'>🕒 Recent Activity</h3>", unsafe_allow_html=True)

    tab_added, tab_borrowed, tab_returned = st.tabs([
        "📖 Recently Added Books",
        "📥 Active Borrowings",
        "✅ Recent Returns"
    ])

    with tab_added:
        recent_books = database.get_recent_added_books(limit=5)
        if recent_books:
            df_rb = pd.DataFrame(recent_books)
            df_rb["title"] = df_rb["title"].str.replace("_", " ")
            df_rb["author_name"] = df_rb["author_name"].str.replace("_", " ")
            df_rb["subject"] = df_rb["subject"].str.replace("_", " ")
            df_rb = df_rb.rename(columns={
                "book_id": "ID", "title": "Title", "author_name": "Author",
                "subject": "Subject", "availability_status": "Status"
            })
            st.dataframe(df_rb, use_container_width=True, hide_index=True)
        else:
            st.info("No books have been recorded.")

    with tab_borrowed:
        recent_loans = database.get_recent_borrowings(limit=5)
        if recent_loans:
            df_rl = pd.DataFrame(recent_loans)
            df_rl["student_name"] = df_rl["student_name"].str.replace("_", " ")
            df_rl["book_title"] = df_rl["book_title"].str.replace("_", " ")
            df_rl = df_rl.rename(columns={
                "borrowing_id": "Loan ID", "student_name": "Student",
                "book_title": "Book Title", "borrow_date": "Borrow Date", "status": "Status"
            })
            st.dataframe(df_rl, use_container_width=True, hide_index=True)
        else:
            st.info("No active borrowings currently recorded.")

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
            st.info("No returns recorded yet.")

if __name__ == "__main__":
    render_dashboard()

