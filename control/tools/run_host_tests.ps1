param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$outputRoot = Join-Path $controlRoot 'build'
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
$program = Join-Path $outputRoot 'test_control.exe'
& $Compiler -std=c99 -Wall -Wextra -Wconversion -Werror -pedantic -I (Join-Path $controlRoot 'Core/Inc') -I (Join-Path $controlRoot 'App/Car') -I (Join-Path $controlRoot 'App/Diagnostics') -I (Join-Path $controlRoot 'Drivers_Custom/Board') -I (Join-Path $controlRoot 'Drivers_Custom/Motor') -I (Join-Path $controlRoot 'Drivers_Custom/Communication') (Join-Path $controlRoot 'Drivers_Custom/Communication/protocol.c') (Join-Path $controlRoot 'App/Car/car.c') (Join-Path $controlRoot 'Tests/Host/test_control.c') -o $program
if ($LASTEXITCODE -ne 0) { throw 'Host compilation failed.' }
& $program | Tee-Object -FilePath (Join-Path $outputRoot 'host_tests.log')
if ($LASTEXITCODE -ne 0) { throw 'Host tests failed.' }
