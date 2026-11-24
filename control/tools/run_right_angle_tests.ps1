param([string]$Compiler = 'gcc', [switch]$Voice)
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$name = if ($Voice) { 'right_angle_voice' } else { 'right_angle' }
$output = Join-Path $controlRoot "build/test_$name.exe"
New-Item -ItemType Directory -Force -Path (Split-Path $output -Parent) | Out-Null
$arguments = @('-std=c99','-Wall','-Wextra','-Wconversion','-Werror','-pedantic','-DRIGHT_ANGLE_TARGET=1')
if ($Voice) { $arguments += '-DRIGHT_ANGLE_VOICE_TARGET=1' }
foreach ($include in @('App/Motion','Algorithms/Speed','Algorithms/Encoder','Drivers_Custom/Communication')) {
    $arguments += @('-I',(Join-Path $controlRoot $include))
}
foreach ($source in @('App/Motion/lap_motion.c','App/Motion/speed_match.c','Algorithms/Speed/speed_pi.c',
    'Algorithms/Speed/straight_guide.c','Algorithms/Speed/corner_guide.c','Algorithms/Encoder/encoder_counter.c',
    'Drivers_Custom/Communication/lap_link.c','Drivers_Custom/Communication/protocol.c',"Tests/Host/test_$name.c")) {
    $arguments += (Join-Path $controlRoot $source)
}
& $Compiler @arguments -lm -o $output
if ($LASTEXITCODE -ne 0) { throw 'RightAngle host build failed.' }
& $output | Tee-Object -FilePath (Join-Path $controlRoot "build/${name}_tests.log")
if ($LASTEXITCODE -ne 0) { throw 'RightAngle scenarios failed.' }
