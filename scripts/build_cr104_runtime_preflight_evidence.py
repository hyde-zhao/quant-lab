from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Sequence


FORBIDDEN_COUNTERS = {
    "account_id_values": 0,
    "security_code_values": 0,
    "raw_quantity_values": 0,
    "raw_cash_values": 0,
    "order_fields": 0,
    "fill_fields": 0,
    "submit_cancel_calls": 0,
    "buy_sell_calls": 0,
    "nas_operations": 0,
    "provider_lake_publish": 0,
}


def build_preflight_evidence(
    *,
    run_id: str,
    authorization_ref: str,
    generated_at: str,
    reason_code: str,
) -> dict[str, object]:
    digest = hashlib.sha256(f"{run_id}|{authorization_ref}|{reason_code}".encode("utf-8")).hexdigest()
    endpoint_block = {
        "attempted": True,
        "status": "blocked",
        "reason_code": reason_code,
        "raw_payload_emitted": False,
    }
    return {
        "schema_version": 1,
        "cr_id": "CR-099",
        "run_id": run_id,
        "authorization_ref": authorization_ref,
        "generated_at": generated_at,
        "execution_mode": "blocked-preflight",
        "endpoints": {
            "health": dict(endpoint_block),
            "capabilities": {
                **endpoint_block,
                "readonly_supported": False,
            },
            "query_positions_readonly": {
                **endpoint_block,
                "position_count_bucket": "unknown",
                "positions_digest": f"sha256:{digest}",
                "items_redacted_count": 0,
            },
        },
        "forbidden_counters": dict(FORBIDDEN_COUNTERS),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    generated_at = args.generated_at or datetime.now(tz=timezone.utc).isoformat()
    evidence = build_preflight_evidence(
        run_id=args.run_id,
        authorization_ref=args.authorization_ref,
        generated_at=generated_at,
        reason_code=args.reason_code,
    )
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "output_json": str(output_path)}, ensure_ascii=False, sort_keys=True))
    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build CR104 blocked-preflight redacted evidence without runtime access.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--authorization-ref", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--generated-at", default="")
    parser.add_argument("--reason-code", default="missing_runtime_authorization")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
