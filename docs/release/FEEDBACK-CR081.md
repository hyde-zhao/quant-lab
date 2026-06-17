# CR081 Feedback

## Observation Signals

| Signal | Threshold | Action |
|---|---|---|
| `process/STATE.md` not readable | Any failure | Run bootstrap or rollback. |
| CR tracking consistency fails | Any failure | Inspect symlink and external process project. |
| Git status is unexpectedly clean for process removals | Before commit decision | Recheck `git rm --cached` outcome. |
| External process unavailable | Any normal workflow use | Restore symlink target or rollback from backup. |

## Follow-up Candidates

| Candidate | Status | Notes |
|---|---|---|
| CR078 remote Git governance | candidate | Decide whether and how to publish current repository boundary. |
| CR077 old root retirement | candidate | Only after rollback confidence is sufficient. |
| docs externalization CR | optional candidate | Only if process-style `docs/*` should also move outside the business repo. |
