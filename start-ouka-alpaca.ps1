# Démarre le serveur Alpaca Ouka au démarrage Windows.
# Installation : copier ce script et créer une tâche planifiée
# "Au démarrage" pointant vers ce fichier, ou l'ajouter au dossier Startup.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$AppScript = Join-Path $ScriptDir "app.py"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Création de l'environnement virtuel..."
    python -m venv .venv
    & (Join-Path $ScriptDir ".venv\Scripts\pip.exe") install -r requirements.txt
}

Write-Host "Démarrage du serveur Alpaca Ouka..."
& $VenvPython $AppScript
