"""Intelligent Query page for Intelligent Library Knowledge and Query System.
Supports natural language queries and raw FOL queries with unification, variable bindings,
and explainable step-by-step proof provenance.
"""
import streamlit as st
import pandas as pd
from query_engine import process_query, get_supported_syntax_documentation

def render_intelligent_query(kb):
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #f1f5f9;">
            🧠 Intelligent FOL Query System
        </h1>
        <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 1.05rem;">
            Ask questions in natural language or enter First-Order Logic predicate queries.
            Answers are computed live via term unification and forward-chaining Horn rules.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Manage query state in session
    if "user_query_input" not in st.session_state:
        st.session_state["user_query_input"] = ""
    if "active_query_result" not in st.session_state:
        st.session_state["active_query_result"] = None

    # Query Input Form
    with st.container():
        st.markdown("<h4 style='color: #e2e8f0; margin-bottom: 8px;'>Enter Query</h4>", unsafe_allow_html=True)
        query_text = st.text_input(
            "Query Input",
            value=st.session_state.get("user_query_input", ""),
            placeholder="e.g. Find books written by Russell, or WrittenBy(b, Russell)",
            label_visibility="collapsed",
            key="query_text_box"
        )

        col_submit, col_clear, _ = st.columns([1.2, 1, 5])
        with col_submit:
            submit_clicked = st.button("🔍 Submit Query", type="primary", use_container_width=True)
        with col_clear:
            clear_clicked = st.button("🗑️ Clear", use_container_width=True)

    if clear_clicked:
        st.session_state["user_query_input"] = ""
        st.session_state["active_query_result"] = None
        st.rerun()

    if submit_clicked:
        if not query_text.strip():
            st.warning("Please enter a query before submitting.")
        else:
            st.session_state["user_query_input"] = query_text
            with st.spinner("Reasoning over knowledge base..."):
                result = process_query(query_text, kb)
                st.session_state["active_query_result"] = result

    # Display Query Results
    result = st.session_state.get("active_query_result")
    if result:
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.divider()

        if not result["success"]:
            st.error(f"**Query Not Recognized:** {result.get('explanation', 'Unable to process query.')}")
            st.markdown("<h5 style='margin-top: 15px;'>📖 Supported Query Guide</h5>", unsafe_allow_html=True)
            st.info("You can phrase your query in plain English or write standard First-Order Logic predicates. See supported options below:")
            syntax_df = pd.DataFrame(result.get("supported_syntax", get_supported_syntax_documentation()))
            st.dataframe(syntax_df, use_container_width=True, hide_index=True)
            return

        # Success path
        truth = result["truth"]
        fol_expr = result["fol_query"]
        is_nl = result["is_natural_language"]
        intention = result.get("intention")

        # Query metadata banner
        meta_col1, meta_col2 = st.columns([2, 1])
        with meta_col1:
            if is_nl:
                st.markdown(
                    f"<div style='background: #0f2744; padding: 10px 14px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-bottom: 15px;'>"
                    f"<span style='color: #94a3b8; font-size: 0.85rem;'>INTENTION:</span> <strong style='color: #e2e8f0;'>{intention}</strong><br/>"
                    f"<span style='color: #94a3b8; font-size: 0.85rem;'>TRANSLATED FOL FORMULA:</span> <code style='color: #38bdf8;'>{fol_expr}</code>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='background: #0f2744; padding: 10px 14px; border-radius: 8px; border-left: 4px solid #818cf8; margin-bottom: 15px;'>"
                    f"<span style='color: #94a3b8; font-size: 0.85rem;'>EVALUATING FIRST-ORDER LOGIC PREDICATE:</span> <code style='color: #818cf8;'>{fol_expr}</code>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        with meta_col2:
            if truth:
                num_answers = len(result["matches"])
                if num_answers > 0:
                    st.success(f"**TRUE** · Found {num_answers} match{'es' if num_answers != 1 else ''}")
                else:
                    st.success("**TRUE** · Ground formula satisfied")
            else:
                st.error("**FALSE** · No matching fact in KB")

        # Result Details Section
        res_tab1, res_tab2, res_tab3 = st.tabs([
            "📋 Answer & Substitutions",
            "🔍 Proof & Explanation",
            "📚 Facts Used (Provenance)"
        ])

        with res_tab1:
            if truth:
                if result["formatted_answers"]:
                    st.markdown("<h5 style='color: #cbd5e1; margin-top: 5px;'>Answer(s):</h5>", unsafe_allow_html=True)
                    # Display answers in clean cards or badges
                    ans_cols = st.columns(min(len(result["formatted_answers"]), 3))
                    for i, ans in enumerate(result["formatted_answers"]):
                        with ans_cols[i % len(ans_cols)]:
                            st.markdown(
                                f"<div style='background: #112a4c; border: 1px solid #1e40af; border-radius: 8px; padding: 12px; margin-bottom: 8px;'>"
                                f"<span style='color: #93c5fd; font-weight: 600;'>{ans}</span>"
                                f"</div>",
                                unsafe_allow_html=True
                            )

                    if result["matches"]:
                        st.markdown("<h6 style='color: #94a3b8; margin-top: 15px;'>Variable Bindings (Unification Mappings):</h6>", unsafe_allow_html=True)
                        bindings_df = pd.DataFrame(result["matches"])
                        st.dataframe(bindings_df, use_container_width=True, hide_index=True)
                else:
                    st.write("Assertion is valid in the knowledge base.")
            else:
                st.markdown("""
                <div style='background: #2a1215; border: 1px solid #7f1d1d; border-radius: 8px; padding: 16px; margin: 10px 0;'>
                    <h5 style='color: #fca5a5; margin: 0 0 8px 0;'>No Answer Found</h5>
                    <p style='color: #e2e8f0; margin: 0;'>
                        No ground facts or inference rule conclusions could unify with this query.
                        If you asked about book availability, the book may currently be checked out.
                        If you asked about a specific relationship, it is not present in the library records.
                    </p>
                </div>
                """, unsafe_allow_html=True)

        with res_tab2:
            st.markdown("<h5 style='color: #cbd5e1;'>How this answer was obtained:</h5>", unsafe_allow_html=True)
            st.markdown(result["explanation"])

            if result["inferred_facts"]:
                st.markdown("<h6 style='color: #f59e0b; margin-top: 15px;'>Inference Rules Applied:</h6>", unsafe_allow_html=True)
                for inf in result["inferred_facts"]:
                    r_id = inf.get("rule", "Unknown")
                    r_info = inf.get("rule_details") or {}
                    st.markdown(
                        f"- **Rule {r_id}** ({r_info.get('name', 'Inference')}): "
                        f"`{r_info.get('fol', '')}` — *{r_info.get('english', '')}*"
                    )

        with res_tab3:
            orig = result["original_facts"]
            inferred = result["inferred_facts"]

            c_orig, c_inf = st.columns(2)
            with c_orig:
                st.markdown("<h6 style='color: #60a5fa;'>Original Facts (from Database):</h6>", unsafe_allow_html=True)
                if orig:
                    df_orig = pd.DataFrame([{"Fact": f["fact"], "Predicate": f["predicate"], "Arguments": ", ".join(f["args"])} for f in orig])
                    st.dataframe(df_orig, use_container_width=True, hide_index=True)
                else:
                    st.caption("No original database facts were directly unified.")

            with c_inf:
                st.markdown("<h6 style='color: #f59e0b;'>Inferred Facts (Derived via Rules):</h6>", unsafe_allow_html=True)
                if inferred:
                    df_inf = pd.DataFrame([{"Fact": f["fact"], "Rule": f.get("rule", "-"), "Arguments": ", ".join(f["args"])} for f in inferred])
                    st.dataframe(df_inf, use_container_width=True, hide_index=True)
                else:
                    st.caption("No derived/inferred facts were needed for this query.")

    # Syntax Reference Expander at bottom
    with st.expander("ℹ️ Supported Query Syntax & Natural Language Examples"):
        st.markdown("""
        The system supports both natural language questions and First-Order Logic formulas:
        - **Variables:** Begin with a lowercase letter (e.g. `b`, `x`, `author`, `student`).
        - **Constants:** Begin with an uppercase letter (e.g. `Russell`, `AI_A_Modern_Approach`, `Ravi`).
        - **Ground Queries:** Contain only constants (e.g. `Available(Algorithms_in_C)`).
        - **Unification Queries:** Contain one or more variables to solve for (e.g. `WrittenBy(b, Russell)`).
        """)
        st.dataframe(pd.DataFrame(get_supported_syntax_documentation()), use_container_width=True, hide_index=True)

