from __future__ import annotations


def software_decision(item: dict, user: dict) -> dict:
    """Eligibility and approval for a catalog item. Pure function used by the API and tests."""
    departments = item.get("departments") or ["*"]
    department = user.get("department") or "Unknown"
    name = user.get("name") or "The requester"
    if "*" not in departments and department not in departments:
        allowed = ", ".join(departments)
        return {
            "eligible": False,
            "approval_required": False,
            "reason": f"{item['name']} is limited to {allowed}. {name} is in {department}, so the request stops before a catalog task is opened.",
        }
    if item.get("contractors_allowed") is False and user.get("employee_type") == "Contractor":
        return {
            "eligible": False,
            "approval_required": False,
            "reason": f"{item['name']} is not issued to contractors. {name} is flagged as a contractor on the employee record.",
        }

    reason = item.get("approval_reason") or ""
    total = item.get("licenses_total")
    used = item.get("licenses_used")
    if isinstance(total, int) and isinstance(used, int):
        free = total - used
        reason = f"{reason} License pool: {used} of {total} assigned ({free} free)."
        if free <= 0 and item.get("approval") == "none":
            return {
                "eligible": True,
                "approval_required": True,
                "reason": reason + " The pool is exhausted, so a manager must free or buy a seat before provisioning.",
            }
    if item.get("approval") == "none":
        return {"eligible": True, "approval_required": False, "reason": reason}
    return {"eligible": True, "approval_required": True, "reason": reason}
