"""Query answering engine by unification against the knowledge base,
with automatic natural language to FOL translation and explainable reasoning.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from unification import (
    parse_predicate, unify_predicates, UnificationError, is_variable, apply_substitution
)
from rules import RULES

PREDICATES = {
    "Book": 1,
    "Author": 1,
    "Student": 1,
    "Faculty": 1,
    "LibraryUser": 1,
    "Subject": 1,
    "Department": 1,
    "WrittenBy": 2,
    "BelongsTo": 2,
    "SpecializesIn": 2,
    "Borrowed": 2,
    "HasBorrowed": 2,
    "Available": 1,
    "MemberOf": 2
}

RULE_DESCRIPTIONS = {r["id"]: r for r in RULES}

def answer_query(query: str, kb) -> Dict[str, Any]:
    """Execute an FOL predicate query against the knowledge base using unification."""
    name, args = parse_predicate(query)
    if name not in PREDICATES:
        raise ValueError(f"Unknown predicate '{name}'. Supported predicates: {', '.join(sorted(PREDICATES))}")
    if len(args) != PREDICATES[name]:
        raise ValueError(f"{name} expects {PREDICATES[name]} argument(s), received {len(args)}.")

    matches = []
    supports = []
    for fact in kb.by_predicate(name):
        try:
            subst, _ = unify_predicates((name, args), (fact.predicate, fact.args))
            visible = {k: v for k, v in subst.items() if is_variable(k)}
            matches.append(visible)
            supports.append({
                "fact": str(fact),
                "predicate": fact.predicate,
                "args": fact.args,
                "provenance": kb.provenance.get(fact, {})
            })
        except UnificationError:
            continue

    truth = bool(matches) if any(is_variable(a) for a in args) else bool(supports)
    if not any(is_variable(a) for a in args):
        # Ground query without variables, e.g. Available(AI_Book) or WrittenBy(AI_Book, Russell)
        truth = len(supports) > 0

    explanation = (
        "Matched against stored and inferred facts using predicate unification."
        if truth else
        "No fact in the current knowledge base unifies with this query."
    )

    return {
        "query": query,
        "predicate": name,
        "args": args,
        "truth": truth,
        "matches": matches,
        "supporting_facts": supports,
        "explanation": explanation
    }

def normalize_text_token(token: str) -> str:
    """Helper to convert strings into potential FOL constant form."""
    clean = re.sub(r"[^A-Za-z0-9]+", "_", token.strip()).strip("_")
    if clean and clean[0].islower():
        clean = clean[0].upper() + clean[1:]
    return clean

def find_best_entity_match(candidate: str, candidates_pool: list[str]) -> Optional[str]:
    """Match a natural language string to an entity constant from the pool."""
    cand_norm = candidate.strip().lower().replace(" ", "_")
    cand_norm = re.sub(r"[^a-z0-9_]", "", cand_norm)

    # 1. Exact match (case insensitive)
    for c in candidates_pool:
        c_low = c.lower()
        if c_low == cand_norm or c_low.replace("_", " ") == candidate.strip().lower():
            return c

    # 2. Substring or partial match
    for c in candidates_pool:
        c_low = c.lower()
        if cand_norm and (cand_norm in c_low or c_low in cand_norm):
            return c

    # 3. Default normalized
    return normalize_text_token(candidate) if candidate.strip() else None

def translate_natural_language_to_fol(query_text: str, kb) -> Tuple[Optional[str], Optional[str]]:
    """
    Translate natural language queries into supported FOL predicate queries.
    Returns (fol_query, intention_description) or (None, None).
    """
    text = query_text.strip()
    clean_text = text.rstrip("?.!").strip()
    low = clean_text.lower()

    # Collect known entities from KB
    books = [f.args[0] for f in kb.by_predicate("Book")]
    authors = [f.args[0] for f in kb.by_predicate("Author")]
    students = [f.args[0] for f in kb.by_predicate("Student")]
    subjects = [f.args[0] for f in kb.by_predicate("Subject")]

    # 1. Available books queries
    # e.g., "is AI A Modern Approach available?", "check whether ... is available"
    m = re.search(r"^(?:check\s+(?:whether|if)\s+|is\s+)(.+?)\s+available$", low)
    if m:
        target = m.group(1).strip()
        matched_book = find_best_entity_match(target, books)
        if matched_book:
            return f"Available({matched_book})", f"Check availability of book '{matched_book.replace('_', ' ')}'"

    m = re.search(r"^(?:check\s+availability\s+(?:of|for)\s+)(.+)$", low)
    if m:
        target = m.group(1).strip()
        matched_book = find_best_entity_match(target, books)
        if matched_book:
            return f"Available({matched_book})", f"Check availability of book '{matched_book.replace('_', ' ')}'"

    if re.search(r"^(?:which\s+books\s+are\s+available|find\s+available\s+books|show\s+available\s+books|available\s+books|list\s+available\s+books)$", low):
        return "Available(b)", "Find all books currently available in the library"

    # 2. Author queries
    # e.g., "who wrote <book>?", "author of <book>"
    m = re.search(r"^(?:who\s+wrote|who\s+is\s+the\s+author\s+of|author\s+of)\s+(.+)$", low)
    if m:
        target = m.group(1).strip()
        matched_book = find_best_entity_match(target, books)
        if matched_book:
            return f"WrittenBy({matched_book}, a)", f"Find the author of '{matched_book.replace('_', ' ')}'"

    # e.g., "find books written by Russell", "books by Norvig", "which books were written by Cormen"
    m = re.search(r"^(?:find\s+books\s+written\s+by|books\s+written\s+by|which\s+books\s+(?:were\s+)?written\s+by|books\s+by|find\s+books\s+by)\s+(.+)$", low)
    if m:
        target = m.group(1).strip()
        matched_author = find_best_entity_match(target, authors)
        if matched_author:
            return f"WrittenBy(b, {matched_author})", f"Find books written by author '{matched_author.replace('_', ' ')}'"

    # 3. Subject queries
    # e.g., "find books belonging to Artificial Intelligence", "books related to Artificial Intelligence", "books about Data Structures"
    m = re.search(r"^(?:find\s+books\s+(?:belonging\s+to|related\s+to|in|about|on)|books\s+(?:belonging\s+to|related\s+to|in|about|on)|which\s+books\s+belong\s+to)\s+(.+)$", low)
    if m:
        target = m.group(1).strip()
        matched_subject = find_best_entity_match(target, subjects)
        if matched_subject:
            return f"BelongsTo(b, {matched_subject})", f"Find books classified under subject '{matched_subject.replace('_', ' ')}'"

    # 4. Borrowing queries
    # e.g., "who borrowed AI A Modern Approach?", "which student borrowed <book>?"
    m = re.search(r"^(?:who\s+(?:has\s+)?borrowed|which\s+student\s+borrowed|find\s+which\s+student\s+borrowed|find\s+student\s+who\s+borrowed)\s+(.+)$", low)
    if m:
        target = m.group(1).strip()
        matched_book = find_best_entity_match(target, books)
        if matched_book:
            return f"Borrowed(s, {matched_book})", f"Find which student borrowed '{matched_book.replace('_', ' ')}'"

    # e.g., "find books borrowed by Ravi", "which books did Ravi borrow?", "what did Ravi borrow?"
    m = re.search(r"^(?:find\s+books\s+borrowed\s+by|books\s+borrowed\s+by|which\s+books\s+did\s+(.+?)\s+borrow|what\s+did\s+(.+?)\s+borrow)$", low)
    if m:
        target = m.group(1) or m.group(2)
        if not target and "borrowed by" in low:
            target = low.split("borrowed by", 1)[1]
        target = target.strip()
        matched_student = find_best_entity_match(target, students)
        if matched_student:
            return f"Borrowed({matched_student}, b)", f"Find books borrowed by student '{matched_student.replace('_', ' ')}'"

    # 5. General listings
    if re.search(r"^(?:list\s+all\s+books|show\s+all\s+books|all\s+books|list\s+books|find\s+all\s+books)$", low):
        return "Book(b)", "List all books in the catalog"

    if re.search(r"^(?:list\s+all\s+authors|show\s+all\s+authors|all\s+authors|list\s+authors|find\s+all\s+authors)$", low):
        return "Author(a)", "List all authors"

    if re.search(r"^(?:list\s+all\s+students|show\s+all\s+students|all\s+students|list\s+students|find\s+all\s+students)$", low):
        return "Student(s)", "List all students"

    if re.search(r"^(?:who\s+is\s+a\s+library\s+user|list\s+library\s+users|who\s+are\s+the\s+library\s+users|library\s+users)$", low):
        return "LibraryUser(u)", "Find all recognized library users (derived via forward chaining)"

    # Check author specialization
    # e.g. "what is Russell's specialization", "specialization of Norvig"
    m = re.search(r"^(?:what\s+is\s+(.+?)'?s?\s+specialization|specialization\s+of\s+(.+))$", low)
    if m:
        target = (m.group(1) or m.group(2)).strip()
        matched_author = find_best_entity_match(target, authors)
        if matched_author:
            return f"SpecializesIn({matched_author}, s)", f"Find specialization of author '{matched_author.replace('_', ' ')}'"

    return None, None

def process_query(user_query: str, kb) -> Dict[str, Any]:
    """
    Main entry point for intelligent querying.
    Supports both direct First-Order Logic formulas and natural language queries.
    Provides detailed proof provenance, separating original vs. inferred facts.
    """
    text = user_query.strip()
    if not text:
        raise ValueError("Please enter a query.")

    fol_query = None
    intention = None
    is_nl = False

    # Check if query matches FOL syntax: Predicate(...)
    if "(" in text and text.endswith(")"):
        pred_candidate = text.split("(", 1)[0].strip()
        if pred_candidate in PREDICATES:
            fol_query = text
            intention = f"Direct First-Order Logic predicate evaluation for '{pred_candidate}'"
        else:
            raise ValueError(
                f"Unknown predicate '{pred_candidate}'. Known predicates: {', '.join(sorted(PREDICATES))}"
            )
    else:
        # Attempt natural language translation
        fol_query, intention = translate_natural_language_to_fol(text, kb)
        if fol_query:
            is_nl = True
        else:
            # Check if user typed something like "WrittenBy b Russell" without parens
            tokens = text.replace(",", " ").split()
            if tokens and tokens[0] in PREDICATES:
                p_name = tokens[0]
                args = tokens[1:]
                if len(args) == PREDICATES[p_name]:
                    fol_query = f"{p_name}({', '.join(args)})"
                    intention = f"Parsed FOL query for '{p_name}'"

    if not fol_query:
        return {
            "success": False,
            "error_type": "unsupported_syntax",
            "user_query": user_query,
            "explanation": (
                "The query could not be translated into a supported First-Order Logic expression. "
                "Please check the supported syntax guide below."
            ),
            "supported_syntax": get_supported_syntax_documentation()
        }

    # Execute the FOL query
    try:
        raw_result = answer_query(fol_query, kb)
    except Exception as exc:
        return {
            "success": False,
            "error_type": "evaluation_error",
            "user_query": user_query,
            "fol_query": fol_query,
            "explanation": str(exc),
            "supported_syntax": get_supported_syntax_documentation()
        }

    # Separate original and inferred supporting facts
    original_facts = []
    inferred_facts = []
    for sf in raw_result["supporting_facts"]:
        prov = sf.get("provenance", {})
        source = prov.get("source", "original")
        item = {
            "fact": sf["fact"],
            "predicate": sf["predicate"],
            "args": sf["args"],
            "source": source,
            "rule": prov.get("rule"),
            "rule_details": RULE_DESCRIPTIONS.get(prov.get("rule")),
            "substitution": prov.get("substitution", {})
        }
        if source == "inferred":
            inferred_facts.append(item)
        else:
            original_facts.append(item)

    # Format human-readable answers
    formatted_answers = []
    if raw_result["truth"]:
        if raw_result["matches"]:
            for match in raw_result["matches"]:
                parts = [f"{var} = {val.replace('_', ' ')}" for var, val in match.items()]
                formatted_answers.append(", ".join(parts))
        else:
            # Ground query, truth is True
            formatted_answers.append("True (Assertion holds in knowledge base)")
    else:
        formatted_answers = []

    # Build rich human-readable explanation
    detailed_explanation = build_detailed_explanation(
        raw_result, original_facts, inferred_facts, fol_query
    )

    return {
        "success": True,
        "user_query": user_query,
        "fol_query": fol_query,
        "is_natural_language": is_nl,
        "intention": intention,
        "truth": raw_result["truth"],
        "matches": raw_result["matches"],
        "formatted_answers": formatted_answers,
        "explanation": detailed_explanation,
        "original_facts": original_facts,
        "inferred_facts": inferred_facts,
        "all_supporting_facts": raw_result["supporting_facts"]
    }

def build_detailed_explanation(raw_result: dict, original_facts: list, inferred_facts: list, fol_query: str) -> str:
    """Construct an educational step-by-step reasoning explanation."""
    truth = raw_result["truth"]
    if not truth:
        return (
            f"The query **{fol_query}** evaluated to **False** because no fact in the active "
            "knowledge base (original ground database facts or forward-chained derived facts) "
            "could be unified with this formula."
        )

    num_matches = len(raw_result["matches"])
    explanation_parts = []
    if num_matches > 0:
        explanation_parts.append(
            f"Found **{num_matches}** valid variable substitution(s) satisfying **{fol_query}**."
        )
    else:
        explanation_parts.append(f"The formula **{fol_query}** is directly verified as **True**.")

    if original_facts:
        f_list = ", ".join(f"`{f['fact']}`" for f in original_facts[:3])
        more = f" (and {len(original_facts)-3} more)" if len(original_facts) > 3 else ""
        explanation_parts.append(f"Ground facts matched from SQLite storage: {f_list}{more}.")

    if inferred_facts:
        for inf in inferred_facts[:2]:
            r_id = inf.get("rule")
            r_info = inf.get("rule_details")
            r_name = r_info["name"] if r_info else r_id
            fol_repr = r_info["fol"] if r_info else ""
            explanation_parts.append(
                f"Inferred fact `{inf['fact']}` was derived using Rule **{r_id}** ({r_name}): `{fol_repr}`."
            )

    return " ".join(explanation_parts)

def get_supported_syntax_documentation() -> List[Dict[str, str]]:
    """Return documentation of supported FOL predicates and natural language query intentions."""
    return [
        {
            "Intention": "Find books by an author",
            "Natural Language Example": "Find books written by Russell",
            "FOL Syntax": "WrittenBy(b, Russell)",
            "Notes": "Returns all books with author Russell. Use lowercase variable 'b' or 'x'."
        },
        {
            "Intention": "Find author of a book",
            "Natural Language Example": "Who wrote AI A Modern Approach?",
            "FOL Syntax": "WrittenBy(AI_A_Modern_Approach, a)",
            "Notes": "Returns author name bound to variable 'a'."
        },
        {
            "Intention": "Find books by subject",
            "Natural Language Example": "Find books related to Artificial Intelligence",
            "FOL Syntax": "BelongsTo(b, Artificial_Intelligence)",
            "Notes": "Matches subject classification or author specialization (via R2)."
        },
        {
            "Intention": "Check book availability",
            "Natural Language Example": "Is AI A Modern Approach available?",
            "FOL Syntax": "Available(AI_A_Modern_Approach)",
            "Notes": "Evaluates to True if book has no active borrowing loan (Rule R4)."
        },
        {
            "Intention": "List all available books",
            "Natural Language Example": "Which books are available?",
            "FOL Syntax": "Available(b)",
            "Notes": "Binds variable 'b' to each currently available book."
        },
        {
            "Intention": "Find borrower of a book",
            "Natural Language Example": "Who borrowed Computer Networking?",
            "FOL Syntax": "Borrowed(s, Computer_Networking)",
            "Notes": "Returns student who currently has the book checked out."
        },
        {
            "Intention": "Find books borrowed by a student",
            "Natural Language Example": "Find books borrowed by Ravi",
            "FOL Syntax": "Borrowed(Ravi, b)",
            "Notes": "Returns active loans for student Ravi."
        },
        {
            "Intention": "Identify library users",
            "Natural Language Example": "Who is a library user?",
            "FOL Syntax": "LibraryUser(u)",
            "Notes": "Derived via Rule R1: Anyone who borrowed a book is a LibraryUser."
        },
        {
            "Intention": "List all catalog books",
            "Natural Language Example": "List all books",
            "FOL Syntax": "Book(b)",
            "Notes": "Unary predicate over all books in catalog."
        }
    ]
