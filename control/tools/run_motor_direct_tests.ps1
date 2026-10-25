param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$outputRoot = Join-Path $controlRoot 'build'
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
# 真实GPIO适配器／入口／状态机与R1故障场景，只有SPL与寄存器边界使用电脑替身。
foreach ($case in @(
    @{ Name = 'motor_direct'; Source = 'test_motor_direct.c'; Fake = 'motor_direct' },
    @{ Name = 'motor_direct_b'; Source = 'test_motor_direct.c'; Fake = 'motor_direct' },
    @{ Name = 'motor_direct_startup'; Source = 'test_motor_direct_startup.c'; Fake = 'motor_bench_startup' }
)) {
    $program = Join-Path $outputRoot ($case.Name + '.exe')
    $directMacro = if ($case.Name -eq 'motor_direct_b') { '-DMOTOR_DIRECT_B_TARGET=1' } else { '-DMOTOR_DIRECT_A_TARGET=1' }
    & $Compiler -std=c99 -Wall -Wextra -Wconversion -Werror -pedantic $directMacro -I (Join-Path $controlRoot ('Tests/Host/fakes/' + $case.Fake)) -I (Join-Path $controlRoot 'Core/Inc') -I (Join-Path $controlRoot 'App/Car') -I (Join-Path $controlRoot 'App/Diagnostics') -I (Join-Path $controlRoot 'Drivers_Custom/Board') -I (Join-Path $controlRoot 'Drivers_Custom/Motor') -I (Join-Path $controlRoot 'Drivers_Custom/Communication') (Join-Path $controlRoot 'App/Diagnostics/motor_bench.c') (Join-Path $controlRoot ('Tests/Host/' + $case.Source)) -o $program
    if ($LASTEXITCODE -ne 0) { throw ('MotorDirect test compilation failed: ' + $case.Name) }
    & $program 2>&1 | Tee-Object -FilePath (Join-Path $outputRoot ($case.Name + '_tests.log'))
    if ($LASTEXITCODE -ne 0) { throw ('MotorDirect test failed: ' + $case.Name) }
}
