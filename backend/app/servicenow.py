from __future__ import annotations

import logging
from typing import Any
import httpx

from app.config import Settings
from app.util import now_iso, snow_sys_id

logger = logging.getLogger("servicenow")

# Mapping priority string to ServiceNow numeric priority
PRIORITY_MAP = {"P1": "1", "P2": "2", "P3": "3", "P4": "4"}
URGENCY_MAP = {"High": "1", "Medium": "2", "Low": "3"}
IMPACT_MAP = {"Site": "1", "Group": "2", "Individual": "3"}
STATE_MAP = {"Open": "1", "In Progress": "2", "Pending": "3", "Resolved": "6", "Closed": "7"}


class ServiceNowClient:
    """ServiceNow REST Table API client with live HTTP calls and resilient mock fallback."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.is_live = bool(settings.servicenow_instance and (settings.servicenow_password or settings.servicenow_token))
        self.instance = settings.servicenow_instance or "dev-northline"
        self.base_url = f"https://{self.instance}.service-now.com/api/now/table"
        self._inc_counter = 10042
        self._req_counter = 1245
        self._mock_records: dict[str, dict] = {}

    def _next_incident_number(self) -> str:
        self._inc_counter += 1
        return f"INC00{self._inc_counter}"

    def _next_request_number(self) -> str:
        self._req_counter += 1
        return f"REQ00{self._req_counter}"

    def sync_counters_from_store(self, tickets: list[dict], requests: list[dict]) -> None:
        """Seed incident and request counters from highest numbers in store so numbers never repeat across server restarts."""
        import re
        for t in tickets:
            num = t.get("number", "")
            match = re.search(r"INC0*(\d+)", num)
            if match:
                val = int(match.group(1))
                if val > self._inc_counter:
                    self._inc_counter = val
        for r in requests:
            num = r.get("number", "")
            match = re.search(r"REQ0*(\d+)", num)
            if match:
                val = int(match.group(1))
                if val > self._req_counter:
                    self._req_counter = val

    def create_incident(
        self,
        summary: str,
        description: str,
        category: str,
        subcategory: str,
        priority: str,
        urgency: str,
        impact: str,
        assignment_group: str,
        caller_name: str,
        caller_email: str,
        configuration_item: str = "Employee Laptop",
        work_notes: str | None = None,
        resolved: bool = False,
        resolution_notes: str | None = None,
    ) -> dict:
        """Create an incident in ServiceNow Table API (or mock)."""
        number = self._next_incident_number()
        sys_id = snow_sys_id()
        state = "6" if resolved else "1"
        state_label = "Resolved" if resolved else "Open"

        payload = {
            "short_description": summary,
            "description": description,
            "category": category.lower(),
            "subcategory": subcategory.lower(),
            "priority": PRIORITY_MAP.get(priority, "3"),
            "urgency": URGENCY_MAP.get(urgency, "2"),
            "impact": IMPACT_MAP.get(impact, "3"),
            "assignment_group": assignment_group,
            "cmdb_ci": configuration_item,
            "caller_id": caller_name,
            "contact_type": "self-service",
            "state": state,
        }
        if work_notes:
            payload["work_notes"] = work_notes
        if resolved:
            payload["close_code"] = "Solved (Permanently)"
            payload["close_notes"] = resolution_notes or "Resolved automatically by AI Self-Healing agent."

        if self.is_live:
            try:
                headers = {"Accept": "application/json", "Content-Type": "application/json"}
                auth = None
                if self.settings.servicenow_token:
                    headers["Authorization"] = f"Bearer {self.settings.servicenow_token}"
                else:
                    auth = (self.settings.servicenow_user, self.settings.servicenow_password)

                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(
                        f"{self.base_url}/incident",
                        json=payload,
                        headers=headers,
                        auth=auth,
                    )
                    if resp.status_code in (200, 201):
                        data = resp.json().get("result", {})
                        number = data.get("number", number)
                        sys_id = data.get("sys_id", sys_id)
                        logger.info(f"Created live ServiceNow incident {number} ({sys_id})")
                        record = {
                            "mode": "live",
                            "table": "incident",
                            "number": number,
                            "sys_id": sys_id,
                            "url": f"https://{self.instance}.service-now.com/nav_to.do?uri=incident.do?sys_id={sys_id}",
                            "state": state_label,
                            "payload": data,
                        }
                        self._mock_records[number] = record
                        self._mock_records[sys_id] = record
                        return record
            except Exception as exc:
                logger.warning(f"Live ServiceNow call failed ({exc}), falling back to mock mode.")

        # Mock Mode
        url = f"https://{self.instance}.service-now.com/nav_to.do?uri=incident.do?sys_id={sys_id}"
        record = {
            "mode": "mock",
            "table": "incident",
            "number": number,
            "sys_id": sys_id,
            "url": url,
            "state": state_label,
            "payload": payload,
        }
        self._mock_records[number] = record
        self._mock_records[sys_id] = record
        return record

    def get_incident(self, sys_id_or_number: str) -> dict:
        """Retrieve an Incident from ServiceNow Table API (or mock store)."""
        if self.is_live:
            try:
                headers = {"Accept": "application/json"}
                auth = None
                if self.settings.servicenow_token:
                    headers["Authorization"] = f"Bearer {self.settings.servicenow_token}"
                else:
                    auth = (self.settings.servicenow_user, self.settings.servicenow_password)

                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(
                        f"{self.base_url}/incident/{sys_id_or_number}",
                        headers=headers,
                        auth=auth,
                    )
                    if resp.status_code == 200:
                        data = resp.json().get("result", {})
                        return {
                            "mode": "live",
                            "table": "incident",
                            "number": data.get("number", sys_id_or_number),
                            "sys_id": data.get("sys_id", sys_id_or_number),
                            "url": f"https://{self.instance}.service-now.com/nav_to.do?uri=incident.do?sys_id={sys_id_or_number}",
                            "state": data.get("state", "Open"),
                            "payload": data,
                        }
            except Exception as exc:
                logger.warning(f"Live get_incident failed ({exc}); reading from mock.")

        # Return mock record if exists, otherwise build clean mock representation
        if sys_id_or_number in self._mock_records:
            return self._mock_records[sys_id_or_number]

        # Generate on-the-fly realistic record
        number = sys_id_or_number if sys_id_or_number.startswith("INC") else "INC0010042"
        sys_id = sys_id_or_number if not sys_id_or_number.startswith("INC") else snow_sys_id()
        record = {
            "mode": "mock",
            "table": "incident",
            "number": number,
            "sys_id": sys_id,
            "url": f"https://{self.instance}.service-now.com/nav_to.do?uri=incident.do?sys_id={sys_id}",
            "state": "Open",
            "payload": {
                "short_description": "Network connectivity issue",
                "category": "network",
                "priority": "2",
                "state": "1",
            },
        }
        self._mock_records[number] = record
        self._mock_records[sys_id] = record
        return record

    def update_incident(self, sys_id_or_number: str, updates: dict[str, Any], work_note: str | None = None) -> dict:
        """Update an existing incident (state transition, work note, or close notes)."""
        if self.is_live:
            try:
                headers = {"Accept": "application/json", "Content-Type": "application/json"}
                auth = None
                if self.settings.servicenow_token:
                    headers["Authorization"] = f"Bearer {self.settings.servicenow_token}"
                else:
                    auth = (self.settings.servicenow_user, self.settings.servicenow_password)

                patch_data = dict(updates)
                if work_note:
                    patch_data["work_notes"] = work_note

                with httpx.Client(timeout=10.0) as client:
                    resp = client.patch(
                        f"{self.base_url}/incident/{sys_id_or_number}",
                        json=patch_data,
                        headers=headers,
                        auth=auth,
                    )
                    if resp.status_code in (200, 201):
                        data = resp.json().get("result", {})
                        return {
                            "mode": "live",
                            "table": "incident",
                            "number": data.get("number", sys_id_or_number),
                            "sys_id": data.get("sys_id", sys_id_or_number),
                            "url": f"https://{self.instance}.service-now.com/nav_to.do?uri=incident.do?sys_id={sys_id_or_number}",
                            "state": data.get("state", "Updated"),
                            "payload": data,
                        }
            except Exception as exc:
                logger.warning(f"Live update failed ({exc}); applying to mock.")

        record = self._mock_records.get(sys_id_or_number, {
            "mode": "mock",
            "table": "incident",
            "number": sys_id_or_number if sys_id_or_number.startswith("INC") else "INC0010042",
            "sys_id": sys_id_or_number if not sys_id_or_number.startswith("INC") else snow_sys_id(),
            "url": f"https://{self.instance}.service-now.com/nav_to.do?uri=incident.do?sys_id={sys_id_or_number}",
            "state": "Updated",
            "payload": {},
        })
        record["payload"].update(updates)
        if "state" in updates:
            val = updates["state"]
            inv_state = {v: k for k, v in STATE_MAP.items()}
            record["state"] = inv_state.get(val, val)
        return record

    def create_service_request(
        self,
        item_name: str,
        requester_name: str,
        requester_email: str,
        department: str,
        justification: str,
        status: str = "Requested",
    ) -> dict:
        """Create a ServiceNow Service Catalog Request (sc_request)."""
        number = self._next_request_number()
        sys_id = snow_sys_id()

        payload = {
            "short_description": f"Software Request: {item_name}",
            "description": f"Requester: {requester_name} ({requester_email}, {department})\nJustification: {justification}",
            "requested_for": requester_name,
            "stage": status,
            "cat_item": item_name,
        }

        if self.is_live:
            try:
                headers = {"Accept": "application/json", "Content-Type": "application/json"}
                auth = None
                if self.settings.servicenow_token:
                    headers["Authorization"] = f"Bearer {self.settings.servicenow_token}"
                else:
                    auth = (self.settings.servicenow_user, self.settings.servicenow_password)

                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(
                        f"{self.base_url}/sc_request",
                        json=payload,
                        headers=headers,
                        auth=auth,
                    )
                    if resp.status_code in (200, 201):
                        data = resp.json().get("result", {})
                        number = data.get("number", number)
                        sys_id = data.get("sys_id", sys_id)
                        record = {
                            "mode": "live",
                            "table": "sc_request",
                            "number": number,
                            "sys_id": sys_id,
                            "url": f"https://{self.instance}.service-now.com/nav_to.do?uri=sc_request.do?sys_id={sys_id}",
                            "state": status,
                            "payload": data,
                        }
                        self._mock_records[number] = record
                        self._mock_records[sys_id] = record
                        return record
            except Exception as exc:
                logger.warning(f"Live sc_request call failed ({exc}); falling back to mock.")

        url = f"https://{self.instance}.service-now.com/nav_to.do?uri=sc_request.do?sys_id={sys_id}"
        record = {
            "mode": "mock",
            "table": "sc_request",
            "number": number,
            "sys_id": sys_id,
            "url": url,
            "state": status,
            "payload": payload,
        }
        self._mock_records[number] = record
        self._mock_records[sys_id] = record
        return record

    def update_service_request(
        self,
        sys_id_or_number: str,
        status: str,
        work_note: str | None = None,
    ) -> dict:
        """Update a ServiceNow Service Request status (e.g. Approved, Provisioning, Completed, Rejected)."""
        if self.is_live:
            try:
                headers = {"Accept": "application/json", "Content-Type": "application/json"}
                auth = None
                if self.settings.servicenow_token:
                    headers["Authorization"] = f"Bearer {self.settings.servicenow_token}"
                else:
                    auth = (self.settings.servicenow_user, self.settings.servicenow_password)

                patch_data: dict[str, Any] = {"stage": status}
                if work_note:
                    patch_data["work_notes"] = work_note

                with httpx.Client(timeout=10.0) as client:
                    resp = client.patch(
                        f"{self.base_url}/sc_request/{sys_id_or_number}",
                        json=patch_data,
                        headers=headers,
                        auth=auth,
                    )
                    if resp.status_code in (200, 201):
                        data = resp.json().get("result", {})
                        return {
                            "mode": "live",
                            "table": "sc_request",
                            "number": data.get("number", sys_id_or_number),
                            "sys_id": data.get("sys_id", sys_id_or_number),
                            "url": f"https://{self.instance}.service-now.com/nav_to.do?uri=sc_request.do?sys_id={sys_id_or_number}",
                            "state": status,
                            "payload": data,
                        }
            except Exception as exc:
                logger.warning(f"Live update_service_request failed ({exc}); falling back to mock.")

        record = self._mock_records.get(sys_id_or_number, {
            "mode": "mock",
            "table": "sc_request",
            "number": sys_id_or_number if sys_id_or_number.startswith("REQ") else "REQ001245",
            "sys_id": sys_id_or_number if not sys_id_or_number.startswith("REQ") else snow_sys_id(),
            "url": f"https://{self.instance}.service-now.com/nav_to.do?uri=sc_request.do?sys_id={sys_id_or_number}",
            "state": status,
            "payload": {},
        })
        record["state"] = status
        record["payload"]["stage"] = status
        if work_note:
            record["payload"]["work_notes"] = work_note
        return record
