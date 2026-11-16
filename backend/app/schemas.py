from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserIn(BaseModel):
    id: str = "emma.walsh"
    name: str = "Emma Walsh"
    email: str = "emma.walsh@northline.com"
    title: str = "Product Engineer"
    department: str = "Engineering"
    location: str = "Austin HQ"
    employee_type: str = "Employee"


class ChatIn(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    session_id: str | None = None
    user: UserIn = Field(default_factory=UserIn)


class IntakeIn(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    user: UserIn = Field(default_factory=UserIn)
    channel: str = "Employee portal"


class DecideIn(BaseModel):
    decision: Literal["approve", "reject"]
    actor: str = "Jordan Hale"
    note: str = ""


class ApproveArticleIn(BaseModel):
    actor: str = "Priya Nair"
    title: str | None = None


class CatalogRequestIn(BaseModel):
    item_id: str
    justification: str = "Required for my role."
    user: UserIn = Field(default_factory=UserIn)


class EntityOut(BaseModel):
    application: str
    error_text: str
    user: str
    location: str


class ClassificationOut(BaseModel):
    intent: str
    category: str
    subcategory: str
    priority: Literal["P1", "P2", "P3", "P4"]
    urgency: Literal["High", "Medium", "Low"]
    impact: Literal["Individual", "Group", "Site"]
    assignment_group: str
    configuration_item: str
    summary: str
    suggested_resolution: str
    entities: EntityOut
    confidence: float
    rationale: str


class StepOut(BaseModel):
    name: str
    plan: str
    result: str = ""
    status: Literal["pending", "success", "failed"] = "pending"
    at: str | None = None


class ActionOut(BaseModel):
    id: str
    playbook_id: str
    title: str
    confidence: float
    policy: Literal["auto", "approval_required"]
    status: Literal["proposed", "executed", "rejected"]
    rationale: str
    risk: str
    steps: list[StepOut]


class TimelineOut(BaseModel):
    id: str
    at: str
    actor: str
    action: str
    detail: str
    result: str | None = None


class WorkNote(BaseModel):
    at: str
    author: str
    text: str


class SnowOut(BaseModel):
    mode: str
    table: str
    number: str
    sys_id: str
    url: str
    state: str
    work_notes: list[WorkNote] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)


class CitationOut(BaseModel):
    id: str
    title: str
    category: str = ""
    score: float
    confidence: float
    excerpt: str


class DuplicateOut(BaseModel):
    number: str
    summary: str
    status: str
    score: float
    caller_name: str


class TicketOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: str
    caller_name: str
    caller_email: str
    department: str
    location: str
    channel: str
    status: Literal["Open", "In Progress", "Pending", "Resolved", "Escalated"]
    description: str
    classification: ClassificationOut
    servicenow: SnowOut
    timeline: list[TimelineOut]
    actions: list[ActionOut]
    citations: list[CitationOut]
    duplicate_of: str | None = None
    duplicate_score: float | None = None
    resolution_notes: str | None = None
    resolution_mode: str | None = None
    ai_resolved: bool = False
    kb_draft_id: str | None = None
    escalation_reason: str | None = None
    created_at: str
    updated_at: str


class ArticleOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    category: str
    tags: list[str]
    owner: str
    status: Literal["published", "draft"]
    updated: str
    symptoms: str
    steps: list[str]
    source_ticket: str | None = None
    approved_by: str | None = None


class CatalogItemOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    owner: str
    license_type: str
    licenses_total: int | None = None
    licenses_used: int | None = None
    approval: str
    approval_reason: str
    provision_minutes: int
    eligible: str
    departments: list[str]
    contractors_allowed: bool = True
    summary: str
    aliases: list[str] = Field(default_factory=list)


class RequestEvent(BaseModel):
    at: str
    status: str
    detail: str


class SoftwareRequestOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: str
    item_id: str
    software: str
    requester_name: str
    requester_email: str
    department: str
    justification: str
    status: Literal["Requested", "Pending approval", "Approved", "Provisioning", "Completed", "Rejected"]
    approval_required: bool
    eligible: bool
    reason: str
    provision_minutes: int
    timeline: list[RequestEvent]
    work_notes: list[WorkNote] = Field(default_factory=list)
    servicenow: SnowOut | None = None
    created_at: str
    updated_at: str


class ChatOut(BaseModel):
    session_id: str
    intent: str
    reply: str
    confidence: float
    knows: bool
    offer_ticket: bool = False
    provider_label: str
    narrative_source: str
    provider_note: str | None = None
    citations: list[CitationOut] = Field(default_factory=list)
    classification: ClassificationOut | None = None
    ticket: TicketOut | None = None
    duplicate: DuplicateOut | None = None
    proposed_actions: list[ActionOut] = Field(default_factory=list)
    auto_resolved: bool = False
    software_request: SoftwareRequestOut | None = None
    escalated: bool = False


class SearchOut(BaseModel):
    query: str
    results: list[CitationOut]
    confidence: float
    knows: bool


class GapOut(BaseModel):
    topic: str
    count: int
    examples: list[str]
    hint: str


class HealthOut(BaseModel):
    status: str
    service: str
    provider: str
    provider_label: str
    provider_note: str
    model: str
    store: str
    servicenow: str
    embeddings: str
    vector_search: str
    thresholds: dict
    counts: dict
