"""Shared gate and admission status primitives.

The existing admission modules keep their domain-specific dataclasses, but use
these stable values to avoid inventing new status spellings.
"""

from __future__ import annotations

from enum import Enum


class GateStatus(str, Enum):
    PASS = "pass"
    BLOCKED = "blocked"
    NOT_EVALUATED = "not_evaluated"
    RESEARCH_LIMITED = "research_limited"
    WARN = "warn"
    FAIL = "fail"


class AdmissionStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    BLOCKED = "blocked"

