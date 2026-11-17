from __future__ import annotations

import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.agent import HelpdeskAgent
from app.config import load_settings
from app.embeddings import Embedder
from app.policy import software_decision
from app.rag import RAGEngine
from app.schemas import (
    ArticleOut,
    CatalogItemOut,
    CatalogRequestIn,
    ChatIn,
    ChatOut,
    DecideIn,
    HealthOut,
    IntakeIn,
    SearchOut,
    SoftwareRequestOut,
    TicketOut,
)
from app.servicenow import ServiceNowClient
from app.store import DataStore
from app.util import now_iso, snow_sys_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Load settings and initialize singletons
settings = load_settings()
embedder = Embedder(backend=settings.embedding_backend)
servicenow = ServiceNowClient(settings)
store = DataStore(settings, embedder)
servicenow.sync_counters_from_store(store.tickets, store.software_requests)
rag = RAGEngine(settings, embedder, store)
agent = HelpdeskAgent(settings, store, rag, servicenow)

app = FastAPI(
    title="SORIM.AI — Autonomous ITSM Helpdesk Engine",
    description="Enterprise IT Service Management with FAISS Vector Search, RAG, Self-Healing Agents, and ServiceNow Integration",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthOut)
def get_health() -> dict:
    total_tickets = len(store.tickets)
    ai_resolved = len([t for t in store.tickets if t.get("ai_resolved")])
    return {
        "status": "operational",
        "service": "SORIM.AI ITSM Engine",
        "provider": "Hugging Face / Open Source",
        "provider_label": f"Hugging Face ({settings.hf_model})" if settings.hf_token else f"Hugging Face Open-Source ({settings.hf_model}) / Grounded Synthesizer",
        "provider_note": "FAISS FlatIP 384-dim dense vector database with all-MiniLM-L6-v2 embeddings.",
        "model": settings.hf_model,
        "store": "MongoDB Atlas" if store.use_mongo else "Local Persistent JSON Store",
        "servicenow": "Live ServiceNow Table API" if servicenow.is_live else "Enterprise ServiceNow Mock (Table API Spec)",
        "embeddings": embedder.kind,
        "vector_search": "FAISS Inner Product (384-dim)",
        "thresholds": {
            "auto_resolve": settings.auto_resolve_threshold,
            "escalate_below": settings.escalate_below,
            "rag_threshold": settings.rag_threshold,
        },
        "counts": {
            "tickets": total_tickets,
            "ai_resolved": ai_resolved,
            "articles": len(store.articles),
            "chunks": len(store.chunks),
            "catalog": len(store.catalog),
            "software_requests": len(store.software_requests),
            "audit_logs": len(store.audit_logs),
        },
    }


@app.post("/api/chat", response_model=ChatOut)
def chat_endpoint(payload: ChatIn) -> ChatOut:
    """Core employee portal chat endpoint with chat history persistence."""
    user_dict = payload.user.model_dump()
    response = agent.handle_message(
        message=payload.message,
        user=user_dict,
        session_id=payload.session_id,
    )

    # Persist chat history in MongoDB Atlas / store
    ticket_num = response.ticket.number if response.ticket else None
    store.record_chat(
        session_id=response.session_id,
        user=user_dict,
        message=payload.message,
        reply=response.reply,
        intent=response.intent,
        confidence=response.confidence,
        ticket_number=ticket_num,
    )

    return response


@app.get("/api/chat/history")
def get_chat_history(session_id: str | None = None) -> list[dict]:
    """Retrieve saved chat history from MongoDB Atlas / store."""
    if session_id:
        return store.chat_sessions.get(session_id, [])
    return store.chat_history


@app.post("/api/intake", response_model=ChatOut)
def intake_endpoint(payload: IntakeIn) -> ChatOut:
    """Direct ticket intake endpoint."""
    user_dict = payload.user.model_dump()
    return agent.handle_message(
        message=payload.message,
        user=user_dict,
    )


@app.get("/api/tickets", response_model=list[TicketOut])
def list_tickets(status: str | None = Query(None)) -> list[dict]:
    tickets = store.tickets
    if status and status != "All":
        tickets = [t for t in tickets if t.get("status") == status]
    return tickets


