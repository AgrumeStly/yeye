param([string]$KeilRoot = 'C:\Keil_v5')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $controlRoot 'MDK-ARM/encoder_bench.uvprojx'
$log = Join-Path $controlRoot 'build/firmware/EncoderBench_build.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log -Parent) | Out-Null
# 只编译独立工程和导出BIN，不枚举DAPLink、不下载、不访问板卡。
$process = Start-Process -FilePath (Join-Path $KeilRoot 'UV4/UV4.exe') -ArgumentList @('-b',('"'+$project+'"'),'-t','EncoderBench','-j0','-o',('"'+$log+'"')) -WindowStyle Hidden -PassThru -Wait
Get-Content -LiteralPath $log
if ($process.ExitCode -ne 0) { throw ('EncoderBench build failed or warned: ' + $process.ExitCode) }
$output = Join-Path $controlRoot 'build/firmware/encoder_bench/encoder_bench'
& (Join-Path $KeilRoot 'ARM/ARMCC/bin/fromelf.exe') --bin --output ($output + '.bin') ($output + '.axf')
if ($LASTEXITCODE -ne 0) { throw 'EncoderBench BIN export failed.' }
Get-FileHash -Algorithm SHA256 -LiteralPath ($output + '.bin')
