[CmdletBinding()]
param(
    [switch]$ExecutePipeline
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$Source = Join-Path $Root 'data\01_raw\source\online_retail_ii_uci.csv'
$ExportDir = Join-Path $Root 'deliverables\powerbi\data_model_exports'
$Validation = Join-Path $Root 'data\04_reconciliation\final_validation_report.json'
$ExpectedExports = @(
    'dim_date.csv', 'dim_product.csv', 'dim_customer.csv',
    'fact_merchandise_sales.csv', 'fact_returns_and_cancellations.csv',
    'fact_non_merch_adjustments.csv', 'fact_audit_waterfall.csv',
    'sim_inventory_sku_scenarios.csv'
)

function Fail([string]$Message) {
    Write-Error $Message
    exit 1
}

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    Fail "Python environment not found: $Python"
}
if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
    Fail "Genuine UCI source not found: $Source"
}

if ($ExecutePipeline) {
    Write-Host 'Running the documented full pipeline...'
    & $Python (Join-Path $Root 'run_pipeline.py') --mode full --skip-tests
    if ($LASTEXITCODE -ne 0) {
        Fail "Pipeline failed with exit code $LASTEXITCODE. Outputs were not accepted."
    }
} else {
    Write-Host 'Validation-only mode. No pipeline was executed.'
}

foreach ($Name in $ExpectedExports) {
    $Path = Join-Path $ExportDir $Name
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Fail "Expected Power BI export missing: $Path"
    }
}
if (-not (Test-Path -LiteralPath $Validation -PathType Leaf)) {
    Fail "Validation report missing: $Validation"
}

$ReportText = Get-Content -LiteralPath $Validation -Raw
if ($ReportText -notmatch '20112163\.17' -or $ReportText -notmatch '726611\.45') {
    Fail 'Expected merchandise and returns control totals were not found in the validation report.'
}
if ($ReportText -notmatch '"source_type"\s*:\s*"genuine_uci"' -or $ReportText -match '"fixture_mode"\s*:\s*true') {
    Fail 'Validation report is not marked as genuine UCI data with fixture_mode=false.'
}

Write-Host 'PASS: source, Python environment, eight Power BI exports, and reconciliation report are present.'
Write-Host 'Control totals found: merchandise £20,112,163.17; returns/cancellations £726,611.45.'
Write-Host 'Next step: refresh the Power BI Desktop PBIP/PBIX model.'
