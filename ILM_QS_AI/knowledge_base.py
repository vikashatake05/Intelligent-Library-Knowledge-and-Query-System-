"""Fact storage and knowledge synchronization for the Intelligent Library Knowledge and Query System."""
from dataclasses import dataclass
from typing import Iterable, Optional

@dataclass(frozen=True)
class Fact:
    predicate: str
    args: tuple[str, ...]

    def __str__(self):
        return f"{self.predicate}({', '.join(self.args)})"

    def to_dict(self):
        return {"Predicate": self.predicate, "Arguments": ", ".join(self.args), "Fact": str(self)}

class KnowledgeBase:
    def __init__(self, facts: Iterable[Fact] = ()):
        self.facts: list[Fact] = []
        self._set = set()
        self.provenance: dict[Fact, dict] = {}
        for fact in facts:
            self.add_fact(fact)

    def add_fact(self, fact: Fact, source="original", rule=None, substitution=None):
        if fact in self._set:
            return False
        self._set.add(fact)
        self.facts.append(fact)
        self.provenance[fact] = {
            "source": source,
            "rule": rule,
            "substitution": substitution or {}
        }
        return True

    def contains(self, fact: Fact) -> bool:
        return fact in self._set

    def by_predicate(self, predicate: str):
        return [f for f in self.facts if f.predicate == predicate]

    def count(self, predicate: str) -> int:
        return len(self.by_predicate(predicate))

    def original_facts(self):
        return [f for f in self.facts if self.provenance.get(f, {}).get("source") == "original"]

    def inferred_facts(self):
        return [f for f in self.facts if self.provenance.get(f, {}).get("source") == "inferred"]

    def to_rows(self):
        return [f.to_dict() | {"Type": self.provenance.get(f, {}).get("source", "original"),
                              "Rule": self.provenance.get(f, {}).get("rule") or "-"}
                for f in self.facts]

    def clear_inferred(self):
        """Discard all inferred facts, keeping only original database-backed facts."""
        keep = self.original_facts()
        self.facts, self._set, self.provenance = [], set(), {}
        for fact in keep:
            self.add_fact(fact, source="original")

    def remove_fact(self, fact: Fact):
        """Remove a fact and its provenance; return True when it existed."""
        if fact not in self._set:
            return False
        self._set.remove(fact)
        self.facts.remove(fact)
        self.provenance.pop(fact, None)
        return True

    def remove_where(self, predicate_fn):
        """Remove all facts matching a callback."""
        doomed = [fact for fact in self.facts if predicate_fn(fact)]
        for fact in doomed:
            self.remove_fact(fact)
        return len(doomed)

    def reload_from_db(self, db_path: Optional[str] = None):
        """
        Reload the knowledge base from SQLite persistent storage.
        Clears outdated facts and runs the forward-chaining inference engine.
        """
        import database
        from inference_engine import run_forward_chaining
        raw_facts = database.load_fol_facts_from_db(db_path) if db_path else database.load_fol_facts_from_db()
        self.facts, self._set, self.provenance = [], set(), {}
        for f in raw_facts:
            self.add_fact(f, source="original")
        run_forward_chaining(self)
