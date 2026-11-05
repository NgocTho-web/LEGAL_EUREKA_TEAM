"""
vocabulary_loader.py
Loads the Real Estate Controlled Vocabulary JSON and provides fast, normalized lookups
by ID, Vietnamese canonical name, and aliases.
"""

import os
import json
import re
from typing import Dict, List, Optional, Set, Any


def normalize_text(text: str) -> str:
    """
    Normalizes Vietnamese text for case-insensitive, whitespace-tolerant matching.
    """
    if not text:
        return ""
    # Lowercase, collapse spaces
    cleaned = " ".join(str(text).strip().lower().split())
    # Remove surrounding punctuation
    cleaned = cleaned.strip(".,;:\"'()[]{}")
    return cleaned


class VocabularyLoader:
    def __init__(self, vocab_path: str = "real_estate_controlled_vocabulary.json"):
        if not os.path.isabs(vocab_path) and not os.path.exists(vocab_path):
            # Try finding in parent directory if called from subfolder
            candidates = [
                vocab_path,
                os.path.join("..", vocab_path),
                os.path.join(os.path.dirname(__file__), "..", vocab_path),
                os.path.join(os.path.dirname(__file__), "..", "..", vocab_path),
            ]
            for c in candidates:
                if os.path.exists(c):
                    vocab_path = c
                    break

        if not os.path.exists(vocab_path):
            raise FileNotFoundError(f"Cannot find controlled vocabulary at {vocab_path}")

        with open(vocab_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.concepts: Dict[str, Dict[str, Any]] = {}
        self.subjects: Dict[str, Dict[str, Any]] = {}
        self.conditions: Dict[str, Dict[str, Any]] = {}
        self.procedures: Dict[str, Dict[str, Any]] = {}

        self.concept_lookup: Dict[str, str] = {}
        self.subject_lookup: Dict[str, str] = {}
        self.condition_lookup: Dict[str, str] = {}
        self.procedure_lookup: Dict[str, str] = {}

        self._build_lookups()

    def _build_lookups(self):
        # 1. Legal Concepts
        for item in self.data.get("legal_concepts", []):
            cid = item["id"]
            self.concepts[cid] = item
            self._register_lookup(self.concept_lookup, item.get("name_vi"), cid)
            for alias in item.get("aliases", []):
                self._register_lookup(self.concept_lookup, alias, cid)

        # 2. Legal Subjects
        for item in self.data.get("legal_subjects", []):
            sid = item["id"]
            self.subjects[sid] = item
            self._register_lookup(self.subject_lookup, item.get("name_vi"), sid)
            for alias in item.get("aliases", []):
                self._register_lookup(self.subject_lookup, alias, sid)

        # 3. Legal Conditions
        for item in self.data.get("legal_conditions", []):
            cond_id = item["id"]
            self.conditions[cond_id] = item
            self._register_lookup(self.condition_lookup, item.get("name_vi"), cond_id)
            for alias in item.get("aliases", []):
                self._register_lookup(self.condition_lookup, alias, cond_id)

        # 4. Legal Procedures
        for item in self.data.get("legal_procedures", []):
            pid = item["id"]
            self.procedures[pid] = item
            self._register_lookup(self.procedure_lookup, item.get("name_vi"), pid)
            for alias in item.get("aliases", []):
                self._register_lookup(self.procedure_lookup, alias, pid)

    def _register_lookup(self, lookup_dict: Dict[str, str], text: Optional[str], target_id: str):
        if not text:
            return
        norm = normalize_text(text)
        if norm:
            lookup_dict[norm] = target_id

    def is_valid_id(self, entity_id: str) -> bool:
        return (
            entity_id in self.concepts or
            entity_id in self.subjects or
            entity_id in self.conditions or
            entity_id in self.procedures
        )

    def get_entity_type(self, entity_id: str) -> Optional[str]:
        if entity_id in self.concepts:
            return "LegalConcept"
        if entity_id in self.subjects:
            return "LegalSubject"
        if entity_id in self.conditions:
            return "LegalCondition"
        if entity_id in self.procedures:
            return "LegalProcedure"
        return None

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        return (
            self.concepts.get(entity_id) or
            self.subjects.get(entity_id) or
            self.conditions.get(entity_id) or
            self.procedures.get(entity_id)
        )

    def all_ids(self) -> Set[str]:
        return (
            set(self.concepts.keys()) |
            set(self.subjects.keys()) |
            set(self.conditions.keys()) |
            set(self.procedures.keys())
        )
