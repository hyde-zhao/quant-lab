"""CR014-S06 candidate retention dry-run 合同。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Iterable, Mapping

from .incremental import cr014_s06_zero_permission_counters

RETENTION_ACTION_RETAIN = "retain"
RETENTION_ACTION_RECOMMEND_ARCHIVE = "recommend_archive"
RETENTION_ACTION_RECOMMEND_DELETE = "recommend_delete"
RETENTION_ACTION_BLOCKED = "blocked"

PUBLISHED_TRUTH_PROTECTED = "published_truth_protected"
AUDIT_REF_PROTECTED = "audit_ref_protected"
RETENTION_DRY_RUN_RECOMMENDATION = "retention_dry_run_recommendation"
RETENTION_EXECUTE_NOT_AUTHORIZED = "retention_execute_not_authorized"
RETENTION_POLICY_RETAIN = "retention_policy_retain"


@dataclass(frozen=True, slots=True)
class CandidateRetentionPolicy:
    archive_after_days: int = 30
    delete_after_days: int = 90
    execute_authorization_id: str | None = None

    @property
    def execute_authorized(self) -> bool:
        return bool(str(self.execute_authorization_id or "").strip())


@dataclass(frozen=True, slots=True)
class RetentionRecommendation:
    target_ref: str
    dataset: str
    run_id: str | None
    action: str
    recommended_action: str
    reason_code: str
    dry_run: bool
    protected_by_publish: bool
    protected_by_audit: bool
    requires_execute_authorization: bool
    execute_authorized: bool = False
    permission_counters: dict[str, int] = field(default_factory=cr014_s06_zero_permission_counters)
    delete_count: int = 0
    archive_count: int = 0
    migrate_count: int = 0
    lake_writes: int = 0
    current_pointer_changes: int = 0
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_ref": self.target_ref,
            "dataset": self.dataset,
            "run_id": self.run_id,
            "action": self.action,
            "recommended_action": self.recommended_action,
            "reason_code": self.reason_code,
            "dry_run": self.dry_run,
            "protected_by_publish": self.protected_by_publish,
            "protected_by_audit": self.protected_by_audit,
            "requires_execute_authorization": self.requires_execute_authorization,
            "execute_authorized": self.execute_authorized,
            "permission_counters": dict(self.permission_counters),
            "delete_count": self.delete_count,
            "archive_count": self.archive_count,
            "migrate_count": self.migrate_count,
            "lake_writes": self.lake_writes,
            "current_pointer_changes": self.current_pointer_changes,
            "details": [dict(item) for item in self.details],
        }


def _payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, str):
        return {"candidate_ref": value}
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _published_refs(publish_status: Mapping[str, Any] | Iterable[Any] | None) -> set[str]:
    if publish_status is None:
        return set()
    if isinstance(publish_status, Mapping):
        refs: set[str] = set()
        for key, value in publish_status.items():
            if value in (True, "published", "current_truth", "published_current_truth"):
                refs.add(str(key))
        for key in ("published_refs", "current_truth_refs"):
            value = publish_status.get(key)
            if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                refs.update(str(item) for item in value)
        return refs
    return {str(item) for item in publish_status}


def _audit_ref_map(audit_refs: Mapping[str, Any] | Iterable[Any] | None) -> dict[str, Any]:
    if audit_refs is None:
        return {}
    if isinstance(audit_refs, Mapping):
        return dict(audit_refs)
    return {str(item): True for item in audit_refs}


def _target_ref(candidate: Mapping[str, Any]) -> str:
    for key in ("candidate_ref", "candidate_path", "target_ref", "ref"):
        value = candidate.get(key)
        if value is not None and str(value).strip():
            return str(value)
    dataset = candidate.get("dataset", "")
    run_id = candidate.get("run_id", "")
    return f"candidate://{dataset}/{run_id}"


def _recommended_action(age_days: int, policy: CandidateRetentionPolicy) -> str:
    if age_days >= policy.delete_after_days:
        return "delete"
    if age_days >= policy.archive_after_days:
        return "archive"
    return RETENTION_ACTION_RETAIN


def evaluate_candidate_retention(
    candidates: Iterable[Any],
    publish_status: Mapping[str, Any] | Iterable[Any] | None = None,
    audit_refs: Mapping[str, Any] | Iterable[Any] | None = None,
    policy: CandidateRetentionPolicy | Mapping[str, Any] | None = None,
    *,
    dry_run: bool = True,
) -> tuple[RetentionRecommendation, ...]:
    """评估 candidate retention；默认只输出 recommendation，不执行删除或迁移。"""

    if policy is None:
        retention_policy = CandidateRetentionPolicy()
    elif isinstance(policy, CandidateRetentionPolicy):
        retention_policy = policy
    else:
        retention_policy = CandidateRetentionPolicy(
            archive_after_days=int(policy.get("archive_after_days", 30)),
            delete_after_days=int(policy.get("delete_after_days", 90)),
            execute_authorization_id=policy.get("execute_authorization_id"),
        )

    published = _published_refs(publish_status)
    audit_map = _audit_ref_map(audit_refs)
    recommendations: list[RetentionRecommendation] = []
    for item in candidates:
        candidate = _payload(item)
        target_ref = _target_ref(candidate)
        dataset = str(candidate.get("dataset") or "")
        run_id = candidate.get("run_id")
        published_status = candidate.get("publish_status")
        protected_by_publish = (
            target_ref in published
            or candidate.get("published") is True
            or published_status in ("published", "current_truth", "published_current_truth")
        )
        candidate_audit_refs = candidate.get("audit_refs") or ()
        protected_by_audit = bool(audit_map.get(target_ref) or candidate_audit_refs)
        age_days = int(candidate.get("age_days") or 0)
        recommended = _recommended_action(age_days, retention_policy)

        if protected_by_publish:
            action = RETENTION_ACTION_RETAIN
            reason = PUBLISHED_TRUTH_PROTECTED
            requires_execute = False
        elif protected_by_audit:
            action = RETENTION_ACTION_RETAIN
            reason = AUDIT_REF_PROTECTED
            requires_execute = False
        elif recommended == RETENTION_ACTION_RETAIN:
            action = RETENTION_ACTION_RETAIN
            reason = RETENTION_POLICY_RETAIN
            requires_execute = False
        elif dry_run:
            action = (
                RETENTION_ACTION_RECOMMEND_DELETE
                if recommended == "delete"
                else RETENTION_ACTION_RECOMMEND_ARCHIVE
            )
            reason = RETENTION_DRY_RUN_RECOMMENDATION
            requires_execute = True
        elif not retention_policy.execute_authorized:
            action = RETENTION_ACTION_BLOCKED
            reason = RETENTION_EXECUTE_NOT_AUTHORIZED
            requires_execute = True
        else:
            action = f"execute_{recommended}_authorized_noop"
            reason = "execute_authorized_no_side_effect_in_s06_contract"
            requires_execute = True

        recommendations.append(
            RetentionRecommendation(
                target_ref=target_ref,
                dataset=dataset,
                run_id=str(run_id) if run_id is not None else None,
                action=action,
                recommended_action=recommended,
                reason_code=reason,
                dry_run=dry_run,
                protected_by_publish=protected_by_publish,
                protected_by_audit=protected_by_audit,
                requires_execute_authorization=requires_execute,
                execute_authorized=retention_policy.execute_authorized,
                details=(
                    {
                        "age_days": age_days,
                        "archive_after_days": retention_policy.archive_after_days,
                        "delete_after_days": retention_policy.delete_after_days,
                    },
                ),
            )
        )
    return tuple(recommendations)


__all__ = [
    "AUDIT_REF_PROTECTED",
    "CandidateRetentionPolicy",
    "PUBLISHED_TRUTH_PROTECTED",
    "RETENTION_ACTION_BLOCKED",
    "RETENTION_ACTION_RECOMMEND_ARCHIVE",
    "RETENTION_ACTION_RECOMMEND_DELETE",
    "RETENTION_ACTION_RETAIN",
    "RETENTION_DRY_RUN_RECOMMENDATION",
    "RETENTION_EXECUTE_NOT_AUTHORIZED",
    "RETENTION_POLICY_RETAIN",
    "RetentionRecommendation",
    "evaluate_candidate_retention",
]
