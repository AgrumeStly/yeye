param([string]$KeilRoot = 'C:\Keil_v5', [ValidateSet('LogicDemo','HardwareBench')][string]$Target = 'LogicDemo')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $controlRoot 'firmware/yeye_control.uvprojx'
$log = Join-Path $controlRoot 'firmware/build/keil_build.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log -Parent) | Out-Null
$keilExe = Join-Path $KeilRoot 'UV4/UV4.exe'
if (-not (Test-Path -LiteralPath $keilExe)) { throw "Keil not found: $keilExe" }
$process = Start-Process -FilePath $keilExe -ArgumentList @('-b',('"'+$project+'"'),'-t',$Target,'-j0','-o',('"'+$log+'"')) -WindowStyle Hidden -PassThru -Wait
if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log }
if ($process.ExitCode -ne 0) { throw "Keil build failed or warned (exit $($process.ExitCode))." }
