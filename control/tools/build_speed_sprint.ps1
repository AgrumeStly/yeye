param([string]$KeilRoot = 'D:\software\Keil5')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $controlRoot 'MDK-ARM/speed_sprint.uvprojx'
$log = Join-Path $controlRoot 'build/firmware/SpeedSprint_build.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log -Parent) | Out-Null
# 只构建独立目标、导出BIN，不下载、不访问DAPLink。
# -j0为Keil无界面批处理；管道等待GUI子系统程序结束。
# 本机PowerShell可能不给UV4返回LASTEXITCODE，使用独立新日志核实本次结果。
$runLog = Join-Path $controlRoot ('build/firmware/SpeedSprint_' + [guid]::NewGuid().ToString('N') + '.log')
& (Join-Path $KeilRoot 'UV4/UV4.exe') -b $project -t SpeedSprint -j0 -o $runLog | Out-Null
if (-not (Test-Path -LiteralPath $runLog)) { throw 'Keil did not create a fresh build log.' }
$buildText = Get-Content -LiteralPath $runLog -Raw
$buildText
Copy-Item -LiteralPath $runLog -Destination $log
if ($buildText -notmatch '0 Error\(s\), 0 Warning\(s\)\.') { throw 'SpeedSprint build failed or warned.' }
$output = Join-Path $controlRoot 'build/firmware/speed_sprint/speed_sprint'
& (Join-Path $KeilRoot 'ARM/ARMCC/bin/fromelf.exe') --bin --output ($output + '.bin') ($output + '.axf')
if ($LASTEXITCODE -ne 0) { throw 'SpeedSprint BIN export failed.' }
Get-FileHash -Algorithm SHA256 -LiteralPath ($output + '.bin')
