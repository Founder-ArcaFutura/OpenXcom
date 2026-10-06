[CmdletBinding()]
param(
    [string]$SteamApps = 'C:\Program Files (x86)\Steam\steamapps',
    [string]$MSBuildPath = 'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe',
    [switch]$SkipBuild
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$localRoot = Join-Path $repoRoot 'build\local'
$runtimeRoot = Join-Path $localRoot 'runtime'
$resourceFolders = @('GEODATA', 'GEOGRAPH', 'MAPS', 'ROUTES', 'SOUND', 'TERRAIN', 'UFOGRAPH', 'UNITS')
$games = @(
    @{ Name = 'UFO'; Source = Join-Path $SteamApps 'common\XCom UFO Defense\XCOM'; Optional = @('UFOINTRO') },
    @{ Name = 'TFTD'; Source = Join-Path $SteamApps 'common\X-COM Terror from the Deep\TFD'; Optional = @('ANIMS', 'FLOP_INT') }
)
# Original executables and saves are not copied.
foreach ($game in $games) {
    foreach ($folder in $resourceFolders) {
        $source = Join-Path $game.Source $folder
        if (-not (Test-Path -LiteralPath $source -PathType Container)) {
            throw "Missing original game resource directory: $source"
        }
    }
}
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
# The upstream project copies dependency DLLs here even when OutDir is overridden.
New-Item -ItemType Directory -Path (Join-Path $repoRoot 'bin\x64') -Force | Out-Null
if (-not $SkipBuild) {
    # SavedGame embeds AlienCommand. Rebuild all users when its layout changes;
    # stale objects can otherwise link successfully with incompatible offsets.
    $layoutHeader = Join-Path $repoRoot 'src\Savegame\AlienCommand.h'
    $layoutMarker = Join-Path $localRoot 'alien-command-layout.sha256'
    $layoutHash = (Get-FileHash -LiteralPath $layoutHeader -Algorithm SHA256).Hash
    $layoutChanged = -not (Test-Path -LiteralPath $layoutMarker) -or (Get-Content -LiteralPath $layoutMarker -Raw).Trim() -ne $layoutHash
    if (-not (Test-Path -LiteralPath $MSBuildPath -PathType Leaf)) {
        throw 'MSBuild was not found. Supply -MSBuildPath for your Visual Studio C++ installation.'
    }
    $buildArguments = @(
        (Join-Path $repoRoot 'src\OpenXcom.2010.vcxproj'),
        '/m:2', '/nologo', '/v:minimal', '/clp:ErrorsOnly;Summary',
        '/p:Configuration=Release', '/p:Platform=x64', '/p:PlatformToolset=v142',
        '/p:WindowsTargetPlatformVersion=10.0.19041.0', '/p:PreferredToolArchitecture=x64', '/p:CL_MPCount=2',
        "/p:OutDir=$runtimeRoot\", "/p:IntDir=$localRoot\obj\", '/fl',
        "/flp:logfile=$localRoot\baseline-build.log;verbosity=normal"
    )
    if ($layoutChanged) { $buildArguments += '/t:Rebuild' }
    & $MSBuildPath @buildArguments
    if ($LASTEXITCODE -ne 0) { throw "Engine build failed with exit code $LASTEXITCODE" }
    Set-Content -LiteralPath $layoutMarker -Value $layoutHash
}
foreach ($folder in @('common', 'standard')) {
    $destination = Join-Path $runtimeRoot $folder
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $repoRoot "bin\$folder") -Force |
        Copy-Item -Destination $destination -Recurse -Force
}
foreach ($game in $games) {
    $destination = Join-Path $runtimeRoot $game.Name
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    foreach ($folder in ($resourceFolders + $game.Optional)) {
        $source = Join-Path $game.Source $folder
        if (Test-Path -LiteralPath $source -PathType Container) {
            Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
        }
    }
}
Get-ChildItem -LiteralPath (Join-Path $repoRoot 'deps\lib\x64') -Filter '*.dll' |
    Copy-Item -Destination $runtimeRoot -Force
New-Item -ItemType Directory -Path (Join-Path $localRoot 'user') -Force | Out-Null
Write-Output "Development runtime: $runtimeRoot"
Write-Output 'Launch with scripts\run-local.ps1 (UFO) or scripts\run-local.ps1 -Game TFTD.'
