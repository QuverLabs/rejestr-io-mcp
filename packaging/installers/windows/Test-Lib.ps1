Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Lib.ps1')

$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

try {
    # --- Merge-ClaudeConfig ---

    # Case 1: fresh/missing file
    $config1 = Join-Path $tmpDir 'fresh.json'
    Merge-ClaudeConfig -ConfigPath $config1 -ServerName 'rejestr-io' -Command '/bin/rejestr-io-mcp' -EnvName 'REJESTR_IO_API_KEY' -EnvValue 'key1'
    $parsed1 = Get-Content $config1 -Raw | ConvertFrom-Json
    if ($parsed1.mcpServers.'rejestr-io'.command -ne '/bin/rejestr-io-mcp') { throw "FAIL: fresh file command mismatch" }
    Write-Host "PASS: Merge-ClaudeConfig fresh file"

    # Case 2: existing entry preserved
    $config2 = Join-Path $tmpDir 'existing.json'
    Set-Content -Path $config2 -Value '{"mcpServers":{"other-server":{"command":"foo"}}}'
    Merge-ClaudeConfig -ConfigPath $config2 -ServerName 'rejestr-io' -Command '/bin/rejestr-io-mcp' -EnvName 'REJESTR_IO_API_KEY' -EnvValue 'key2'
    $parsed2 = Get-Content $config2 -Raw | ConvertFrom-Json
    if ($parsed2.mcpServers.'other-server'.command -ne 'foo') { throw "FAIL: unrelated entry not preserved" }
    if ($parsed2.mcpServers.'rejestr-io'.command -ne '/bin/rejestr-io-mcp') { throw "FAIL: rejestr-io entry missing" }
    Write-Host "PASS: Merge-ClaudeConfig existing entry preserved"

    # Case 3: re-run replaces, does not duplicate
    Merge-ClaudeConfig -ConfigPath $config2 -ServerName 'rejestr-io' -Command '/new/path' -EnvName 'REJESTR_IO_API_KEY' -EnvValue 'key3'
    $parsed3 = Get-Content $config2 -Raw | ConvertFrom-Json
    if ($parsed3.mcpServers.'other-server'.command -ne 'foo') { throw "FAIL: unrelated entry lost on re-run" }
    if ($parsed3.mcpServers.'rejestr-io'.command -ne '/new/path') { throw "FAIL: rejestr-io entry not replaced" }
    Write-Host "PASS: Merge-ClaudeConfig re-run replaces without duplicating"

    # Case 3b: merging into an existing file backs it up first
    if (-not (Test-Path "$config2.bak")) { throw "FAIL: backup file $config2.bak was not created" }
    $parsedBak = Get-Content "$config2.bak" -Raw | ConvertFrom-Json
    if ($parsedBak.mcpServers.'rejestr-io'.command -ne '/bin/rejestr-io-mcp') { throw "FAIL: backup does not contain the pre-merge content" }
    Write-Host "PASS: Merge-ClaudeConfig backup file created on merge"

    # --- Merge-CodexToml ---

    # Case 1: fresh/missing file
    $toml1 = Join-Path $tmpDir 'fresh.toml'
    Merge-CodexToml -TomlPath $toml1 -BinPath '/bin/rejestr-io-mcp' -ApiKey 'key1'
    $content1 = Get-Content $toml1 -Raw
    if ($content1 -notmatch [regex]::Escape('[mcp_servers.rejestr-io]')) { throw "FAIL: missing header (fresh)" }
    if ($content1 -notmatch [regex]::Escape('command = "/bin/rejestr-io-mcp"')) { throw "FAIL: missing command (fresh)" }
    Write-Host "PASS: Merge-CodexToml fresh file"

    # Case 2: existing unrelated entry preserved
    $toml2 = Join-Path $tmpDir 'existing.toml'
    @'
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]

