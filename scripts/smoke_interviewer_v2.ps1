param(
    [string]$BaseUrl = "http://localhost:8000/api",
    [int]$TargetDurationMinutes = 30,
    [switch]$StrictMode = $true
)

$ErrorActionPreference = 'Stop'

$suffix = [Guid]::NewGuid().ToString('N').Substring(0, 8)
$email = "iv2.e2e.$suffix@example.com"
$username = "iv2e2e_$suffix"
$password = 'SmokePass123!'

$registerBody = @{
    email = $email
    username = $username
    password = $password
    full_name = 'IV2 E2E Smoke'
} | ConvertTo-Json

$registerResponse = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/register" -ContentType 'application/json' -Body $registerBody
$token = $registerResponse.access_token

$tempDir = Join-Path $env:TEMP ("iv2_smoke_" + $suffix)
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
$cvPath = Join-Path $tempDir 'cv.txt'
$jdPath = Join-Path $tempDir 'jd.txt'

$cvText = 'Senior DevOps engineer with AWS, Kubernetes, Terraform, ArgoCD, Prometheus, SRE and incident response experience.'
$jdText = 'We need a Platform Engineer with strong AWS, Kubernetes, CI/CD, observability, IAM and security governance skills.'

Set-Content -Path $cvPath -Value $cvText -Encoding UTF8
Set-Content -Path $jdPath -Value $jdText -Encoding UTF8

$cvJson = & curl.exe -sS -X POST "$BaseUrl/interviewer-v2/documents/cv" -H "Authorization: Bearer $token" -F "file=@$cvPath;type=text/plain" -F "raw_text=$cvText"
$jdJson = & curl.exe -sS -X POST "$BaseUrl/interviewer-v2/documents/job-description" -H "Authorization: Bearer $token" -F "file=@$jdPath;type=text/plain" -F "raw_text=$jdText"

$cv = $cvJson | ConvertFrom-Json
$jd = $jdJson | ConvertFrom-Json

$blueprintBody = @{
    cv_document_id = $cv.document_id
    jd_document_id = $jd.document_id
    target_duration_minutes = $TargetDurationMinutes
    strict_mode = [bool]$StrictMode
} | ConvertTo-Json

$blueprint = Invoke-RestMethod -Method Post -Uri "$BaseUrl/interviewer-v2/blueprints/generate" -Headers @{ Authorization = "Bearer $token" } -ContentType 'application/json' -Body $blueprintBody

$result = [PSCustomObject]@{
    user_email = $email
    cv_document_id = $cv.document_id
    jd_document_id = $jd.document_id
    blueprint_id = $blueprint.blueprint_id
    delivery_mode = $blueprint.delivery_mode
    strict_mode = $blueprint.strict_mode
    competency_count = ($blueprint.competencies | Measure-Object).Count
    question_count = ($blueprint.question_plan | Measure-Object).Count
}

"IV2_E2E_RESULT_START"
$result | ConvertTo-Json -Compress
"IV2_E2E_RESULT_END"
