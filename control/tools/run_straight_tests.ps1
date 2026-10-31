param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$outputRoot = Join-Path $controlRoot 'build'
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
foreach ($case in @('test','integration')) {
    $output = Join-Path $outputRoot ('test_straight_' + $case + '.exe')
    & $Compiler -std=c99 -Wall -Wextra -Wconversion -Werror -pedantic -I (Join-Path $controlRoot 'Tests/Host/fakes/motor_bench_pwm') -I (Join-Path $controlRoot 'App/Diagnostics') -I (Join-Path $controlRoot 'Drivers_Custom/Motor') (Join-Path $controlRoot 'App/Diagnostics/straight_test.c') (Join-Path $controlRoot ('Tests/Host/test_straight_' + $case + '.c')) -o $output
    if ($LASTEXITCODE -ne 0) { throw ('StraightTest compile failed: ' + $case) }
    & $output | Tee-Object -FilePath (Join-Path $outputRoot ('straight_' + $case + '_tests.log'))
    if ($LASTEXITCODE -ne 0) { throw ('StraightTest tests failed: ' + $case) }
}
