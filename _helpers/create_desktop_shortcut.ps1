# Crea acceso directo en el Escritorio para garciabermeo.net
$AppRoot = Split-Path $PSScriptRoot -Parent
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "garciabermeo.net.lnk"
$Launcher = Join-Path $AppRoot "iniciar_garciabermeo.bat"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Launcher
$Shortcut.WorkingDirectory = $AppRoot
$Shortcut.WindowStyle = 1
$Shortcut.Description = "Iniciar garciabermeo.net - Gestion de expedientes judiciales"
$Shortcut.Save()

Write-Host "Acceso directo creado: $ShortcutPath"
