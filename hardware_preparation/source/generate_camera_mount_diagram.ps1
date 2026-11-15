# 摄像头初装示意图生成器：只使用 Windows 自带绘图库，同时保存 PNG 和可编辑 SVG。
# 图中光轴按离地 18 cm、向下 40°绘制；右侧俯视图为位置示意，不表示实测视场。
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$outputDirectory = Split-Path $PSScriptRoot -Parent
$bitmap = New-Object System.Drawing.Bitmap 1600,1000
$canvas = [System.Drawing.Graphics]::FromImage($bitmap)
$canvas.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$canvas.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$canvas.Clear([System.Drawing.Color]::White)
$svg = New-Object 'System.Collections.Generic.List[string]'
$svg.Add('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000" viewBox="0 0 1600 1000"><rect width="1600" height="1000" fill="white"/>')
function Draw-Line($x1,$y1,$x2,$y2,$color='#334155',$width=3,$dash=$false) {
    $pen = New-Object System.Drawing.Pen ([System.Drawing.ColorTranslator]::FromHtml($color)),$width
    if ($dash) { $pen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash }
    $canvas.DrawLine($pen,[single]$x1,[single]$y1,[single]$x2,[single]$y2)
    $pen.Dispose()
    $dashAttribute = if ($dash) { ' stroke-dasharray="10 7"' } else { '' }
    $svg.Add("<line x1='$x1' y1='$y1' x2='$x2' y2='$y2' stroke='$color' stroke-width='$width'$dashAttribute/>")
}
function Draw-Box($x,$y,$w,$h,$color) {
    $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml($color))
    $canvas.FillRectangle($brush,[single]$x,[single]$y,[single]$w,[single]$h)
    $brush.Dispose()
    $svg.Add("<rect x='$x' y='$y' width='$w' height='$h' rx='4' fill='$color'/>")
}
function Draw-Circle($x,$y,$radius,$color) {
    $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml($color))
    $canvas.FillEllipse($brush,[single]($x-$radius),[single]($y-$radius),[single](2*$radius),[single](2*$radius))
    $brush.Dispose()
    $svg.Add("<circle cx='$x' cy='$y' r='$radius' fill='$color'/>")
}
function Draw-Text($x,$y,$value,$size=24,$color='#334155') {
    $font = New-Object System.Drawing.Font 'Microsoft YaHei',$size,([System.Drawing.FontStyle]::Regular),([System.Drawing.GraphicsUnit]::Pixel)
    $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml($color))
    $canvas.DrawString($value,$font,$brush,[single]$x,[single]$y)
    $font.Dispose(); $brush.Dispose()
    $escaped = [System.Security.SecurityElement]::Escape($value)
    $svg.Add("<text x='$x' y='$($y+$size)' font-family='Microsoft YaHei, sans-serif' font-size='$size' fill='$color'>$escaped</text>")
}
function Draw-Arrow($x1,$y1,$x2,$y2,$color='#2563eb',$width=3) {
    Draw-Line $x1 $y1 $x2 $y2 $color $width
    $angle = [Math]::Atan2(($y2-$y1),($x2-$x1))
    foreach ($offset in @(-0.45,0.45)) {
        Draw-Line $x2 $y2 ($x2-15*[Math]::Cos($angle+$offset)) ($y2-15*[Math]::Sin($angle+$offset)) $color $width
    }
}

Draw-Text 55 32 '摄像头初装：镜头中心离地 18 cm，向下俯视 40°' 38 '#0f172a'
Draw-Text 58 91 '工程建议起点 · 实拍后微调 · 非比赛指定参数 · 2026-11-06' 22 '#64748b'
Draw-Box 45 145 940 610 '#f8fafc'
Draw-Box 1010 145 545 610 '#f8fafc'
Draw-Text 70 165 '侧视：高度从地面量，角度从水平线量' 27 '#0f172a'
Draw-Text 1035 165 '俯视：车头居中，朝正前方' 27 '#0f172a'

