$ErrorActionPreference = "Stop"

try {
    docker compose version | Out-Null
} catch {
    Write-Error "Quizbank needs Docker Desktop with Docker Compose."
    exit 2
}

$env:QUIZBANK_UID = "0"
$env:QUIZBANK_GID = "0"
docker compose run --rm quizbank @args
exit $LASTEXITCODE

