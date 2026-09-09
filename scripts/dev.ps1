# Project-local entrypoint. Does not edit global PATH, trust, auth, or permissions.
# Keep raw arguments: an advanced param block steals CLI flags such as snapshot -i.
$Tool = if ($args.Count -gt 0) { [string]$args[0] } else { 'bridge' }
$ToolArgs = @($args | Select-Object -Skip 1)
$ErrorActionPreference = 'Stop'
# Buffer a supplied PowerShell pipeline before version probes can consume it.
# Leave ordinary interactive Codex stdin/TTY alone.
$hasPromptInput = $MyInvocation.ExpectingInput
$promptInput = if ($hasPromptInput) { @($input) } else { @() }
if (-not $hasPromptInput -and $Tool -eq 'codex' -and $ToolArgs -contains 'exec' -and $ToolArgs -contains '-' -and [Console]::IsInputRedirected) {
    $hasPromptInput = $true
    $promptInput = @([Console]::In.ReadToEnd())
}
if ($Tool -notin @('codex', 'browser', 'gate', 'bridge')) {
    throw 'Usage: scripts/dev.ps1 codex|browser|gate|bridge [arguments...]'
}
$repoRoot = Split-Path -Parent $PSScriptRoot

function Invoke-LegacyNative([string]$Executable, [object[]]$NativeArgs) {
    # Keep console handles inherited for ordinary interactive use. Framework's
    # redirected stdin writer emits a BOM before the first write, so supplied
    # text input uses a byte-preserving Python child and temporary file instead.
    # The body stays off argv so large piped prompts do not hit Windows limits.
    $inputPath = $null
    $process = $null
    try {
        if ($hasPromptInput) {
            $utf8 = [System.Text.UTF8Encoding]::new($false)
            $inputText = (@($promptInput | ForEach-Object { [string]$_ + "`r`n" }) -join '')
            $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
            if (-not $pythonCommand) { throw 'Windows Python is required for PowerShell 5 piped input; install/configure the project runtime or use PowerShell 7.' }
            $inputPath = [System.IO.Path]::GetTempFileName()
            [System.IO.File]::WriteAllText($inputPath, $inputText, $utf8)
            $encodedArgv = @(@($Executable) + @($NativeArgs) | ForEach-Object { [string]$_ })
            $envelope = @{ argv=$encodedArgv; stdin_path=$inputPath }
            $encoded = [Convert]::ToBase64String($utf8.GetBytes((ConvertTo-Json -InputObject $envelope -Compress -Depth 4)))
            $Executable = $pythonCommand.Source
            $NativeArgs = @('-c', "import base64,json,pathlib,subprocess,sys; p=json.loads(base64.b64decode(sys.argv[1]).decode('utf-8')); data=pathlib.Path(p['stdin_path']).read_bytes(); sys.exit(subprocess.run(p['argv'],input=data).returncode)", $encoded)
        }

        # CRT quoting bypasses the PS5 serializer, including empty strings and
        # backslashes adjacent to quotes. Leave simple switches unquoted for WSL.
        $quoted = foreach ($argument in $NativeArgs) {
            $value = [string]$argument
            if ($value.Length -eq 0 -or $value -match '[\s"]') {
                '"' + (($value -replace '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1') + '"'
            } else { $value }
        }
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = $Executable
        $startInfo.Arguments = $quoted -join ' '
        $startInfo.UseShellExecute = $false
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $startInfo
        [void]$process.Start()
        $process.WaitForExit()
        return $process.ExitCode
    } finally {
        if ($process) { $process.Dispose() }
        if ($inputPath) { Remove-Item -LiteralPath $inputPath -Force }
    }
}

if ($Tool -eq 'codex') {
    $appBin = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin'
    $running = @(Get-Process -Name codex -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Path -Unique |
        Where-Object { $_ -and $_.StartsWith($appBin, [StringComparison]::OrdinalIgnoreCase) })
    $installed = @(Get-ChildItem -LiteralPath $appBin -Filter codex.exe -Recurse -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTimeUtc -Descending | Select-Object -ExpandProperty FullName)
    $npmPackage = Join-Path $env:APPDATA 'npm\node_modules\@openai\codex'
    $npmBinaries = @(Get-ChildItem -LiteralPath $npmPackage -Filter codex.exe -Recurse -File -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty FullName)
    $candidates = @($npmBinaries + $running + $installed | Select-Object -Unique)
    $compatible = @()
    foreach ($candidate in $candidates) {
        $versionText = ('' | & $candidate --version 2>$null | Out-String).Trim()
        if ($LASTEXITCODE -eq 0 -and $versionText -match 'codex-cli (\d+)\.(\d+)\.(\d+)') {
            $version = [version]::new([int]$Matches[1], [int]$Matches[2], [int]$Matches[3])
            if ($version -ge [version]'0.153.0') {
                $compatible += [pscustomobject]@{Path=$candidate; Version=$version; Stable=($versionText -notmatch '-alpha|-beta|-rc')}
            }
        }
    }
    $codexExe = $compatible | Sort-Object Version,Stable -Descending | Select-Object -First 1 -ExpandProperty Path
    if (-not $codexExe) {
        throw 'No Astra-capable Codex found (minimum observed version 0.153.0). Update the Codex app or CLI.'
    }
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        exit (Invoke-LegacyNative $codexExe (@('-C', $repoRoot) + @($ToolArgs)))
    }
    if ($hasPromptInput) { $promptInput | & $codexExe -C $repoRoot @ToolArgs }
    else { & $codexExe -C $repoRoot @ToolArgs }
    exit $LASTEXITCODE
}

