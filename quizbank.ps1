$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot
$CallerDir = (Get-Location).Path
$BankPath = $null
$OutputPath = $null

for ($i = 0; $i -lt $args.Count; $i++) {
    $arg = [string]$args[$i]
    if ($arg -eq "--bank" -and $i + 1 -lt $args.Count) {
        $BankPath = [string]$args[$i + 1]
        $i++
        continue
    }
    if ($arg.StartsWith("--bank=")) {
        $BankPath = $arg.Substring(7)
        continue
    }
    if ($arg -eq "--output-dir" -and $i + 1 -lt $args.Count) {
        $OutputPath = [string]$args[$i + 1]
        $i++
        continue
    }
    if ($arg.StartsWith("--output-dir=")) {
        $OutputPath = $arg.Substring(13)
        continue
    }
}

if ($BankPath) {
    if ([System.IO.Path]::IsPathRooted($BankPath)) {
        $BankFull = [System.IO.Path]::GetFullPath($BankPath)
    } else {
        $BankFull = [System.IO.Path]::GetFullPath((Join-Path $CallerDir $BankPath))
    }
    if (-not (Test-Path -LiteralPath $BankFull -PathType Leaf)) {
        Write-Error "Quizbank bank file not found: $BankFull"
        exit 2
    }
    $env:QUIZBANK_BANK_DIR = Split-Path -Parent $BankFull
    $env:QUIZBANK_EXTERNAL_BANK = "/quizbank-bank/$(Split-Path -Leaf $BankFull)"
}

if ($OutputPath) {
    if ([System.IO.Path]::IsPathRooted($OutputPath)) {
        $OutputFull = [System.IO.Path]::GetFullPath($OutputPath)
    } else {
        $OutputFull = [System.IO.Path]::GetFullPath((Join-Path $CallerDir $OutputPath))
    }
    $OutputParent = Split-Path -Parent $OutputFull
    if (-not (Test-Path -LiteralPath $OutputParent -PathType Container)) {
        Write-Error "Quizbank output parent directory not found: $OutputParent"
        exit 2
    }
    $env:QUIZBANK_OUTPUT_DIR = $OutputParent
    $env:QUIZBANK_EXTERNAL_OUTPUT = "/quizbank-output/$(Split-Path -Leaf $OutputFull)"
}

try {
    docker compose version | Out-Null
} catch {
    Write-Error "Quizbank needs Docker Desktop with Docker Compose."
    exit 2
}

$env:QUIZBANK_UID = "0"
$env:QUIZBANK_GID = "0"
docker compose --project-directory $ScriptDir -f (Join-Path $ScriptDir "compose.yaml") run --rm quizbank @args
exit $LASTEXITCODE
