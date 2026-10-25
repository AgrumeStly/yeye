param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$outputRoot = Join-Path $controlRoot 'build'
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
$program = Join-Path $outputRoot 'test_motor_bench.exe'
& $Compiler -std=c99 -Wall -Wextra -Wconversion -Werror -pedantic -I (Join-Path $controlRoot 'Core/Inc') -I (Join-Path $controlRoot 'App/Car') -I (Join-Path $controlRoot 'App/Diagnostics') -I (Join-Path $controlRoot 'Drivers_Custom/Board') -I (Join-Path $controlRoot 'Drivers_Custom/Motor') -I (Join-Path $controlRoot 'Drivers_Custom/Communication') (Join-Path $controlRoot 'App/Diagnostics/motor_bench.c') (Join-Path $controlRoot 'Tests/Host/test_motor_bench.c') -o $program
if ($LASTEXITCODE -ne 0) { throw 'Motor bench host compilation failed.' }
& $program | Tee-Object -FilePath (Join-Path $outputRoot 'motor_bench_tests.log')
if ($LASTEXITCODE -ne 0) { throw 'Motor bench host tests failed.' }
