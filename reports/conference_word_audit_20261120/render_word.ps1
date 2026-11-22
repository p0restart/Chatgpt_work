$ErrorActionPreference = 'Stop'
$auditRoot = $PSScriptRoot
$wordApp = New-Object -ComObject Word.Application
$wordApp.Visible = $false
$wordApp.DisplayAlerts = 0
$wordApp.AutomationSecurity = 3
$targets = @(
    @{Label='en'; Path=(Join-Path $auditRoot 'input\A Finite-Resource Network Defense Decision Method Based on a Nonzero-Sum Differential Game.docx')},
    @{Label='zh'; Path=(Join-Path $auditRoot 'input\1119-final-基于非零和微分博弈的有限资源网络防御决策方法.docx')},
    @{Label='template'; Path=(Join-Path $auditRoot 'template\Conference-template-letter.docx')}
)
try {
    foreach ($target in $targets) {
        $document = $null
        try {
            $document = $wordApp.Documents.Open($target.Path, $false, $true, $false)
            $document.Repaginate()
            $pageCount = $document.ComputeStatistics(2)
            $pdfPath = Join-Path $auditRoot ($target.Label + '.pdf')
            $document.ExportAsFixedFormat($pdfPath, 17)
            $pageData = @()
            foreach ($paragraph in $document.Paragraphs) {
                $range = $paragraph.Range
                $pageData += @{Text=$range.Text; Page=$range.Information(3); Start=$range.Start; End=$range.End}
            }
            @{Label=$target.Label; Pages=$pageCount; Paragraphs=$pageData} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $auditRoot ($target.Label + '_word_pages.json')) -Encoding utf8
            Write-Output ($target.Label + ': ' + $pageCount + ' pages; ' + $pdfPath)
        } finally {
            if ($null -ne $document) { $document.Close(0); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
        }
    }
} finally {
    $wordApp.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp)
}
