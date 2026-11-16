from __future__ import annotations

import re

RULES: list[dict] = [
    {
        "id": "vpn",
        "any": ["vpn", "globalprotect", "pangps"],
        "boost": ["809", "error 809", "globalprotect", "authentication"],
        "playbook": "vpn_repair",
        "base": 0.90,
        "intent": "Incident",
        "category": "Network",
        "subcategory": "VPN",
        "priority": "P2",
        "urgency": "High",
        "impact": "Individual",
        "assignment_group": "Network Support",
        "configuration_item": "GlobalProtect VPN",
        "application": "GlobalProtect",
        "summary": "VPN authentication failure",
        "suggested_resolution": "VPN troubleshooting",
    },
    {
        "id": "password",
        "any": [
            "password expired",
            "password has expired",
            "expired password",
            "forgot my password",
            "reset my password",
            "password reset",
            "can't sign in",
            "cannot sign in",
        ],
        "boost": ["expired", "temporary password"],
        "playbook": "password_reset",
        "base": 0.88,
        "intent": "Incident",
        "category": "Identity",
        "subcategory": "Password",
        "priority": "P3",
        "urgency": "High",
        "impact": "Individual",
        "assignment_group": "Identity Operations",
        "configuration_item": "Entra ID",
        "application": "Entra ID",
        "summary": "Password expired",
        "suggested_resolution": "Issue a temporary Entra ID password and require a change at next sign-in",
    },
    {
        "id": "mfa",
        "any": ["mfa", "authenticator", "multi-factor", "multifactor", "mfa code"],
        "boost": ["authenticator", "new phone"],
        "playbook": "mfa_reset",
        "base": 0.87,
        "intent": "Incident",
        "category": "Identity",
        "subcategory": "MFA",
        "priority": "P3",
        "urgency": "High",
        "impact": "Individual",
        "assignment_group": "Identity Operations",
        "configuration_item": "Microsoft Authenticator",
        "application": "Microsoft Authenticator",
        "summary": "MFA method failing",
        "suggested_resolution": "Reset Microsoft Authenticator registration",
    },
    {
        "id": "unlock",
        "any": ["account locked", "locked out", "unlock my account", "too many sign-in", "account lockout"],
        "boost": ["locked"],
        "playbook": "account_unlock",
        "base": 0.87,
        "intent": "Incident",
        "category": "Identity",
        "subcategory": "Account unlock",
        "priority": "P3",
        "urgency": "High",
        "impact": "Individual",
        "assignment_group": "Identity Operations",
        "configuration_item": "Entra ID",
        "application": "Entra ID",
        "summary": "Account locked out",
        "suggested_resolution": "Clear the Entra ID lockout and confirm a sign-in",
    },
    {
        "id": "outlook",
        "any": ["outlook", "mailbox", "ost file", "out of sync"],
        "boost": ["synchron", "ost", "cache"],
        "playbook": "outlook_repair",
        "base": 0.84,
        "intent": "Incident",
        "category": "Collaboration",
        "subcategory": "Outlook",
        "priority": "P3",
        "urgency": "Medium",
        "impact": "Individual",
        "assignment_group": "Collaboration Support",
        "configuration_item": "Microsoft 365 Outlook",
        "application": "Outlook",
        "summary": "Outlook synchronization failure",
        "suggested_resolution": "Rebuild the Outlook cache after confirming the mailbox is healthy",
    },
    {
        "id": "teams",
        "any": ["microsoft teams", "teams meeting", "teams audio", "teams camera"],
        "boost": ["audio", "camera"],
        "playbook": None,
        "base": 0.8,
        "intent": "Incident",
        "category": "Collaboration",
        "subcategory": "Teams",
        "priority": "P3",
        "urgency": "Medium",
        "impact": "Individual",
        "assignment_group": "Collaboration Support",
        "configuration_item": "Microsoft Teams",
        "application": "Microsoft Teams",
        "summary": "Teams meeting audio or video issue",
        "suggested_resolution": "Reset Teams media permissions and rejoin the meeting",
    },
    {
        "id": "printer",
        "any": ["printer", "printing", "papercut", "print queue", "spooler", "follow-me", "follow me print"],
        "boost": ["papercut", "spooler"],
        "playbook": "printer_repair",
        "base": 0.84,
        "intent": "Incident",
        "category": "End User Computing",
        "subcategory": "Printing",
        "priority": "P3",
        "urgency": "Medium",
        "impact": "Individual",
        "assignment_group": "End User Computing",
        "configuration_item": "PaperCut Follow-Me Print",
        "application": "PaperCut",
        "summary": "Follow-me print queue stuck",
        "suggested_resolution": "Clear stuck PaperCut jobs and restart the spooler",
    },
    {
        "id": "disk",
        "any": ["disk space", "low disk", "disk full", "storage full", "c: drive", "c drive"],
        "boost": ["disk"],
        "playbook": "disk_cleanup",
        "base": 0.86,
        "intent": "Incident",
        "category": "End User Computing",
        "subcategory": "Disk space",
        "priority": "P3",
        "urgency": "Medium",
        "impact": "Individual",
        "assignment_group": "End User Computing",
        "configuration_item": "Windows 11 Standard Laptop",
        "application": "Windows 11",
        "summary": "Low disk space on the laptop",
        "suggested_resolution": "Clear temp files with the approved Storage Sense runbook",
    },
    {
        "id": "service",
        "any": ["service stopped", "windows service", "service won't start", "service will not start", "restart the service"],
        "boost": ["service"],
        "playbook": "service_restart",
        "base": 0.82,
        "intent": "Incident",
        "category": "End User Computing",
        "subcategory": "Windows service",
        "priority": "P3",
        "urgency": "Medium",
        "impact": "Individual",
        "assignment_group": "End User Computing",
        "configuration_item": "Windows 11 Standard Laptop",
        "application": "Windows 11",
        "summary": "Windows service stopped",
        "suggested_resolution": "Restart the named Windows service after an analyst confirms it",
    },
    {
        "id": "wifi",
        "any": ["wi-fi", "wifi", "northline-corp", "wireless"],
        "boost": ["northline-corp", "wifi"],
        "playbook": None,
        "base": 0.8,
        "intent": "Incident",
        "category": "Network",
        "subcategory": "Wi-Fi",
        "priority": "P4",
        "urgency": "Low",
        "impact": "Individual",
        "assignment_group": "Network Support",
        "configuration_item": "Northline-Corp SSID",
        "application": "Northline-Corp Wi-Fi",
        "summary": "Cannot join Northline-Corp Wi-Fi",
        "suggested_resolution": "Forget the network, renew the machine certificate, and rejoin Northline-Corp",
    },
]

