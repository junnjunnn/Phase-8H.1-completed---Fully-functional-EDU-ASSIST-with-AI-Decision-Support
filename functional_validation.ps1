$BASE_URL = "http://127.0.0.1:8000"
$FRONTEND_URL = "http://localhost:5173"
$RESULTS = @()
$TEST_DATA = @{}

function Log-Result($Module, $Workflow, $Status, $Details) {
    $Result = @{
        Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        Module = $Module
        Workflow = $Workflow
        Status = $Status
        Details = $Details
    }
    $global:RESULTS += $Result
    Write-Host "[$Status] $Module > $Workflow`: $Details" -ForegroundColor $(if ($Status -eq "PASS") { "Green" } else { "Red" })
}

function Test-Authentication {
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "TESTING: Authentication Workflow" -ForegroundColor Cyan
    Write-Host "$('='*60)" -ForegroundColor Cyan
    
    $LoginData = @{
        username = "demo_admin"
        password = "secure_password_123"
    } | ConvertTo-Json
    
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/token/" -Method POST -Body $LoginData -ContentType "application/json" -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            $Tokens = $Response.Content | ConvertFrom-Json
            if ($Tokens.access -and $Tokens.refresh) {
                $global:TEST_DATA.access_token = $Tokens.access
                $global:TEST_DATA.refresh_token = $Tokens.refresh
                Log-Result "Authentication" "login" "✓ PASS" "Valid credentials accepted"
            }
            else {
                Log-Result "Authentication" "login" "✗ FAIL" "Tokens missing from response"
            }
        }
    }
    catch {
        Log-Result "Authentication" "login" "✗ FAIL" $_.Exception.Message
    }
    
    # Test token validation
    if ($global:TEST_DATA.access_token) {
        try {
            $Headers = @{ Authorization = "Bearer $($global:TEST_DATA.access_token)" }
            $Response = Invoke-WebRequest -Uri "$BASE_URL/api/me/" -Headers $Headers -TimeoutSec 5
            if ($Response.StatusCode -eq 200) {
                $User = $Response.Content | ConvertFrom-Json
                if ($User.username -eq "demo_admin") {
                    Log-Result "Authentication" "token_validation" "✓ PASS" "Token grants access to protected endpoint"
                }
                else {
                    Log-Result "Authentication" "token_validation" "✗ FAIL" "Wrong user returned"
                }
            }
        }
        catch {
            Log-Result "Authentication" "token_validation" "✗ FAIL" $_.Exception.Message
        }
    }
    
    # Test unauthorized access
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/students/" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($Response.StatusCode -ne 401) {
            Log-Result "Authentication" "unauthorized_access" "✗ FAIL" "Expected 401, got $($Response.StatusCode)"
        }
    }
    catch {
        if ($_.Exception.Response.StatusCode.Value__ -eq 401) {
            Log-Result "Authentication" "unauthorized_access" "✓ PASS" "Endpoint requires authentication"
        }
        else {
            Log-Result "Authentication" "unauthorized_access" "✗ FAIL" $_.Exception.Message
        }
    }
}

function Test-HealthCheck {
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "TESTING: Backend Health Check" -ForegroundColor Cyan
    Write-Host "$('='*60)" -ForegroundColor Cyan
    
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/health/" -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            $Health = $Response.Content | ConvertFrom-Json
            if ($Health.status -eq "ok" -and $Health.database -eq "connected") {
                Log-Result "System" "backend_health" "✓ PASS" "Backend and database operational"
            }
            else {
                Log-Result "System" "backend_health" "✗ FAIL" "Health check returned: $($Health | ConvertTo-Json)"
            }
        }
    }
    catch {
        Log-Result "System" "backend_health" "✗ FAIL" $_.Exception.Message
    }
}

function Test-StudentEndpoints {
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "TESTING: Student Management Endpoints" -ForegroundColor Cyan
    Write-Host "$('='*60)" -ForegroundColor Cyan
    
    if (-not $global:TEST_DATA.access_token) {
        Log-Result "Students" "endpoints" "✗ FAIL" "No authentication token available"
        return
    }
    
    $Headers = @{ Authorization = "Bearer $($global:TEST_DATA.access_token)" }
    
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/students/" -Headers $Headers -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            $Students = $Response.Content | ConvertFrom-Json
            $Count = if ($Students.results) { $Students.results.Count } else { $Students.Count }
            Log-Result "Students" "list_students" "✓ PASS" "Retrieved $Count students"
        }
    }
    catch {
        Log-Result "Students" "list_students" "✗ FAIL" $_.Exception.Message
    }
}

function Test-AcademicEndpoints {
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "TESTING: Academic Structure Endpoints" -ForegroundColor Cyan
    Write-Host "$('='*60)" -ForegroundColor Cyan
    
    if (-not $global:TEST_DATA.access_token) {
        Log-Result "Academics" "endpoints" "✗ FAIL" "No authentication token available"
        return
    }
    
    $Headers = @{ Authorization = "Bearer $($global:TEST_DATA.access_token)" }
    
    # Academic years
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/academic-years/" -Headers $Headers -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Log-Result "Academics" "list_academic_years" "✓ PASS" "Retrieved academic years"
        }
    }
    catch {
        Log-Result "Academics" "list_academic_years" "✗ FAIL" $_.Exception.Message
    }
    
    # Grade levels
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/grade-levels/" -Headers $Headers -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Log-Result "Academics" "list_grade_levels" "✓ PASS" "Retrieved grade levels"
        }
    }
    catch {
        Log-Result "Academics" "list_grade_levels" "✗ FAIL" $_.Exception.Message
    }
    
    # Sections
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/sections/" -Headers $Headers -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Log-Result "Academics" "list_sections" "✓ PASS" "Retrieved sections"
        }
    }
    catch {
        Log-Result "Academics" "list_sections" "✗ FAIL" $_.Exception.Message
    }
}

