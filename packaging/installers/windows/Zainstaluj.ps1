Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
    . (Join-Path $PSScriptRoot 'Lib.ps1')

    $SourceBinary = Join-Path $PSScriptRoot 'rejestr-io-mcp.exe'
    $InstallDir = Join-Path $env:LOCALAPPDATA 'rejestr-io-mcp'
    $InstallBinary = Join-Path $InstallDir 'rejestr-io-mcp.exe'
    $ClaudeConfig = Join-Path $env:APPDATA 'Claude\claude_desktop_config.json'
    $CodexConfig = Join-Path $env:USERPROFILE '.codex\config.toml'

    Write-Host "=== Instalator rejestr-io-mcp ==="
    Write-Host ""

    if (-not (Test-Path $SourceBinary)) {
        Write-Host "BLAD: nie znaleziono pliku rejestr-io-mcp.exe w tym samym folderze co instalator." -ForegroundColor Red
        Write-Host "Upewnij sie, ze rozpakowales/as cale archiwum ZIP, a nie tylko ten plik." -ForegroundColor Red
        Read-Host "Nacisnij Enter, aby zamknac to okno"
        exit 1
    }

    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Copy-Item -Path $SourceBinary -Destination $InstallBinary -Force
    Write-Host "Skopiowano rejestr-io-mcp.exe do: $InstallBinary"

    $ApiKey = ""
    while ([string]::IsNullOrWhiteSpace($ApiKey)) {
        $secureApiKey = Read-Host -Prompt "Podaj swoj klucz API rejestr.io" -AsSecureString
        $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureApiKey)
        try {
            $ApiKey = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        } finally {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
        if ([string]::IsNullOrWhiteSpace($ApiKey)) {
            Write-Host "Klucz nie moze byc pusty, sprobuj ponownie."
        }
    }

    Merge-ClaudeConfig -ConfigPath $ClaudeConfig -ServerName "rejestr-io" -Command $InstallBinary -EnvName "REJESTR_IO_API_KEY" -EnvValue $ApiKey
    Write-Host "Skonfigurowano Claude Desktop."

    Merge-CodexToml -TomlPath $CodexConfig -BinPath $InstallBinary -ApiKey $ApiKey
    Write-Host "Skonfigurowano ChatGPT desktop / Codex CLI."

    Write-Host ""
    Write-Host "Gotowe! Uruchom ponownie Claude Desktop i/lub aplikacje ChatGPT, aby zmiany zaczely dzialac."
    Write-Host "W ChatGPT wpisz /mcp w oknie rozmowy, aby sprawdzic, czy serwer rejestr-io jest widoczny."
    Read-Host "Nacisnij Enter, aby zamknac to okno"
}
catch {
    Write-Host ""
    Write-Host "BLAD: instalacja nie powiodla sie." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Nacisnij Enter, aby zamknac to okno"
    exit 1
}
