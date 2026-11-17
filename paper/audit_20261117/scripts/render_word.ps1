param([Parameter(Mandatory=$true)][string]$InputDocument, [Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference='Stop'
$sourcePath=(Resolve-Path -LiteralPath $InputDocument).Path
$targetPath=[System.IO.Path]::GetFullPath($OutputPdf)
$workspacePath=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not $targetPath.StartsWith($workspacePath+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)) { throw 'PDF output must stay in the audit workspace.' }
$wordApplication=$null
$wordDocument=$null
try {
    $wordApplication=New-Object -ComObject Word.Application
    $wordApplication.Visible=$false
    $wordApplication.DisplayAlerts=0
    $wordDocument=$wordApplication.Documents.Open($sourcePath,$false,$true)
    $wordDocument.Repaginate()
    $wordDocument.ExportAsFixedFormat($targetPath,17)
    Write-Output ('PDF exported. Pages: '+$wordDocument.ComputeStatistics(2))
} finally {
    if ($null -ne $wordDocument) { $wordDocument.Close(0) }
    if ($null -ne $wordApplication) { $wordApplication.Quit() }
}
