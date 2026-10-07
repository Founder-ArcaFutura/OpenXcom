[CmdletBinding()]
param([int]$Port=18870,
 [ValidateSet('valid','save','invalid','duplicate','overbudget','invalidstrategy')]
 [string[]]$Modes=@('valid','save','invalid','duplicate','overbudget','invalidstrategy'))
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$python=Join-Path $repoRoot 'build\local\laya-venv\Scripts\python.exe'
$previous=$env:OPENXCOM_PORTFOLIO_FIXTURE
try {
 foreach ($mode in $Modes) {
  $env:OPENXCOM_PORTFOLIO_FIXTURE=$mode
  $fixture=Join-Path $repoRoot 'tests\alien-command-portfolio-fixture.py'
  $service=Start-Process -FilePath $python -ArgumentList @('-u',('"'+$fixture+'"'),'--port',"$Port",'--mode',$mode) -WindowStyle Hidden -PassThru
  try {
   Start-Sleep -Milliseconds 500
   if ($service.HasExited) { throw 'Portfolio fixture failed to start.' }
   Write-Output "Scripted portfolio fixture: $mode (engine wiring, not learned performance)"
   & (Join-Path $PSScriptRoot 'test-alien-command.ps1') -SkipEngineBuild -ModelPort $Port
   foreach ($master in @('xcom1','xcom2')) {
    Copy-Item -LiteralPath (Join-Path $repoRoot "build\local\test-model-$master\$master\portfolio-audit.jsonl") -Destination (Join-Path $repoRoot "build\local\portfolio-fixture-$mode-$master.jsonl") -Force
   }
  } finally {
   Get-CimInstance Win32_Process -Filter "ParentProcessId=$($service.Id)" -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
   if (-not $service.HasExited) { Stop-Process -Id $service.Id -ErrorAction SilentlyContinue }
  }
 }
} finally { $env:OPENXCOM_PORTFOLIO_FIXTURE=$previous }
