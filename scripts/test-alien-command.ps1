[CmdletBinding()]
param(
    [string]$MSBuildPath = 'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe',
    [switch]$SkipEngineBuild,
    [ValidateRange(0,65535)][int]$ModelPort = 0
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$localRoot = Join-Path $repoRoot 'build\local'
$runtimeRoot = Join-Path $localRoot 'runtime'
if (-not $SkipEngineBuild) { & (Join-Path $PSScriptRoot 'setup-local.ps1') -MSBuildPath $MSBuildPath }
$objects = @(Get-ChildItem -LiteralPath (Join-Path $localRoot 'obj') -Filter '*.obj' -Recurse)
if ($objects.Count -lt 100) { throw 'Build the real engine first; its object files are required.' }
& $MSBuildPath (Join-Path $repoRoot 'tests\AlienCommandTests.vcxproj') '/nologo' '/v:minimal' '/p:Configuration=Release' '/p:Platform=x64'
if ($LASTEXITCODE -ne 0) { throw "Test build failed: $LASTEXITCODE" }
$previousVideo = $env:SDL_VIDEODRIVER
$previousAudio = $env:SDL_AUDIODRIVER
try {
    $env:SDL_VIDEODRIVER = 'dummy'
    $env:SDL_AUDIODRIVER = 'dummy'
    foreach ($master in @('xcom1', 'xcom2')) {
        $testName = if ($ModelPort) { "test-model-$master" } else { "test-$master" }
        $testUser = Join-Path $localRoot $testName
        New-Item -ItemType Directory -Path $testUser -Force | Out-Null
        $testLog = Join-Path $localRoot "$testName.log"
        & (Join-Path $runtimeRoot 'AlienCommandTests.exe') -data $runtimeRoot -user $testUser -config $testUser -master $master -playIntro false -useOpenGL false -fullscreen false -alienCommandPortfolio false -alienCommandModelPort $ModelPort *> $testLog
        if ($LASTEXITCODE -ne 0) {
            Get-Content -LiteralPath $testLog -Tail 10
            throw "Engine tests failed for $master; see $testLog"
        }
        Select-String -LiteralPath $testLog -Pattern '^PASS:' | ForEach-Object { $_.Line }
    }
}
finally {
    $env:SDL_VIDEODRIVER = $previousVideo
    $env:SDL_AUDIODRIVER = $previousAudio
}