function Test-DashboardEndpoints {
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "TESTING: Dashboard Endpoints" -ForegroundColor Cyan
    Write-Host "$('='*60)" -ForegroundColor Cyan
    
    if (-not $global:TEST_DATA.access_token) {
        Log-Result "Dashboard" "endpoints" "✗ FAIL" "No authentication token available"
        return
    }
    
    $Headers = @{ Authorization = "Bearer $($global:TEST_DATA.access_token)" }
    
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/dashboard-summary/" -Headers $Headers -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            $Dashboard = $Response.Content | ConvertFrom-Json
            if ($Dashboard.results -and $Dashboard.results.Count -gt 0) {
                $Summary = $Dashboard.results[0]
                if ($Summary.summary) {
                    Log-Result "Dashboard" "summary" "✓ PASS" "Dashboard returns metrics"
                }
                else {
                    Log-Result "Dashboard" "summary" "✗ FAIL" "Missing summary in response"
                }
            }
            else {
                Log-Result "Dashboard" "summary" "✗ FAIL" "Unexpected response format"
            }
        }
    }
    catch {
        Log-Result "Dashboard" "summary" "✗ FAIL" $_.Exception.Message
    }
}

function Test-PredictionEndpoints {
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "TESTING: Prediction Engine Endpoints" -ForegroundColor Cyan
    Write-Host "$('='*60)" -ForegroundColor Cyan
    
    if (-not $global:TEST_DATA.access_token) {
        Log-Result "Predictions" "endpoints" "✗ FAIL" "No authentication token available"
        return
    }
    
    $Headers = @{ Authorization = "Bearer $($global:TEST_DATA.access_token)" }
    
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/risk-predictions/" -Headers $Headers -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Log-Result "Predictions" "list_predictions" "✓ PASS" "Retrieved predictions"
        }
    }
    catch {
        Log-Result "Predictions" "list_predictions" "✗ FAIL" $_.Exception.Message
    }
}

function Test-AttendanceEndpoints {
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "TESTING: Attendance Endpoints" -ForegroundColor Cyan
    Write-Host "$('='*60)" -ForegroundColor Cyan
    
    if (-not $global:TEST_DATA.access_token) {
        Log-Result "Attendance" "endpoints" "✗ FAIL" "No authentication token available"
        return
    }
    
    $Headers = @{ Authorization = "Bearer $($global:TEST_DATA.access_token)" }
    
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/attendance-records/" -Headers $Headers -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Log-Result "Attendance" "list_records" "✓ PASS" "Retrieved attendance records"
        }
    }
    catch {
        Log-Result "Attendance" "list_records" "✗ FAIL" $_.Exception.Message
    }
}

function Test-ReportEndpoints {
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "TESTING: Report Endpoints" -ForegroundColor Cyan
    Write-Host "$('='*60)" -ForegroundColor Cyan
    
    if (-not $global:TEST_DATA.access_token) {
        Log-Result "Reports" "endpoints" "✗ FAIL" "No authentication token available"
        return
    }
    
    $Headers = @{ Authorization = "Bearer $($global:TEST_DATA.access_token)" }
    
    try {
        $Response = Invoke-WebRequest -Uri "$BASE_URL/api/reports/center/" -Headers $Headers -TimeoutSec 5
        if ($Response.StatusCode -eq 200) {
            Log-Result "Reports" "center_report" "✓ PASS" "Report center endpoint accessible"
        }
    }
    catch {
        Log-Result "Reports" "center_report" "✗ FAIL" $_.Exception.Message
    }
}

function Generate-Report {
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "TEST SUMMARY" -ForegroundColor Cyan
    Write-Host "$('='*60)" -ForegroundColor Cyan
    
    $Passed = @($global:RESULTS | Where-Object { $_.Status -eq "✓ PASS" }).Count
    $Failed = @($global:RESULTS | Where-Object { $_.Status -eq "✗ FAIL" }).Count
    $Total = $global:RESULTS.Count
    
    Write-Host "`nTotal Tests: $Total"
    Write-Host "Passed: $Passed" -ForegroundColor Green
    Write-Host "Failed: $Failed" -ForegroundColor Red
    if ($Total -gt 0) {
        $SuccessRate = [math]::Round(($Passed/$Total)*100, 1)
        Write-Host "Success Rate: $SuccessRate%" -ForegroundColor $(if ($SuccessRate -eq 100) { "Green" } else { "Yellow" })
    }
    
    if ($Failed -gt 0) {
        Write-Host "`n$('-'*60)" -ForegroundColor Red
        Write-Host "FAILED TESTS:" -ForegroundColor Red
        Write-Host "$('-'*60)" -ForegroundColor Red
        foreach ($Result in $global:RESULTS | Where-Object { $_.Status -eq "✗ FAIL" }) {
            Write-Host "  $($Result.Module) > $($Result.Workflow): $($Result.Details)" -ForegroundColor Red
        }
    }
    
    # Write JSON report
    $global:RESULTS | ConvertTo-Json | Out-File -FilePath "functional_test_report.json" -Encoding UTF8
    Write-Host "`nReport saved to: functional_test_report.json"
}

# Main execution
Write-Host "EDU ASSIST Functional Validation - STARTING" -ForegroundColor Cyan
Write-Host "Backend URL: $BASE_URL" -ForegroundColor White
Write-Host "Frontend URL: $FRONTEND_URL" -ForegroundColor White
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White

Test-HealthCheck
Test-Authentication
Test-StudentEndpoints
Test-AcademicEndpoints
Test-DashboardEndpoints
Test-PredictionEndpoints
Test-AttendanceEndpoints
Test-ReportEndpoints

Generate-Report
