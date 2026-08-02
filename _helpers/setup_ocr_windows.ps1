# Instala dependencias OCR para garciabermeo.net en Windows (ejecutar como administrador si falla).
# Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# Poppler:  https://github.com/oschwartz10612/poppler-windows/releases

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "=== Dependencias OCR para garciabermeo.net ===" -ForegroundColor Cyan

function Test-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# Tesseract via winget
if (Test-Command tesseract) {
    Write-Host "[OK] Tesseract:" (tesseract --version 2>&1 | Select-Object -First 1)
} else {
    Write-Host "[..] Instalando Tesseract con winget..."
    winget install --id UB-Mannheim.TesseractOCR -e --accept-source-agreements --accept-package-agreements
}

# Poppler via winget (si está disponible) o instrucción manual
if (Test-Command pdftoppm) {
    Write-Host "[OK] Poppler:" (Get-Command pdftoppm).Source
} else {
    Write-Host "[!!] Poppler no detectado en PATH." -ForegroundColor Yellow
    Write-Host "     Descargue poppler-windows, extraiga y defina POPPLER_PATH apuntando a la carpeta bin."
    Write-Host "     Ejemplo: `$env:POPPLER_PATH = 'C:\poppler\Library\bin'"
}

Write-Host ""
Write-Host "Verificación Python:" -ForegroundColor Cyan
Set-Location $Root
python -c "from legal_ui.system_deps import check_ocr_dependencies; [print(f'{s.name}:', s.detail) for s in check_ocr_dependencies()]"

Write-Host ""
Write-Host "Reinicie la terminal tras instalar para actualizar PATH." -ForegroundColor Green
