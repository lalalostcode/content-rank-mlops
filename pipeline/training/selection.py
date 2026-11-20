from pipeline.evaluation.ranking import LEARNED_STRATEGIES


GATE_CRITERIA = {
    "primary_k": 50, "minimum_macro_precision_delta_exclusive": 0.0,
    "maximum_client_precision_regression": 0.10, "require_both_label_values": True,
}
EPSILON = 1e-12


def evaluate_gate(method, criteria):
    k = str(criteria["primary_k"])
    delta = method["macro_delta_vs_rule"][k]["precision"]
    clients = method["clients"]
    positives = sum(values["positives"] for values in clients.values())
    eligible_rows = method["coverage"]["eligible_rows"]
    regressions = {
        client: values["at_k"][k]["precision_delta_vs_rule"]
        for client, values in clients.items()
        if values["eligible_rows"] and values["at_k"][k]["precision_delta_vs_rule"] < -EPSILON
    }
    max_regression = criteria["maximum_client_precision_regression"]
    severe = sorted(client for client, value in regressions.items() if value < -max_regression - EPSILON)
    checks = {
        "beats_rule": delta is not None and delta > criteria["minimum_macro_precision_delta_exclusive"] + EPSILON,
        "client_regression_limit": not severe,
        "label_coverage": not criteria["require_both_label_values"] or 0 < positives < eligible_rows,
    }
    return {"passed": all(checks.values()), "checks": checks, "macro_precision_delta": delta,
            "client_precision_regressions": regressions, "clients_over_regression_limit": severe}


def freeze_candidate(development):
    gates = {name: evaluate_gate(development[name], GATE_CRITERIA) for name in LEARNED_STRATEGIES}
    eligible = [name for name in LEARNED_STRATEGIES if gates[name]["passed"]]

    def key(name):
        metrics = development[name]["macro"][str(GATE_CRITERIA["primary_k"])]
        return metrics["precision"], metrics["ndcg"]

    # Candidate order breaks exact ties in favor of the simpler strategy.
    candidate = max(eligible or LEARNED_STRATEGIES, key=key)
    return {"candidate": candidate, "gate_criteria": GATE_CRITERIA,
            "development_gates": gates, "development_passed": gates[candidate]["passed"]}