@app.get("/api/tickets/{number}", response_model=TicketOut)
def get_ticket(number: str) -> dict:
    ticket = next((t for t in store.tickets if t.get("number") == number), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.get("/api/servicenow/incident/{sys_id_or_number}")
def get_servicenow_incident(sys_id_or_number: str) -> dict:
    """Demonstrate 'Get Incident' REST integration against ServiceNow Table API."""
    record = servicenow.get_incident(sys_id_or_number)
    return record


@app.post("/api/tickets/{number}/actions/{action_id}/execute")
def execute_action(number: str, action_id: str, actor: str = "IT Analyst") -> dict:
    try:
        updated_ticket = agent.execute_ticket_action(number, action_id, actor=actor)
        return updated_ticket
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/tickets/{number}/escalate")
def escalate_ticket(number: str, reason: str = "Employee requested human escalation") -> dict:
    ticket = next((t for t in store.tickets if t.get("number") == number), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket["status"] = "Escalated"
    ticket["escalation_reason"] = reason
    ticket["updated_at"] = now_iso()
    ticket["timeline"].append({
        "id": snow_sys_id()[:12],
        "at": now_iso(),
        "actor": "Employee",
        "action": "Escalation",
        "detail": f"Escalated to Tier-2 support: {reason}",
    })

    servicenow.update_incident(
        ticket["servicenow"]["sys_id"],
        {"urgency": "1", "work_notes": f"Escalated to human support: {reason}"},
    )
    store.save()
    return ticket


@app.get("/api/requests", response_model=list[SoftwareRequestOut])
def list_software_requests() -> list[dict]:
    return store.software_requests


@app.post("/api/requests", response_model=SoftwareRequestOut)
def create_software_request(payload: CatalogRequestIn) -> dict:
    item = next((it for it in store.catalog if it["id"] == payload.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Catalog item '{payload.item_id}' not found")

    user_dict = payload.user.model_dump()
    decision = software_decision(item, user_dict)
    requester_name = user_dict.get("name", "Emma Walsh")
    requester_email = user_dict.get("email", "emma.walsh@northline.com")
    department = user_dict.get("department", "Engineering")

    snow_req = servicenow.create_service_request(
        item_name=item["name"],
        requester_name=requester_name,
        requester_email=requester_email,
        department=department,
        justification=payload.justification,
        status="Requested" if decision["approval_required"] else "Provisioning",
    )

    events = [
        {"at": now_iso(), "status": "Requested", "detail": f"Requested: {payload.justification}"}
    ]
    if not decision["eligible"]:
        status = "Rejected"
        events.append({"at": now_iso(), "status": "Rejected", "detail": f"Ineligible: {decision['reason']}"})
    elif decision["approval_required"]:
        status = "Pending approval"
    else:
        events.append({"at": now_iso(), "status": "Approved", "detail": "Pre-approved standard tool"})
        events.append({"at": now_iso(), "status": "Provisioning", "detail": "Dispatched via Intune"})
        events.append({"at": now_iso(), "status": "Completed", "detail": "Software installed successfully"})
        status = "Completed"

    record = {
        "number": snow_req["number"],
        "item_id": item["id"],
        "software": item["name"],
        "requester_name": requester_name,
        "requester_email": requester_email,
        "department": department,
        "justification": payload.justification,
        "status": status,
        "approval_required": decision["approval_required"],
        "eligible": decision["eligible"],
        "reason": decision["reason"],
        "provision_minutes": item.get("provision_minutes", 1),
        "timeline": events,
        "work_notes": [{"at": now_iso(), "author": "System", "text": f"Created REQ {snow_req['number']}"}],
        "servicenow": snow_req,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    store.software_requests.insert(0, record)
    store.save()
    return record


@app.post("/api/requests/{number}/decide")
def decide_software_request(number: str, payload: DecideIn) -> dict:
    req = next((r for r in store.software_requests if r["number"] == number), None)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.get("status") not in ("Pending approval", "Requested"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot decide request {number} because current status is '{req.get('status')}'. Only 'Pending approval' or 'Requested' requests can be approved or rejected.",
        )

    if payload.decision == "approve":
        req["status"] = "Completed"
        req["timeline"].append({"at": now_iso(), "status": "Approved", "detail": f"Approved by {payload.actor}: {payload.note}"})
        req["timeline"].append({"at": now_iso(), "status": "Provisioning", "detail": "Intune agent deployment triggered"})
        req["timeline"].append({"at": now_iso(), "status": "Completed", "detail": "Installation completed"})
        servicenow.update_service_request(req["servicenow"]["sys_id"], "Completed", f"Approved by {payload.actor}")
    else:
        req["status"] = "Rejected"
        req["timeline"].append({"at": now_iso(), "status": "Rejected", "detail": f"Rejected by {payload.actor}: {payload.note}"})
        servicenow.update_service_request(req["servicenow"]["sys_id"], "Rejected", f"Rejected by {payload.actor}")

    req["updated_at"] = now_iso()
    store.save()
    return req


@app.get("/api/catalog", response_model=list[CatalogItemOut])
def get_catalog() -> list[dict]:
    return store.catalog


@app.get("/api/knowledge", response_model=list[ArticleOut])
def get_knowledge() -> list[dict]:
    return store.articles


@app.get("/api/knowledge/{id}", response_model=ArticleOut)
def get_article(id: str) -> dict:
    art = next((a for a in store.articles if a["id"] == id), None)
    if not art:
        raise HTTPException(status_code=404, detail="Article not found")
    return art


@app.post("/api/knowledge/search", response_model=SearchOut)
def search_knowledge(query: str = Query(..., min_length=2), top_k: int = Query(3, ge=1, le=10)) -> SearchOut:
    return rag.search(query, top_k=top_k)


@app.get("/api/dashboard/stats")
def get_dashboard_stats() -> dict:
    total_tickets = len(store.tickets)
    open_tickets = len([t for t in store.tickets if t.get("status") in ("Open", "In Progress", "Pending")])
    ai_resolved = len([t for t in store.tickets if t.get("ai_resolved")])
    escalated = len([t for t in store.tickets if t.get("status") == "Escalated"])
    total_sw = len(store.software_requests)
    completed_sw = len([s for s in store.software_requests if s.get("status") == "Completed"])
    auto_rate = round((ai_resolved / total_tickets * 100), 1) if total_tickets > 0 else 0.0

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "ai_resolved": ai_resolved,
        "escalated": escalated,
        "software_requests_total": total_sw,
        "software_requests_completed": completed_sw,
        "automation_rate": auto_rate,
        "mttr_minutes": 1.4,
        "audit_actions_count": len(store.audit_logs),
    }


@app.get("/api/audit")
def get_audit_logs() -> list[dict]:
    return store.audit_logs


@app.post("/api/seed")
def reset_seed() -> dict:
    """Reset the database to default seed state."""
    store.tickets = []
    store.articles = []
    store.chunks = []
    store.catalog = []
    store.software_requests = []
    store.audit_logs = []
    store.chat_history = []
    store.chat_sessions = {}
    store._seed_if_empty()
    rag._rebuild_index()
    servicenow._inc_counter = 10042
    servicenow._req_counter = 1245
    servicenow.sync_counters_from_store(store.tickets, store.software_requests)
    return {"status": "ok", "message": "Store and FAISS index reset and re-seeded successfully."}
