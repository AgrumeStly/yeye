param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$outputRoot = Join-Path $controlRoot 'build'
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
$algorithm = Join-Path $controlRoot 'Algorithms/Encoder/encoder_counter.c'
$includes = @('-I', (Join-Path $controlRoot 'Algorithms/Encoder'))
foreach ($case in @('counter','bench')) {
    $sources = @($algorithm, (Join-Path $controlRoot ('Tests/Host/test_encoder_' + $case + '.c')))
    $caseIncludes = $includes
    if ($case -eq 'bench') {
        $sources += Join-Path $controlRoot 'App/Diagnostics/encoder_bench.c'
        $caseIncludes += @('-I',(Join-Path $controlRoot 'Tests/Host/fakes/encoder'),'-I',(Join-Path $controlRoot 'App/Diagnostics'),'-I',(Join-Path $controlRoot 'Drivers_Custom/Encoder'))
    }
    $program = Join-Path $outputRoot ('test_encoder_' + $case + '.exe')
    & $Compiler -std=c99 -Wall -Wextra -Wconversion -Werror -pedantic -DENCODER_BENCH_TARGET=1 @caseIncludes @sources -o $program
    if ($LASTEXITCODE -ne 0) { throw ('Encoder host compilation failed: ' + $case) }
    & $program 2>&1 | Tee-Object -FilePath (Join-Path $outputRoot ('encoder_' + $case + '_tests.log'))
    if ($LASTEXITCODE -ne 0) { throw ('Encoder host tests failed: ' + $case) }
}
