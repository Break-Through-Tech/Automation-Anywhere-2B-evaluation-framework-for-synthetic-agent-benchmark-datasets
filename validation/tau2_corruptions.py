"""Construct defects from declared rules, never from mutated evaluator verdicts."""

from copy import deepcopy

from evaluation.tau2.runtime import fresh_environment

CAMPAIGNS = ("malformed_action", "unknown_tool", "wrong_type", "missing_argument",
             "unexpected_argument", "missing_entity", "broken_precondition")
ACTION_PATH = ["definition", "evaluation_criteria", "actions"]


def _unique_action(actions, name, arguments, requestor="assistant"):
    """Make a call descriptor without colliding with an existing action ID."""
    action_id = "__controlled_precondition__"
    existing = {a.get("action_id") for a in actions}
    while action_id in existing:
        action_id += "_"
    return {"action_id": action_id, "requestor": requestor, "name": name, "arguments": arguments}


def _domain_probe(domain, env):
    """A declared parameterized read for trajectories containing only no-arg tools."""
    if domain == "telecom":
        customer = sorted(env.tools.db.customers, key=lambda c: c.customer_id)[0]
        return "get_customer_by_id", {"customer_id": customer.customer_id}
    if domain == "airline":
        reservation = sorted(env.tools.db.reservations)[0]
        return "get_reservation_details", {"reservation_id": reservation}
    return "get_order_details", {"order_id": sorted(env.tools.db.orders)[0]}


def _domain_precondition(domain, env, actions, definition):
    """Choose a typed, grounded call that violates an explicit tool precondition.

    Expectations come from the pinned tool contracts, never corrupted verdicts.
    Do not guess post-initialization airline state: its controlled construction
    applies only when there are no initialization modifications.
    """
    if domain == "telecom":
        # The tool rejects gb_amount <= 0 regardless of line status. Initialization
        # functions in the benchmark do not delete these owned entities.
        initial = definition.get("initial_state") or {}
        if not isinstance(initial, dict) or initial.get("initialization_data"):
            return None
        for customer in sorted(env.tools.db.customers, key=lambda c: c.customer_id):
            lines = {line.line_id for line in env.tools.db.lines}
            line_id = next((key for key in customer.line_ids if key in lines), None)
            if line_id:
                action = _unique_action(actions, "refuel_data", {"customer_id": customer.customer_id,
                                        "line_id": line_id, "gb_amount": 0.0})
                return action, "refuel_amount_must_be_positive"
    if domain == "airline":
        initial = definition.get("initial_state") or {}
        if not isinstance(initial, dict) or any(initial.get(key) for key in ("initialization_data", "initialization_actions", "message_history")):
            return None
        # Use a different owner from every reference call, so a successful booking
        # cannot consume our certificate or alter our chosen reservation.
        owners = set()
        for action in actions:
            args = action["arguments"]
            if "user_id" in args:
                owners.add(args["user_id"])
            reservation = env.tools.db.reservations.get(args.get("reservation_id"))
            if reservation:
                owners.add(reservation.user_id)
        for key, reservation in sorted(env.tools.db.reservations.items()):
            user = env.tools.db.users[reservation.user_id]
            if user.user_id in owners:
                continue
            certificate = next((pid for pid, payment in sorted(user.payment_methods.items())
                                if payment.source == "certificate"), None)
            if certificate:
                action = _unique_action(actions, "update_reservation_baggages", {
                    "reservation_id": key, "total_baggages": reservation.total_baggages,
                    "nonfree_baggages": reservation.nonfree_baggages, "payment_id": certificate})
                return action, "certificate_cannot_pay_for_reservation_update"
    return None


