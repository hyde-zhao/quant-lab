[CmdletBinding()]
param(
    [ValidateSet("DryRunPreflight", "RuntimeReadonly")]
    [string]$Mode = "DryRunPreflight",
    [string]$EvidenceRoot = ".quant-lab\evidence\qmt\runtime-validation\redacted",
    [string]$AuthorizationRef = "dry-run-preflight-not-runtime-authorization",
    [string]$BaseUrl = "http://127.0.0.1:8182",
    [string]$OutputJson = ""
)

$ErrorActionPreference = "Stop"

function New-RunId {
    return "runtime-validation-" + (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
}

$RunId = New-RunId
$EvidenceDir = Join-Path $EvidenceRoot $RunId
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

if ($Mode -eq "DryRunPreflight") {
    $EvidencePath = if ([string]::IsNullOrWhiteSpace($OutputJson)) {
        Join-Path $EvidenceDir "dry-run-preflight-evidence.json"
    } else {
        $OutputJson
    }
    & uv run --python 3.11 python scripts/qmt/build_runtime_preflight_evidence.py `
        --run-id $RunId `
        --authorization-ref $AuthorizationRef `
        --output-json $EvidencePath `
        --reason-code "missing_runtime_authorization"
    & uv run --python 3.11 python scripts/quality/check_redacted_evidence.py --evidence $EvidencePath --json
    exit $LASTEXITCODE
}

if ([string]::IsNullOrWhiteSpace($AuthorizationRef) -or $AuthorizationRef -eq "dry-run-preflight-not-runtime-authorization") {
    Write-Output "reason=missing_explicit_runtime_authorization"
    Write-Output "required_ack=IApproveRuntimeReadonlyAuthorization"
    exit 2
}

$RuntimeEvidencePath = if ([string]::IsNullOrWhiteSpace($OutputJson)) {
    Join-Path $EvidenceDir "readonly-runtime-evidence.json"
} else {
    $OutputJson
}
& uv run --python 3.11 python scripts/qmt/collect_readonly_smoke_evidence.py `
    --base-url $BaseUrl `
    --authorization-ref $AuthorizationRef `
    --run-id $RunId `
    --output-json $RuntimeEvidencePath
exit $LASTEXITCODE
