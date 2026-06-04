# One-time local setup for Presidio PII (spaCy model not installed via pip).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

& $py -m pip install -e $root
& $py -m spacy download en_core_web_sm
& $py -c "from agentic_guardrail.phase2.presidio_pii import presidio_available, scan_pii_presidio; assert presidio_available(); print('Presidio OK:', scan_pii_presidio('test@example.com').token_map)"
