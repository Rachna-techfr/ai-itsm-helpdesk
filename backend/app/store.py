from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import Settings
from app.embeddings import Embedder
from app.kb import ARTICLES, CATALOG_ITEMS, chunk_articles
from app.util import ago, nid, now_iso

logger = logging.getLogger("store")


class DataStore:
    """Data Store supporting MongoDB Atlas with seamless offline JSON fallback and chat history."""

    def __init__(self, settings: Settings, embedder: Embedder):
        self.settings = settings
        self.embedder = embedder
        self.use_mongo = False
        self.mongo_client = None
        self.db = None
        self.storage_file: Path = settings.data_dir / "store.json"

        # In-memory document storage
        self.tickets: list[dict] = []
        self.articles: list[dict] = []
        self.chunks: list[dict] = []
        self.catalog: list[dict] = []
        self.software_requests: list[dict] = []
        self.audit_logs: list[dict] = []
        self.chat_history: list[dict] = []
        self.chat_sessions: dict[str, list[dict]] = {}

        self._init_backend()
        self._seed_if_empty()

    def _init_backend(self) -> None:
        if self.settings.mongodb_uri:
            try:
                from pymongo import MongoClient

                self.mongo_client = MongoClient(self.settings.mongodb_uri, serverSelectionTimeoutMS=3000)
                # Verify connection with ping
                self.mongo_client.admin.command("ping")
                self.db = self.mongo_client[self.settings.mongodb_db]
                self.use_mongo = True
                logger.info("Connected successfully to MongoDB Atlas database: %s", self.settings.mongodb_db)
                self._load_from_mongo()
                return
            except Exception as exc:
                logger.warning("MongoDB Atlas connection failed (%s). Falling back to local storage.", exc)
                self.use_mongo = False

        # Local JSON backend
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tickets = data.get("tickets", [])
                    self.articles = data.get("articles", [])
                    self.chunks = data.get("chunks", [])
                    self.catalog = data.get("catalog", [])
                    self.software_requests = data.get("software_requests", [])
                    self.audit_logs = data.get("audit_logs", [])
                    self.chat_history = data.get("chat_history", [])
                    self.chat_sessions = data.get("chat_sessions", {})
                logger.info("Loaded state from local store.json")
            except Exception as exc:
                logger.warning("Failed to load local store.json (%s), creating fresh store.", exc)

    def _load_from_mongo(self) -> None:
        if not self.use_mongo or self.db is None:
            return
        self.tickets = list(self.db.tickets.find({}, {"_id": 0}))
        self.articles = list(self.db.kb_articles.find({}, {"_id": 0}))
        self.chunks = list(self.db.kb_chunks.find({}, {"_id": 0}))
        self.catalog = list(self.db.software_catalog.find({}, {"_id": 0}))
        self.software_requests = list(self.db.software_requests.find({}, {"_id": 0}))
        self.audit_logs = list(self.db.audit_logs.find({}, {"_id": 0}))
        self.chat_history = list(self.db.chat_history.find({}, {"_id": 0}).sort("timestamp", -1).limit(100))

    def save(self) -> None:
        """Persist data to MongoDB Atlas or local JSON file."""
        if self.use_mongo and self.db is not None:
            try:
                for col_name, data_list in [
                    ("tickets", self.tickets),
                    ("kb_articles", self.articles),
                    ("kb_chunks", self.chunks),
                    ("software_catalog", self.catalog),
                    ("software_requests", self.software_requests),
                    ("audit_logs", self.audit_logs),
                ]:
                    col = self.db[col_name]
                    col.delete_many({})
                    if data_list:
                        col.insert_many([dict(item) for item in data_list])
                return
            except Exception as exc:
                logger.warning("MongoDB write failed (%s); writing to local disk.", exc)

        # Local save
        try:
            self.settings.data_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "tickets": self.tickets,
                "articles": self.articles,
                "chunks": self.chunks,
                "catalog": self.catalog,
                "software_requests": self.software_requests,
                "audit_logs": self.audit_logs,
                "chat_history": self.chat_history[-200:],  # keep last 200 turns
                "chat_sessions": self.chat_sessions,
            }
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as exc:
            logger.error("Failed to save local store.json: %s", exc)

    def record_chat(
        self,
        session_id: str,
        user: dict,
        message: str,
        reply: str,
        intent: str,
        confidence: float,
        ticket_number: str | None = None,
    ) -> dict:
        """Record chat interaction to MongoDB Atlas and local memory."""
        turn = {
            "id": nid(),
            "session_id": session_id,
            "timestamp": now_iso(),
            "user_id": user.get("id", "emma.walsh"),
            "user_name": user.get("name", "Emma Walsh"),
            "department": user.get("department", "Engineering"),
            "message": message,
            "reply": reply,
            "intent": intent,
            "confidence": confidence,
            "ticket_number": ticket_number,
        }
        self.chat_history.insert(0, turn)
        self.chat_sessions.setdefault(session_id, []).append(turn)

        if self.use_mongo and self.db is not None:
            try:
                self.db.chat_history.insert_one(dict(turn))
            except Exception as exc:
                logger.warning("Failed to save chat to MongoDB: %s", exc)

        self.save()
        return turn

    def _seed_if_empty(self) -> None:
        if not self.articles:
            self.articles = list(ARTICLES)
        if not self.catalog:
            self.catalog = list(CATALOG_ITEMS)
        if not self.chunks:
            raw_chunks = chunk_articles(self.articles)
            texts = [c["text"] for c in raw_chunks]
            self.embedder.fit(texts)
            for chunk in raw_chunks:
                chunk["embedding"] = self.embedder.embed(chunk["text"])
            self.chunks = raw_chunks

        if not self.tickets:
            self.tickets = [
                {
                    "number": "INC0010021",
                    "caller_name": "Marcus Vance",
                    "caller_email": "marcus.vance@northline.com",
                    "department": "Engineering",
                    "location": "Austin HQ",
                    "channel": "Employee portal",
                    "status": "Resolved",
                    "description": "My corporate password expired this morning and I cannot sign into Microsoft 365 or VPN.",
                    "classification": {
                        "intent": "Incident",
                        "category": "Identity",
                        "subcategory": "Password",
                        "priority": "P3",
                        "urgency": "High",
                        "impact": "Individual",
                        "assignment_group": "Identity Operations",
                        "configuration_item": "Entra ID",
                        "summary": "Password expired",
                        "suggested_resolution": "Issue temporary one-time password via verified secure manager channel.",
                        "entities": {
                            "application": "Entra ID",
                            "error_text": "Sign-in rejected",
                            "user": "Marcus Vance",
                            "location": "Austin HQ",
                        },
                        "confidence": 0.94,
                        "rationale": "Matched expired password keywords. Entra ID identity policy allowed automated unattended reset.",
                    },
                    "servicenow": {
                        "mode": "mock",
                        "table": "incident",
                        "number": "INC0010021",
                        "sys_id": "b9f2e301a92e448b8120c1840ef90a12",
                        "url": "https://dev-northline.service-now.com/nav_to.do?uri=incident.do?sys_id=b9f2e301a92e448b8120c1840ef90a12",
                        "state": "Resolved",
                        "work_notes": [
                            {"at": ago(hours=3), "author": "AI Self-Healing Agent", "text": "Diagnosed account: Expired=True, Privileged=False."},
                            {"at": ago(hours=3), "author": "AI Self-Healing Agent", "text": "Issued temporary Entra ID password to manager channel. Verified successful bind."},
                        ],
                        "payload": {},
                    },
                    "timeline": [
                        {"id": nid(), "at": ago(hours=3), "actor": "Marcus Vance", "action": "Ticket Created", "detail": "Incident submitted via Employee Portal"},
                        {"id": nid(), "at": ago(hours=3), "actor": "AI Self-Healing Agent", "action": "Self-Heal Executed", "detail": "Playbook password_reset completed successfully"},
                        {"id": nid(), "at": ago(hours=3), "actor": "ServiceNow Integration", "action": "State Transition", "detail": "Incident state updated to Resolved in ServiceNow"},
                    ],
                    "actions": [],
                    "citations": [
                        {"id": "KB0002", "title": "Password Expiration & Self-Service Entra ID Reset", "category": "Identity", "score": 0.88, "confidence": 0.94, "excerpt": "Enterprise security policy mandates password expiration every 90 days..."}
                    ],
                    "duplicate_of": None,
                    "duplicate_score": None,
                    "resolution_notes": "Automated self-healing issued one-time temporary password. User verified sign-in.",
                    "resolution_mode": "self_heal",
                    "ai_resolved": True,
                    "kb_draft_id": None,
                    "escalation_reason": None,
                    "created_at": ago(hours=3),
                    "updated_at": ago(hours=3),
                },
                {
                    "number": "INC0010018",
                    "caller_name": "Sarah Chen",
                    "caller_email": "sarah.chen@northline.com",
                    "department": "Sales",
                    "location": "London Office",
                    "channel": "Employee portal",
                    "status": "Resolved",
                    "description": "Salesforce SSO integration timing out on macOS during client demos.",
                    "classification": {
                        "intent": "Incident",
                        "category": "Software",
                        "subcategory": "Salesforce",
                        "priority": "P3",
                        "urgency": "Medium",
                        "impact": "Individual",
                        "assignment_group": "Applications Support",
                        "configuration_item": "Salesforce SSO",
                        "summary": "Salesforce SSO authentication timeout",
                        "suggested_resolution": "Flushed Okta token session and re-authenticated workstation browser profile.",
                        "confidence": 0.91,
                        "rationale": "SAML token expiration identified on client browser cache.",
                    },
                    "servicenow": {
                        "mode": "mock",
                        "table": "incident",
                        "number": "INC0010018",
                        "sys_id": "c7a1029e84b248a88120c1840ef90b44",
                        "url": "https://dev-northline.service-now.com/nav_to.do?uri=incident.do?sys_id=c7a1029e84b248a88120c1840ef90b44",
                        "state": "Resolved",
                        "work_notes": [{"at": ago(hours=6), "author": "AI Helpdesk", "text": "Token refreshed via Okta API."}],
                        "payload": {},
                    },
                    "timeline": [
                        {"id": nid(), "at": ago(hours=6), "actor": "Sarah Chen", "action": "Ticket Created", "detail": "Submitted via portal"},
                        {"id": nid(), "at": ago(hours=6), "actor": "AI Helpdesk", "action": "Resolved", "detail": "Session refreshed"},
                    ],
                    "actions": [],
                    "citations": [],
                    "duplicate_of": None,
                    "duplicate_score": None,
                    "resolution_notes": "SAML token session cleared and refreshed.",
                    "resolution_mode": "self_heal",
                    "ai_resolved": True,
                    "kb_draft_id": None,
                    "escalation_reason": None,
                    "created_at": ago(hours=6),
                    "updated_at": ago(hours=6),
                },
                {
                    "number": "INC0010015",
                    "caller_name": "Alex Rivera",
                    "caller_email": "alex.rivera@northline.com",
                    "department": "Marketing",
                    "location": "New York HQ",
                    "channel": "Employee portal",
                    "status": "In Progress",
                    "description": "GlobalProtect VPN connection failed with error 809 from remote hotel Wi-Fi.",
                    "classification": {
                        "intent": "Incident",
                        "category": "Network",
                        "subcategory": "VPN",
                        "priority": "P2",
                        "urgency": "High",
                        "impact": "Individual",
                        "assignment_group": "Network Support",
                        "configuration_item": "GlobalProtect Gateway",
                        "summary": "VPN connection error 809",
                        "suggested_resolution": "Switch to SSL transport fallback mode on port 443.",
                        "entities": {
                            "application": "GlobalProtect VPN",
                            "error_text": "Error 809",
                            "user": "Alex Rivera",
                            "location": "New York HQ",
                        },
                        "confidence": 0.89,
                        "rationale": "Hotel firewall blocking IPsec UDP port 500/4500.",
                    },
                    "servicenow": {
                        "mode": "mock",
                        "table": "incident",
                        "number": "INC0010015",
                        "sys_id": "d8b2130f95c349b99120c1840ef90c55",
                        "url": "https://dev-northline.service-now.com/nav_to.do?uri=incident.do?sys_id=d8b2130f95c349b99120c1840ef90c55",
                        "state": "In Progress",
                        "work_notes": [{"at": ago(hours=8), "author": "Tier-2 Network", "text": "Investigating captive portal interference."}],
                        "payload": {},
                    },
                    "timeline": [
                        {"id": nid(), "at": ago(hours=8), "actor": "Alex Rivera", "action": "Ticket Created", "detail": "Submitted via portal"},
                        {"id": nid(), "at": ago(hours=7), "actor": "Network Support", "action": "Assigned", "detail": "Investigating gateway NAT traversal"},
                    ],
                    "actions": [],
                    "citations": [],
                    "duplicate_of": None,
                    "duplicate_score": None,
                    "resolution_notes": None,
                    "resolution_mode": None,
                    "ai_resolved": False,
                    "kb_draft_id": None,
                    "escalation_reason": "Captive portal IPsec block",
                    "created_at": ago(hours=8),
                    "updated_at": ago(hours=7),
                },
                {
                    "number": "INC0010009",
                    "caller_name": "Priya Patel",
                    "caller_email": "priya.patel@northline.com",
                    "department": "Product",
                    "location": "Singapore",
                    "channel": "Employee portal",
                    "status": "Resolved",
                    "description": "Outlook client freezing when syncing shared executive calendar.",
                    "classification": {
                        "intent": "Incident",
                        "category": "Hardware & Peripherals",
                        "subcategory": "Outlook",
                        "priority": "P3",
                        "urgency": "Medium",
                        "impact": "Individual",
                        "assignment_group": "Workplace Tech",
                        "configuration_item": "Microsoft 365 Exchange",
                        "summary": "Shared calendar sync freeze",
                        "suggested_resolution": "Disabled Turn On Shared Calendar Improvements in Account Settings.",
                        "entities": {
                            "application": "Microsoft 365 Outlook",
                            "error_text": "Calendar sync freeze",
                            "user": "Priya Patel",
                            "location": "Singapore",
                        },
                        "confidence": 0.92,
                        "rationale": "Known Exchange M365 cache sync bug.",
                    },
                    "servicenow": {
                        "mode": "mock",
                        "table": "incident",
                        "number": "INC0010009",
                        "sys_id": "e9c3241a06d450ca0120c1840ef90d66",
                        "url": "https://dev-northline.service-now.com/nav_to.do?uri=incident.do?sys_id=e9c3241a06d450ca0120c1840ef90d66",
                        "state": "Resolved",
                        "work_notes": [{"at": ago(hours=12), "author": "AI Helpdesk", "text": "Resolved via KB0005 standard procedure."}],
                        "payload": {},
                    },
                    "timeline": [
                        {"id": nid(), "at": ago(hours=12), "actor": "Priya Patel", "action": "Ticket Created", "detail": "Submitted via portal"},
                        {"id": nid(), "at": ago(hours=12), "actor": "AI Helpdesk", "action": "Resolved", "detail": "KB0005 procedure applied"},
                    ],
                    "actions": [],
                    "citations": [],
                    "duplicate_of": None,
                    "duplicate_score": None,
                    "resolution_notes": "Exchange sync cache refreshed.",
                    "resolution_mode": "rag",
                    "ai_resolved": True,
                    "kb_draft_id": None,
                    "escalation_reason": None,
                    "created_at": ago(hours=12),
                    "updated_at": ago(hours=12),
                }
            ]

        if not self.software_requests:
            self.software_requests = [
                {
                    "number": "REQ001240",
                    "item_id": "vscode",
                    "software": "Visual Studio Code",
                    "requester_name": "David Kim",
                    "requester_email": "david.kim@northline.com",
                    "department": "Engineering",
                    "justification": "Required for backend Python and FastAPI development.",
                    "status": "Completed",
                    "approval_required": False,
                    "eligible": True,
                    "reason": "Pre-approved developer tool.",
                    "provision_minutes": 1,
                    "timeline": [
                        {"at": ago(hours=5), "status": "Requested", "detail": "User submitted request"},
                        {"at": ago(hours=5), "status": "Approved", "detail": "Auto-approved per catalog policy"},
                        {"at": ago(hours=5), "status": "Provisioning", "detail": "Intune silent installation dispatched"},
                        {"at": ago(hours=5), "status": "Completed", "detail": "Package deployed to laptop"},
                    ],
                    "work_notes": [
                        {"at": ago(hours=5), "author": "System", "text": "Created ServiceNow request REQ001240"}
                    ],
                    "servicenow": {
                        "mode": "mock",
                        "table": "sc_request",
                        "number": "REQ001240",
                        "sys_id": "a1829e30a91e448b8120c1840ef90111",
                        "url": "https://dev-northline.service-now.com/nav_to.do?uri=sc_request.do?sys_id=a1829e30a91e448b8120c1840ef90111",
                        "state": "Completed",
                        "work_notes": [],
                        "payload": {},
                    },
                    "created_at": ago(hours=5),
                    "updated_at": ago(hours=5),
                }
            ]

        if not self.audit_logs:
            self.audit_logs = [
                {
                    "id": nid(),
                    "timestamp": ago(hours=3),
                    "ticket_number": "INC0010021",
                    "playbook_id": "password_reset",
                    "actor": "AI Self-Healing Agent",
                    "action": "Issue temporary Entra ID password",
                    "policy": "auto",
                    "confidence": 0.94,
                    "status": "success",
                    "details": "Account diagnosed as expired. Password reset executed. Directory bind validated. ServiceNow incident updated to Resolved.",
                }
            ]

        self.save()

    def record_audit(
        self,
        ticket_number: str,
        playbook_id: str,
        actor: str,
        action: str,
        policy: str,
        confidence: float,
        status: str,
        details: str,
    ) -> dict:
        entry = {
            "id": nid(),
            "timestamp": now_iso(),
            "ticket_number": ticket_number,
            "playbook_id": playbook_id,
            "actor": actor,
            "action": action,
            "policy": policy,
            "confidence": confidence,
            "status": status,
            "details": details,
        }
        self.audit_logs.insert(0, entry)
        self.save()
        return entry