LOCATIONS = [
    ("austin hq", "Austin HQ"),
    ("austin", "Austin HQ"),
    ("london", "London"),
    ("singapore", "Singapore"),
    ("remote", "Remote"),
    ("home", "Home"),
]


def _error_text(text: str) -> str:
    match = re.search(r"error\s*([0-9a-z]{3,})", text, flags=re.I)
    if match:
        return f"error {match.group(1)}"
    match = re.search(r"\b(0x[0-9a-f]{4,})\b", text, flags=re.I)
    if match:
        return match.group(1)
    return "None found"


def _location(text: str, profile: str) -> str:
    low = text.lower()
    for needle, label in LOCATIONS:
        if needle in low:
            return label
    return profile or "Not stated"


def _named_user(text: str, fallback: str) -> str:
    email = re.search(r"[\w.+-]+@northline\.com", text, flags=re.I)
    if email:
        return email.group(0)
    named = re.search(r"\buser\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", text)
    if named:
        return named.group(1)
    return fallback


def _apply_scope(rule: dict, text: str) -> dict:
    updated = dict(rule)
    low = text.lower()
    if any(phrase in low for phrase in ["all users", "entire office", "everyone in", "site down", "whole site"]):
        updated["impact"] = "Site"
        updated["priority"] = "P1"
        updated["urgency"] = "High"
    elif any(phrase in low for phrase in ["my team", "our floor", "several users", "group of users"]):
        updated["impact"] = "Group"
        if updated["priority"] == "P4":
            updated["priority"] = "P3"
        if updated["priority"] == "P3":
            updated["priority"] = "P2"
    return updated


def classify_text(text: str, user: dict | None = None) -> dict:
    user = user or {}
    low = text.lower().replace("’", "'")
    matches: list[tuple[float, dict, list[str]]] = []
    for rule in RULES:
        hits = [token for token in rule["any"] if token in low]
        if not hits:
            continue
        boosts = [token for token in rule["boost"] if token in low]
        score = min(0.95, rule["base"] + 0.015 * len(boosts))
        matches.append((score, rule, hits))

    if any(rule["id"] == "vpn" for _, rule, _ in matches):
        matches = [item for item in matches if item[1]["id"] not in {"password", "unlock"}]
    if any(rule["id"] == "printer" for _, rule, _ in matches):
        matches = [item for item in matches if item[1]["id"] != "service"]

    caller = user.get("name") or "the caller"
    if not matches:
        rationale = (
            "No approved intent rule matched the wording strongly enough to name a specialist queue. "
            f"Confidence is below the 0.62 human-escalation threshold, so this goes to the Service Desk queue. "
            f"Caller location {_location(text, user.get('location', ''))} comes from the employee profile."
        )
        return {
            "intent": "Incident",
            "category": "Service Desk",
            "subcategory": "General",
            "priority": "P3",
            "urgency": "Medium",
            "impact": "Individual",
            "assignment_group": "Service Desk",
            "configuration_item": "Employee Laptop",
            "summary": text.strip()[:80],
            "suggested_resolution": "Analyst review. The knowledge base did not provide an approved automated path.",
            "entities": {
                "application": "Not identified",
                "error_text": _error_text(text),
                "user": _named_user(text, caller),
                "location": _location(text, user.get("location", "")),
            },
            "confidence": 0.46,
            "rationale": rationale,
            "playbook_id": None,
            "matched_terms": [],
        }

    score, rule, hits = max(matches, key=lambda item: item[0])
    rule = _apply_scope(rule, text)
    terms = ", ".join(hits)
    rationale = (
        f"Matched {terms} and mapped the request to {rule['category']} / {rule['subcategory']}. "
        f"Impact is {rule['impact']} and urgency is {rule['urgency']}, so priority is {rule['priority']}. "
        f"Assignment group is {rule['assignment_group']}. Configuration item is {rule['configuration_item']}. "
        f"Caller location {_location(text, user.get('location', ''))} is taken from the words in the request or the employee profile."
    )
    return {
        "intent": rule["intent"],
        "category": rule["category"],
        "subcategory": rule["subcategory"],
        "priority": rule["priority"],
        "urgency": rule["urgency"],
        "impact": rule["impact"],
        "assignment_group": rule["assignment_group"],
        "configuration_item": rule["configuration_item"],
        "summary": rule["summary"],
        "suggested_resolution": rule["suggested_resolution"],
        "entities": {
            "application": rule["application"],
            "error_text": _error_text(text),
            "user": _named_user(text, caller),
            "location": _location(text, user.get("location", "")),
        },
        "confidence": round(score, 2),
        "rationale": rationale,
        "playbook_id": rule["playbook"],
        "matched_terms": hits,
    }