# 侧视图长度比例 15 px/cm；镜头坐标 (490,380)，地面 y=650。
Draw-Line 160 275 945 275 '#dc2626' 2 $true
Draw-Text 175 235 '整车最高点 ≤25 cm（含支架、线束）' 23 '#dc2626'
Draw-Line 165 650 945 650 '#475569' 4
Draw-Text 885 664 '地面' 23
Draw-Box 215 580 290 28 '#64748b'
Draw-Circle 270 620 29 '#1e293b'
Draw-Circle 452 620 29 '#1e293b'
Draw-Box 315 520 100 60 '#94a3b8'
Draw-Text 318 535 '车体' 23 '#ffffff'
Draw-Box 450 385 16 195 '#475569'
Draw-Line 460 395 490 380 '#475569' 10
Draw-Box 470 354 35 40 '#0f766e'
Draw-Circle 490 380 10 '#14b8a6'
Draw-Text 290 325 '镜头中心' 24 '#0f766e'
Draw-Line 425 350 482 375 '#0f766e' 2
Draw-Line 490 380 490 650 '#94a3b8' 2 $true
Draw-Line 145 380 460 380 '#94a3b8' 2 $true
Draw-Arrow 145 515 145 380 '#2563eb'
Draw-Arrow 145 515 145 650 '#2563eb'
Draw-Text 70 465 '18 cm' 27 '#2563eb'
Draw-Line 490 380 920 380 '#94a3b8' 2 $true
Draw-Text 795 344 '水平参考线' 22 '#64748b'
$axisEnd = 490+270/[Math]::Tan(40*[Math]::PI/180)
Draw-Arrow 490 380 $axisEnd 650 '#ea580c' 5
Draw-Text 674 495 '镜头朝向／光轴' 23 '#c2410c'
for ($degree=0; $degree -lt 40; $degree+=2) {
    $a=$degree*[Math]::PI/180; $b=($degree+2)*[Math]::PI/180
    Draw-Line (490+105*[Math]::Cos($a)) (380+105*[Math]::Sin($a)) (490+105*[Math]::Cos($b)) (380+105*[Math]::Sin($b)) '#ea580c' 3
}
Draw-Text 601 405 '40° 向下' 28 '#c2410c'
Draw-Circle $axisEnd 650 6 '#ea580c'
Draw-Arrow 490 698 $axisEnd 698 '#2563eb' 2
Draw-Arrow $axisEnd 698 490 698 '#2563eb' 2
Draw-Text 528 708 '约 21.5 cm（光轴落地点）' 23 '#2563eb'
Draw-Arrow 255 688 385 688 '#334155' 3
Draw-Text 255 710 '车头方向' 22

# 俯视图只说明安装中心线，不画未经确认的视场边界或孔距。
Draw-Box 1150 440 280 245 '#cbd5e1'
Draw-Box 1115 565 35 95 '#1e293b'
Draw-Box 1430 565 35 95 '#1e293b'
Draw-Line 1290 250 1290 710 '#94a3b8' 2 $true
Draw-Box 1255 415 70 38 '#0f766e'
Draw-Circle 1290 423 10 '#14b8a6'
Draw-Arrow 1290 400 1290 265 '#0f766e' 5
Draw-Text 1320 305 '正前方' 23 '#0f766e'
Draw-Text 1180 490 '摄像头左右居中' 25 '#0f172a'
Draw-Text 1190 530 '支架固定在底板' 23
Draw-Text 1090 715 '左右不歪，画面方向由视觉核对' 23

Draw-Box 45 785 1510 165 '#eff6ff'
Draw-Text 70 805 '安装顺序：断电接排线 → 支架可调固定 → 静态看图 → 锁紧并复查' 28 '#1e40af'
Draw-Text 70 853 '调节余量：离地 16–20 cm；俯角 35–50°。支架抬高量需扣除底板离地高度及镜头安装偏置。' 23
Draw-Text 70 895 '先看清前方约 30–50 cm 的道路和边界；画面底部不一定能同时容纳整条 50 cm 宽车道。' 23
Draw-Text 55 965 '示意图非加工图；未表示镜头完整视场，安装尺寸与清晰度须以实物确认。' 20 '#64748b'

$bitmap.Save((Join-Path $outputDirectory 'camera_mount_diagram.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$svg.Add('</svg>')
[System.IO.File]::WriteAllLines((Join-Path $outputDirectory 'camera_mount_diagram.svg'),$svg,(New-Object System.Text.UTF8Encoding $false))
$canvas.Dispose(); $bitmap.Dispose()
Write-Output 'Generated camera_mount_diagram.png and camera_mount_diagram.svg'
