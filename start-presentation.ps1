param([int]$Port = 8002)

$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv-nlp\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) {
    throw 'Create .venv-nlp and install the NLP dependencies and spaCy model as described in the README.'
}

$localDemo = Join-Path $env:LOCALAPPDATA 'TextDetective/Presentation'
$env:STORAGE_DIR = Join-Path $localDemo 'storage'
$env:DATA_DIR = Join-Path $localDemo 'data'
$env:LLM_PROVIDER = 'mock'
$env:MODEL_ASSISTED_ANALYSIS = 'false'
$env:DEMO_MODE = 'true'
$env:SPACY_MODEL = 'en_core_web_sm'
$env:USE_FAISS = 'true'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:OMP_NUM_THREADS = '2'
$env:MKL_NUM_THREADS = '2'

Push-Location $PSScriptRoot
try {
    & $python -m uvicorn backend.app.main:app --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw "Text Detective exited with code $LASTEXITCODE." }
} finally {
    Pop-Location
}
