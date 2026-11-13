"""Intelligent Library Knowledge and Query System Using First-Order Logic (FOL)
Main application entry point with persistent SQLite storage and explainable AI reasoning.
"""
import os
import streamlit as st
import pandas as pd
import database
from knowledge_base import KnowledgeBase, Fact
from query_engine import PREDICATES
from utils import validate_fact, predicate_reference
from rules import RULES

# Modular page view imports
from pages.dashboard import render_dashboard
from pages.intelligent_query import render_intelligent_query
from pages.library_management import render_library_management

# ---------------------------------------------------------
# Page Configuration & Professional Academic Theme
# ---------------------------------------------------------
st.set_page_config(
    page_title="Intelligent Library Knowledge & Query System (FOL)",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Base theme styling */
.stApp {
    background: linear-gradient(135deg, #071426 0%, #0b1d35 55%, #10294a 100%);
    color: #edf4ff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
section[data-testid="stSidebar"] {
    background: #081629;
    border-right: 1px solid #1e3a5f;
}
h1, h2, h3, h4, h5, h6 {
    color: #e8f2ff;
    font-weight: 600;
}
div[data-testid="stMetric"] {
    background: #102846;
    padding: 16px;
    border: 1px solid #24486d;
    border-radius: 10px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}
div[data-testid="stMetricLabel"] p {
    color: #94a3b8 !important;
    font-weight: 500 !important;
}
div[data-testid="stMetricValue"] div {
    color: #38bdf8 !important;
    font-weight: 700 !important;
}
.stButton>button {
    background: #1d4ed8;
    color: white;
    border-radius: 8px;
    border: 0;
    font-weight: 500;
    transition: all 0.15s ease-in-out;
}
.stButton>button:hover {
    background: #2563eb;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}
div[data-testid="stDataFrame"] {
    border: 1px solid #24486d;
    border-radius: 10px;
}
.small-muted {
    color: #9db4ce;
    font-size: 0.85rem;
}
/* Tab active style */
button[data-baseweb="tab"] {
    color: #94a3b8;
    font-weight: 500;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #38bdf8 !important;
    border-bottom-color: #38bdf8 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Database & Knowledge Base Initialization
# ---------------------------------------------------------
# Ensure database and tables exist (seeded if empty)
database.init_db()

# Initialize KnowledgeBase in session state
if "kb" not in st.session_state:
    kb_instance = KnowledgeBase()
    kb_instance.reload_from_db()
    st.session_state["kb"] = kb_instance

kb: KnowledgeBase = st.session_state["kb"]

# ---------------------------------------------------------
# Sidebar Navigation (Unnecessary pages removed)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; padding: 10px 0 15px 0;">
        <span style="font-size: 2rem;">📚</span>
        <div>
            <h3 style="margin: 0; font-size: 1.15rem; color: #f8fafc;">Library FOL</h3>
            <span style="font-size: 0.78rem; color: #60a5fa; font-weight: 500;">First-Order Logic System</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_options = [
        "Dashboard",
        "Intelligent Query",
        "Library Management",
        "Knowledge Base",
        "Library Explorer",
        "Logical Rules",
        "Ontology"
    ]

    selected_page = st.radio(
        "Navigation",
        nav_options,
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<hr style='border-color: #1e3a5f; margin: 20px 0 15px 0;'/>", unsafe_allow_html=True)

    # Knowledge Base Live Status Pill
    orig_count = len(kb.original_facts())
    inf_count = len(kb.inferred_facts())
    st.markdown(f"""
    <div style="background: #0f2744; border: 1px solid #1e40af; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
        <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; font-weight: 600;">KB Live Status</div>
        <div style="color: #38bdf8; font-size: 1.1rem; font-weight: 700; margin: 4px 0;">{len(kb.facts)} Total Facts</div>
        <div style="color: #cbd5e1; font-size: 0.8rem;">
            • Ground DB Facts: <strong>{orig_count}</strong><br/>
            • Inferred (Rules): <strong>{inf_count}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Resync KB with Database", use_container_width=True):
        kb.reload_from_db()
        st.success("Knowledge base resynchronized!")
        st.rerun()

    st.caption("First-Order Logic • Predicate Unification • Forward Chaining • SQLite")

# Helper to render fact tables
def show_fact_table(facts=None):
    rows = [
        f.to_dict() | {
            "Type": kb.provenance.get(f, {}).get("source", "original"),
            "Rule": kb.provenance.get(f, {}).get("rule") or "-"
        }
        for f in (facts if facts is not None else kb.facts)
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# Page Routing
# ---------------------------------------------------------

if selected_page == "Dashboard":
    render_dashboard()

elif selected_page == "Intelligent Query":
    render_intelligent_query(kb)

elif selected_page == "Library Management":
    render_library_management(kb)

elif selected_page == "Knowledge Base":
    st.title("📖 First-Order Logic Knowledge Base")
    st.write("Browse, search, filter, and inspect the ground atomic formulas currently asserted in the library system.")

    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("Search facts", placeholder="e.g. Ravi, Artificial_Intelligence, or Russell")
    with col2:
        pred = st.selectbox("Filter by Predicate", ["All"] + sorted(PREDICATES))

    filtered = [
        f for f in kb.facts
        if (pred == "All" or f.predicate == pred) and (search.lower() in str(f).lower())
    ]
    show_fact_table(filtered)
    st.caption(f"Displaying {len(filtered)} fact(s) out of {len(kb.facts)} total.")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    with st.expander("➕ Assert Ground Fact Directly into Knowledge Base"):
        st.caption("Enter a ground fact expression. Format: `Predicate(Constant, Constant)`. Constants must start with an uppercase letter.")
        fact_text = st.text_input("Fact expression", placeholder="e.g. Book(Advanced_AI) or WrittenBy(Advanced_AI, Russell)", key="new_direct_fact")
        if st.button("Add Ground Fact"):
            try:
                p, args = validate_fact(fact_text)
                new_fact = Fact(p, args)
                if kb.add_fact(new_fact, source="original"):
                    from inference_engine import run_forward_chaining
                    run_forward_chaining(kb)
                    st.success(f"Successfully asserted {new_fact}. Inferences recalculated.")
                    st.rerun()
                else:
                    st.info("That fact already exists in the knowledge base.")
            except Exception as e:
                st.error(str(e))

    with st.expander("💾 Export Knowledge Base"):
        payload = [
            {"predicate": f.predicate, "args": list(f.args), "source": kb.provenance.get(f, {}).get("source", "original")}
            for f in kb.facts
        ]
        import json
        st.download_button(
            "Download Knowledge Base (JSON)",
            json.dumps(payload, indent=2),
            "library_knowledge_base.json",
            "application/json",
            use_container_width=True
        )

elif selected_page == "Library Explorer":
    st.title("🔍 Library Entity Explorer")
    st.write("Inspect entities and relationships in the knowledge base.")

    kind = st.selectbox(
        "Explore Entity Type",
        ["Books", "Authors", "Subjects", "Students", "Departments", "Borrowing Records", "Library Users", "Available Books"]
    )
    mapping = {
        "Books": "Book",
        "Authors": "Author",
        "Subjects": "Subject",
        "Students": "Student",
        "Departments": "Department",
        "Borrowing Records": "Borrowed",
        "Library Users": "LibraryUser",
        "Available Books": "Available"
    }
    facts = kb.by_predicate(mapping[kind])
    if facts:
        st.dataframe(
            pd.DataFrame([
                {"Fact": str(f), "Arguments": ", ".join(f.args), "Type": kb.provenance.get(f, {}).get("source", "original")}
                for f in facts
            ]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"No facts found for entity type '{kind}'.")

    if kind == "Books" and facts:
        st.subheader("Book Relationship Inspector")
        chosen = st.selectbox("Select a book to inspect relations", [f.args[0] for f in facts])
        clean_name = chosen.replace("_", " ")
        c_a, c_s, c_b = st.columns(3)
        with c_a:
            st.markdown(f"**Authorship (`WrittenBy`):**")
            written = [f.args[1].replace("_", " ") for f in kb.by_predicate("WrittenBy") if f.args[0] == chosen]
            st.write(", ".join(written) if written else "None recorded")
        with c_s:
            st.markdown(f"**Subject Classification (`BelongsTo`):**")
            belongs = [f.args[1].replace("_", " ") for f in kb.by_predicate("BelongsTo") if f.args[0] == chosen]
            st.write(", ".join(belongs) if belongs else "None recorded")
        with c_b:
            st.markdown(f"**Active Loan (`Borrowed`):**")
            borrowed_by = [f.args[0].replace("_", " ") for f in kb.by_predicate("Borrowed") if f.args[1] == chosen]
            if borrowed_by:
                st.warning(f"Borrowed by: {', '.join(borrowed_by)}")
            else:
                st.success("Available (Not currently borrowed)")

elif selected_page == "Logical Rules":
    st.title("📜 Executable Logical Rules")
    st.write("The knowledge base derives conclusions using definite Horn clauses and closed-world negation checks.")

    for r in RULES:
        with st.expander(f"{r['id']} · {r['name']}", expanded=True):
            st.latex(
                r["fol"]
                .replace("∀", "\\forall ")
                .replace("∧", "\\land ")
                .replace("¬", "\\neg ")
                .replace("∃", "\\exists ")
                .replace("→", "\\rightarrow ")
            )
            st.markdown(f"**Natural Language:** {r['english']}")
            st.markdown(f"**Premises:** {', '.join(r['premises'])}")
            st.markdown(f"**Conclusion:** `{r['conclusion']}`")
            if r.get("note"):
                st.info(f"**Implementation Note:** {r['note']}")

elif selected_page == "Ontology":
    st.title("🌐 Library Knowledge Ontology")
    st.write("Conceptual schema showing entity classes (unary predicates) and associative relations (binary predicates).")

    st.graphviz_chart("""
    digraph Library {
      graph [bgcolor="transparent", rankdir=LR];
      node [shape=box, style="rounded,filled", fillcolor="#12385c", color="#56a5e8", fontcolor="white", fontname="Helvetica"];
      edge [color="#78b9ed", fontcolor="#cbd5e1", fontname="Helvetica", fontsize=10];

      Book; Author; Subject; Student; Faculty; LibraryUser; Department;

      Author -> Book [label="WrittenBy"];
      Book -> Subject [label="BelongsTo"];
      Author -> Subject [label="SpecializesIn"];
      Student -> LibraryUser [label="Rule R1 (Borrowed)"];
      Student -> Department [label="MemberOf"];
      Student -> Book [label="Borrowed / HasBorrowed"];
      Book -> Book [label="Rule R4 (Available)"];
    }
    """)

    st.subheader("Predicate Signatures & Descriptions")
    st.dataframe(
        pd.DataFrame(predicate_reference(), columns=["Predicate Signature", "Semantics"]),
        use_container_width=True,
        hide_index=True
    )
