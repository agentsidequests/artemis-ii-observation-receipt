param()
$ErrorActionPreference = 'Stop'
$requestPath = Join-Path $PSScriptRoot 'horizons-requests.json'
$config = Get-Content -LiteralPath $requestPath -Raw | ConvertFrom-Json -DateKind String
if ($config.endpoint -ne 'https://ssd.jpl.nasa.gov/api/horizons.api') { throw 'Unexpected source endpoint' }
if ($config.max_response_bytes_each -ne 65536 -or $config.automatic_retries -ne 0) { throw 'Unexpected acquisition limits' }
$sourceDirectory = Join-Path $PSScriptRoot 'source'
New-Item -ItemType Directory -Path $sourceDirectory -Force | Out-Null
$resolvedDirectory = [IO.Path]::GetFullPath($sourceDirectory)
$calendarTimes = foreach ($time in $config.times) { "'" + $time.utc.Replace('T',' ').TrimEnd('Z') + "'" }
$expectedFiles = @('object.txt','vectors.txt','reverse-vectors.txt','observer.txt')
if (@(Compare-Object $expectedFiles @($config.requests.file)).Count -ne 0) { throw 'Unexpected request inventory' }
foreach ($request in $config.requests) {
    if (Test-Path -LiteralPath (Join-Path $sourceDirectory $request.file)) { throw 'Existing source: inspect it, do not overwrite or repeat acquisition' }
}
$client = [Net.Http.HttpClient]::new()
$client.Timeout = [TimeSpan]::FromSeconds($config.timeout_seconds_each)
try {
    foreach ($request in $config.requests) {
        $parameters = [ordered]@{}
        foreach ($property in $request.parameters.PSObject.Properties) { $parameters[$property.Name] = [string]$property.Value }
        if ($request.file -ne 'object.txt') { $parameters['TLIST'] = $calendarTimes -join ' ' }
        $pairs = foreach ($entry in $parameters.GetEnumerator()) { [Uri]::EscapeDataString($entry.Key) + '=' + [Uri]::EscapeDataString($entry.Value) }
        $url = $config.endpoint + '?' + ($pairs -join '&')
        $response = $client.GetAsync($url, [Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
        try {
            if (-not $response.IsSuccessStatusCode) { throw "Source access rejected: $([int]$response.StatusCode); stop without retry" }
            $stream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
            try {
                $buffer = [byte[]]::new($config.max_response_bytes_each + 1)
                $count = 0
                while ($count -lt $buffer.Length) {
                    $next = $stream.Read($buffer, $count, $buffer.Length - $count)
                    if ($next -eq 0) { break }
                    $count += $next
                }
                if ($count -gt $config.max_response_bytes_each) { throw 'Source response exceeded bounded acquisition' }
                $text = [Text.Encoding]::UTF8.GetString($buffer,0,$count)
                if (-not $text.Contains('API SOURCE: NASA/JPL Horizons API')) { throw 'Wrong provider response' }
                if ($request.file -eq 'object.txt') {
                    if (-not $text.Contains('Artemis II / Spacecraft') -or -not $text.Contains('-1024')) { throw 'Unresolved spacecraft identity' }
                } elseif (-not $text.Contains('$$SOE') -or -not $text.Contains('$$EOE')) { throw 'No complete ephemeris table; stop without retry' }
                $destination = [IO.Path]::GetFullPath((Join-Path $sourceDirectory $request.file))
                if ([IO.Path]::GetDirectoryName($destination) -ne $resolvedDirectory) { throw 'Source path escaped its owner' }
                # Preserve bounded network response bytes as evidence, not rewritten text.
                $fileStream = [IO.File]::Open($destination,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
                try { $fileStream.Write($buffer,0,$count) } finally { $fileStream.Dispose() }
                [pscustomobject]@{file=$request.file;url=$url;http=[int]$response.StatusCode;bytes=$count;sha256=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant();acquired_at_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress
            } finally { $stream.Dispose() }
        } finally { $response.Dispose() }
    }
} finally { $client.Dispose() }
