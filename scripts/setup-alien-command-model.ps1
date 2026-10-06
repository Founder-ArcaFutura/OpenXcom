[CmdletBinding()]
param([string]$SourcePython = 'python')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $repoRoot 'build\local\laya-venv'
& $SourcePython -m venv --system-site-packages $venv
if ($LASTEXITCODE -ne 0) { throw 'Could not create isolated Python runtime.' }
$python = Join-Path $venv 'Scripts\python.exe'
& $python -m pip install --disable-pip-version-check --no-deps laya==0.1.6 transformers==4.48.0 huggingface-hub==0.36.2 tokenizers==0.21.4
if ($LASTEXITCODE -ne 0) { throw 'Could not install the pinned Laya runtime.' }
& $python -c 'import torch,laya; print("Laya",laya.__version__,"Torch",torch.__version__)'
if ($LASTEXITCODE -ne 0) { throw 'A working local PyTorch installation is required.' }
