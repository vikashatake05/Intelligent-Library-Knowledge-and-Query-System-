"""Intelligent Library Knowledge and Query System Using First-Order Logic (FOL)
Main application entry point with centralized Unslop styling and persistent SQLite storage.
"""
import os
import json
import streamlit as st
import pandas as pd
import database
from knowledge_base import KnowledgeBase, Fact
from query_engine import PREDICATES
from utils import validate_fact, predicate_reference
from rules import RULES

# Centralized UI & Design System
from ui_components import load_design_system, render_page_header, render_badge

# Modular page view imports
from pages.dashboard import render_dashboard
from pages.intelligent_query import render_intelligent_query
from pages.library_management import render_library_management

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Intelligent Library FOL System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject centralized design system tokens & component styles
load_design_system()

# ---------------------------------------------------------
# Database & Knowledge Base Initialization
# ---------------------------------------------------------
database.init_db()

if "kb" not in st.session_state:
    kb_instance = KnowledgeBase()
    kb_instance.reload_from_db()
    st.session_state["kb"] = kb_instance

kb: KnowledgeBase = st.session_state["kb"]

# ---------------------------------------------------------
# Sidebar Navigation (Unslop design, zero emojis)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="fol-sidebar-brand">
        <h2 class="fol-sidebar-logo">Library FOL</h2>
        <div class="fol-sidebar-subtext">First-Order Logic System</div>
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

    st.markdown("<hr style='border-color: var(--border-subtle); margin: 20px 0 16px 0;'/>", unsafe_allow_html=True)

    # Knowledge Base Live Status Indicator
    orig_count = len(kb.original_facts())
    inf_count = len(kb.inferred_facts())
    st.markdown(f"""
    <div class="fol-sidebar-status">
        <div style="font-size: 0.72rem; font-family: var(--font-mono); color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Knowledge State</div>
        <div style="font-size: 1.15rem; font-family: var(--font-mono); font-weight: 500; color: var(--text-primary); margin: 4px 0;">{len(kb.facts)} Total Facts</div>
        <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.45;">
            Ground Facts: <strong style="color: var(--text-primary);">{orig_count}</strong><br/>
            Inferred Facts: <strong style="color: var(--accent-amber);">{inf_count}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Resynchronize Knowledge Base", use_container_width=True):
        kb.reload_from_db()
        st.success("Knowledge base resynchronized.")
        st.rerun()

    st.caption("First-Order Logic · Predicate Unification · SQLite Storage")

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
# Page Routing & Views
# ---------------------------------------------------------

if selected_page == "Dashboard":
    render_dashboard()

elif selected_page == "Intelligent Query":
    render_intelligent_query(kb)

elif selected_page == "Library Management":
    render_library_management(kb)

elif selected_page == "Knowledge Base":
    render_page_header(
        title="First-Order Logic Knowledge Base",
        subtitle="Search, filter, and inspect ground atomic formulas asserted in the system, distinguishing stored database ground facts from forward-chained conclusions.",
        tag="Knowledge Representation"
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("Search ground facts", placeholder="Filter by constant e.g. Ravi, Artificial_Intelligence, or Russell", label_visibility="collapsed")
    with col2:
        pred = st.selectbox("Filter by Predicate", ["All"] + sorted(PREDICATES), label_visibility="collapsed")

    filtered = [
        f for f in kb.facts
        if (pred == "All" or f.predicate == pred) and (search.lower() in str(f).lower())
    ]
    show_fact_table(filtered)
    st.caption(f"Displaying {len(filtered)} fact(s) out of {len(kb.facts)} total in knowledge base.")

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        with st.expander("Assert Ground Fact"):
            st.caption("Enter a ground fact formula: `Predicate(Constant, Constant)`. Constants must begin with an uppercase letter.")
            fact_text = st.text_input("Fact expression", placeholder="e.g. Book(Advanced_AI) or WrittenBy(Advanced_AI, Russell)", key="new_direct_fact")
            if st.button("Assert Fact"):
                try:
                    p, args = validate_fact(fact_text)
                    new_fact = Fact(p, args)
                    if kb.add_fact(new_fact, source="original"):
                        from inference_engine import run_forward_chaining
                        run_forward_chaining(kb)
                        st.success(f"Asserted {new_fact}. Inferences recalculated.")
                        st.rerun()
                    else:
                        st.info("Fact already exists in knowledge base.")
                except Exception as e:
                    st.error(str(e))

    with col_a2:
        with st.expander("Export Knowledge Base"):
            st.caption("Export all current facts and derivation provenance as a standardized JSON structure.")
            payload = [
                {"predicate": f.predicate, "args": list(f.args), "source": kb.provenance.get(f, {}).get("source", "original")}
                for f in kb.facts
            ]
            st.download_button(
                "Download JSON",
                json.dumps(payload, indent=2),
                "library_knowledge_base.json",
                "application/json",
                use_container_width=True
            )

elif selected_page == "Library Explorer":
    render_page_header(
        title="Library Entity & Relationship Explorer",
        subtitle="Traverse relational associations between books, authors, subjects, and student borrowers across the First-Order Logic domain.",
        tag="Relational Inspection"
    )

    kind = st.selectbox(
        "Select Entity Domain",
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
                {"Fact Expression": str(f), "Arguments": ", ".join(f.args), "Provenance Type": kb.provenance.get(f, {}).get("source", "original")}
                for f in facts
            ]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"No facts found for entity domain '{kind}'.")

    if kind == "Books" and facts:
        st.markdown("### Book Associative Linkage")
        chosen = st.selectbox("Select catalog title", [f.args[0] for f in facts])
        clean_name = chosen.replace("_", " ")

        c_a, c_s, c_b = st.columns(3)
        with c_a:
            st.markdown("<div style='font-size: 0.8rem; font-family: var(--font-mono); color: var(--text-muted); text-transform: uppercase;'>Authorship (WrittenBy)</div>", unsafe_allow_html=True)
            written = [f.args[1].replace("_", " ") for f in kb.by_predicate("WrittenBy") if f.args[0] == chosen]
            st.write(", ".join(written) if written else "None recorded")
        with c_s:
            st.markdown("<div style='font-size: 0.8rem; font-family: var(--font-mono); color: var(--text-muted); text-transform: uppercase;'>Classification (BelongsTo)</div>", unsafe_allow_html=True)
            belongs = [f.args[1].replace("_", " ") for f in kb.by_predicate("BelongsTo") if f.args[0] == chosen]
            st.write(", ".join(belongs) if belongs else "None recorded")
        with c_b:
            st.markdown("<div style='font-size: 0.8rem; font-family: var(--font-mono); color: var(--text-muted); text-transform: uppercase;'>Circulation State (Borrowed)</div>", unsafe_allow_html=True)
            borrowed_by = [f.args[0].replace("_", " ") for f in kb.by_predicate("Borrowed") if f.args[1] == chosen]
            if borrowed_by:
                st.markdown(f'<span class="fol-badge fol-badge-negative">Borrowed by: {", ".join(borrowed_by)}</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="fol-badge fol-badge-positive">Available (Rule R4 Derived)</span>', unsafe_allow_html=True)

elif selected_page == "Logical Rules":
    render_page_header(
        title="Definite Horn Clauses & Inference Rules",
        subtitle="Formal specifications of the deductive rules governing forward-chaining reasoning, subject inheritance, and non-monotonic availability.",
        tag="Deductive Logic"
    )

    for r in RULES:
        with st.expander(f"Rule {r['id']} — {r['name']}", expanded=True):
            st.latex(
                r["fol"]
                .replace("∀", "\\forall ")
                .replace("∧", "\\land ")
                .replace("¬", "\\neg ")
                .replace("∃", "\\exists ")
                .replace("→", "\\rightarrow ")
            )
            st.markdown(f"**Paraphrase:** {r['english']}")
            st.markdown(f"**Antecedent Premises:** {', '.join(r['premises'])}")
            st.markdown(f"**Consequent Goal:** `{r['conclusion']}`")
            if r.get("note"):
                st.caption(f"Semantics note: {r['note']}")

elif selected_page == "Ontology":
    render_page_header(
        title="Library Domain Ontology & Schema",
        subtitle="Formal conceptual schema illustrating unary entity classes and binary associative predicates.",
        tag="Ontological Schema"
    )

    st.graphviz_chart("""
    digraph Library {
      graph [bgcolor="transparent", rankdir=LR];
      node [shape=box, style="rounded,filled", fillcolor="#1e232e", color="#3b82f6", fontcolor="#eef0f5", fontname="Helvetica", fontsize=10, height=0.32];
      edge [color="#6b7385", fontcolor="#9da5b4", fontname="Helvetica", fontsize=9];

      Book; Author; Subject; Student; Faculty; LibraryUser; Department;

      Author -> Book [label="WrittenBy"];
      Book -> Subject [label="BelongsTo"];
      Author -> Subject [label="SpecializesIn"];
      Student -> LibraryUser [label="Rule R1"];
      Student -> Department [label="MemberOf"];
      Student -> Book [label="Borrowed"];
      Book -> Book [label="Rule R4"];
    }
    """)

    st.markdown("### Predicate Signatures")
    st.dataframe(
        pd.DataFrame(predicate_reference(), columns=["Signature", "Semantics"]),
        use_container_width=True,
        hide_index=True
    )
