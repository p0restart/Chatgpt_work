param([Parameter(Mandatory=$true)][string]$InputPath,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
$wordApp=New-Object -ComObject Word.Application
$wordApp.Visible=$false
$wordApp.DisplayAlerts=0
$wordApp.AutomationSecurity=3
$document=$null
try {
 $document=$wordApp.Documents.Open($InputPath,$false,$true,$false)
 $document.Repaginate()
 $document.ExportAsFixedFormat($OutputPath,17)
 Write-Output ('Pages: '+$document.ComputeStatistics(2))
} finally {
 if($null -ne $document){$document.Close(0);[void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document)}
 $wordApp.Quit();[void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp)
}
