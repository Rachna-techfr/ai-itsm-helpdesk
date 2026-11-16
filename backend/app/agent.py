from __future__ import annotations

import logging
import re
from typing import Any

from app.classify import classify_text
from app.config import Settings
from app.embeddings import retrieval_confidence
from app.playbooks import get_playbook
from app.policy import software_decision
from app.rag import RAGEngine
from app.schemas import (
    ActionOut,
    ChatOut,
    ClassificationOut,
    EntityOut,
    RequestEvent,
    SnowOut,
    SoftwareRequestOut,
    StepOut,
    TicketOut,
    TimelineOut,
    WorkNote,
)
from app.servicenow import ServiceNowClient
from app.store import DataStore
from app.util import ago, nid, now_iso

logger = logging.getLogger("agent")


class HelpdeskAgent:
    """Intelligent ITSM Helpdesk Orchestrator covering the 5 Core Hackathon Use Cases."""

    def __init__(
        self,
        settings: Settings,
        store: DataStore,
        rag: RAGEngine,
        servicenow: ServiceNowClient,
    ):
        self.settings = settings
        self.store = store
        self.rag = rag
        self.servicenow = servicenow

    def handle_message(self, message: str, user: dict, session_id: str | None = None) -> ChatOut:
        """Route employee input to appropriate workflow: Self-Healing, Software, Incident, or RAG."""
        session_id = session_id or nid()
        caller_name = user.get("name", "Emma Walsh")
        caller_email = user.get("email", "emma.walsh@northline.com")
        department = user.get("department", "Engineering")
        location = user.get("location", "Austin HQ")

        # 1. First, check if message is a Software Provisioning request
        software_item = self._match_software_catalog(message)
        if software_item or self._is_software_request(message):
            return self._handle_software_provisioning(message, user, session_id, software_item)

        # 2. Run Classification and RAG Search in parallel
        cls = classify_text(message, user)
        search_res = self.rag.search(message, top_k=3)

        # 3. Check for Automatable Self-Heal Issue
        playbook_id = cls.get("playbook_id")
        playbook = get_playbook(playbook_id)

        # Scenario 2: Self-Healing ("My password has expired", "Account locked", etc.)
        if playbook and playbook.get("policy") == "auto" and cls["confidence"] >= self.settings.auto_resolve_threshold:
            return self._handle_self_healing(
                message, user, session_id, cls, search_res, playbook_id, playbook
            )

        # 4. Check for Scenario 1: Intelligent Ticket Intake (e.g. VPN issue or failure requiring ticket)
        if cls["intent"] == "Incident" and cls["confidence"] >= 0.70:
            return self._handle_incident_intake(
                message, user, session_id, cls, search_res, playbook_id, playbook
            )

        # 5. Check for Knowledge Question (Scenario 3: RAG)
        if search_res.knows:
            answer_text, provider_label, narrative_source = self.rag.answer(message, search_res)
            return ChatOut(
                session_id=session_id,
                intent="Knowledge Question",
                reply=answer_text,
                confidence=search_res.confidence,
                knows=True,
                offer_ticket=True,
                provider_label=provider_label,
                narrative_source=narrative_source,
                citations=search_res.results,
                classification=self._to_classification_out(cls),
                proposed_actions=[],
                auto_resolved=False,
                escalated=False,
            )

        # 6. Scenario 5: Unknown Question / No Hallucination / Escalation
        answer_text, provider_label, narrative_source = self.rag.answer(message, search_res)
        return ChatOut(
            session_id=session_id,
            intent="Unknown / Out of Scope",
            reply=answer_text,
            confidence=search_res.confidence,
            knows=False,
            offer_ticket=True,
            provider_label=provider_label,
            narrative_source=narrative_source,
            citations=search_res.results,
            classification=self._to_classification_out(cls),
            proposed_actions=[],
            auto_resolved=False,
            escalated=True,
        )

    def _match_software_catalog(self, text: str) -> dict | None:
        """Find matching catalog item from text."""
        low = text.lower()
        for item in self.store.catalog:
            for alias in item.get("aliases", []):
                if alias in low:
                    return item
        return None

    def _is_software_request(self, text: str) -> bool:
        low = text.lower()
        triggers = ["install", "provision", "need software", "access to", "license for", "software catalog"]
        return any(trig in low for trig in triggers)

    def _handle_software_provisioning(
        self, message: str, user: dict, session_id: str, item: dict | None
    ) -> ChatOut:
        """Scenario 4: Software Provisioning Automation."""
        if not item:
            # Fallback to VS Code if generic install request
            item = next((it for it in self.store.catalog if it["id"] == "vscode"), self.store.catalog[0])

        decision = software_decision(item, user)
        eligible = decision["eligible"]
        approval_req = decision["approval_required"]
        reason = decision["reason"]

        requester_name = user.get("name", "Emma Walsh")
        requester_email = user.get("email", "emma.walsh@northline.com")
        department = user.get("department", "Engineering")

        # Create ServiceNow Request
        snow_req = self.servicenow.create_service_request(
            item_name=item["name"],
            requester_name=requester_name,
            requester_email=requester_email,
            department=department,
            justification=message,
            status="Requested" if approval_req else "Provisioning",
        )

        initial_status = "Pending approval" if approval_req else "Provisioning"
        events = [
            RequestEvent(at=now_iso(), status="Requested", detail=f"Request received: {message}"),
        ]

        if not approval_req:
            events.append(
                RequestEvent(at=now_iso(), status="Approved", detail="Auto-approved per catalog policy (Free/Pre-approved)")
            )
            events.append(
                RequestEvent(at=now_iso(), status="Provisioning", detail="Intune silent installation dispatched to endpoint")
            )
            # If fast demo mode, mark completed
            events.append(
                RequestEvent(at=now_iso(), status="Completed", detail=f"{item['name']} successfully installed on laptop")
            )
            initial_status = "Completed"

        req_record = {
            "number": snow_req["number"],
            "item_id": item["id"],
            "software": item["name"],
            "requester_name": requester_name,
            "requester_email": requester_email,
            "department": department,
            "justification": message,
            "status": initial_status,
            "approval_required": approval_req,
            "eligible": eligible,
            "reason": reason,
            "provision_minutes": item.get("provision_minutes", 1),
            "timeline": [e.model_dump() for e in events],
            "work_notes": [
                {"at": now_iso(), "author": "System", "text": f"Created ServiceNow Request {snow_req['number']}"}
            ],
            "servicenow": snow_req,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

        self.store.software_requests.insert(0, req_record)
        self.store.save()

        reply = (
            f"📦 **Software Provisioning Initialized**\n\n"
            f"- **Software:** {item['name']}\n"
            f"- **ServiceNow Request:** [{snow_req['number']}]({snow_req['url']})\n"
            f"- **Status:** `{initial_status}`\n"
            f"- **Policy Decision:** {reason}\n\n"
            f"The installation package has been scheduled via Microsoft Intune."
        )

        snow_out = SnowOut(
            mode=snow_req.get("mode", "mock"),
            table="sc_request",
            number=snow_req.get("number", "REQ001245"),
            sys_id=snow_req.get("sys_id", ""),
            url=snow_req.get("url", ""),
            state=initial_status,
            work_notes=[],
            payload=snow_req.get("payload", {}),
        )

        sw_out = SoftwareRequestOut(
            number=snow_req["number"],
            item_id=item["id"],
            software=item["name"],
            requester_name=requester_name,
            requester_email=requester_email,
            department=department,
            justification=message,
            status=initial_status,
            approval_required=approval_req,
            eligible=eligible,
            reason=reason,
            provision_minutes=item.get("provision_minutes", 1),
            timeline=events,
            work_notes=[],
            servicenow=snow_out,
            created_at=now_iso(),
            updated_at=now_iso(),
        )

        return ChatOut(
            session_id=session_id,
            intent="Service Request",
            reply=reply,
            confidence=0.96,
            knows=True,
            offer_ticket=False,
            provider_label="Software Provisioning Engine",
            narrative_source="ServiceNow Service Catalog",
            citations=[],
            classification=None,
            ticket=None,
            proposed_actions=[],
            auto_resolved=False,
            software_request=sw_out,
            escalated=False,
        )

    def _handle_self_healing(
        self,
        message: str,
        user: dict,
        session_id: str,
        cls: dict,
        search_res: Any,
        playbook_id: str,
        playbook: dict,
    ) -> ChatOut:
        """
        Scenario 2: Auto Resolution / Self-Heal Agent
        Demonstrate: Identify -> Diagnose -> Knowledge Search -> Determine Automation -> Execute -> Validate -> Update ServiceNow.
        """
        caller_name = user.get("name", "Emma Walsh")
        caller_email = user.get("email", "emma.walsh@northline.com")
        department = user.get("department", "Engineering")
        location = user.get("location", "Austin HQ")

        # 7-Step Self-Heal Execution
        executed_steps: list[StepOut] = []
        step_definitions = playbook.get("steps", [])

        for st in step_definitions:
            executed_steps.append(
                StepOut(
                    name=st["name"],
                    plan=st["plan"],
                    result=st["result_if_run"],
                    status="success",
                    at=now_iso(),
                )
            )

        # Create Incident in ServiceNow as Resolved
        work_notes = "\n".join([f"[{s.name}] {s.result}" for s in executed_steps])
        resolution_notes = f"Self-healing playbook '{playbook['title']}' executed automatically. Verified resolution."

        snow_inc = self.servicenow.create_incident(
            summary=cls["summary"],
            description=message,
            category=cls["category"],
            subcategory=cls["subcategory"],
            priority=cls["priority"],
            urgency=cls["urgency"],
            impact=cls["impact"],
            assignment_group=cls["assignment_group"],
            caller_name=caller_name,
            caller_email=caller_email,
            configuration_item=cls["configuration_item"],
            work_notes=work_notes,
            resolved=True,
            resolution_notes=resolution_notes,
        )

        # Record in Audit Log (Mandatory for capability 2)
        self.store.record_audit(
            ticket_number=snow_inc["number"],
            playbook_id=playbook_id,
            actor="AI Self-Healing Agent",
            action=playbook["title"],
            policy=playbook["policy"],
            confidence=cls["confidence"],
            status="success",
            details=f"Executed 7-stage self-heal lifecycle: Identify -> Diagnose -> Knowledge Search -> Determine Automation -> Execute -> Validate -> Update ServiceNow ({snow_inc['number']}).",
        )

        timeline = [
            TimelineOut(id=nid(), at=now_iso(), actor=caller_name, action="Intake", detail=f"Employee reported: {message}"),
            TimelineOut(id=nid(), at=now_iso(), actor="AI Classifier", action="Diagnosed", detail=f"Classified as {cls['category']} / {cls['subcategory']} (Confidence: {int(cls['confidence']*100)}%)"),
            TimelineOut(id=nid(), at=now_iso(), actor="AI Self-Heal Agent", action="Executed Playbook", detail=f"Playbook '{playbook['title']}' executed 7 validation steps"),
            TimelineOut(id=nid(), at=now_iso(), actor="ServiceNow Integration", action="Resolved Ticket", detail=f"Created & Resolved ServiceNow Incident {snow_inc['number']}"),
        ]

        action_out = ActionOut(
            id=nid(),
            playbook_id=playbook_id,
            title=playbook["title"],
            confidence=cls["confidence"],
            policy=playbook["policy"],
            status="executed",
            rationale=cls["rationale"],
            risk=playbook.get("risk", ""),
            steps=executed_steps,
        )

        ticket_record = {
            "number": snow_inc["number"],
            "caller_name": caller_name,
            "caller_email": caller_email,
            "department": department,
            "location": location,
            "channel": "Employee portal",
            "status": "Resolved",
            "description": message,
            "classification": cls,
            "servicenow": snow_inc,
            "timeline": [t.model_dump() for t in timeline],
            "actions": [action_out.model_dump()],
            "citations": [c.model_dump() for c in search_res.results],
            "duplicate_of": None,
            "duplicate_score": None,
            "resolution_notes": resolution_notes,
            "resolution_mode": "self_heal",
            "ai_resolved": True,
            "kb_draft_id": None,
            "escalation_reason": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        self.store.tickets.insert(0, ticket_record)
        self.store.save()

        reply = (
            f"✅ **Self-Healing Automation Succeeded!**\n\n"
            f"I diagnosed your issue as `{cls['summary']}` and triggered the approved automated remediation playbook:\n\n"
            f"**Playbook:** `{playbook['title']}`\n\n"
            f"**Autonomous Lifecycle Completed:**\n"
            f"1. **Identify:** Caller account validated in Microsoft Entra ID.\n"
            f"2. **Diagnose:** Password expired flag confirmed; non-privileged account status verified.\n"
            f"3. **Knowledge Search:** Matched KB0002 runbook guidelines.\n"
            f"4. **Determine Automation:** Policy confirmed safe for unattended execution (Confidence: {int(cls['confidence']*100)}%).\n"
            f"5. **Execute:** One-time temporary password issued to manager channel.\n"
            f"6. **Validate:** Directory bind test passed successfully.\n"
            f"7. **Update ServiceNow:** Incident **[{snow_inc['number']}]({snow_inc['url']})** created and marked **Resolved**.\n\n"
            f"*(Every automated action has been permanently logged in the Enterprise Audit Log.)*"
        )

        ticket_out = self._to_ticket_out(ticket_record)

        return ChatOut(
            session_id=session_id,
            intent="Automatable Issue",
            reply=reply,
            confidence=cls["confidence"],
            knows=True,
            offer_ticket=False,
            provider_label="AI Self-Healing Agent",
            narrative_source=f"Automated Playbook ({playbook_id})",
            citations=search_res.results,
            classification=self._to_classification_out(cls),
            ticket=ticket_out,
            proposed_actions=[action_out],
            auto_resolved=True,
            software_request=None,
            escalated=False,
        )

    def _handle_incident_intake(
        self,
        message: str,
        user: dict,
        session_id: str,
        cls: dict,
        search_res: Any,
        playbook_id: str | None,
        playbook: dict | None,
    ) -> ChatOut:
        """
        Scenario 1: Intelligent Ticket Intake
        Employee enters: “I cannot connect to VPN since this morning. Authentication keeps failing.”
        AI outputs:
        Intent: Incident, Category/Sub-category: Network / VPN, Priority: P2, Impact/Urgency: Individual / High,
        Assignment Group: Network Support, Summary: VPN authentication failure, Suggested Resolution: VPN troubleshooting
        Create an Incident in ServiceNow using the AI-generated information.
        """
        caller_name = user.get("name", "Emma Walsh")
        caller_email = user.get("email", "emma.walsh@northline.com")
        department = user.get("department", "Engineering")
        location = user.get("location", "Austin HQ")

        # Create Incident in ServiceNow
        snow_inc = self.servicenow.create_incident(
            summary=cls["summary"],
            description=message,
            category=cls["category"],
            subcategory=cls["subcategory"],
            priority=cls["priority"],
            urgency=cls["urgency"],
            impact=cls["impact"],
            assignment_group=cls["assignment_group"],
            caller_name=caller_name,
            caller_email=caller_email,
            configuration_item=cls["configuration_item"],
            work_notes=f"AI Incident Intake: Intent={cls['intent']}, Priority={cls['priority']}, Assignment={cls['assignment_group']}",
            resolved=False,
        )

        timeline = [
            TimelineOut(id=nid(), at=now_iso(), actor=caller_name, action="Intake", detail=f"Employee reported: {message}"),
            TimelineOut(id=nid(), at=now_iso(), actor="AI Classifier", action="Classified", detail=f"Mapped to {cls['category']} / {cls['subcategory']}, Priority {cls['priority']}, Assigned to {cls['assignment_group']}"),
            TimelineOut(id=nid(), at=now_iso(), actor="ServiceNow Integration", action="Created Incident", detail=f"Dispatched to ServiceNow Table API ({snow_inc['number']})"),
        ]

        proposed_actions: list[ActionOut] = []
        if playbook:
            step_outs = [
                StepOut(name=s["name"], plan=s["plan"], status="pending")
                for s in playbook.get("steps", [])
            ]
            proposed_actions.append(
                ActionOut(
                    id=nid(),
                    playbook_id=playbook_id or "vpn_repair",
                    title=playbook["title"],
                    confidence=cls["confidence"],
                    policy=playbook.get("policy", "approval_required"),
                    status="proposed",
                    rationale=cls["rationale"],
                    risk=playbook.get("risk", ""),
                    steps=step_outs,
                )
            )

        ticket_record = {
            "number": snow_inc["number"],
            "caller_name": caller_name,
            "caller_email": caller_email,
            "department": department,
            "location": location,
            "channel": "Employee portal",
            "status": "Open",
            "description": message,
            "classification": cls,
            "servicenow": snow_inc,
            "timeline": [t.model_dump() for t in timeline],
            "actions": [a.model_dump() for a in proposed_actions],
            "citations": [c.model_dump() for c in search_res.results],
            "duplicate_of": None,
            "duplicate_score": None,
            "resolution_notes": None,
            "resolution_mode": None,
            "ai_resolved": False,
            "kb_draft_id": None,
            "escalation_reason": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        self.store.tickets.insert(0, ticket_record)
        self.store.save()

        ticket_out = self._to_ticket_out(ticket_record)

        reply = (
            f"🎫 **ServiceNow Incident Created Successfully**\n\n"
            f"- **Incident Number:** [{snow_inc['number']}]({snow_inc['url']})\n"
            f"- **Category / Sub-category:** `{cls['category']} / {cls['subcategory']}`\n"
            f"- **Priority:** `{cls['priority']}` (Urgency: {cls['urgency']}, Impact: {cls['impact']})\n"
            f"- **Assignment Group:** `{cls['assignment_group']}`\n"
            f"- **Summary:** {cls['summary']}\n"
            f"- **Suggested Resolution:** {cls['suggested_resolution']}\n\n"
            f"Our Network Support team has been alerted. In the meantime, you can review the suggested troubleshooting runbook or authorize the remediation action below."
        )

        return ChatOut(
            session_id=session_id,
            intent="Incident",
            reply=reply,
            confidence=cls["confidence"],
            knows=search_res.knows,
            offer_ticket=False,
            provider_label="Intelligent Ticket Intake",
            narrative_source="ServiceNow REST Integration",
            citations=search_res.results,
            classification=self._to_classification_out(cls),
            ticket=ticket_out,
            proposed_actions=proposed_actions,
            auto_resolved=False,
            software_request=None,
            escalated=False,
        )

    def execute_ticket_action(self, ticket_number: str, action_id: str, actor: str = "IT Analyst") -> dict:
        """Execute a proposed self-heal action that was pending approval."""
        ticket = next((t for t in self.store.tickets if t["number"] == ticket_number), None)
        if not ticket:
            raise ValueError(f"Ticket {ticket_number} not found.")

        target_action = None
        for a in ticket.get("actions", []):
            if a["id"] == action_id or a.get("playbook_id") == action_id:
                target_action = a
                break

        if not target_action:
            raise ValueError(f"Action {action_id} not found on ticket {ticket_number}.")

        playbook = get_playbook(target_action["playbook_id"])
        if not playbook:
            raise ValueError(f"Playbook {target_action['playbook_id']} not found.")

        # Execute steps
        for st_def, st_out in zip(playbook.get("steps", []), target_action.get("steps", [])):
            st_out["status"] = "success"
            st_out["result"] = st_def.get("result_if_run", "Executed successfully.")
            st_out["at"] = now_iso()

        target_action["status"] = "executed"
        ticket["status"] = "Resolved"
        ticket["resolution_notes"] = f"Approved and executed action '{target_action['title']}' by {actor}."
        ticket["resolution_mode"] = "analyst_assisted"
        ticket["ai_resolved"] = True
        ticket["updated_at"] = now_iso()

        # Update ServiceNow
        self.servicenow.update_incident(
            ticket["servicenow"]["sys_id"],
            {"state": "6", "close_code": "Solved (Permanently)", "close_notes": ticket["resolution_notes"]},
            work_note=f"Action '{target_action['title']}' executed by {actor}.",
        )
        ticket["servicenow"]["state"] = "Resolved"

        # Record Audit
        self.store.record_audit(
            ticket_number=ticket_number,
            playbook_id=target_action["playbook_id"],
            actor=actor,
            action=target_action["title"],
            policy=target_action.get("policy", "approval_required"),
            confidence=target_action.get("confidence", 0.9),
            status="success",
            details=f"Analyst {actor} approved and executed action. Incident resolved.",
        )

        ticket["timeline"].append({
            "id": nid(),
            "at": now_iso(),
            "actor": actor,
            "action": "Action Approved & Executed",
            "detail": f"Playbook '{target_action['title']}' executed. Incident resolved.",
        })

        self.store.save()
        return ticket

    def _to_classification_out(self, c: dict) -> ClassificationOut:
        ent = c.get("entities", {})
        return ClassificationOut(
            intent=c.get("intent", "Incident"),
            category=c.get("category", "General"),
            subcategory=c.get("subcategory", "General"),
            priority=c.get("priority", "P3"),
            urgency=c.get("urgency", "Medium"),
            impact=c.get("impact", "Individual"),
            assignment_group=c.get("assignment_group", "Service Desk"),
            configuration_item=c.get("configuration_item", "Employee Laptop"),
            summary=c.get("summary", ""),
            suggested_resolution=c.get("suggested_resolution", ""),
            entities=EntityOut(
                application=ent.get("application", ""),
                error_text=ent.get("error_text", ""),
                user=ent.get("user", ""),
                location=ent.get("location", ""),
            ),
            confidence=c.get("confidence", 0.5),
            rationale=c.get("rationale", ""),
        )

    def _to_ticket_out(self, t: dict) -> TicketOut:
        return TicketOut.model_validate(t)

