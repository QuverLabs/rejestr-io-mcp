function Set-Utf8NoBom {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content
    )
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Merge-ClaudeConfig {
    param(
        [Parameter(Mandatory)][string]$ConfigPath,
        [Parameter(Mandatory)][string]$ServerName,
        [Parameter(Mandatory)][string]$Command,
        [Parameter(Mandatory)][string]$EnvName,
        [Parameter(Mandatory)][string]$EnvValue
    )

    $configDir = Split-Path -Parent $ConfigPath
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }

    if (Test-Path $ConfigPath) {
        Copy-Item -Path $ConfigPath -Destination "$ConfigPath.bak" -Force
    }

    if (Test-Path $ConfigPath) {
        $raw = Get-Content -Path $ConfigPath -Raw -Encoding UTF8
        if ([string]::IsNullOrWhiteSpace($raw)) {
            $config = [PSCustomObject]@{}
        } else {
            $config = $raw | ConvertFrom-Json
        }
    } else {
        $config = [PSCustomObject]@{}
    }

    if ($null -eq $config.PSObject.Properties['mcpServers']) {
        $config | Add-Member -MemberType NoteProperty -Name 'mcpServers' -Value ([PSCustomObject]@{})
    }

    $envObject = [PSCustomObject]@{}
    $envObject | Add-Member -MemberType NoteProperty -Name $EnvName -Value $EnvValue

    $entry = [PSCustomObject]@{
        command = $Command
        env     = $envObject
    }

    if ($null -ne $config.mcpServers.PSObject.Properties[$ServerName]) {
        $config.mcpServers.PSObject.Properties.Remove($ServerName)
    }
    $config.mcpServers | Add-Member -MemberType NoteProperty -Name $ServerName -Value $entry

    $json = $config | ConvertTo-Json -Depth 10
    Set-Utf8NoBom -Path $ConfigPath -Content ($json + [Environment]::NewLine)
}

function ConvertTo-TomlBasicString {
    param([Parameter(Mandatory)][string]$Value)
    $escaped = $Value.Replace('\', '\\').Replace('"', '\"')
    return '"' + $escaped + '"'
}

function Merge-CodexToml {
    param(
        [Parameter(Mandatory)][string]$TomlPath,
        [Parameter(Mandatory)][string]$BinPath,
        [Parameter(Mandatory)][string]$ApiKey
    )

    $tomlDir = Split-Path -Parent $TomlPath
    if (-not (Test-Path $tomlDir)) {
        New-Item -ItemType Directory -Path $tomlDir -Force | Out-Null
    }

    if (Test-Path $TomlPath) {
        Copy-Item -Path $TomlPath -Destination "$TomlPath.bak" -Force
    }

    $lines = @()
    if (Test-Path $TomlPath) {
        $lines = @(Get-Content -Path $TomlPath -Encoding UTF8)
    }

    $kept = New-Object System.Collections.Generic.List[string]
    $skip = $false
    foreach ($line in $lines) {
        if ($line -eq '[mcp_servers.rejestr-io]' -or $line -eq '[mcp_servers.rejestr-io.env]') {
            $skip = $true
            continue
        }
        if ($skip -and $line.StartsWith('[')) {
            $skip = $false
        }
        if ($skip) { continue }
        $kept.Add($line)
    }

    # Trim trailing blank lines so re-running this merge doesn't accumulate
    # an extra separator blank line on every pass (mirrors how bash's
    # $(...) command substitution strips trailing newlines in the
    # equivalent macOS implementation).
    while ($kept.Count -gt 0 -and $kept[$kept.Count - 1] -eq '') {
        $kept.RemoveAt($kept.Count - 1)
    }

    $output = New-Object System.Collections.Generic.List[string]
    if ($kept.Count -gt 0) {
        $output.AddRange($kept)
        $output.Add('')
    }
    $output.Add('[mcp_servers.rejestr-io]')
    $output.Add('command = ' + (ConvertTo-TomlBasicString $BinPath))
    $output.Add('')
    $output.Add('[mcp_servers.rejestr-io.env]')
    $output.Add('REJESTR_IO_API_KEY = ' + (ConvertTo-TomlBasicString $ApiKey))

    Set-Utf8NoBom -Path $TomlPath -Content (($output -join [Environment]::NewLine) + [Environment]::NewLine)
}
