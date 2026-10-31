param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$output = Join-Path $controlRoot 'build/test_speed_match.exe'
& $Compiler -std=c99 -Wall -Wextra -Wconversion -Werror -pedantic -I (Join-Path $controlRoot 'App/Motion') -I (Join-Path $controlRoot 'Algorithms/Speed') -I (Join-Path $controlRoot 'Algorithms/Encoder') (Join-Path $controlRoot 'App/Motion/speed_match.c') (Join-Path $controlRoot 'Algorithms/Speed/speed_pi.c') (Join-Path $controlRoot 'Algorithms/Encoder/encoder_counter.c') (Join-Path $controlRoot 'Tests/Host/test_speed_match.c') -lm -o $output
if ($LASTEXITCODE -ne 0) { throw 'SpeedMatch tests did not compile.' }
& $output | Tee-Object -FilePath (Join-Path $controlRoot 'build/speed_match_tests.log')
if ($LASTEXITCODE -ne 0) { throw 'SpeedMatch tests failed.' }
$integration = Join-Path $controlRoot 'build/test_speed_match_integration.exe'
& $Compiler -std=c99 -Wall -Wextra -Wconversion -Werror -pedantic -I (Join-Path $controlRoot 'Tests/Host/fakes/encoder') -I (Join-Path $controlRoot 'App/Motion') -I (Join-Path $controlRoot 'Algorithms/Speed') -I (Join-Path $controlRoot 'Algorithms/Encoder') -I (Join-Path $controlRoot 'Drivers_Custom/Motor') -I (Join-Path $controlRoot 'Drivers_Custom/Encoder') (Join-Path $controlRoot 'App/Motion/speed_match.c') (Join-Path $controlRoot 'Algorithms/Speed/speed_pi.c') (Join-Path $controlRoot 'Algorithms/Encoder/encoder_counter.c') (Join-Path $controlRoot 'Tests/Host/test_speed_match_integration.c') -o $integration
if ($LASTEXITCODE -ne 0) { throw 'SpeedMatch integration did not compile.' }
& $integration | Tee-Object -FilePath (Join-Path $controlRoot 'build/speed_match_integration_tests.log')
if ($LASTEXITCODE -ne 0) { throw 'SpeedMatch integration failed.' }
