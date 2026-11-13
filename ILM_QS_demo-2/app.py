import streamlit as st
import pandas as pd
from knowledge_base import KnowledgeBase, Fact
from data import sample_facts
from inference_engine import run_forward_chaining
from query_engine import answer_query, PREDICATES
from unification import parse_predicate, unify_predicates, UnificationError
from utils import validate_fact, predicate_reference
import json, os

st.set_page_config(page_title="Intelligent Library FOL", page_icon="📚", layout="wide")
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#071426 0%,#0b1d35 55%,#10294a 100%); color:#edf4ff;}
section[data-testid="stSidebar"] {background:#081629;}
h1,h2,h3 {color:#e8f2ff;}
div[data-testid="stMetric"] {background:#102846;padding:16px;border:1px solid #24486d;border-radius:12px;}
.stButton>button {background:#1769aa;color:white;border-radius:9px;border:0;}
div[data-testid="stDataFrame"] {border:1px solid #24486d;border-radius:10px;}
.small-muted {color:#9db4ce;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_kb():
    kb = KnowledgeBase(sample_facts())
    return kb
kb = get_kb()

st.sidebar.title("📚 Library Intelligence")
page = st.sidebar.radio("Navigate",[
    "Dashboard","Knowledge Base","Ontology","Logical Rules",
    "Inference Engine","Unification Demo","Intelligent Query",
    "Library Explorer","Documentation"
])
st.sidebar.caption("First-Order Logic • Knowledge Representation • Inference")

def show_fact_table(facts=None):
    rows = [f.to_dict() | {"Type":kb.provenance[f]["source"],"Rule":kb.provenance[f]["rule"] or "-"}
            for f in (facts if facts is not None else kb.facts)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

if page == "Dashboard":
    st.title("Intelligent Library Knowledge and Query System")
    st.caption("An explainable First-Order Logic engine for a college library.")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Books",kb.count("Book")); c2.metric("Authors",kb.count("Author"))
    c3.metric("Students",kb.count("Student")); c4.metric("Library users",kb.count("LibraryUser"))
    c5,c6,c7,c8 = st.columns(4)
    c5.metric("Borrowing records",kb.count("Borrowed"))
    c6.metric("Available books",kb.count("Available"))
    c7.metric("Total known facts",len(kb.facts))
    c8.metric("Inferred facts",len(kb.inferred_facts()))
    st.subheader("Knowledge base snapshot")
    st.write("The sample library includes books, people, subjects, departments, authorship and borrowing relations.")
    st.bar_chart(pd.DataFrame({"Facts":[kb.count(p) for p in ["Book","Author","Student","Faculty","Borrowed","Available"]],
                               "Predicate":["Book","Author","Student","Faculty","Borrowed","Available"]}).set_index("Predicate"))
    with st.expander("Recent facts"):
        show_fact_table(kb.facts[-15:])

elif page == "Knowledge Base":
    st.title("Knowledge Base")
    st.write("Each row is a ground atomic formula. Lowercase variables belong in queries, not stored facts.")
    col1,col2 = st.columns([2,1])
    with col1:
        search = st.text_input("Search facts",placeholder="e.g. Ravi or Artificial_Intelligence")
    with col2:
        pred = st.selectbox("Filter predicate",["All"]+sorted(PREDICATES))
    filtered = [f for f in kb.facts if (pred=="All" or f.predicate==pred) and search.lower() in str(f).lower()]
    show_fact_table(filtered)
    st.subheader("Add a fact")
    st.caption("Example: Book(New_AI_Book) or WrittenBy(New_AI_Book, Russell)")
    fact_text = st.text_input("Fact expression",key="new_fact")
    if st.button("Add fact"):
        try:
            p,args = validate_fact(fact_text)
            if kb.add_fact(Fact(p,args)):
                st.success(f"Added {Fact(p,args)}")
            else: st.info("That fact already exists; duplicates are ignored.")
        except Exception as e: st.error(str(e))
    if st.button("Export knowledge base as JSON"):
        payload=[{"predicate":f.predicate,"args":list(f.args),"source":kb.provenance[f]["source"]} for f in kb.facts]
        st.download_button("Download JSON",json.dumps(payload,indent=2),"library_knowledge_base.json","application/json")

elif page == "Ontology":
    st.title("Library Ontology")
    st.write("Entities are represented by unary predicates; relationships are represented by binary predicates.")
    st.graphviz_chart("""
    digraph Library {
      graph [bgcolor="transparent", rankdir=LR];
      node [shape=box, style="rounded,filled", fillcolor="#12385c", color="#56a5e8", fontcolor="white"];
      edge [color="#78b9ed", fontcolor="white"];
      Book; Author; Subject; Student; Faculty; LibraryUser; BorrowingRecord; Department;
      Author -> Book [label="WrittenBy"];
      Book -> Subject [label="BelongsTo"];
      Author -> Subject [label="SpecializesIn"];
      Student -> LibraryUser [label="is-a / inferred"];
      Faculty -> LibraryUser [label="library role"];
      Student -> Department [label="MemberOf"];
      Faculty -> Department [label="MemberOf"];
      LibraryUser -> BorrowingRecord [label="Borrowed"];
      BorrowingRecord -> Book [label="references"];
      Book -> Book [label="Available / not borrowed"];
    }
    """)
    st.subheader("Predicate dictionary")
    st.dataframe(pd.DataFrame(predicate_reference(),columns=["Predicate","Meaning"]),use_container_width=True,hide_index=True)

elif page == "Logical Rules":
    st.title("Executable Logical Rules")
    from rules import RULES
    for r in RULES:
        with st.expander(f"{r['id']} · {r['name']}",expanded=True):
            st.latex(r["fol"].replace("∀","\\forall ").replace("∧","\\land ").replace("¬","\\neg ").replace("→","\\rightarrow "))
            st.write("**English:**",r["english"])
            st.write("**Premises:**",", ".join(r["premises"]))
            st.write("**Conclusion:**",r["conclusion"])
            if r.get("note"): st.warning(r["note"])

elif page == "Inference Engine":
    st.title("Forward-Chaining Inference Engine")
    st.write("The engine repeatedly joins rule premises against facts until the positive rules reach a fixed point. Availability is then checked using the full borrowing relation.")
    if st.button("▶ Run forward chaining"):
        result=run_forward_chaining(kb)
        st.session_state["last_inference"]=result
        st.success(f"Completed: {result['derived_count']} new facts derived.")
    result=st.session_state.get("last_inference")
    if result:
        a,b,c=st.columns(3); a.metric("Initial facts",result["initial_count"]); b.metric("Derived this run",result["derived_count"]); c.metric("Final facts",result["final_count"])
        st.subheader("Execution trace")
        if result["steps"]:
            st.dataframe(pd.DataFrame([{"Rule":x["rule"],"Substitution":str(x["substitution"]),"Derived fact":x["derived"]} for x in result["steps"]]),use_container_width=True,hide_index=True)
        else: st.info("No new facts were needed; the knowledge base is already at a fixed point.")
    with st.expander("Original facts"): show_fact_table(kb.original_facts())
    with st.expander("Inferred facts"): show_fact_table(kb.inferred_facts())
    with st.expander("Complete knowledge base"): show_fact_table()

elif page == "Unification Demo":
    st.title("First-Order Logic Unification")
    left=st.text_input("Predicate 1","Borrowed(x, AI_Book)")
    right=st.text_input("Predicate 2","Borrowed(Ravi, AI_Book)")
    if st.button("Unify predicates"):
        try:
            lp,la=parse_predicate(left); rp,ra=parse_predicate(right)
            steps=[]
            subst,steps=unify_predicates((lp,la),(rp,ra),steps)
            st.success("Unification successful")
            st.code(str(subst) if subst else "{}")
            st.subheader("Unification trace")
            for i,s in enumerate(steps,1): st.write(f"{i}. {s}")
        except Exception as e: st.error(f"Unification failed: {e}")

elif page == "Intelligent Query":
    st.title("Intelligent Query System")
    st.write("Enter a predicate query. Use lowercase variable names such as x, y, author.")
    examples=["LibraryUser(Ravi)","Borrowed(Ravi, x)","WrittenBy(x, Russell)",
              "BelongsTo(x, Artificial_Intelligence)","Available(x)",
              "Book(AI_A_Modern_Approach)"]
    sample=st.selectbox("Try a sample query",examples)
    query=st.text_input("FOL query",sample)
    if st.button("Execute query"):
        try:
            result=answer_query(query,kb)
            if result["truth"]: st.success("TRUE · Matching substitution(s) found")
            else: st.error("FALSE · No matching fact found")
            st.write("**Substitutions:**",result["matches"])
            st.write("**Explanation:**",result["explanation"])
            if result["supporting_facts"]:
                st.subheader("Supporting facts and provenance")
                st.dataframe(pd.DataFrame([{"Fact":x["fact"],"Source":x["provenance"].get("source"),
                                            "Rule":x["provenance"].get("rule") or "Original",
                                            "Substitution":str(x["provenance"].get("substitution",{}))}
                                           for x in result["supporting_facts"]]),use_container_width=True,hide_index=True)
        except Exception as e: st.error(f"Invalid query: {e}")
    st.info("Run the Inference Engine first to derive rules-based facts such as LibraryUser(Ravi), HasBorrowed(...), and Available(...).")

elif page == "Library Explorer":
    st.title("Library Explorer")
    kind=st.selectbox("Explore",["Books","Authors","Subjects","Students","Faculty","Departments","Borrowing records"])
    mapping={"Books":"Book","Authors":"Author","Subjects":"Subject","Students":"Student","Faculty":"Faculty","Departments":"Department","Borrowing records":"Borrowed"}
    facts=kb.by_predicate(mapping[kind])
    st.dataframe(pd.DataFrame([{"Fact":str(f),"Arguments":", ".join(f.args)} for f in facts]),use_container_width=True,hide_index=True)
    if kind=="Books":
        chosen=st.selectbox("Select a book",[f.args[0] for f in facts])
        st.write("**Authorship**", [str(f) for f in kb.by_predicate("WrittenBy") if f.args[0]==chosen])
        st.write("**Subject**", [str(f) for f in kb.by_predicate("BelongsTo") if f.args[0]==chosen])
        st.write("**Borrowing**", [str(f) for f in kb.by_predicate("Borrowed") if f.args[1]==chosen])

else:
    st.title("Project Documentation")
    sections=[
    ("1. First-Order Logic","FOL is a formal language used to describe objects, their properties and relationships. For example, Book(AI_Book) says AI_Book is a book."),
    ("2. Knowledge Base","A knowledge base is a collection of facts and rules. Facts describe known information; rules let the system derive additional information."),
    ("3. Predicates and Constants","A predicate describes a property or relationship. Book(x) is unary; WrittenBy(book, author) is binary. Constants name specific entities such as Ravi."),
    ("4. Variables","Variables such as x, y and book stand for unknown or general entities. A query like Borrowed(Ravi, x) asks which values of x make the formula true."),
    ("5. Logical Inference Rules","Rules express implications. Borrowed(x,y) → LibraryUser(x) means every borrower can be inferred to be a library user."),
    ("6. Forward Chaining","Forward chaining starts with known facts, finds rule premises that match, adds conclusions, and repeats until no new facts can be added."),
    ("7. Unification","Unification finds substitutions that make two predicates identical. Borrowed(x,AI_Book) and Borrowed(Ravi,AI_Book) unify with x=Ravi."),
    ("8. Intelligent Query Processing","The query parser reads a predicate, checks its signature, then unifies it against facts. Matching substitutions and provenance are returned."),
    ("9. AI Demonstration","The project demonstrates symbolic AI: explicit knowledge representation, rule-based reasoning, variable binding, explainable inference and query answering.")
    ]
    for title,body in sections:
        with st.expander(title,expanded=True): st.write(body)
    st.warning("Modeling note: the sample uses a closed-world interpretation for current borrowing records. In a production library, returns, due dates and historical loans would need explicit status/time predicates.")
