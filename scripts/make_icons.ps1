# Generates the plugin icons (Retro 82 palette) in .\Images
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\make_icons.ps1

Add-Type -AssemblyName System.Drawing

$out = Join-Path (Split-Path $PSScriptRoot -Parent) 'Images'
New-Item -ItemType Directory -Force $out | Out-Null

$C = @{
    bg    = [Drawing.ColorTranslator]::FromHtml('#00172e')
    amber = [Drawing.ColorTranslator]::FromHtml('#faa968')
    teal  = [Drawing.ColorTranslator]::FromHtml('#35a2a7')
    cream = [Drawing.ColorTranslator]::FromHtml('#f6dcac')
    muted = [Drawing.ColorTranslator]::FromHtml('#57898a')
}

function RoundRect([float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
    $p = New-Object Drawing.Drawing2D.GraphicsPath
    $d = $r * 2
    $p.AddArc($x, $y, $d, $d, 180, 90)
    $p.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $p.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $p.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $p.CloseFigure()
    return $p
}

function New-Icon([string]$name, [scriptblock]$draw) {
    $bmp = New-Object Drawing.Bitmap 64, 64
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = 'AntiAlias'
    $g.TextRenderingHint = 'AntiAliasGridFit'
    $g.Clear([Drawing.Color]::Transparent)
    $g.FillPath((New-Object Drawing.SolidBrush $C.bg), (RoundRect 0 0 64 64 12))
    & $draw $g
    $bmp.Save((Join-Path $out "$name.png"), [Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
}

# Drawing helpers (0..64 coordinates)
function Box($g, $x, $y, $w, $h, $col) { $g.FillPath((New-Object Drawing.SolidBrush $C[$col]), (RoundRect $x $y $w $h 3)) }
function Frame($g, $x, $y, $w, $h, $col, $t = 2.5) { $g.DrawPath((New-Object Drawing.Pen $C[$col], $t), (RoundRect $x $y $w $h 3)) }
function Ln($g, $x1, $y1, $x2, $y2, $col, $t = 4) { $pen = New-Object Drawing.Pen $C[$col], $t; $pen.StartCap = 'Round'; $pen.EndCap = 'Round'; $g.DrawLine($pen, $x1, $y1, $x2, $y2) }
function Txt($g, $text, $size, $col, $y = 0) {
    $f = New-Object Drawing.Font 'Segoe UI', $size, ([Drawing.FontStyle]::Bold), ([Drawing.GraphicsUnit]::Pixel)
    $sf = New-Object Drawing.StringFormat; $sf.Alignment = 'Center'; $sf.LineAlignment = 'Center'
    $g.DrawString($text, $f, (New-Object Drawing.SolidBrush $C[$col]), (New-Object Drawing.RectangleF 0, $y, 64, 64), $sf)
}

# --- Main icon: ultrawide three columns ---
New-Icon 'icon' { param($g) Box $g 9 12 12 40 'teal'; Box $g 23 12 18 40 'amber'; Box $g 43 12 12 40 'teal' }

# --- Window ---
New-Icon 'float' { param($g) Frame $g 9 9 20 20 'muted' 2; Frame $g 35 9 20 20 'muted' 2; Frame $g 9 35 20 20 'muted' 2; Frame $g 35 35 20 20 'muted' 2; Box $g 17 17 30 30 'amber' }
New-Icon 'monocle' { param($g) Box $g 10 10 44 44 'amber' }
New-Icon 'maximize' { param($g) Frame $g 8 8 48 48 'amber' 4; Ln $g 22 22 42 42 'cream' 4; Ln $g 42 30 42 42 'cream' 4; Ln $g 30 42 42 42 'cream' 4 }
New-Icon 'send' { param($g) Box $g 8 14 18 36 'amber'; Frame $g 40 14 16 36 'teal' 3; Ln $g 28 32 37 32 'cream' 4; Ln $g 32 26 37 32 'cream' 4; Ln $g 32 38 37 32 'cream' 4 }
New-Icon 'focus' { param($g) $g.DrawEllipse((New-Object Drawing.Pen $C.amber, 4), 14, 14, 36, 36); $g.FillEllipse((New-Object Drawing.SolidBrush $C.cream), 27, 27, 10, 10) }

# --- Workspace ---
New-Icon 'rename' { param($g) Txt $g 'Ab' 28 'cream' -2; Ln $g 14 50 50 50 'amber' 4 }
New-Icon 'zen' { param($g) Frame $g 8 8 48 48 'muted' 2; Box $g 21 21 22 22 'amber' }
New-Icon 'gap-none' { param($g) Box $g 8 8 24 24 'amber'; Box $g 32 8 24 24 'teal'; Box $g 8 32 24 24 'teal'; Box $g 32 32 24 24 'amber' }
New-Icon 'gap-normal' { param($g) Box $g 10 10 20 20 'amber'; Box $g 34 10 20 20 'teal'; Box $g 10 34 20 20 'teal'; Box $g 34 34 20 20 'amber' }
New-Icon 'tiling' { param($g) Box $g 9 9 21 46 'amber'; Box $g 34 9 21 21 'teal'; Box $g 34 34 21 21 'teal'; Ln $g 8 56 56 8 'cream' 4 }
New-Icon 'stack' { param($g) Frame $g 22 8 32 32 'muted' 3; Frame $g 16 16 32 32 'teal' 3; Box $g 10 24 32 32 'amber' }

# --- Layouts ---
New-Icon 'layout-bsp' { param($g) Box $g 8 10 23 44 'amber'; Box $g 34 10 22 21 'teal'; Box $g 34 34 9 20 'teal'; Box $g 46 34 10 20 'teal' }
New-Icon 'layout-columns' { param($g) Box $g 7 10 10 44 'amber'; Box $g 20 10 10 44 'teal'; Box $g 33 10 10 44 'teal'; Box $g 46 10 10 44 'teal' }
New-Icon 'layout-rows' { param($g) Box $g 8 8 48 10 'amber'; Box $g 8 21 48 10 'teal'; Box $g 8 34 48 10 'teal'; Box $g 8 47 48 9 'teal' }
New-Icon 'layout-vertical-stack' { param($g) Box $g 8 10 26 44 'amber'; Box $g 37 10 19 21 'teal'; Box $g 37 34 19 20 'teal' }
New-Icon 'layout-horizontal-stack' { param($g) Box $g 8 8 48 24 'amber'; Box $g 8 35 23 21 'teal'; Box $g 34 35 22 21 'teal' }
New-Icon 'layout-ultrawide-vertical-stack' { param($g) Box $g 6 10 12 44 'teal'; Box $g 21 10 22 44 'amber'; Box $g 46 10 12 21 'teal'; Box $g 46 34 12 20 'teal' }
New-Icon 'layout-grid' { param($g) Box $g 7 10 15 21 'amber'; Box $g 25 10 14 21 'teal'; Box $g 42 10 15 21 'teal'; Box $g 7 34 15 20 'teal'; Box $g 25 34 14 20 'teal'; Box $g 42 34 15 20 'teal' }
New-Icon 'layout-right-main-vertical-stack' { param($g) Box $g 8 10 19 21 'teal'; Box $g 8 34 19 20 'teal'; Box $g 30 10 26 44 'amber' }
New-Icon 'layout-scrolling' { param($g) Frame $g 2 14 8 36 'muted' 2; Box $g 13 14 11 36 'teal'; Box $g 27 14 11 36 'amber'; Box $g 41 14 11 36 'teal'; Frame $g 55 14 8 36 'muted' 2 }
New-Icon 'layout-auto' { param($g) Box $g 6 18 12 38 'teal'; Box $g 21 18 22 38 'amber'; Box $g 46 18 12 38 'teal'; Txt $g 'AUTO' 11 'cream' -24 }

# --- Komorebi ---
New-Icon 'pause' { param($g) Box $g 18 14 10 36 'amber'; Box $g 36 14 10 36 'amber' }
New-Icon 'reload' { param($g) $pen = New-Object Drawing.Pen $C.amber, 5; $pen.StartCap = 'Round'; $g.DrawArc($pen, 14, 14, 36, 36, 20, 290); $pts = [Drawing.PointF[]]@((New-Object Drawing.PointF 50, 14), (New-Object Drawing.PointF 52, 30), (New-Object Drawing.PointF 37, 24)); $g.FillPolygon((New-Object Drawing.SolidBrush $C.amber), $pts) }
New-Icon 'restart' { param($g) $pen = New-Object Drawing.Pen $C.amber, 5; $pen.StartCap = 'Round'; $pen.EndCap = 'Round'; $g.DrawArc($pen, 14, 16, 36, 36, 300, 300); Ln $g 32 10 32 32 'cream' 5 }
New-Icon 'config' { param($g) Txt $g '{ }' 30 'amber' -2 }

Write-Host "Icons written to $out"

# --- Gallery for the README (assets\icons.png) ---
$gallery = Join-Path (Split-Path $PSScriptRoot -Parent) 'assets\icons.png'
New-Item -ItemType Directory -Force (Split-Path $gallery) | Out-Null
$icons = Get-ChildItem $out -Filter *.png | Sort-Object Name
$cols = 9; $cell = 112; $rows = [Math]::Ceiling($icons.Count / $cols)
$sheet = New-Object Drawing.Bitmap ($cols * $cell), ($rows * $cell + 16)
$g = [Drawing.Graphics]::FromImage($sheet)
$g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAliasGridFit'
$g.Clear([Drawing.ColorTranslator]::FromHtml('#0d1117'))
$font = New-Object Drawing.Font 'Segoe UI', 10, ([Drawing.FontStyle]::Regular), ([Drawing.GraphicsUnit]::Pixel)
$label = New-Object Drawing.SolidBrush ([Drawing.ColorTranslator]::FromHtml('#8b949e'))
$sf = New-Object Drawing.StringFormat; $sf.Alignment = 'Center'; $sf.Trimming = 'EllipsisCharacter'
for ($i = 0; $i -lt $icons.Count; $i++) {
    $x = ($i % $cols) * $cell; $y = [Math]::Floor($i / $cols) * $cell + 8
    $img = [Drawing.Image]::FromFile($icons[$i].FullName)
    $g.DrawImage($img, $x + 24, $y + 8, 64, 64)
    $g.DrawString(($icons[$i].BaseName -replace '^layout-', ''), $font, $label, (New-Object Drawing.RectangleF $x, ($y + 78), $cell, 28), $sf)
    $img.Dispose()
}
$sheet.Save($gallery, [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $sheet.Dispose()
Write-Host "Gallery written to $gallery"
