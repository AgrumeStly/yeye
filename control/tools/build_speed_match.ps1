param([string]$KeilRoot = 'D:\software\Keil5')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $controlRoot 'MDK-ARM/speed_match.uvprojx'
$log = Join-Path $controlRoot 'build/firmware/SpeedMatch_build.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log -Parent) | Out-Null
# 只构建独立目标、导出BIN，不下载、不访问DAPLink。
# -j0为Keil无界面批处理；管道等待GUI子系统程序结束。
# 本机PowerShell可能不给UV4返回LASTEXITCODE，使用独立新日志核实本次结果。
$runLog = Join-Path $controlRoot ('build/firmware/SpeedMatch_' + [guid]::NewGuid().ToString('N') + '.log')
& (Join-Path $KeilRoot 'UV4/UV4.exe') -b $project -t SpeedMatch -j0 -o $runLog | Out-Null
if (-not (Test-Path -LiteralPath $runLog)) { throw 'Keil did not create a fresh build log.' }
$buildText = Get-Content -LiteralPath $runLog -Raw
$buildText
Copy-Item -LiteralPath $runLog -Destination $log
if ($buildText -notmatch '0 Error\(s\), 0 Warning\(s\)\.') { throw 'SpeedMatch build failed or warned.' }
$output = Join-Path $controlRoot 'build/firmware/speed_match/speed_match'
& (Join-Path $KeilRoot 'ARM/ARMCC/bin/fromelf.exe') --bin --output ($output + '.bin') ($output + '.axf')
if ($LASTEXITCODE -ne 0) { throw 'SpeedMatch BIN export failed.' }
Get-FileHash -Algorithm SHA256 -LiteralPath ($output + '.bin')
