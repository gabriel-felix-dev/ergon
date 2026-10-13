$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Ergon - API de testes (porta 5001)'
$backend = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $backend

$certificate = Join-Path $backend '.certificado-supabase\prod-ca-2021.crt'
if (-not (Test-Path -LiteralPath $certificate)) {
    throw "Certificado do Supabase nao encontrado: $certificate"
}

$env:DATABASE_SSL_CA_FILE = $certificate
$env:FRONTEND_ORIGIN = 'http://127.0.0.1:5174'
$env:PUBLIC_FRONTEND_URL = 'http://127.0.0.1:5174'
$env:MAIL_SERVER = '127.0.0.1'
$env:MAIL_PORT = '1025'
$env:MAIL_USE_TLS = 'false'
$env:MAIL_DEFAULT_SENDER = 'testes@ergon.local'

$secureUri = Read-Host 'Cole a URI completa do Supabase, com a senha atual' -AsSecureString
$env:DATABASE_URL = [System.Net.NetworkCredential]::new('', $secureUri).Password
$secureUri.Dispose()
if ($env:DATABASE_URL -notmatch '^postgres(ql)?://' -or $env:DATABASE_URL -match '\[YOUR-PASSWORD\]') {
    throw 'A URI do PostgreSQL nao foi informada corretamente.'
}

Write-Host 'Iniciando a API de testes em http://127.0.0.1:5001 ...'
try {
    & '.\.venv\Scripts\python.exe' -m flask --app app run --host 127.0.0.1 --port 5001
} finally {
    Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
}
