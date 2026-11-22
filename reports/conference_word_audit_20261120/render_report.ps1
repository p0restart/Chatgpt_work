$ErrorActionPreference = 'Stop'
$reportRoot = $PSScriptRoot
$wordApp = New-Object -ComObject Word.Application
$wordApp.Visible = $false
$wordApp.DisplayAlerts = 0
$wordApp.AutomationSecurity = 3
$document = $null
try {
    $reportPath = Join-Path $reportRoot '论文模板与中英对照审查报告_20261120.docx'
    $document = $wordApp.Documents.Open($reportPath, $false, $true, $false)
    $document.Repaginate()
    $document.ExportAsFixedFormat((Join-Path $reportRoot 'audit_report.pdf'), 17)
    Write-Output ('Audit report: ' + $document.ComputeStatistics(2) + ' pages')
} finally {
    if ($null -ne $document) { $document.Close(0); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
    $wordApp.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp)
}