def build_corruption_manifest(dataset):
    """Use schema/DB facts to declare corruption expectations independently.

    Fully specified vectors describe fail-fast blocking. Unsupported constructions
    are recorded; an unexercised named campaign stays inconclusive in the harness.
    """
    manifest = deepcopy(dataset)
    manifest.update(mutations=[], campaign_names=list(CAMPAIGNS), excluded_mutations=[])
    for entry in manifest["tasks"]:
        key, payload = entry["id"], entry["task"]
        definition = payload["definition"]
        actions = ((definition.get("evaluation_criteria") or {}).get("actions") or []) if isinstance(definition, dict) else []
        cases, rules = [], {}
        if isinstance(definition, dict) and isinstance(definition.get("evaluation_criteria"), dict) and "actions" in definition["evaluation_criteria"]:
            cases.append(("malformed_action", "schema", ACTION_PATH, ["invalid action"],
                          {"schema": 0, "signatures": None, "references": None, "output_consistency": None}))
        signature_vector = {"schema": 1, "signatures": 0, "references": None, "output_consistency": None}
        if actions and all(isinstance(a, dict) and isinstance(a.get("arguments"), dict) for a in actions):
            env, schemas, _ = fresh_environment(payload["source"])
            domain = payload["source"]["domain"]
            first = actions[0]
            cases.append(("unknown_tool", "signatures", ACTION_PATH + [0, "name"],
                          "__unknown_tool__", signature_vector))
            # Telecom often starts with no-argument user tools. Search the whole
            # trajectory, and otherwise append a known assistant read whose
            # required argument is malformed; do not mislabel an extra arg as a
            # type or missing-argument corruption.
            constructed_signatures = set()
            for index, action in enumerate(actions):
                args = action["arguments"]
                validator = schemas.get(action.get("requestor", "assistant"), {}).get(action["name"])
                if validator is None or not validator.is_valid(args):
                    continue
                if "wrong_type" not in constructed_signatures:
                    for field, value in args.items():
                        replacement = 123 if isinstance(value, str) else "__wrong_type__"
                        if not validator.is_valid({**args, field: replacement}):
                            cases.append(("wrong_type", "signatures", ACTION_PATH + [index, "arguments", field], replacement, signature_vector))
                            constructed_signatures.add("wrong_type")
                            break
                if "missing_argument" not in constructed_signatures:
                    field = next((k for k in validator.schema.get("required", []) if k in args), None)
                    if field:
                        reduced = {k: v for k, v in args.items() if k != field}
                        cases.append(("missing_argument", "signatures", ACTION_PATH + [index, "arguments"], reduced, signature_vector))
                        constructed_signatures.add("missing_argument")
                if len(constructed_signatures) == 2:
                    break
            if len(constructed_signatures) < 2:
                name, probe = _domain_probe(domain, env)
                if "wrong_type" not in constructed_signatures:
                    bad_args = {key: 123 for key in probe}
                    call = _unique_action(actions, name, bad_args)
                    cases.append(("wrong_type", "signatures", ACTION_PATH, actions + [call], signature_vector))
                if "missing_argument" not in constructed_signatures:
                    call = _unique_action(actions, name, {})
                    cases.append(("missing_argument", "signatures", ACTION_PATH, actions + [call], signature_vector))
            extra = {**first["arguments"], "__unexpected_argument__": True}
            cases.append(("unexpected_argument", "signatures", ACTION_PATH + [0, "arguments"], extra, signature_vector))
            # The first direct entity lookup is safe to corrupt without executing
            # a prefix to infer expected outcomes. A sentinel is checked against DB.
            mapping = ({"order_id": "orders", "user_id": "users", "product_id": "products"}
                       if domain == "retail" else
                       {"reservation_id": "reservations", "user_id": "users"} if domain == "airline" else
                       {"customer_id": "customers", "line_id": "lines", "bill_id": "bills",
                        "plan_id": "plans", "device_id": "devices"})
            for index, action in enumerate(actions):
                matching = next((field for field in mapping if field in action["arguments"]), None)
                if domain == "telecom" and action["name"] == "get_details_by_id" and "id" in action["arguments"]:
                    matching = "id"
                if matching:
                    sentinel = "__missing_entity__"
                    if matching == "id":
                        sentinel = "C__missing_entity__"
                        existing = {c.customer_id for c in env.tools.db.customers}
                    else:
                        collection = getattr(env.tools.db, mapping[matching])
                        existing = set(collection) if isinstance(collection, dict) else {getattr(v, matching) for v in collection}
                    while sentinel in existing:
                        sentinel += "_"
                    cases.append(("missing_entity", "references", ACTION_PATH + [index, "arguments", matching], sentinel,
                                  {"schema": 1, "signatures": 1, "references": 0, "output_consistency": None}))
                    break
            repeatable_failure = {"cancel_pending_order", "exchange_delivered_order_items",
                                  "return_delivered_order_items", "modify_pending_order_items"}
            # These retail tools consume a status precondition. Repeating the
            # final write preserves valid signatures/references but cannot succeed.
            if domain == "retail":
                writes = [a for a in actions if a["name"] in repeatable_failure]
                if writes:
                    duplicate = deepcopy(writes[-1])
                    if duplicate["name"] == "modify_pending_order_items":
                        # The first call replaces old items. Reverse the IDs so
                        # the duplicate still refers to items currently in the
                        # order; only the consumed status precondition is broken.
                        arguments = duplicate["arguments"]
                        arguments["item_ids"], arguments["new_item_ids"] = (
                            arguments["new_item_ids"], arguments["item_ids"])
                    duplicate["action_id"] = "__repeat_precondition__"
                    existing = {a.get("action_id") for a in actions}
                    while duplicate["action_id"] in existing:
                        duplicate["action_id"] += "_"
                    cases.append(("broken_precondition", "output_consistency", ACTION_PATH, actions + [duplicate],
                                  {"schema": 1, "signatures": 1, "references": 1, "output_consistency": 0}))
                    rules["broken_precondition"] = "repeat_consumed_order_status_precondition"
            else:
                precondition = _domain_precondition(domain, env, actions, definition)
                if precondition:
                    call, rule = precondition
                    cases.append(("broken_precondition", "output_consistency", ACTION_PATH, actions + [call],
                                  {"schema": 1, "signatures": 1, "references": 1, "output_consistency": 0}))
                    rules["broken_precondition"] = rule
        constructed = set()
        for kind, check, path, replacement, vector in cases:
            original = payload
            for component in path:
                original = original[component]
            if original == replacement:
                continue
            manifest["mutations"].append({"task_id": key, "kind": kind, "expected_check": check,
                                          "path": path, "replacement": replacement, "expected_checks": vector,
                                          "construction_rule": rules.get(kind, kind)})
            constructed.add(kind)
        manifest["excluded_mutations"].extend({"task_id": key, "kind": kind, "reason": "construction_not_applicable"}
                                               for kind in CAMPAIGNS if kind not in constructed)
    return manifest


