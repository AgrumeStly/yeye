param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$outputRoot = Join-Path $controlRoot 'build'
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
# 同一真实入口及PWM实现，显式开启持续目标宏；测试替身只供电脑，不加入Keil。
foreach ($case in @(
    @{ Name = 'motor_continuous'; Source = 'test_motor_bench_pwm_diag.c'; Fake = 'motor_bench_pwm' },
    @{ Name = 'motor_continuous_startup'; Source = 'test_motor_bench_startup.c'; Fake = 'motor_bench_startup' }
)) {
    $program = Join-Path $outputRoot ($case.Name + '.exe')
    & $Compiler -std=c99 -Wall -Wextra -Wconversion -Werror -pedantic -DMOTOR_CONTINUOUS_A_TARGET=1 -I (Join-Path $controlRoot ('Tests/Host/fakes/' + $case.Fake)) -I (Join-Path $controlRoot 'Core/Inc') -I (Join-Path $controlRoot 'App/Car') -I (Join-Path $controlRoot 'App/Diagnostics') -I (Join-Path $controlRoot 'Drivers_Custom/Board') -I (Join-Path $controlRoot 'Drivers_Custom/Motor') -I (Join-Path $controlRoot 'Drivers_Custom/Communication') (Join-Path $controlRoot 'App/Diagnostics/motor_bench.c') (Join-Path $controlRoot ('Tests/Host/' + $case.Source)) -o $program
    if ($LASTEXITCODE -ne 0) { throw ('Continuous test compilation failed: ' + $case.Name) }
    & $program 2>&1 | Tee-Object -FilePath (Join-Path $outputRoot ($case.Name + '_tests.log'))
    if ($LASTEXITCODE -ne 0) { throw ('Continuous test failed: ' + $case.Name) }
}
