[CmdletBinding()]
param(
    [ValidateSet("DryRunPreflight", "ReadonlyRuntime")]
    [string]$Mode = "DryRunPreflight",

    [string]$RunId = "",
    [string]$EvidenceRoot = ".quant-lab\evidence\qmt\cr104\redacted",
    [string]$AuthorizationRef = "cr104-dry-run-preflight-not-runtime-authorization",

    [string]$EnvFile = "",
    [string]$BaseUrl = "",
    [string]$HostName = "",
    [int]$Port = 0,
    [int]$TimeoutSeconds = 10,

    [switch]$IApproveCR104CP2RuntimeAuthorization,
    [switch]$SkipChecker
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $RepoRoot

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = "cr104-" + (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
}

$EvidenceDir = Join-Path $RepoRoot (Join-Path $EvidenceRoot $RunId)
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Invoke-Cr104Checker {
    param([string]$EvidencePath)

    if ($SkipChecker) {
        Write-Output "checker_status=SKIPPED"
        return
    }

    & uv run --python 3.11 python scripts/quality/check_redacted_evidence.py --evidence $EvidencePath --json
    if ($LASTEXITCODE -ne 0) {
        throw "redacted evidence checker failed: exit_code=$LASTEXITCODE"
    }
}

if ($Mode -eq "DryRunPreflight") {
    $EvidencePath = Join-Path $EvidenceDir "cr104-dry-run-preflight-evidence.json"

    & uv run --python 3.11 python scripts/qmt/build_runtime_preflight_evidence.py `
        --run-id $RunId `
        --authorization-ref $AuthorizationRef `
        --output-json $EvidencePath
    if ($LASTEXITCODE -ne 0) {
        throw "preflight evidence builder failed: exit_code=$LASTEXITCODE"
    }

    Invoke-Cr104Checker -EvidencePath $EvidencePath

    Write-Output "cr_id=CR-104"
    Write-Output "mode=DryRunPreflight"
    Write-Output "runtime_started=false"
    Write-Output "env_or_credential_read=false"
    Write-Output "account_or_position_raw_read=false"
    Write-Output "order_or_trade_action=false"
    Write-Output "evidence_path=$EvidencePath"
    Write-Output "run_id=$RunId"
    exit 0
}

if (-not $IApproveCR104CP2RuntimeAuthorization) {
    Write-Output "cr_id=CR-104"
    Write-Output "mode=ReadonlyRuntime"
    Write-Output "runtime_status=BLOCKED"
    Write-Output "reason=missing_explicit_cr104_cp2_runtime_authorization"
    Write-Output "next_action=prepare_and_approve_CR104_CP2_runtime_authorization"
    exit 20
}

if ([string]::IsNullOrWhiteSpace($EnvFile)) {
    throw "EnvFile is required only after explicit CR104 CP2 runtime authorization."
}

if ([string]::IsNullOrWhiteSpace($AuthorizationRef) -or $AuthorizationRef -eq "cr104-dry-run-preflight-not-runtime-authorization") {
    throw "AuthorizationRef must be a concrete CR104 CP2 approval reference for ReadonlyRuntime mode."
}

$RuntimeEvidencePath = Join-Path $EvidenceDir "cr104-readonly-runtime-evidence.json"
$CollectorArgs = @(
    "run", "--python", "3.11", "python", "scripts/qmt/collect_readonly_smoke_evidence.py",
    "--env-file", $EnvFile,
    "--authorization-ref", $AuthorizationRef,
    "--run-id", $RunId,
    "--timeout-seconds", [string]$TimeoutSeconds,
    "--output-json", $RuntimeEvidencePath
)

if (-not [string]::IsNullOrWhiteSpace($BaseUrl)) {
    $CollectorArgs += @("--base-url", $BaseUrl)
}
if (-not [string]::IsNullOrWhiteSpace($HostName)) {
    $CollectorArgs += @("--host", $HostName)
}
if ($Port -gt 0) {
    $CollectorArgs += @("--port", [string]$Port)
}

& uv @CollectorArgs
if ($LASTEXITCODE -ne 0) {
    throw "readonly runtime collector failed: exit_code=$LASTEXITCODE"
}

Invoke-Cr104Checker -EvidencePath $RuntimeEvidencePath

Write-Output "cr_id=CR-104"
Write-Output "mode=ReadonlyRuntime"
Write-Output "runtime_scope=health,capabilities,query_positions_readonly"
Write-Output "order_or_trade_action=false"
Write-Output "evidence_path=$RuntimeEvidencePath"
Write-Output "run_id=$RunId"
