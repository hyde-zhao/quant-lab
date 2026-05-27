import json
from dataclasses import replace
from pathlib import Path

import pytest

from market_data.backup_restore import (
    ARCHIVE_ROOT_ENV,
    BACKUP_ROOT_ENV,
    LAKE_ROOT_ENV,
    RESTORE_ROOT_ENV,
    BackupRequest,
    BackupRestoreError,
    RetentionRequest,
    RestoreRequest,
    backup_plan,
    backup_report,
    backup_run,
    backup_verify,
    retention_plan,
    resolve_roots,
    restore_drill,
    restore_plan,
    restore_run,
)
from market_data.cli import main


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _fixture_lake(lake_root: Path, *, run_id: str = "run-1", dataset: str = "prices") -> dict[str, Path]:
    canonical = _write(
        lake_root / "canonical" / dataset / "1.0" / f"run_id={run_id}" / "part.txt",
        "canonical-prices\n",
    )
    raw = _write(
        lake_root / "raw" / "tushare" / "prices.daily" / "20260102" / f"run_id={run_id}" / "b1.jsonl",
        "{\"close\": 10.2}\n",
    )
    gold = _write(
        lake_root / "gold" / dataset / "1.0" / f"run_id={run_id}" / "part.txt",
        "gold-prices\n",
    )
    quality = _write(
        lake_root / "quality" / dataset / run_id / "quality.csv",
        "dataset,status\nprices,pass\n",
    )
    _write(lake_root / "catalog" / "catalog.json", json.dumps({"datasets": {dataset: {"published": True}}}))
    manifest = {
        "run_id": run_id,
        "interface": "prices.daily",
        "params": {"target_dataset": dataset},
        "raw_path": str(raw.relative_to(lake_root)),
        "canonical_path": str(canonical.relative_to(lake_root)),
    }
    _write(lake_root / "manifest" / "market_data_manifest.jsonl", json.dumps(manifest) + "\n")
    _write(lake_root / ".env", "TOKEN=should-not-be-read\n")
    _write(lake_root / "raw" / "token.txt", "secret\n")
    return {"canonical": canonical, "raw": raw, "gold": gold, "quality": quality}


def _assert_no_sensitive_output(payload: dict) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    assert "should-not-be-read" not in rendered
    assert "TOKEN" not in rendered
    assert ".env" not in rendered
    assert "token.txt" not in rendered


def test_resolve_roots_prefers_explicit_values_and_plan_is_redacted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_lake = tmp_path / "env-lake"
    env_backup = tmp_path / "env-backup"
    explicit_lake = tmp_path / "explicit-lake"
    explicit_backup = tmp_path / "explicit-backup"
    archive = tmp_path / "archive"
    restore = tmp_path / "restore"
    _fixture_lake(explicit_lake)
    monkeypatch.setenv(LAKE_ROOT_ENV, str(env_lake))
    monkeypatch.setenv(ARCHIVE_ROOT_ENV, str(archive))
    monkeypatch.setenv(BACKUP_ROOT_ENV, str(env_backup))
    monkeypatch.setenv(RESTORE_ROOT_ENV, str(restore))

    roots = resolve_roots(lake_root=explicit_lake, backup_root=explicit_backup)
    assert roots.lake_root == explicit_lake
    assert roots.backup_root == explicit_backup
    assert roots.archive_root == archive
    assert roots.restore_root == restore
    assert roots.public_labels() == {
        "lake_root": "<configured-lake-root>",
        "archive_root": "<configured-archive-root>",
        "backup_root": "<configured-backup-root>",
        "restore_root": "<configured-restore-root>",
    }

    payload = backup_plan(
        BackupRequest(
            lake_root=explicit_lake,
            backup_root=explicit_backup,
            release_id="rel-1",
            run_id="run-1",
            dataset="prices",
            include_gold=False,
        )
    )

    assert payload["ok"] is True
    assert payload["dry_run"] is True
    assert payload["summary"]["file_count"] == 5
    assert {item["relative_path"] for item in payload["files"]} == {
        "raw/tushare/prices.daily/20260102/run_id=run-1/b1.jsonl",
        "manifest/market_data_manifest.jsonl",
        "canonical/prices/1.0/run_id=run-1/part.txt",
        "quality/prices/run-1/quality.csv",
        "catalog/catalog.json",
    }
    assert not explicit_backup.exists()
    assert str(explicit_lake) not in json.dumps(payload, ensure_ascii=False)
    assert str(explicit_backup) not in json.dumps(payload, ensure_ascii=False)
    _assert_no_sensitive_output(payload)


