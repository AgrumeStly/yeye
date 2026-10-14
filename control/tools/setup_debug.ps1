$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$destination = Join-Path $controlRoot 'firmware/yeye_control.uvoptx'
if (Test-Path -LiteralPath $destination) {
    Write-Output 'Existing local debug settings retained.'
} else {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'debug_options.xml') -Destination $destination
    Write-Output 'LogicDemo simulator and HardwareBench CMSIS-DAP defaults installed.'
}
