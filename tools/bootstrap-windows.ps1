# Downloads a private, portable copy of Python into .\runtime\python-win (no admin rights, nothing installed system-wide).
# Source: the official python.org "embeddable" package. The SHA-256 below was computed from the python.org download.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$root = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $root 'runtime\python-win'
$url  = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip'
$sha  = '4ACBED6DD1C744B0376E3B1CF57CE906F9DC9E95E68824584C8099A63025A3C3'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
$zip = Join-Path $env:TEMP ('nabd-python-' + [guid]::NewGuid() + '.zip')
Write-Host 'Downloading Python 3.12 (about 11 MB) from python.org ...'
Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
$got = (Get-FileHash -Path $zip -Algorithm SHA256).Hash
if ($got -ne $sha) { Remove-Item $zip -Force; throw "Checksum mismatch for the Python download ($got). Nothing was installed." }
if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $dest -Force
Remove-Item $zip -Force
Write-Host 'Python is ready.'