def test_backup_run_defaults_to_dry_run_then_execute_and_skip_same_checksum(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    backup = tmp_path / "backup"
    files = _fixture_lake(lake)
    request = BackupRequest(lake_root=lake, backup_root=backup, release_id="rel-1", run_id="run-1", dataset="prices")

    dry_run = backup_run(request)
    assert dry_run["dry_run"] is True
    assert dry_run["summary"]["actions"] == {"would_copy": 6}
    assert not (backup / "rel-1").exists()

    executed = backup_run(replace(request, execute=True))
    assert executed["execute"] is True
    assert executed["summary"]["actions"] == {"copied": 6}
    copied = backup / "rel-1" / "files" / files["canonical"].relative_to(lake)
    assert copied.read_text(encoding="utf-8") == "canonical-prices\n"

    rerun = backup_run(replace(request, execute=True))
    assert rerun["summary"]["actions"] == {"skip": 6}
    assert rerun["summary"]["checksum_status"] == {"same": 6}


def test_backup_run_checksum_mismatch_fails_without_overwrite(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    backup = tmp_path / "backup"
    files = _fixture_lake(lake)
    target = backup / "rel-1" / "files" / files["canonical"].relative_to(lake)
    _write(target, "different-existing-content\n")

    with pytest.raises(BackupRestoreError) as exc:
        backup_run(
            BackupRequest(
                lake_root=lake,
                backup_root=backup,
                release_id="rel-1",
                run_id="run-1",
                dataset="prices",
                execute=True,
            )
        )

    assert exc.value.code == "checksum_mismatch"
    assert exc.value.details == {"relative_paths": ["canonical/prices/1.0/run_id=run-1/part.txt"]}
    assert target.read_text(encoding="utf-8") == "different-existing-content\n"


def test_backup_verify_reports_missing_and_mismatch_without_overwrite(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    backup = tmp_path / "backup"
    files = _fixture_lake(lake)
    request = BackupRequest(lake_root=lake, backup_root=backup, release_id="rel-1", run_id="run-1", dataset="prices")
    backup_run(replace(request, execute=True))
    canonical_target = backup / "rel-1" / "files" / files["canonical"].relative_to(lake)
    canonical_target.write_text("corrupted\n", encoding="utf-8")

    verified = backup_verify(request)
    assert verified["ok"] is False
    assert verified["summary"]["checksum_status"]["mismatch"] == 1
    assert canonical_target.read_text(encoding="utf-8") == "corrupted\n"

    report = backup_report(BackupRequest(backup_root=backup, release_id="rel-1", run_id="run-1", dataset="prices"))
    assert report["ok"] is True
    assert report["summary"]["file_count"] == 6
    assert report["summary"]["checksum_status"] == {"computed": 6}
    _assert_no_sensitive_output(report)


def test_restore_plan_rejects_lake_root_and_restore_root_collision(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    backup = tmp_path / "backup"
    _fixture_lake(lake)
    backup_run(
        BackupRequest(
            lake_root=lake,
            backup_root=backup,
            release_id="rel-1",
            run_id="run-1",
            dataset="prices",
            execute=True,
        )
    )

    with pytest.raises(BackupRestoreError) as exc:
        restore_plan(
            RestoreRequest(
                lake_root=lake,
                backup_root=backup,
                restore_root=lake,
                release_id="rel-1",
                run_id="run-1",
                dataset="prices",
            )
        )

    assert exc.value.code == "restore_root_conflict"
    assert exc.value.details == {
        "lake_root": "<configured-lake-root>",
        "restore_root": "<configured-restore-root>",
    }


def test_restore_run_execute_restores_to_separate_root_and_skips_same(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    backup = tmp_path / "backup"
    restore = tmp_path / "restore"
    files = _fixture_lake(lake)
    backup_run(
        BackupRequest(
            lake_root=lake,
            backup_root=backup,
            release_id="rel-1",
            run_id="run-1",
            dataset="prices",
            execute=True,
        )
    )
    request = RestoreRequest(
        lake_root=lake,
        backup_root=backup,
        restore_root=restore,
        release_id="rel-1",
        run_id="run-1",
        dataset="prices",
        execute=True,
    )

    restored = restore_run(request)
    assert restored["summary"]["actions"] == {"restored": 6}
    restored_canonical = restore / files["canonical"].relative_to(lake)
    assert restored_canonical.read_text(encoding="utf-8") == "canonical-prices\n"

    rerun = restore_run(request)
    assert rerun["summary"]["actions"] == {"skip": 6}
    assert rerun["summary"]["checksum_status"] == {"same": 6}


def test_restore_drill_uses_temporary_root_and_returns_offline_segments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lake = tmp_path / "lake"
    backup = tmp_path / "backup"
    configured_restore = tmp_path / "configured-restore"
    _fixture_lake(lake)
    monkeypatch.setenv(RESTORE_ROOT_ENV, str(configured_restore))
    backup_run(
        BackupRequest(
            lake_root=lake,
            backup_root=backup,
            release_id="rel-1",
            run_id="run-1",
            dataset="prices",
            execute=True,
        )
    )

    drilled = restore_drill(
        RestoreRequest(
            lake_root=lake,
            backup_root=backup,
            release_id="rel-1",
            run_id="run-1",
            dataset="prices",
        )
    )

    assert drilled["ok"] is True
    assert drilled["read"]["status"] == "available"
    assert drilled["revalidate"]["status"] == "pass"
    assert drilled["replay"] == {
        "status": "offline_planned",
        "network_calls": 0,
        "auto_execute": False,
        "root_label": "<configured-restore-root>",
    }
    assert drilled["summary"]["network_calls"] == 0
    assert drilled["summary"]["auto_execute"] is False
    assert not configured_restore.exists()
    _assert_no_sensitive_output(drilled)


def test_retention_plan_protects_published_failed_and_candidate_runs(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    _fixture_lake(lake, run_id="run-1", dataset="prices")
    manifest_path = lake / "manifest" / "market_data_manifest.jsonl"
    manifest_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "run_id": "run-1",
                        "status": "success",
                        "interface": "prices.daily",
                        "params": {"target_dataset": "prices"},
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "run_id": "run-failed",
                        "status": "failed",
                        "interface": "prices.daily",
                        "params": {"target_dataset": "prices"},
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    catalog = {
        "schema_version": "1.0",
        "datasets": {
            "prices": {
                "dataset": "prices",
                "published": True,
                "latest_manifest_run_id": "run-1",
            },
            "events": {
                "dataset": "events",
                "published": False,
                "latest_manifest_run_id": "run-candidate",
            },
        },
    }
    (lake / "catalog" / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    payload = retention_plan(RetentionRequest(lake_root=lake))
    decisions = {row["decision"] for row in payload["rows"]}

    assert payload["ok"] is True
    assert payload["summary"]["protected_count"] == len(payload["rows"])
    assert {
        "protect_published_run",
        "retain_candidate_run",
        "retain_failed_or_candidate_run",
        "requires_backup_verify_before_cleanup",
    } <= decisions
    _assert_no_sensitive_output(payload)

    with pytest.raises(BackupRestoreError) as exc:
        retention_plan(RetentionRequest(lake_root=lake, execute=True))

    assert exc.value.code == "retention_protected_run"


def test_cli_backup_restore_commands_accept_uv_template_flags_and_keep_output_redacted(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lake = tmp_path / "lake"
    backup = tmp_path / "backup"
    restore = tmp_path / "restore"
    _fixture_lake(lake)
    monkeypatch.setenv(LAKE_ROOT_ENV, str(lake))
    monkeypatch.setenv(BACKUP_ROOT_ENV, str(backup))
    monkeypatch.setenv(RESTORE_ROOT_ENV, str(restore))

    assert main(["backup-plan", "--release-id", "rel-cli", "--json"]) == 0
    plan_payload = json.loads(capsys.readouterr().out)
    assert plan_payload["command"] == "backup-plan"
    assert plan_payload["roots"]["lake_root"] == "<configured-lake-root>"
    assert str(lake) not in json.dumps(plan_payload, ensure_ascii=False)

    assert main(["backup-run", "--release-id", "rel-cli", "--execute", "--json"]) == 0
    run_payload = json.loads(capsys.readouterr().out)
    assert run_payload["execute"] is True
    assert run_payload["summary"]["actions"] == {"copied": 6}

    assert main(["restore-drill", "--release-id", "rel-cli", "--execute", "--json"]) == 0
    drill_payload = json.loads(capsys.readouterr().out)
    assert drill_payload["command"] == "restore-drill"
    assert drill_payload["replay"]["network_calls"] == 0
    assert drill_payload["replay"]["auto_execute"] is False
    assert str(lake) not in json.dumps(drill_payload, ensure_ascii=False)
    assert str(backup) not in json.dumps(drill_payload, ensure_ascii=False)
    assert str(restore) not in json.dumps(drill_payload, ensure_ascii=False)


def test_cli_restore_root_collision_returns_structured_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    lake = tmp_path / "lake"
    backup = tmp_path / "backup"
    _fixture_lake(lake)
    backup_run(BackupRequest(lake_root=lake, backup_root=backup, release_id="rel-1", execute=True))

    code = main(
        [
            "restore-plan",
            "--lake-root",
            str(lake),
            "--backup-root",
            str(backup),
            "--restore-root",
            str(lake),
            "--release-id",
            "rel-1",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert code == 2
    assert payload["error_type"] == "restore_root_conflict"
    assert str(lake) not in captured.err