[mcp_servers.context7.env]
FOO = "bar"
'@ | Set-Content -Path $toml2
    Merge-CodexToml -TomlPath $toml2 -BinPath '/bin/rejestr-io-mcp' -ApiKey 'key2'
    $content2 = Get-Content $toml2 -Raw
    if ($content2 -notmatch [regex]::Escape('[mcp_servers.context7]')) { throw "FAIL: context7 header dropped" }
    if ($content2 -notmatch [regex]::Escape('FOO = "bar"')) { throw "FAIL: context7 env dropped" }
    Write-Host "PASS: Merge-CodexToml existing entry preserved"

    # Case 3: re-run replaces, does not duplicate
    Merge-CodexToml -TomlPath $toml2 -BinPath '/new/path' -ApiKey 'key3'
    $content3 = Get-Content $toml2 -Raw
    $context7Count = ([regex]::Matches($content3, [regex]::Escape('[mcp_servers.context7]'))).Count
    $rejestrCount = ([regex]::Matches($content3, [regex]::Escape('[mcp_servers.rejestr-io]'))).Count
    if ($context7Count -ne 1) { throw "FAIL: context7 header count is $context7Count" }
    if ($rejestrCount -ne 1) { throw "FAIL: rejestr-io header count is $rejestrCount (expected 1, no duplicate)" }
    if ($content3 -notmatch [regex]::Escape('command = "/new/path"')) { throw "FAIL: rejestr-io command not updated" }
    Write-Host "PASS: Merge-CodexToml re-run replaces without duplicating"

    # Case 3b: merging into an existing file backs it up first
    if (-not (Test-Path "$toml2.bak")) { throw "FAIL: backup file $toml2.bak was not created" }
    $contentBak = Get-Content "$toml2.bak" -Raw
    if ($contentBak -notmatch [regex]::Escape('[mcp_servers.context7]')) { throw "FAIL: backup does not contain the pre-merge content" }
    if ($contentBak -notmatch [regex]::Escape('command = "/bin/rejestr-io-mcp"')) { throw "FAIL: backup is not the pre-re-run state" }
    Write-Host "PASS: Merge-CodexToml backup file created on merge"

    # Case 5 (regression): repeated merges against a file with unrelated
    # content present do not keep accumulating blank lines
    $toml5 = Join-Path $tmpDir 'stability.toml'
    @'
[mcp_servers.context7]
command = "npx"
'@ | Set-Content -Path $toml5
    Merge-CodexToml -TomlPath $toml5 -BinPath '/bin/a' -ApiKey 'k'
    Merge-CodexToml -TomlPath $toml5 -BinPath '/bin/b' -ApiKey 'k'
    $lineCountAfter2 = (Get-Content $toml5).Count
    Merge-CodexToml -TomlPath $toml5 -BinPath '/bin/c' -ApiKey 'k'
    $lineCountAfter3 = (Get-Content $toml5).Count
    if ($lineCountAfter3 -ne $lineCountAfter2) { throw "FAIL: line count grew from $lineCountAfter2 to $lineCountAfter3 across repeated merges against a file with unrelated content (blank-line accumulation regression)" }
    Write-Host "PASS: Merge-CodexToml repeated merges (with unrelated content present) do not accumulate blank lines"

    # Case 4: quote/backslash escaping
    $toml4 = Join-Path $tmpDir 'escaping.toml'
    Merge-CodexToml -TomlPath $toml4 -BinPath 'C:\rejestr-io-mcp.exe' -ApiKey 'key with "quote" and \backslash'
    $content4 = Get-Content $toml4 -Raw
    if ($content4 -notmatch [regex]::Escape('command = "C:\\rejestr-io-mcp.exe"')) { throw "FAIL: path escaping incorrect" }
    if ($content4 -notmatch [regex]::Escape('REJESTR_IO_API_KEY = "key with \"quote\" and \\backslash"')) { throw "FAIL: value escaping incorrect" }
    Write-Host "PASS: Merge-CodexToml quote/backslash escaping"

    Write-Host "All Lib.ps1 tests passed."
}
finally {
    Remove-Item -Recurse -Force $tmpDir
}