# wsl --cd accepts a Windows absolute path. Pass arguments separately, never shell-eval them.
if ($Tool -eq 'bridge' -and $ToolArgs.Count -eq 0) { $ToolArgs = @('doctor') }
# Explicit process-local control transfer, including absent values. Do not forward
# credentials or mutate WSL/global profiles. JSON is an argument, never shell code.
$controlKeys = @(
    'COLAB_HOOKS', 'COLAB_FIX_LANE', 'COLAB_ALLOW_TEST_EDIT',
    'COLAB_TASK_ID', 'COLAB_ROUND', 'COLAB_GATE_REPORT_DIR', 'COLAB_GATE_OUTDIR',
    'COLAB_GATE_JOBS', 'COLAB_GATE_PARALLELISM_MANIFEST', 'COLAB_TEST_ENV_FILE',
    'COLAB_FRONTEND_DIR', 'COLAB_FIXTURE_REACH_ENTRY', 'COLAB_VISUAL_URLS',
    'COLAB_VISUAL_EXEMPT', 'COLAB_VISUAL_ALLOW', 'COLAB_VISUAL_AUDIT',
    'COLAB_HARNESS_EVAL', 'COLAB_HARNESS_EVAL_EXEMPT',
    'COLAB_PLANNING_ROOT', 'COLAB_PLANNING_HOME'
)
$controls = @{}
foreach ($key in $controlKeys) { $controls[$key] = [Environment]::GetEnvironmentVariable($key, 'Process') }
# Encode the complete argument envelope: Windows PowerShell 5 removes embedded
# native-argument double quotes. Base64 also preserves Unicode and explicit nulls.
$payloadArgv = @(@($Tool) + @('--') + @($ToolArgs) | ForEach-Object { [string]$_ })
$payloadJson = ConvertTo-Json -InputObject @{ controls=$controls; argv=$payloadArgv } -Compress -Depth 4
$payloadBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($payloadJson))
$bootstrap = "import base64,json,os,runpy,sys; p=json.loads(base64.b64decode(sys.argv[1]).decode('utf-8')); [(os.environ.pop(k,None) if v is None else os.environ.__setitem__(k,v)) for k,v in p['controls'].items()]; sys.argv=['scripts/agent-bridge.py','run-tool',*p['argv']]; runpy.run_path(sys.argv[0],run_name='__main__')"
if ($PSVersionTable.PSVersion.Major -lt 7) {
    exit (Invoke-LegacyNative 'wsl.exe' @('--cd', $repoRoot, '-e', 'python3', '-c', $bootstrap, $payloadBase64))
}
if ($hasPromptInput) { $promptInput | & wsl.exe --cd $repoRoot -e python3 -c $bootstrap $payloadBase64 }
else { & wsl.exe --cd $repoRoot -e python3 -c $bootstrap $payloadBase64 }
exit $LASTEXITCODE
