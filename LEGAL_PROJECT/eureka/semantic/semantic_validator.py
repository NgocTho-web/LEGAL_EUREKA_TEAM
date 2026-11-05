"""
semantic_validator.py
Validates extraction outputs against the Controlled Vocabulary:
- Verifies that all entity IDs exist in the vocabulary (no new entities).
- Verifies output JSON schema compliance.
- Ensures no duplicate relations or self-loops exist.
"""

from typing import Dict, List, Set, Tuple, Any, Optional
from .vocabulary_loader import VocabularyLoader


class SemanticValidator:
    def __init__(self, vocab: VocabularyLoader):
        self.vocab = vocab

    def validate_item(self, item: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validates a single extraction result dictionary.
        Returns:
            is_valid (bool), error_messages (List[str]), cleaned_item (Dict[str, Any])
        """
        errors = []
        comp_id = item.get("component_id")

        if not comp_id or not isinstance(comp_id, str):
            errors.append(f"Invalid or missing 'component_id': {comp_id}")
            return False, errors, {}

        # 1. Validate regulates_concepts
        raw_concepts = item.get("regulates_concepts", [])
        if not isinstance(raw_concepts, list):
            errors.append(f"'regulates_concepts' must be a list, got {type(raw_concepts)}")
            clean_concepts = []
        else:
            clean_concepts = []
            seen_c = set()
            for cid in raw_concepts:
                if cid in self.vocab.concepts:
                    if cid not in seen_c:
                        seen_c.add(cid)
                        clean_concepts.append(cid)
                else:
                    errors.append(f"Concept ID '{cid}' does not exist in controlled vocabulary!")

        # 2. Validate applies_to_subjects
        raw_subjects = item.get("applies_to_subjects", [])
        if not isinstance(raw_subjects, list):
            errors.append(f"'applies_to_subjects' must be a list, got {type(raw_subjects)}")
            clean_subjects = []
        else:
            clean_subjects = []
            seen_s = set()
            for sid in raw_subjects:
                if sid in self.vocab.subjects:
                    if sid not in seen_s:
                        seen_s.add(sid)
                        clean_subjects.append(sid)
                else:
                    errors.append(f"Subject ID '{sid}' does not exist in controlled vocabulary!")

        # 3. Validate conditions
        raw_conditions = item.get("conditions", [])
        if not isinstance(raw_conditions, list):
            errors.append(f"'conditions' must be a list, got {type(raw_conditions)}")
            clean_conditions = []
        else:
            clean_conditions = []
            seen_cond = set()
            for cond_id in raw_conditions:
                if cond_id in self.vocab.conditions:
                    if cond_id not in seen_cond:
                        seen_cond.add(cond_id)
                        clean_conditions.append(cond_id)
                else:
                    errors.append(f"Condition ID '{cond_id}' does not exist in controlled vocabulary!")

        # 4. Validate procedures
        raw_procedures = item.get("procedures", [])
        if not isinstance(raw_procedures, list):
            errors.append(f"'procedures' must be a list, got {type(raw_procedures)}")
            clean_procedures = []
        else:
            clean_procedures = []
            seen_p = set()
            for pid in raw_procedures:
                if pid in self.vocab.procedures:
                    if pid not in seen_p:
                        seen_p.add(pid)
                        clean_procedures.append(pid)
                else:
                    errors.append(f"Procedure ID '{pid}' does not exist in controlled vocabulary!")

        cleaned_item = {
            "component_id": comp_id,
            "regulates_concepts": clean_concepts,
            "applies_to_subjects": clean_subjects,
            "conditions": clean_conditions,
            "procedures": clean_procedures
        }

        is_valid = len(errors) == 0
        return is_valid, errors, cleaned_item

    def build_unique_relations(self, validated_items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Constructs deduplicated, validated Neo4j relation rows:
        :START_ID, :END_ID, :TYPE
        """
        seen_edges: Set[Tuple[str, str, str]] = set()
        relations: List[Dict[str, str]] = []

        for item in validated_items:
            comp_id = item["component_id"]

            # REGULATES -> LegalConcept
            for cid in item["regulates_concepts"]:
                edge = (comp_id, cid, "REGULATES")
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    relations.append({":START_ID": comp_id, ":END_ID": cid, ":TYPE": "REGULATES"})

            # APPLIES_TO -> LegalSubject
            for sid in item["applies_to_subjects"]:
                edge = (comp_id, sid, "APPLIES_TO")
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    relations.append({":START_ID": comp_id, ":END_ID": sid, ":TYPE": "APPLIES_TO"})

            # HAS_CONDITION -> LegalCondition
            for cond_id in item["conditions"]:
                edge = (comp_id, cond_id, "HAS_CONDITION")
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    relations.append({":START_ID": comp_id, ":END_ID": cond_id, ":TYPE": "HAS_CONDITION"})

                # Also link primary regulates concept to condition if concepts exist
                for cid in item["regulates_concepts"]:
                    c_cond_edge = (cid, cond_id, "HAS_CONDITION")
                    if c_cond_edge not in seen_edges:
                        seen_edges.add(c_cond_edge)
                        relations.append({":START_ID": cid, ":END_ID": cond_id, ":TYPE": "HAS_CONDITION"})

            # REGULATES -> LegalProcedure
            for pid in item["procedures"]:
                edge = (comp_id, pid, "REGULATES")
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    relations.append({":START_ID": comp_id, ":END_ID": pid, ":TYPE": "REGULATES"})

        return relations

    def validate_has_procedure_relation(self, concept_id: str, procedure_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validates that concept_id is an existing LegalConcept and procedure_id is an existing LegalProcedure.
        """
        if concept_id not in self.vocab.concepts:
            return False, f"Concept '{concept_id}' not found in vocabulary."
        if procedure_id not in self.vocab.procedures:
            return False, f"Procedure '{procedure_id}' not found in vocabulary."
        return True, None

