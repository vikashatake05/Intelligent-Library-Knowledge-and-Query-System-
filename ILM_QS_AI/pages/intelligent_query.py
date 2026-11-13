"""Intelligent FOL Query Workbench for Intelligent Library FOL System.
Signature application feature presenting natural language query translation,
predicate unification, and the Formal Logic Deduction Ledger.
"""
import streamlit as st
import pandas as pd
from query_engine import process_query, get_supported_syntax_documentation
from ui_components import render_page_header, render_deduction_ledger, render_badge

def render_intelligent_query(kb):
    render_page_header(
        title="Intelligent FOL Query Workbench",
        subtitle="Formulate queries in plain English or formal First-Order Logic predicates. Unification algorithms resolve variable substitutions against stored database facts and forward-chained Horn clauses.",
        tag="Symbolic Reasoning Engine"
    )

    # Manage query state in Streamlit session
    if "user_query_input" not in st.session_state:
        st.session_state["user_query_input"] = ""
    if "active_query_result" not in st.session_state:
        st.session_state["active_query_result"] = None

    # Query Input Console
    st.markdown("<div style='font-size: 0.9rem; font-weight: 500; color: var(--text-primary); margin-bottom: 6px;'>Query Expression</div>", unsafe_allow_html=True)
    query_text = st.text_input(
        "Query Expression",
        value=st.session_state.get("user_query_input", ""),
        placeholder="Enter natural language query or FOL predicate e.g. WrittenBy(b, Russell) or Is AI A Modern Approach available?",
        label_visibility="collapsed",
        key="query_text_box"
    )

    col_submit, col_clear, _ = st.columns([1.2, 1, 4])
    with col_submit:
        submit_clicked = st.button("Submit Query", type="primary", use_container_width=True)
    with col_clear:
        clear_clicked = st.button("Clear", use_container_width=True)

    # Quick Formulation Reference Pills (clean, text-only)
    st.markdown("""
    <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 10px; margin-bottom: 20px;">
        <span style="font-size: 0.78rem; font-family: var(--font-mono); color: var(--text-muted); text-transform: uppercase;">Formulation examples:</span>
        <span class="fol-badge fol-badge-neutral">WrittenBy(b, Russell)</span>
        <span class="fol-badge fol-badge-neutral">Available(b)</span>
        <span class="fol-badge fol-badge-neutral">Borrowed(Ravi, b)</span>
        <span class="fol-badge fol-badge-neutral">Find books related to Artificial Intelligence</span>
        <span class="fol-badge fol-badge-neutral">Who borrowed Computer Networking?</span>
    </div>
    """, unsafe_allow_html=True)

    if clear_clicked:
        st.session_state["user_query_input"] = ""
        st.session_state["active_query_result"] = None
        st.rerun()

    if submit_clicked:
        if not query_text.strip():
            st.warning("Please enter a query expression.")
        else:
            st.session_state["user_query_input"] = query_text
            with st.spinner("Resolving unification against knowledge base..."):
                result = process_query(query_text, kb)
                st.session_state["active_query_result"] = result

    # Display Signature Element: Formal Logic Deduction Ledger
    result = st.session_state.get("active_query_result")
    if result:
        st.markdown("<hr style='border-color: var(--border-subtle); margin: 24px 0 20px 0;'/>", unsafe_allow_html=True)

        if not result["success"]:
            st.error(f"Syntax or Resolution Error: {result.get('explanation', 'Unable to resolve query.')}")
            st.markdown("### Supported Formulation Reference")
            syntax_df = pd.DataFrame(result.get("supported_syntax", get_supported_syntax_documentation()))
            st.dataframe(syntax_df, use_container_width=True, hide_index=True)
            return

        # Render the signature Formal Logic Deduction Ledger
        render_deduction_ledger(result)

        # Tabular Data Breakdown
        tab_bindings, tab_provenance, tab_syntax = st.tabs([
            "Variable Substitution Table",
            "Knowledge Provenance Audit",
            "FOL Syntax & Predicates Guide"
        ])

        with tab_bindings:
            if result["truth"] and result["matches"]:
                df_matches = pd.DataFrame(result["matches"])
                st.dataframe(df_matches, use_container_width=True, hide_index=True)
                st.caption(f"Unification yielded {len(result['matches'])} valid variable assignment(s).")
            elif result["truth"]:
                st.info("Query is a ground atomic sentence with no free variables. The assertion holds directly in the knowledge base.")
            else:
                st.info("No variable substitutions could satisfy this formula.")

        with tab_provenance:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div style='font-size: 0.85rem; font-weight: 500; color: var(--text-primary); margin-bottom: 8px;'>Ground Facts from SQLite Database</div>", unsafe_allow_html=True)
                if result["original_facts"]:
                    df_of = pd.DataFrame([
                        {"Predicate": f["predicate"], "Arguments": ", ".join(f["args"]), "Fact": f["fact"]}
                        for f in result["original_facts"]
                    ])
                    st.dataframe(df_of, use_container_width=True, hide_index=True)
                else:
                    st.caption("No ground database facts directly unified for this goal.")

            with c2:
                st.markdown("<div style='font-size: 0.85rem; font-weight: 500; color: var(--text-primary); margin-bottom: 8px;'>Inferred Facts from Forward-Chaining Rules</div>", unsafe_allow_html=True)
                if result["inferred_facts"]:
                    df_inf = pd.DataFrame([
                        {"Derived Fact": f["fact"], "Rule ID": f.get("rule", "-"), "Rule Name": (f.get("rule_details") or {}).get("name", "Inference")}
                        for f in result["inferred_facts"]
                    ])
                    st.dataframe(df_inf, use_container_width=True, hide_index=True)
                else:
                    st.caption("No rule-derived facts were required for this goal.")

        with tab_syntax:
            syntax_df = pd.DataFrame(get_supported_syntax_documentation())
            st.dataframe(syntax_df, use_container_width=True, hide_index=True)
