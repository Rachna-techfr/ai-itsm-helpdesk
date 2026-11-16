from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app, store, servicenow


@pytest.fixture
def client():
    # Reset store for clean test run
    store.tickets = []
    store.software_requests = []
    store.audit_logs = []
    store._seed_if_empty()
    return TestClient(app)


def test_scenario_1_intelligent_ticket_vpn(client):
    """Scenario 1: Employee reports VPN failure -> AI extracts required fields -> ServiceNow Incident created."""
    user = {
        "id": "emma.walsh",
        "name": "Emma Walsh",
        "email": "emma.walsh@northline.com",
        "title": "Product Engineer",
        "department": "Engineering",
        "location": "Austin HQ",
        "employee_type": "Employee",
    }
    payload = {
        "message": "I cannot connect to VPN since this morning. Authentication keeps failing.",
        "user": user,
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Verify AI extracted output
    cls = data.get("classification")
    assert cls is not None
    assert cls["intent"] == "Incident"
    assert cls["category"] == "Network"
    assert cls["subcategory"] == "VPN"
    assert cls["priority"] == "P2"
    assert cls["urgency"] == "High"
    assert cls["impact"] == "Individual"
    assert cls["assignment_group"] == "Network Support"
    assert cls["summary"] == "VPN authentication failure"
    assert cls["suggested_resolution"] == "VPN troubleshooting"

    # Verify ServiceNow Incident creation
    ticket = data.get("ticket")
    assert ticket is not None
    assert ticket["number"].startswith("INC")
    assert ticket["status"] == "Open"
    assert ticket["servicenow"]["sys_id"] is not None
    assert "network" in ticket["servicenow"]["payload"]["category"].lower()


def test_scenario_2_self_healing_password(client):
    """Scenario 2: Password expired -> 7-stage autonomous self-heal -> ServiceNow marked Resolved + Audit log."""
    user = {
        "id": "alex.rivera",
        "name": "Alex Rivera",
        "email": "alex.rivera@northline.com",
        "title": "Senior Accountant",
        "department": "Finance",
        "location": "New York",
        "employee_type": "Employee",
    }
    payload = {
        "message": "My password has expired.",
        "user": user,
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["intent"] == "Automatable Issue"
    assert data["auto_resolved"] is True
    assert data["ticket"] is not None
    assert data["ticket"]["status"] == "Resolved"

    # Verify the 7 autonomous self-heal steps
    actions = data.get("proposed_actions", [])
    assert len(actions) > 0
    steps = actions[0].get("steps", [])
    step_names = [s["name"] for s in steps]
    assert any("identify" in n.lower() for n in step_names)
    assert any("diagnose" in n.lower() for n in step_names)
    assert any("knowledge" in n.lower() for n in step_names)
    assert any("determine" in n.lower() for n in step_names)
    assert any("execute" in n.lower() for n in step_names)
    assert any("validate" in n.lower() for n in step_names)

    # Verify audit log was recorded
    audit_resp = client.get("/api/audit")
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    assert len(logs) > 0
    assert any(log["ticket_number"] == data["ticket"]["number"] for log in logs)


def test_scenario_3_rag_outlook_sync(client):
    """Scenario 3: RAG Knowledge search -> Vector similarity -> Grounded answer + Sources cited."""
    payload = {
        "message": "How do I troubleshoot Outlook synchronization?",
        "user": {
            "id": "priya.nair",
            "name": "Priya Nair",
            "email": "priya.nair@northline.com",
            "department": "HR",
        },
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["knows"] is True
    assert len(data["citations"]) > 0
    top_citation = data["citations"][0]
    assert "KB0005" in top_citation["id"] or "outlook" in top_citation["title"].lower()
    assert "ost" in data["reply"].lower() or "cache" in data["reply"].lower() or "outlook" in data["reply"].lower()


def test_scenario_4_software_provisioning(client):
    """Scenario 4: Request VS Code -> Intent detection -> Catalog -> ServiceNow Request -> Provisioning."""
    payload = {
        "message": "I need Visual Studio Code installed on my laptop.",
        "user": {
            "id": "jordan.lee",
            "name": "Jordan Lee",
            "email": "jordan.lee@northline.com",
            "department": "Engineering",
            "employee_type": "Employee",
        },
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["intent"] == "Service Request"
    req = data.get("software_request")
    assert req is not None
    assert req["number"].startswith("REQ")
    assert "Visual Studio Code" in req["software"]
    assert req["status"] in ("Provisioning", "Completed")
    assert req["servicenow"] is not None


def test_scenario_5_unknown_question_safety(client):
    """Scenario 5: Unsupported query -> No hallucination refusal -> Escalation offered."""
    payload = {
        "message": "How do I bake sourdough bread on company time?",
        "user": {
            "id": "test.user",
            "name": "Test User",
            "email": "test@northline.com",
            "department": "General",
        },
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["knows"] is False
    assert data["offer_ticket"] is True
    assert "Approved Knowledge Base Content Insufficient" in data["reply"] or "no verified guidance" in data["reply"].lower()


def test_contractor_policy_denial(client):
    """Policy Governance: Contractors requesting restricted software get rejected cleanly."""
    payload = {
        "item_id": "figma",
        "justification": "Need it for UI testing",
        "user": {
            "id": "contractor.sam",
            "name": "Sam Contractor",
            "email": "sam.c@external.com",
            "department": "Design",
            "employee_type": "Contractor",
        },
    }
    resp = client.post("/api/requests", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["eligible"] is False
    assert "not issued to contractors" in data["reason"].lower()


def test_dashboard_metrics(client):
    """Verify ITSM Dashboard statistics endpoint."""
    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_tickets" in stats
    assert "ai_resolved" in stats
    assert "automation_rate" in stats
    assert "mttr_minutes" in stats

