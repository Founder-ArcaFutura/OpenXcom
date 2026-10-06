[CmdletBinding()]
param([ValidateRange(1,65535)][int]$Port = 18868)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot 'build\local\laya-venv\Scripts\python.exe'
$fixture = Join-Path $repoRoot 'tests\alien-command-operation-fixture.py'
$previous = $env:OPENXCOM_OPERATION_FIXTURE
try {
    foreach ($mode in @('research','base','abstain','invalid')) {
        $env:OPENXCOM_OPERATION_FIXTURE = $mode
        $arguments = @('-u', ('"' + $fixture + '"'), '--port', "$Port", '--mode', $mode)
        $service = Start-Process -FilePath $python -ArgumentList $arguments -WindowStyle Hidden -PassThru
        try {
            Start-Sleep -Milliseconds 500
            if ($service.HasExited) { throw 'Operation fixture failed to start.' }
            Write-Output "Scripted operation fixture: $mode (engine wiring test, not learned performance)"
            & (Join-Path $PSScriptRoot 'test-alien-command.ps1') -SkipEngineBuild -ModelPort $Port
        }
        finally {
            Get-CimInstance Win32_Process -Filter "ParentProcessId=$($service.Id)" -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
            if (-not $service.HasExited) { Stop-Process -Id $service.Id -ErrorAction SilentlyContinue }
        }
    }
}
finally { $env:OPENXCOM_OPERATION_FIXTURE = $previous }
