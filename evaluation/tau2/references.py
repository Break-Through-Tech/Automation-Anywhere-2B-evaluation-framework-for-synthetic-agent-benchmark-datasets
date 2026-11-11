"""Explicit domain entity bindings; no heuristic `_id` suffix matching."""


class ReferenceFailure(ValueError):
    """An argument does not resolve to an entity in the current state."""


def _require(mapping, value, label):
    if value not in mapping:
        raise ReferenceFailure(f"{label} {value!r} does not exist in current state")
    return mapping[value]


def validate_references(domain, env, action):
    """Return the number of checked bindings; raise on a missing relationship."""
    args = action["arguments"]
    db = env.tools.db
    checked = 0
    if domain == "retail":
        order = user = None
        if "order_id" in args:
            order = _require(db.orders, args["order_id"], "order")
            user = _require(db.users, order.user_id, "order owner")
            checked += 1
        if "user_id" in args:
            user = _require(db.users, args["user_id"], "user")
            if order and order.user_id != user.user_id:
                raise ReferenceFailure("Order does not belong to the supplied user")
            checked += 1
        if "product_id" in args:
            _require(db.products, args["product_id"], "product")
            checked += 1
        for field in ("item_id", "item_ids", "new_item_ids"):
            if field not in args:
                continue
            ids = args[field] if isinstance(args[field], list) else [args[field]]
            for value in ids:
                if not any(value in product.variants for product in db.products.values()):
                    raise ReferenceFailure(f"item {value!r} does not exist")
                if order and field == "item_ids" and not any(i.item_id == value for i in order.items):
                    raise ReferenceFailure(f"item {value!r} does not belong to order {order.order_id}")
                checked += 1
        if order and "new_item_ids" in args and "item_ids" in args:
            for old, new in zip(args["item_ids"], args["new_item_ids"]):
                product_id = next(i.product_id for i in order.items if i.item_id == old)
                _require(db.products[product_id].variants, new, "replacement variant of original product")
        if "payment_method_id" in args:
            if user is None:
                raise ReferenceFailure("Cannot resolve payment owner")
            _require(user.payment_methods, args["payment_method_id"], "owner's payment method")
            checked += 1
    elif domain == "airline":
        user = None
        if "reservation_id" in args:
            reservation = _require(db.reservations, args["reservation_id"], "reservation")
            user = _require(db.users, reservation.user_id, "reservation owner")
            checked += 1
        if "user_id" in args:
            supplied = _require(db.users, args["user_id"], "user")
            if user and user.user_id != supplied.user_id:
                raise ReferenceFailure("Reservation does not belong to user")
            user = supplied
            checked += 1
        for flight in args.get("flights", []):
            if "flight_number" in flight:
                found = _require(db.flights, flight["flight_number"], "flight")
                if "date" in flight:
                    _require(found.dates, flight["date"], "flight date")
                checked += 1
        payment_ids = ([args["payment_id"]] if "payment_id" in args else [])
        payment_ids += [p["payment_id"] for p in args.get("payment_methods", []) if "payment_id" in p]
        for payment_id in payment_ids:
            if user is None:
                raise ReferenceFailure("Cannot resolve payment owner")
            _require(user.payment_methods, payment_id, "owner's payment method")
            checked += 1
    elif domain == "telecom":
        if action["name"] == "get_details_by_id" and "id" in args:
            collections = {"C": ("customers", "customer_id"), "L": ("lines", "line_id"),
                           "D": ("devices", "device_id"), "B": ("bills", "bill_id"), "P": ("plans", "plan_id")}
            target = collections.get(args["id"][:1])
            if target is None:
                raise ReferenceFailure(f"Unknown entity ID type: {args['id']!r}")
            collection, field = target
            _require({getattr(v, field): v for v in getattr(db, collection)}, args["id"], field)
            checked += 1
        for field, collection in (("customer_id", "customers"), ("line_id", "lines"),
                                  ("plan_id", "plans"), ("bill_id", "bills"), ("device_id", "devices")):
            if field in args:
                mapping = {getattr(v, field): v for v in getattr(db, collection)}
                _require(mapping, args[field], field)
                checked += 1
        if "customer_id" in args and "line_id" in args:
            customer = next(c for c in db.customers if c.customer_id == args["customer_id"])
            if args["line_id"] not in customer.line_ids:
                raise ReferenceFailure("Line does not belong to customer")
        if "customer_id" in args and "bill_id" in args:
            bill = next(b for b in db.bills if b.bill_id == args["bill_id"])
            if bill.customer_id != args["customer_id"]:
                raise ReferenceFailure("Bill does not belong to customer")
    return checked
