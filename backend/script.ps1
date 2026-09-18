$rand = -join ((48..57)+(97..122) | Get-Random -Count 12 | ForEach-Object {[char]$_})
$email = "test_$rand@example.com"
$password = "TestPass123x"
$body = @{ email = $email; password = $password } | ConvertTo-Json
$reg = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/register" -Method POST -Body $body -ContentType "application/json"
$token = $reg.access_token
$headers = @{ Authorization = "Bearer $token" }
$resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/notion/oauth/authorize" -Method GET -Headers $headers
$clientIdNonEmpty = if ($resp.notion_client_id -and $resp.notion_client_id.Trim() -ne "") { "yes" } else { "no" }
$authUrl = $resp.authorization_url
$uri = [System.Uri]$authUrl
Add-Type -AssemblyName System.Web
$q = [System.Web.HttpUtility]::ParseQueryString($uri.Query)
$redirectUri = $q["redirect_uri"]
$redacted = $authUrl -replace "state=[^&]*", "state=REDACTED"
"notion_client_id non-empty: $clientIdNonEmpty" | Out-File -FilePath out.txt
"redirect_uri: $redirectUri" | Out-File -FilePath out.txt -Append
"authorization_url (redacted): $redacted" | Out-File -FilePath out.txt -Append
