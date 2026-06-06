"""SQLModel table definitions replacing in-memory Pydantic models."""
from uuid import uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from sqlalchemy import String, DateTime, Text, Float, Integer, Boolean

# ---------------------------------------------------------------------------
# Users & Auth (fastapi-users compatible)
# ---------------------------------------------------------------------------
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    hashed_password: str = Field(sa_column=Column(String, nullable=False))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False))
    is_superuser: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    is_verified: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    full_name: Optional[str] = Field(default=None, sa_column=Column(String))
    role: str = Field(default="legal", sa_column=Column(String))  # legal, finance, ceo, admin
    org_id: Optional[str] = Field(default=None, sa_column=Column(String, index=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class Organization(SQLModel, table=True):
    __tablename__ = "organizations"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(sa_column=Column(String, nullable=False))
    slug: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    industry: str = Field(default="", sa_column=Column(String))
    revenue_range: str = Field(default="", sa_column=Column(String))
    employee_count: int = Field(default=0, sa_column=Column(Integer))
    address: str = Field(default="", sa_column=Column(String))
    gstin: str = Field(default="", sa_column=Column(String))
    cin: str = Field(default="", sa_column=Column(String))
    dpo_name: str = Field(default="", sa_column=Column(String))
    dpo_email: str = Field(default="", sa_column=Column(String))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------
class Contract(SQLModel, table=True):
    __tablename__ = "contracts"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    title: str = Field(sa_column=Column(String, nullable=False))
    contract_type: str = Field(default="vendor", sa_column=Column(String))
    status: str = Field(default="draft", sa_column=Column(String, index=True))
    counterparty_name: str = Field(default="", sa_column=Column(String))
    counterparty_email: str = Field(default="", sa_column=Column(String))
    governing_law: str = Field(default="", sa_column=Column(String))
    start_date: Optional[str] = Field(default=None, sa_column=Column(String))
    end_date: Optional[str] = Field(default=None, sa_column=Column(String))
    auto_renewal: bool = Field(default=False, sa_column=Column(Boolean))
    value_inr: float = Field(default=0.0, sa_column=Column(Float))
    risk_score: float = Field(default=0.0, sa_column=Column(Float))
    pdf_path: str = Field(default="", sa_column=Column(String))
    parsed_text: str = Field(default="", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class ContractClause(SQLModel, table=True):
    __tablename__ = "contract_clauses"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    contract_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    clause_type: str = Field(sa_column=Column(String, index=True, nullable=False))
    clause_text: str = Field(sa_column=Column(Text, nullable=False))
    page_number: int = Field(default=1, sa_column=Column(Integer))
    confidence_score: float = Field(default=0.0, sa_column=Column(Float))
    extracted_by: str = Field(default="legal_bert", sa_column=Column(String))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class ContractVersion(SQLModel, table=True):
    __tablename__ = "contract_versions"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    contract_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    version_number: int = Field(default=1, sa_column=Column(Integer))
    title: str = Field(default="", sa_column=Column(String))
    pdf_path: str = Field(default="", sa_column=Column(String))
    parsed_text: str = Field(default="", sa_column=Column(Text))
    created_by: str = Field(default="", sa_column=Column(String))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class PlainEnglishSummary(SQLModel, table=True):
    __tablename__ = "plain_english_summaries"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    contract_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    clause_id: Optional[str] = Field(default=None, sa_column=Column(String, index=True))
    clause_type: str = Field(default="", sa_column=Column(String))
    original_text: str = Field(default="", sa_column=Column(Text))
    plain_english: str = Field(default="", sa_column=Column(Text))
    risk_level: str = Field(default="low", sa_column=Column(String))
    risk_explanation: str = Field(default="", sa_column=Column(Text))
    suggestions: str = Field(default="", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class ClauseHighlight(SQLModel, table=True):
    __tablename__ = "clause_highlights"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    contract_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    clause_id: Optional[str] = Field(default=None, sa_column=Column(String, index=True))
    clause_type: str = Field(default="", sa_column=Column(String))
    page_number: int = Field(default=1, sa_column=Column(Integer))
    x: float = Field(default=0.0, sa_column=Column(Float))
    y: float = Field(default=0.0, sa_column=Column(Float))
    width: float = Field(default=0.0, sa_column=Column(Float))
    height: float = Field(default=0.0, sa_column=Column(Float))
    color: str = Field(default="rgba(255, 179, 0, 0.3)", sa_column=Column(String))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class ContractEmbedding(SQLModel, table=True):
    __tablename__ = "contract_embeddings"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    contract_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    chunk_text: str = Field(default="", sa_column=Column(Text))
    embedding: Optional[List[float]] = Field(default=None, sa_column=Column(JSON))
    page_number: int = Field(default=1, sa_column=Column(Integer))
    embedder: str = Field(default="", sa_column=Column(String))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

# ---------------------------------------------------------------------------
# Obligations
# ---------------------------------------------------------------------------
class Obligation(SQLModel, table=True):
    __tablename__ = "obligations"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    contract_id: str = Field(default="", sa_column=Column(String, index=True))
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    description: str = Field(sa_column=Column(Text, nullable=False))
    obligation_type: str = Field(default="compliance", sa_column=Column(String))
    due_date: Optional[str] = Field(default=None, sa_column=Column(String))
    status: str = Field(default="pending", sa_column=Column(String))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

# ---------------------------------------------------------------------------
# Playbook & Risk
# ---------------------------------------------------------------------------
class PlaybookRule(SQLModel, table=True):
    __tablename__ = "playbook_rules"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    rule_name: str = Field(sa_column=Column(String, nullable=False))
    rule_type: str = Field(sa_column=Column(String, nullable=False))
    condition: str = Field(sa_column=Column(String, nullable=False))
    threshold_value: str = Field(sa_column=Column(String, nullable=False))
    severity: str = Field(default="high", sa_column=Column(String))
    is_active: bool = Field(default=True, sa_column=Column(Boolean))
    contract_type: str = Field(default="", sa_column=Column(String))
    # If empty, applies to all contract types. Otherwise only to matching type.

class RiskAssessment(SQLModel, table=True):
    __tablename__ = "risk_assessments"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    contract_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    overall_score: float = Field(default=0.0, sa_column=Column(Float))
    playbook_score: float = Field(default=0.0, sa_column=Column(Float))
    law_score: float = Field(default=0.0, sa_column=Column(Float))
    regulatory_score: float = Field(default=0.0, sa_column=Column(Float))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class RiskFinding(SQLModel, table=True):
    __tablename__ = "risk_findings"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    assessment_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    clause_id: Optional[str] = Field(default=None, sa_column=Column(String))
    finding_type: str = Field(sa_column=Column(String, nullable=False))
    severity: str = Field(sa_column=Column(String, nullable=False))
    title: str = Field(sa_column=Column(String, nullable=False))
    description: str = Field(sa_column=Column(Text, nullable=False))
    suggested_amendment: str = Field(default="", sa_column=Column(Text))
    statute_reference: str = Field(default="", sa_column=Column(String))
    is_resolved: bool = Field(default=False, sa_column=Column(Boolean))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class EnforceabilityBenchmark(SQLModel, table=True):
    __tablename__ = "enforceability_benchmarks"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    clause_type: str = Field(sa_column=Column(String, nullable=False))
    statute_act: str = Field(sa_column=Column(String, nullable=False))
    section_number: str = Field(sa_column=Column(String, nullable=False))
    enforceability_score: float = Field(default=0.0, sa_column=Column(Float))
    conditions: str = Field(default="", sa_column=Column(Text))

# ---------------------------------------------------------------------------
# Regulatory
# ---------------------------------------------------------------------------
class RegulatorySource(SQLModel, table=True):
    __tablename__ = "regulatory_sources"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(sa_column=Column(String, nullable=False))
    source_type: str = Field(sa_column=Column(String, nullable=False))
    url: str = Field(sa_column=Column(String, nullable=False))
    rss_feed_url: Optional[str] = Field(default=None, sa_column=Column(String))
    last_checked: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))

class RegulatoryUpdate(SQLModel, table=True):
    __tablename__ = "regulatory_updates"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    source_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    title: str = Field(sa_column=Column(String, nullable=False))
    summary: str = Field(default="", sa_column=Column(Text))
    effective_date: Optional[str] = Field(default=None, sa_column=Column(String))
    affected_sectors: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    affected_clause_types: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class RegulatoryAlert(SQLModel, table=True):
    __tablename__ = "regulatory_alerts"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    update_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    title: str = Field(sa_column=Column(String, nullable=False))
    description: str = Field(default="", sa_column=Column(Text))
    affected_contract_ids: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    suggested_actions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    priority: str = Field(default="medium", sa_column=Column(String))
    status: str = Field(default="unread", sa_column=Column(String))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

# ---------------------------------------------------------------------------
# Templates, Approvals, Comments, Notifications
# ---------------------------------------------------------------------------
class ContractTemplate(SQLModel, table=True):
    __tablename__ = "contract_templates"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    name: str = Field(sa_column=Column(String, nullable=False))
    category: str = Field(sa_column=Column(String, nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    variables: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

class ApprovalStage(SQLModel, table=True):
    __tablename__ = "approval_stages"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    contract_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    stage_name: str = Field(default="legal_review", sa_column=Column(String))
    approver_name: str = Field(default="", sa_column=Column(String))
    approver_email: str = Field(default="", sa_column=Column(String))
    status: str = Field(default="pending", sa_column=Column(String))
    comment: str = Field(default="", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))
    resolved_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))

class ContractComment(SQLModel, table=True):
    __tablename__ = "contract_comments"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    contract_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    clause_id: Optional[str] = Field(default=None, sa_column=Column(String))
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    author_name: str = Field(default="", sa_column=Column(String))
    author_role: str = Field(default="", sa_column=Column(String))
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class Notification(SQLModel, table=True):
    __tablename__ = "notifications"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    title: str = Field(sa_column=Column(String, nullable=False))
    message: str = Field(default="", sa_column=Column(Text))
    notification_type: str = Field(default="info", sa_column=Column(String))
    is_read: bool = Field(default=False, sa_column=Column(Boolean))
    link: str = Field(default="", sa_column=Column(String))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

# ---------------------------------------------------------------------------
# Audit & Logs
# ---------------------------------------------------------------------------
class AutomationLog(SQLModel, table=True):
    __tablename__ = "automation_logs"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    automation_type: str = Field(sa_column=Column(String, nullable=False))
    status: str = Field(default="completed", sa_column=Column(String))
    input_summary: str = Field(default="", sa_column=Column(Text))
    output_summary: str = Field(default="", sa_column=Column(Text))
    duration_ms: int = Field(default=0, sa_column=Column(Integer))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class ContractTreeIndex(SQLModel, table=True):
    """PageIndex-style hierarchical tree for contract documents."""
    __tablename__ = "contract_tree_indices"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    contract_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    doc_name: str = Field(default="", sa_column=Column(String))
    structure: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    line_count: int = Field(default=0, sa_column=Column(Integer))
    node_count: int = Field(default=0, sa_column=Column(Integer))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

class AuditTrailEntry(SQLModel, table=True):
    __tablename__ = "audit_trail"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    org_id: str = Field(sa_column=Column(String, index=True, nullable=False))
    actor_id: str = Field(sa_column=Column(String, nullable=False))
    actor_email: str = Field(sa_column=Column(String, nullable=False))
    action: str = Field(sa_column=Column(String, nullable=False))
    resource_type: str = Field(sa_column=Column(String, nullable=False))
    resource_id: str = Field(sa_column=Column(String, nullable=False))
    details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    previous_hash: str = Field(default="", sa_column=Column(String))
    entry_hash: str = Field(sa_column=Column(String, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))
