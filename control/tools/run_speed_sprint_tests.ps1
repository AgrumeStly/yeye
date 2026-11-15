param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$outputRoot = Join-Path $controlRoot 'build'
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
$common = @('-std=c99', '-Wall', '-Wextra', '-Wconversion', '-Werror', '-pedantic', '-DSPEED_SPRINT_TARGET=1')
foreach ($path in @('App/Motion', 'Algorithms/Speed', 'Algorithms/Encoder', 'Drivers_Custom/Motor', 'Drivers_Custom/Encoder', 'Tests/Host/fakes/encoder')) {
    $common += @('-I', (Join-Path $controlRoot $path))
}
$sources = @('App/Motion/speed_match.c', 'App/Motion/speed_sprint.c', 'Algorithms/Speed/speed_pi.c', 'Algorithms/Encoder/encoder_counter.c') | ForEach-Object { Join-Path $controlRoot $_ }
foreach ($case in @('test_speed_sprint', 'test_speed_sprint_integration')) {
    $output = Join-Path $outputRoot ($case + '.exe')
    & $Compiler @common @sources (Join-Path $controlRoot ('Tests/Host/' + $case + '.c')) -lm -o $output
    if ($LASTEXITCODE -ne 0) { throw ('SpeedSprint compile failed: ' + $case) }
    & $output | Tee-Object -FilePath (Join-Path $outputRoot ($case + '.log'))
    if ($LASTEXITCODE -ne 0) { throw ('SpeedSprint tests failed: ' + $case) }
}
