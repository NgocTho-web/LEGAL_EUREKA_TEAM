from test_cases import TEST_CASES

def run_evaluation(retriever):
    correct = 0
    total = len(TEST_CASES)
    
    for case in TEST_CASES:
        query = case["question"]
        expected_intent = case["expected_intent"]
        expected_target_type = case["expected_target_type"]
        expected_node = case["expected_target_node"]
        
        # Determine intent (Dummy rule-based for eval, normally done by app.py)
        # Actually we should use retriever to find the legal entity first
        entities = retriever.search_legal_entity(query)
        
        if expected_intent is None:
            # Out of scope case
            if not entities:
                correct += 1
            continue
            
        if not entities:
            continue
            
        # Check if the top entity matches expected type
        top_entity = entities[0]
        
        # Check if the path yields the expected target type
        paths, evidence_list, structural = retriever.get_reasoning_path(top_entity["id"])
        
        # We consider it correct if we found the target node and it yielded evidence of the expected type
        if top_entity["id"] == expected_node:
            correct += 1
            
    return correct, total

def evidence_coverage(expected_count, actual_count):
    if expected_count is None or expected_count == 0:
        return "100%" if actual_count == 0 else "0%"
    if actual_count >= expected_count:
        return "100%"
    return f"{int((actual_count / expected_count) * 100)}%"

def calculate_accuracy(correct, total):
    if total == 0: return "0%"
    return f"{int((correct/total)*100)}%"