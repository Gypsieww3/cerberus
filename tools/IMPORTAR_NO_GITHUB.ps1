param([string]$Repo = "https://github.com/Gypsieww3/cerberus.git")
$ErrorActionPreference = "Stop"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Instale Git for Windows antes de importar." }
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dest = Join-Path $root "_GITHUB_CERBERUS"
if (-not (Test-Path (Join-Path $dest ".git"))) {
  git clone $Repo $dest
  if ($LASTEXITCODE -ne 0) { throw "Nao foi possivel clonar o GitHub" }
}
foreach ($folder in @("01_MOSS_KYVRAEL","02_ARKHE","03_CERBERUS_CORE","05_TRADING","07_ROBOTICA","08_PROMETHEUS","09_HARDWARE")) {
  $from = Join-Path $root $folder
  $to = Join-Path $dest $folder
  if (-not (Test-Path $from)) { continue }
  if (-not (Test-Path $to)) { New-Item -ItemType Directory -Path $to | Out-Null }
  Copy-Item -Path (Join-Path $from "*") -Destination $to -Recurse -Force
}
Push-Location $dest
try {
  git status --short
  Write-Host "AVISO: o repositorio e PUBLICO. Verifique ficheiros confidenciais e a propriedade intelectual."
  if ((Read-Host "Publicar os ficheiros acima no GitHub? Escreva SIM para confirmar") -ne "SIM") {
    Write-Host "Nao publicado. Copias preparadas em $dest"
    exit 0
  }
  git add 01_MOSS_KYVRAEL 02_ARKHE 03_CERBERUS_CORE 05_TRADING 07_ROBOTICA 08_PROMETHEUS 09_HARDWARE
  git diff --cached --check
  if ($LASTEXITCODE -ne 0) { throw "Diferenças invalidas" }
  git commit -m "Import independent CERBERUS projects"
  if ($LASTEXITCODE -ne 0) { throw "Falha no commit" }
  git push origin main
  if ($LASTEXITCODE -ne 0) { throw "Falha no push, verifique a autenticação GitHub" }
  Write-Host "Concluido."
} finally { Pop-Location }
