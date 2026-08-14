<#
.SYNOPSIS
  Capture a Windows desktop application window to PNG.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File capture_window.ps1 -WindowTitle "Urgh" -Out .visual/t-1/after/app.png

.NOTES
  Matches on a substring of the window title. Use -List to enumerate visible windows
  when the title is unknown. Captures the window rectangle rather than the full
  screen, so the evidence does not carry the rest of the desktop with it.
#>
param(
  [string]$WindowTitle,
  [string]$Out = ".visual/capture/window.png",
  [switch]$List,
  [switch]$FullScreen
)

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@

if ($List) {
  Get-Process | Where-Object { $_.MainWindowTitle } |
    Select-Object ProcessName, MainWindowTitle, Id | Format-Table -AutoSize
  exit 0
}

$dir = Split-Path -Parent $Out
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

if ($FullScreen) {
  $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $x, $y, $w, $h = $bounds.X, $bounds.Y, $bounds.Width, $bounds.Height
} else {
  if (-not $WindowTitle) { Write-Error "Supply -WindowTitle, or use -List, or -FullScreen."; exit 1 }
  $proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*$WindowTitle*" } | Select-Object -First 1
  if (-not $proc) { Write-Error "No visible window matching '$WindowTitle'. Run with -List."; exit 1 }
  [Win]::SetForegroundWindow($proc.MainWindowHandle) | Out-Null
  Start-Sleep -Milliseconds 400
  $r = New-Object Win+RECT
  [Win]::GetWindowRect($proc.MainWindowHandle, [ref]$r) | Out-Null
  $x, $y, $w, $h = $r.L, $r.T, ($r.R - $r.L), ($r.B - $r.T)
  if ($w -le 0 -or $h -le 0) { Write-Error "Window has no drawable area (minimised?)."; exit 1 }
}

$bmp = New-Object System.Drawing.Bitmap $w, $h
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.CopyFromScreen($x, $y, 0, 0, $bmp.Size)
$bmp.Save((Resolve-Path -LiteralPath $dir).Path + "\" + (Split-Path -Leaf $Out),
          [System.Drawing.Imaging.ImageFormat]::Png)
$gfx.Dispose(); $bmp.Dispose()

Write-Output "Captured $Out ($w x $h)"
