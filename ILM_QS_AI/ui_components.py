"""Reusable UI components and design system utilities for Intelligent Library FOL.
Encapsulates centralized styling, consistent layout patterns, and the signature
Formal Logic Deduction Ledger.
"""
import os
import streamlit as st
import altair as alt

THEME_CSS_PATH = os.path.join(os.path.dirname(__file__), "assets", "theme.css")

def load_design_system():
    """Inject the centralized design system CSS into the Streamlit session."""
    if os.path.exists(THEME_CSS_PATH):
        with open(THEME_CSS_PATH, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

def render_page_header(title: str, subtitle: str, tag: str = "System"):
    """Render a clean, unslop academic page header without emojis."""
    st.markdown(
        f"""
        <div class="fol-header">
            <div class="fol-header-tag">{tag}</div>
            <h1 class="fol-header-title">{title}</h1>
            <p class="fol-header-desc">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_badge(text: str, variant: str = "neutral") -> str:
    """Return HTML string for a quiet, accessible status badge."""
    variant_classes = {
        "neutral": "fol-badge-neutral",
        "ground": "fol-badge-ground",
        "inferred": "fol-badge-inferred",
        "positive": "fol-badge-positive",
        "negative": "fol-badge-negative"
    }
    css_cls = variant_classes.get(variant, "fol-badge-neutral")
    return f'<span class="fol-badge {css_cls}">{text}</span>'

def render_deduction_ledger(result: dict):
    """
    Render the Signature Element: The Formal Logic Deduction Ledger.
    Presents formal logic resolution, unified substitutions, and rule provenance
    in an authoritative, explainable ledger view.
    """
    truth = result["truth"]
    fol_expr = result["fol_query"]
    is_nl = result.get("is_natural_language", False)
    intention = result.get("intention", "")
    matches = result.get("matches", [])
    orig_facts = result.get("original_facts", [])
    inferred_facts = result.get("inferred_facts", [])
    explanation = result.get("explanation", "")

    status_badge = (
        render_badge("Truth: Satisfied (Valid)", "positive")
        if truth else
        render_badge("Truth: Unsatisfied (Unprovable)", "negative")
    )

    query_type_badge = (
        render_badge("Query: Natural Language Translation", "neutral")
        if is_nl else
        render_badge("Query: Direct FOL Formula", "neutral")
    )

    html = f"""
    <div class="fol-ledger">
        <div class="fol-ledger-head">
            <div class="fol-ledger-head-left">
                <div class="fol-ledger-head-title">Formal Logic Deduction Ledger</div>
                <div class="fol-ledger-head-expr">{fol_expr}</div>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                {query_type_badge}
                {status_badge}
            </div>
        </div>
        <div class="fol-ledger-body">
    """

    if is_nl and intention:
        html += f"""
        <div class="fol-ledger-section">
            <div class="fol-ledger-section-title">Query Translation & Semantics</div>
            <div style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.45;">
                Parsed intention: <strong style="color: var(--text-primary);">{intention}</strong><br/>
                Formal goal: <code class="fol-deduction-code">{fol_expr}</code>
            </div>
        </div>
        """

    # Section: Unification Bindings
    if truth:
        html += """
        <div class="fol-ledger-section">
            <div class="fol-ledger-section-title">Unification Bindings (Variable Substitutions)</div>
        """
        if matches:
            for idx, m in enumerate(matches, 1):
                bindings_str = ", ".join(f"{k} = {v.replace('_', ' ')}" for k, v in m.items())
                html += f"""
                <div class="fol-deduction-row">
                    <span class="fol-deduction-turnstile">⊢</span>
                    <span class="fol-deduction-content">
                        <strong>Solution {idx}:</strong> <span class="fol-deduction-code">{bindings_str}</span>
                    </span>
                </div>
                """
        else:
            html += """
            <div class="fol-deduction-row">
                <span class="fol-deduction-turnstile">⊢</span>
                <span class="fol-deduction-content">Ground sentence directly holds with empty substitution set {}.</span>
            </div>
            """
        html += "</div>"

        # Section: Derivation Chain & Provenance
        html += """
        <div class="fol-ledger-section">
            <div class="fol-ledger-section-title">Derivation Chain & Ground Support</div>
        """
        if orig_facts:
            for of in orig_facts:
                html += f"""
                <div class="fol-deduction-row">
                    <span class="fol-badge fol-badge-ground">Ground Fact</span>
                    <span class="fol-deduction-content">
                        <code class="fol-deduction-code">{of['fact']}</code>
                    </span>
                    <span class="fol-deduction-provenance">SQLite database record</span>
                </div>
                """
        if inferred_facts:
            for inf in inferred_facts:
                r_id = inf.get("rule", "R?")
                r_details = inf.get("rule_details") or {}
                r_name = r_details.get("name", "Inference Rule")
                r_fol = r_details.get("fol", "")
                html += f"""
                <div class="fol-deduction-row">
                    <span class="fol-badge fol-badge-inferred">Derived Fact</span>
                    <span class="fol-deduction-content">
                        <code class="fol-deduction-code">{inf['fact']}</code>
                        <span style="color: var(--text-secondary); margin-left: 8px;">via <strong>Rule {r_id}</strong> ({r_name})</span>
                    </span>
                    <span class="fol-deduction-provenance">{r_fol}</span>
                </div>
                """
        html += "</div>"

    else:
        # Unsatisfied query
        html += f"""
        <div class="fol-ledger-section">
            <div class="fol-ledger-section-title">Proof Status: Closed-World Negation</div>
            <div style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5;">
                {explanation}
            </div>
        </div>
        """

    # Section: Step-by-Step Proof Explanation
    if explanation and truth:
        html += f"""
        <div class="fol-ledger-section">
            <div class="fol-ledger-section-title">Explainable Deduction Narrative</div>
            <div style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.55;">
                {explanation}
            </div>
        </div>
        """

    html += """
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def apply_altair_unslop_theme(chart: alt.Chart) -> alt.Chart:
    """Apply quiet academic styling to Altair charts (no rainbow noise, quiet grid)."""
    return chart.configure_view(
        stroke="transparent",
        fill="transparent"
    ).configure_axis(
        labelColor="#9da5b4",
        titleColor="#eef0f5",
        gridColor="rgba(238, 240, 245, 0.06)",
        domainColor="rgba(238, 240, 245, 0.12)",
        tickColor="rgba(238, 240, 245, 0.12)",
        labelFont="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        titleFont="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        labelFontSize=11,
        titleFontSize=12,
        titleFontWeight=500
    ).configure_legend(
        labelColor="#9da5b4",
        titleColor="#eef0f5",
        labelFont="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        titleFont="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        labelFontSize=11,
        titleFontSize=12,
        titleFontWeight=500
    )
