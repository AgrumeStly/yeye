param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$output = Join-Path $controlRoot 'build/test_low_speed_lap.exe'
New-Item -ItemType Directory -Force -Path (Split-Path $output -Parent) | Out-Null
$includes = @('App/Motion', 'Algorithms/Speed', 'Algorithms/Encoder', 'Drivers_Custom/Communication')
$arguments = @('-std=c99','-Wall','-Wextra','-Wconversion','-Werror','-pedantic')
foreach ($include in $includes) { $arguments += @('-I', (Join-Path $controlRoot $include)) }
foreach ($source in @('App/Motion/lap_motion.c','App/Motion/speed_match.c','Algorithms/Speed/speed_pi.c','Algorithms/Encoder/encoder_counter.c','Drivers_Custom/Communication/lap_link.c','Drivers_Custom/Communication/protocol.c','Tests/Host/test_lap_motion.c')) { $arguments += (Join-Path $controlRoot $source) }
& $Compiler @arguments -lm -o $output
if ($LASTEXITCODE -ne 0) { throw 'LowSpeedLap model compile failed.' }
& $output | Tee-Object -FilePath (Join-Path $controlRoot 'build/low_speed_lap_tests.log')
if ($LASTEXITCODE -ne 0) { throw 'LowSpeedLap model failed.' }

# Run the production UART ISR against SPL stubs; real IRQ timing remains untested.
$uartOutput = Join-Path $controlRoot 'build/test_lap_uart.exe'
$uartArguments = @('-std=c99','-Wall','-Wextra','-Wconversion','-Werror','-pedantic',
    '-I', (Join-Path $controlRoot 'Tests/Host/lap_uart_stub'),
    '-I', (Join-Path $controlRoot 'Drivers_Custom/Communication'),
    (Join-Path $controlRoot 'Drivers_Custom/Communication/lap_uart.c'),
    (Join-Path $controlRoot 'Tests/Host/test_lap_uart.c'))
& $Compiler @uartArguments -o $uartOutput
if ($LASTEXITCODE -ne 0) { throw 'LowSpeedLap UART host compile failed.' }
& $uartOutput | Tee-Object -FilePath (Join-Path $controlRoot 'build/low_speed_lap_uart_tests.log')
if ($LASTEXITCODE -ne 0) { throw 'LowSpeedLap UART host checks failed.' }
