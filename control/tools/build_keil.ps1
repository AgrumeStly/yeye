param([string]$KeilRoot = 'C:\Keil_v5', [ValidateSet('LogicDemo','HardwareBench','BoardSelfTest','MotorBench','MotorContinuous','MotorDirect')][string]$Target = 'LogicDemo')
$ErrorActionPreference = 'Stop'
$controlRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $controlRoot 'MDK-ARM/yeye_control.uvprojx'
$log = Join-Path $controlRoot ('build/firmware/' + $Target + '_build.log')
New-Item -ItemType Directory -Force -Path (Split-Path $log -Parent) | Out-Null
$keilExe = Join-Path $KeilRoot 'UV4/UV4.exe'
if (-not (Test-Path -LiteralPath $keilExe)) { throw "Keil not found: $keilExe" }
$process = Start-Process -FilePath $keilExe -ArgumentList @('-b',('"'+$project+'"'),'-t',$Target,'-j0','-o',('"'+$log+'"')) -WindowStyle Hidden -PassThru -Wait
if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log }
if ($process.ExitCode -ne 0) { throw "Keil build failed or warned (exit $($process.ExitCode))." }

# 只导出可供主控手动DFU使用的BIN，不枚举设备、更不烧录。
if ($Target -in @('MotorBench','MotorContinuous','MotorDirect')) {
    $fromElf = Join-Path $KeilRoot 'ARM/ARMCC/bin/fromelf.exe'
    $motorOutputName = switch ($Target) {
        'MotorDirect' { 'motor_direct' }
        'MotorContinuous' { 'motor_continuous' }
        default { 'motor_bench' }
    }
    $axf = Join-Path $controlRoot ('build/firmware/' + $motorOutputName + '/' + $motorOutputName + '.axf')
    $bin = Join-Path $controlRoot ('build/firmware/' + $motorOutputName + '/' + $motorOutputName + '.bin')
    & $fromElf --bin --output $bin $axf
    if ($LASTEXITCODE -ne 0) { throw 'Motor test BIN export failed.' }
    Get-FileHash -Algorithm SHA256 -LiteralPath $bin
}
