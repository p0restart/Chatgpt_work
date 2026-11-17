$ErrorActionPreference='Stop'
$taskDirectory=$PSScriptRoot
$inputDocument=Join-Path $taskDirectory '论文终稿_中文.docx'
$outputPdf=Join-Path $taskDirectory '论文终稿_中文.pdf'
$wordApplication=$null
$wordDocument=$null
try {
    $wordApplication=New-Object -ComObject Word.Application
    $wordApplication.Visible=$false
    $wordApplication.DisplayAlerts=0
    $wordDocument=$wordApplication.Documents.Open($inputDocument,$false,$true)
    $wordDocument.Repaginate()
    $wordDocument.ExportAsFixedFormat($outputPdf,17)
    Write-Output ('PDF exported. Pages: '+$wordDocument.ComputeStatistics(2))
} finally {
    if ($null -ne $wordDocument) { $wordDocument.Close(0) }
    if ($null -ne $wordApplication) { $wordApplication.Quit() }
}