def clean_retail_controls(dataset, size=20):
    """Independent cancellation controls using real DB facts and real tools.

    Expected labels/assertions follow the cancellation contract, not evaluator
    outputs. These are constructed controls, NOT human-reviewed benchmark labels.
    Human review provenance can be supplied separately through the CLI labels file.
    """
    if type(size) is not int or size < 1:
        raise ValueError("Control size must be a positive integer")
    source = dataset["tasks"][0]["task"]["source"]
    if source["domain"] != "retail":
        raise ValueError("Cancellation controls require retail")
    env, _, _ = fresh_environment(source)
    tasks = []
    for order_id, order in sorted(env.tools.db.orders.items()):
        if order.status != "pending" or not order.payment_history:
            continue
        user = env.tools.db.users.get(order.user_id)
        if not user or any(p.payment_method_id not in user.payment_methods for p in order.payment_history):
            continue
        key = f"cancel-control-{len(tasks):02}"
        definition = {"id": key, "user_scenario": {"instructions":
                      f"Cancel my pending order {order_id}; it is no longer needed. I confirm cancellation."},
                      "initial_state": None, "evaluation_criteria": {"actions": [
                          {"action_id": f"{key}-read", "name": "get_order_details", "arguments": {"order_id": order_id}},
                          {"action_id": f"{key}-cancel", "name": "cancel_pending_order", "arguments": {
                              "order_id": order_id, "reason": "no longer needed"}}], "reward_basis": ["DB"]}}
        tasks.append({"id": key, "expected_pass": True, "label_provenance": "constructed_tool_contract_control",
                      "task": {"source": deepcopy(source), "definition": definition, "expected_final_state": [
                          {"path": ["agent", "orders", order_id, "status"], "value": "cancelled"},
                          {"path": ["agent", "orders", order_id, "cancel_reason"], "value": "no longer needed"}]}})
        if len(tasks) == size:
            break
    if len(tasks) < size:
        raise ValueError(f"Only {len(tasks)} cancellation controls available; requested {size}")
    return {"dataset": "tau2/retail/constructed-controls", "subject": "constructed_reference_controls",
            "sources": deepcopy(source), "label_provenance": "Tool-contract constructions; no human review claimed",
            "tasks": tasks, "mutations": []}


