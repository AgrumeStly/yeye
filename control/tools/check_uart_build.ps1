param([string]$KeilRoot = 'C:\Keil_v5')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$firmwareRoot = Join-Path $controlRoot 'firmware'
$outputRoot = Join-Path $firmwareRoot 'build/uart_check'
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
[xml]$projectXml = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $firmwareRoot 'yeye_control.uvprojx')
foreach ($targetNode in $projectXml.Project.Targets.Target) {
    $targetNode.TargetOption.TargetCommonOption.OutputDirectory = $outputRoot + '\'
    $targetNode.TargetOption.TargetCommonOption.ListingPath = $outputRoot + '\'
    $targetNode.TargetOption.TargetCommonOption.OutputName = 'uart_compile_check'
    $controls = $targetNode.TargetOption.TargetArmAds.Cads.VariousControls
    $controls.Define = $controls.Define + ',BOARD_UART_ENABLE=1'
}
$temporaryProject = Join-Path $firmwareRoot 'yeye_uart_check.uvprojx'
$encoding = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($temporaryProject, $projectXml.OuterXml, $encoding)
$log = Join-Path $outputRoot 'keil_build.log'
$keilExe = Join-Path $KeilRoot 'UV4/UV4.exe'
$process = Start-Process -FilePath $keilExe -ArgumentList @('-b',('"'+$temporaryProject+'"'),'-t','HardwareBench','-j0','-o',('"'+$log+'"')) -WindowStyle Hidden -PassThru -Wait
if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log }
if ($process.ExitCode -ne 0) { throw "UART-enabled build failed or warned (exit $($process.ExitCode))." }
Write-Output 'UART-enabled compilation passed. The original project keeps UART disabled.'
