"""CR014-S06 replay 与 resume conflict 合同。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Iterable, Mapping

from .incremental import cr014_s06_zero_permission_counters

REPLAY_SOURCE_MISSING = "replay_source_missing"
REPLAY_CANDIDATE_UNPUBLISHED = "candidate_unpublished"
PUBLISHED_ASOF_READY = "ready_for_replay"
PUBLISHED_ASOF_BLOCKED = "blocked"
PUBLISHED_ASOF_SNAPSHOT_MISSING = "published_asof_snapshot_missing"
PUBLISHED_ASOF_NOT_PUBLISHED = "published_asof_not_published"
PUBLISHED_ASOF_REF_INCOMPLETE = "published_asof_ref_incomplete"
RESUME_CONFLICT = "resume_conflict"
PARAMS_HASH_CONFLICT = "params_hash_conflict"
MANIFEST_REF_CONFLICT = "manifest_ref_conflict"
PARTITION_LOCK_CONFLICT = "partition_lock_conflict"


@dataclass(frozen=True, slots=True)
class ReplayRequest:
    run_id: str
    batch_id: str
    dataset: str | None = None
    manifest_refs: tuple[Any, ...] = ()
    raw_refs: tuple[Any, ...] = ()
    candidate_config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReplayCandidate:
    dataset: str
    run_id: str
    batch_id: str
    candidate_path: str
    status: str = REPLAY_CANDIDATE_UNPUBLISHED
    current_pointer_changes: int = 0
    provider_fetches: int = 0
    credential_reads: int = 0
    raw_writes: int = 0
    evidence: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "run_id": self.run_id,
            "batch_id": self.batch_id,
            "candidate_path": self.candidate_path,
            "status": self.status,
            "current_pointer_changes": self.current_pointer_changes,
            "provider_fetches": self.provider_fetches,
            "credential_reads": self.credential_reads,
            "raw_writes": self.raw_writes,
            "evidence": [dict(item) for item in self.evidence],
        }


@dataclass(frozen=True, slots=True)
class ReplayResult:
    run_id: str
    batch_id: str
    status: str
    candidate: ReplayCandidate | None = None
    evidence: tuple[dict[str, Any], ...] = ()
    permission_counters: dict[str, int] = field(default_factory=cr014_s06_zero_permission_counters)
    provider_fetches: int = 0
    credential_reads: int = 0
    raw_writes: int = 0
    current_pointer_changes: int = 0
    publish_count: int = 0
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "batch_id": self.batch_id,
            "status": self.status,
            "candidate": self.candidate.to_dict() if self.candidate else None,
            "evidence": [dict(item) for item in self.evidence],
            "permission_counters": dict(self.permission_counters),
            "provider_fetches": self.provider_fetches,
            "credential_reads": self.credential_reads,
            "raw_writes": self.raw_writes,
            "current_pointer_changes": self.current_pointer_changes,
            "publish_count": self.publish_count,
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


@dataclass(frozen=True, slots=True)
class ReplaySideEffectCheck:
    passed: bool
    counters: dict[str, int]
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PublishedAsOfReplayRequest:
    dataset: str
    as_of_trade_date: str
    run_id: str = "published-asof-replay"
    batch_id: str = "published-asof"


@dataclass(frozen=True, slots=True)
class PublishedAsOfReplayResult:
    dataset: str
    as_of_trade_date: str
    run_id: str
    batch_id: str
    status: str
    published_path: str = ""
    manifest_ref: str = ""
    replay_source: str = "published_asof_snapshot"
    provider_fetches: int = 0
    credential_reads: int = 0
    lake_writes: int = 0
    catalog_writes: int = 0
    manifest_writes: int = 0
    current_pointer_changes: int = 0
    runtime_operations: int = 0
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    @property
    def ready(self) -> bool:
        return self.status == PUBLISHED_ASOF_READY

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "as_of_trade_date": self.as_of_trade_date,
            "run_id": self.run_id,
            "batch_id": self.batch_id,
            "status": self.status,
            "ready": self.ready,
            "published_path": self.published_path,
            "manifest_ref": self.manifest_ref,
            "replay_source": self.replay_source,
            "provider_fetches": self.provider_fetches,
            "credential_reads": self.credential_reads,
            "lake_writes": self.lake_writes,
            "catalog_writes": self.catalog_writes,
            "manifest_writes": self.manifest_writes,
            "current_pointer_changes": self.current_pointer_changes,
            "runtime_operations": self.runtime_operations,
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


@dataclass(frozen=True, slots=True)
class ResumeConflict:
    conflict_type: str
    run_id: str
    existing_ref: str
    requested_ref: str
    resolution_options: tuple[str, ...]
    blocked_side_effects: tuple[str, ...]
    existing_params_hash: str | None = None
    requested_params_hash: str | None = None
    lock_owner: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResumeConflictResult:
    status: str
    has_conflict: bool
    conflict: ResumeConflict | None = None
    provider_fetches: int = 0
    credential_reads: int = 0
    raw_writes: int = 0
    current_pointer_changes: int = 0
    permission_counters: dict[str, int] = field(default_factory=cr014_s06_zero_permission_counters)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "has_conflict": self.has_conflict,
            "conflict": self.conflict.to_dict() if self.conflict else None,
            "provider_fetches": self.provider_fetches,
            "credential_reads": self.credential_reads,
            "raw_writes": self.raw_writes,
            "current_pointer_changes": self.current_pointer_changes,
            "permission_counters": dict(self.permission_counters),
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
        return {"ref": value}
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _published_asof_request(
    value: PublishedAsOfReplayRequest | Mapping[str, Any],
) -> PublishedAsOfReplayRequest:
    if isinstance(value, PublishedAsOfReplayRequest):
        return value
    payload = dict(value)
    return PublishedAsOfReplayRequest(
        dataset=str(payload.get("dataset") or ""),
        as_of_trade_date=str(payload.get("as_of_trade_date") or ""),
        run_id=str(payload.get("run_id") or "published-asof-replay"),
        batch_id=str(payload.get("batch_id") or "published-asof"),
    )


def _published_flag(payload: Mapping[str, Any]) -> bool:
    status = str(payload.get("publish_status") or payload.get("status") or "").strip().lower()
    if status in {"candidate", "candidate_unpublished", "unpublished"}:
        return False
    if status in {"published", "current", "current_truth"}:
        return True
    return bool(payload.get("published"))


def _published_path(payload: Mapping[str, Any]) -> str:
    for key in ("published_path", "current_pointer_path", "canonical_path", "path"):
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def _manifest_ref(payload: Mapping[str, Any]) -> str:
    for key in ("manifest_ref", "manifest_path", "latest_manifest_ref", "latest_manifest_run_id"):
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def _published_asof_block(
    request: PublishedAsOfReplayRequest,
    code: str,
    details: Mapping[str, Any],
) -> PublishedAsOfReplayResult:
    return PublishedAsOfReplayResult(
        dataset=request.dataset,
        as_of_trade_date=request.as_of_trade_date,
        run_id=request.run_id,
        batch_id=request.batch_id,
        status=PUBLISHED_ASOF_BLOCKED,
        error_codes=(code,),
        details=(dict(details),),
    )


def build_published_asof_replay(
    request: PublishedAsOfReplayRequest | Mapping[str, Any],
    published_pointers: Iterable[Any],
) -> PublishedAsOfReplayResult:
    """Select an exact published as_of snapshot without lake/provider fallback."""

    replay_request = _published_asof_request(request)
    for item in published_pointers:
        payload = _payload(item)
        if str(payload.get("dataset") or payload.get("dataset_id") or "") != replay_request.dataset:
            continue
        if str(payload.get("as_of_trade_date") or payload.get("current_truth_as_of") or "") != replay_request.as_of_trade_date:
            continue
        if not _published_flag(payload):
            return _published_asof_block(
                replay_request,
                PUBLISHED_ASOF_NOT_PUBLISHED,
                {
                    "dataset": replay_request.dataset,
                    "as_of_trade_date": replay_request.as_of_trade_date,
                    "unblock_condition": "provide_published_current_pointer_for_requested_as_of",
                },
            )
        path = _published_path(payload)
        manifest_ref = _manifest_ref(payload)
        if not path or not manifest_ref:
            return _published_asof_block(
                replay_request,
                PUBLISHED_ASOF_REF_INCOMPLETE,
                {
                    "published_path_present": bool(path),
                    "manifest_ref_present": bool(manifest_ref),
                    "unblock_condition": "provide_complete_published_pointer_refs",
                },
            )
        return PublishedAsOfReplayResult(
            dataset=replay_request.dataset,
            as_of_trade_date=replay_request.as_of_trade_date,
            run_id=replay_request.run_id,
            batch_id=replay_request.batch_id,
            status=PUBLISHED_ASOF_READY,
            published_path=path,
            manifest_ref=manifest_ref,
        )
    return _published_asof_block(
        replay_request,
        PUBLISHED_ASOF_SNAPSHOT_MISSING,
        {
            "dataset": replay_request.dataset,
            "as_of_trade_date": replay_request.as_of_trade_date,
            "provider_backfill": "forbidden",
        },
    )


def _stable_hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _request(value: ReplayRequest | Mapping[str, Any]) -> ReplayRequest:
    if isinstance(value, ReplayRequest):
        return value
    return ReplayRequest(
        run_id=str(value.get("run_id") or ""),
        batch_id=str(value.get("batch_id") or ""),
        dataset=value.get("dataset"),
        manifest_refs=tuple(value.get("manifest_refs") or ()),
        raw_refs=tuple(value.get("raw_refs") or ()),
        candidate_config=dict(value.get("candidate_config") or {}),
    )


def _manifest_ref_text(payload: Mapping[str, Any]) -> str:
    for key in ("manifest_ref", "ref", "manifest_path", "candidate_path"):
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value)
    run_id = payload.get("run_id", "")
    batch_id = payload.get("batch_id", "")
    dataset = payload.get("dataset", "")
    return f"{dataset}:{run_id}:{batch_id}"


def _raw_ref_from_payload(payload: Mapping[str, Any], raw_refs: tuple[Any, ...]) -> str:
    if raw_refs:
        first = raw_refs[0]
        raw_payload = _payload(first)
        return str(raw_payload.get("raw_ref") or raw_payload.get("ref") or raw_payload.get("raw_path") or first)
    for key in ("raw_ref", "raw_path", "raw_uri"):
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def _find_manifest(request: ReplayRequest) -> dict[str, Any] | None:
    for item in request.manifest_refs:
        payload = _payload(item)
        if payload.get("run_id") not in (None, request.run_id):
            continue
        if payload.get("batch_id") not in (None, request.batch_id):
            continue
        if request.dataset and payload.get("dataset") not in (None, request.dataset):
            continue
        return payload
    return None


def run_replay_from_manifest(request: ReplayRequest | Mapping[str, Any]) -> ReplayResult:
    """只从 manifest/raw refs 派生 replay candidate；缺源时不补抓。"""

    replay_request = _request(request)
    manifest = _find_manifest(replay_request)
    raw_ref = _raw_ref_from_payload(manifest or {}, replay_request.raw_refs)
    if manifest is None or not raw_ref:
        return ReplayResult(
            run_id=replay_request.run_id,
            batch_id=replay_request.batch_id,
            status=REPLAY_SOURCE_MISSING,
            error_codes=(REPLAY_SOURCE_MISSING,),
            details=(
                {
                    "code": REPLAY_SOURCE_MISSING,
                    "manifest_ref_present": manifest is not None,
                    "raw_ref_present": bool(raw_ref),
                    "unblock_condition": "provide_existing_manifest_and_raw_refs_or_authorize_separate_run",
                },
            ),
        )

    dataset = str(replay_request.dataset or manifest.get("dataset") or "")
    candidate_path = str(
        replay_request.candidate_config.get("candidate_path")
        or manifest.get("candidate_path")
        or f"candidate://{dataset}/{replay_request.run_id}/{replay_request.batch_id}"
    )
    evidence = (
        {
            "type": "manifest_ref",
            "ref": _manifest_ref_text(manifest),
            "run_id": replay_request.run_id,
            "batch_id": replay_request.batch_id,
        },
        {"type": "raw_ref", "ref": raw_ref},
        {
            "type": "replay_boundary",
            "provider_fetches": 0,
            "credential_reads": 0,
            "raw_writes": 0,
            "current_pointer_changes": 0,
        },
    )
    candidate = ReplayCandidate(
        dataset=dataset,
        run_id=replay_request.run_id,
        batch_id=replay_request.batch_id,
        candidate_path=candidate_path,
        evidence=evidence,
    )
    return ReplayResult(
        run_id=replay_request.run_id,
        batch_id=replay_request.batch_id,
        status=REPLAY_CANDIDATE_UNPUBLISHED,
        candidate=candidate,
        evidence=evidence,
    )


def assert_no_replay_side_effects(result: ReplayResult | Mapping[str, Any]) -> ReplaySideEffectCheck:
    """返回结构化副作用检查结果，不抛出异常。"""

    payload = result.to_dict() if isinstance(result, ReplayResult) else dict(result)
    counters = {
        "provider_fetches": int(payload.get("provider_fetches") or 0),
        "credential_reads": int(payload.get("credential_reads") or 0),
        "raw_writes": int(payload.get("raw_writes") or 0),
        "current_pointer_changes": int(payload.get("current_pointer_changes") or 0),
    }
    failed = tuple(key for key, value in counters.items() if value != 0)
    if failed:
        return ReplaySideEffectCheck(
            passed=False,
            counters=counters,
            error_codes=("replay_side_effect_detected",),
            details=({"non_zero_counters": list(failed)},),
        )
    return ReplaySideEffectCheck(passed=True, counters=counters)


def _first_existing_ref(run_id: str, manifest_refs: Iterable[Any]) -> dict[str, Any] | None:
    for item in manifest_refs:
        payload = _payload(item)
        if str(payload.get("run_id") or run_id) == run_id:
            return payload
    return None


def _conflict(
    conflict_type: str,
    *,
    run_id: str,
    existing_ref: str,
    requested_ref: str,
    existing_params_hash: str | None,
    requested_params_hash: str | None,
    lock_owner: str | None = None,
    details: dict[str, Any] | None = None,
) -> ResumeConflictResult:
    return ResumeConflictResult(
        status=RESUME_CONFLICT,
        has_conflict=True,
        conflict=ResumeConflict(
            conflict_type=conflict_type,
            run_id=run_id,
            existing_ref=existing_ref,
            requested_ref=requested_ref,
            existing_params_hash=existing_params_hash,
            requested_params_hash=requested_params_hash,
            lock_owner=lock_owner,
            resolution_options=(
                "start_new_run_id",
                "reuse_existing_manifest_and_params",
                "manual_review_required",
            ),
            blocked_side_effects=(
                "silent_overwrite",
                "candidate_overwrite",
                "current_pointer_update",
            ),
            details=dict(details or {}),
        ),
    )


def detect_resume_conflict(
    run_id: str,
    manifest_refs: Iterable[Any],
    requested_params: Mapping[str, Any],
    lock_state: Mapping[str, Any] | None = None,
) -> ResumeConflictResult:
    """检测 resume 冲突；冲突时只返回结构化结果，不覆盖 candidate。"""

    requested_payload = dict(requested_params)
    requested_hash = str(requested_payload.get("params_hash") or _stable_hash(requested_payload))
    requested_ref = str(
        requested_payload.get("requested_manifest_ref")
        or requested_payload.get("manifest_ref")
        or f"{run_id}:{requested_hash}"
    )
    lock_payload = dict(lock_state or {})
    if lock_payload.get("locked") and str(lock_payload.get("run_id") or run_id) != run_id:
        return _conflict(
            PARTITION_LOCK_CONFLICT,
            run_id=run_id,
            existing_ref=str(lock_payload.get("manifest_ref") or lock_payload.get("run_id") or ""),
            requested_ref=requested_ref,
            existing_params_hash=lock_payload.get("params_hash"),
            requested_params_hash=requested_hash,
            lock_owner=lock_payload.get("owner"),
            details={"lock_state": lock_payload},
        )
    if lock_payload.get("locked") and lock_payload.get("params_hash") not in (None, requested_hash):
        return _conflict(
            PARTITION_LOCK_CONFLICT,
            run_id=run_id,
            existing_ref=str(lock_payload.get("manifest_ref") or lock_payload.get("run_id") or ""),
            requested_ref=requested_ref,
            existing_params_hash=str(lock_payload.get("params_hash")),
            requested_params_hash=requested_hash,
            lock_owner=lock_payload.get("owner"),
            details={"lock_state": lock_payload},
        )

    existing = _first_existing_ref(run_id, manifest_refs)
    if existing is None:
        return ResumeConflictResult(status="no_conflict", has_conflict=False)

    existing_hash = existing.get("params_hash")
    existing_ref = _manifest_ref_text(existing)
    if existing_hash and str(existing_hash) != requested_hash:
        return _conflict(
            PARAMS_HASH_CONFLICT,
            run_id=run_id,
            existing_ref=existing_ref,
            requested_ref=requested_ref,
            existing_params_hash=str(existing_hash),
            requested_params_hash=requested_hash,
            details={"existing_manifest": existing},
        )
    if requested_payload.get("manifest_ref") and existing_ref != str(requested_payload["manifest_ref"]):
        return _conflict(
            MANIFEST_REF_CONFLICT,
            run_id=run_id,
            existing_ref=existing_ref,
            requested_ref=str(requested_payload["manifest_ref"]),
            existing_params_hash=str(existing_hash) if existing_hash else None,
            requested_params_hash=requested_hash,
            details={"existing_manifest": existing},
        )
    return ResumeConflictResult(status="no_conflict", has_conflict=False)


__all__ = [
    "MANIFEST_REF_CONFLICT",
    "PARAMS_HASH_CONFLICT",
    "PARTITION_LOCK_CONFLICT",
    "PUBLISHED_ASOF_BLOCKED",
    "PUBLISHED_ASOF_NOT_PUBLISHED",
    "PUBLISHED_ASOF_READY",
    "PUBLISHED_ASOF_REF_INCOMPLETE",
    "PUBLISHED_ASOF_SNAPSHOT_MISSING",
    "REPLAY_CANDIDATE_UNPUBLISHED",
    "REPLAY_SOURCE_MISSING",
    "RESUME_CONFLICT",
    "PublishedAsOfReplayRequest",
    "PublishedAsOfReplayResult",
    "ReplayCandidate",
    "ReplayRequest",
    "ReplayResult",
    "ReplaySideEffectCheck",
    "ResumeConflict",
    "ResumeConflictResult",
    "assert_no_replay_side_effects",
    "build_published_asof_replay",
    "detect_resume_conflict",
    "run_replay_from_manifest",
]