def clean_controls(dataset, size=20):
    """Construct independently specified operational controls for each domain.

    Airline varies reservations/owners; telecom varies owned lines and initial
    device conditions, including both assistant and user tools. No reference
    benchmark task is automatically relabeled clean.
    """
    if type(size) is not int or size < 1:
        raise ValueError("Control size must be a positive integer")
    source = dataset["tasks"][0]["task"]["source"]
    domain = source["domain"]
    if domain == "retail":
        return clean_retail_controls(dataset, size)
    env, _, _ = fresh_environment(source)
    tasks = []

    def add(key, instructions, actions, assertions, initial=None):
        definition = {"id": key, "user_scenario": {"instructions": instructions},
                      "initial_state": initial, "evaluation_criteria": {"actions": actions, "reward_basis": ["DB"]}}
        tasks.append({"id": key, "expected_pass": True, "label_provenance": "constructed_tool_contract_control",
                      "task": {"source": deepcopy(source), "definition": definition,
                               "expected_final_state": assertions}})

    if domain == "airline":
        for reservation_id, reservation in sorted(env.tools.db.reservations.items()):
            user = env.tools.db.users[reservation.user_id]
            credit = next((pid for pid, payment in sorted(user.payment_methods.items())
                           if payment.source == "credit_card"), None)
            if not credit or reservation.status == "cancelled":
                continue
            key = f"baggage-control-{len(tasks):02}"
            total = reservation.total_baggages + 1
            nonfree = reservation.nonfree_baggages + 1
            actions = [{"action_id": f"{key}-read", "name": "get_reservation_details",
                        "arguments": {"reservation_id": reservation_id}},
                       {"action_id": f"{key}-update", "name": "update_reservation_baggages",
                        "arguments": {"reservation_id": reservation_id, "total_baggages": total,
                                      "nonfree_baggages": nonfree, "payment_id": credit}}]
            path = ["agent", "reservations", reservation_id]
            assertions = [{"path": path + ["total_baggages"], "value": total},
                          {"path": path + ["nonfree_baggages"], "value": nonfree},
                          {"path": path + ["payment_history", len(reservation.payment_history), "amount"], "value": 50}]
            add(key, f"Add one paid checked bag to reservation {reservation_id}. I confirm the $50 charge to {credit}.",
                actions, assertions)
            if len(tasks) == size:
                break
    elif domain == "telecom":
        for customer in sorted(env.tools.db.customers, key=lambda c: c.customer_id):
            for line_index, line in enumerate(env.tools.db.lines):
                if line.line_id not in customer.line_ids:
                    continue
                # Distinct line/device-condition combinations rather than copies
                # of a single control. All other source data stays unchanged.
                for airplane, data in ((False, False), (False, True), (True, False), (True, True)):
                    key = f"roaming-control-{len(tasks):02}"
                    owner = {"customer_id": customer.customer_id, "line_id": line.line_id}
                    initial = {"initialization_actions": [
                        {"env_type": "user", "func_name": "set_user_info", "arguments": {
                            "name": customer.full_name, "phone_number": line.phone_number}},
                        {"env_type": "assistant", "func_name": "disable_roaming", "arguments": owner},
                        {"env_type": "user", "func_name": "turn_roaming_off", "arguments": {}},
                        {"env_type": "user", "func_name": "turn_airplane_mode_on" if airplane else "turn_airplane_mode_off", "arguments": {}},
                        {"env_type": "user", "func_name": "turn_data_on" if data else "turn_data_off", "arguments": {}}]}
                    actions = [{"action_id": f"{key}-read", "name": "get_customer_by_id",
                                "arguments": {"customer_id": customer.customer_id}},
                               {"action_id": f"{key}-enable", "name": "enable_roaming", "arguments": owner},
                               {"action_id": f"{key}-device", "requestor": "user", "name": "toggle_roaming", "arguments": {}}]
                    assertions = [{"path": ["agent", "lines", line_index, "roaming_enabled"], "value": True},
                                  {"path": ["user", "device", "roaming_enabled"], "value": True},
                                  {"path": ["user", "surroundings", "roaming_allowed"], "value": True},
                                  {"path": ["user", "device", "data_enabled"], "value": data},
                                  {"path": ["user", "device", "airplane_mode"], "value": airplane}]
                    add(key, f"Enable international roaming for {line.phone_number} on the line and device; keep airplane/data settings unchanged.",
                        actions, assertions, initial)
                    if len(tasks) == size:
                        break
                if len(tasks) == size:
                    break
            if len(tasks) == size:
                break
    else:
        raise ValueError(f"Unsupported control domain: {domain}")
    if len(tasks) < size:
        raise ValueError(f"Only {len(tasks)} {domain} controls available; requested {size}")
    return {"dataset": f"tau2/{domain}/constructed-controls", "subject": "constructed_reference_controls",
            "sources": deepcopy(source), "label_provenance": "Tool-contract constructions; no human review claimed",
            "tasks": tasks, "mutations": []}
