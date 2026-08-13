#!/usr/bin/env python3
"""
EDU ASSIST Complete Functional Validation Script
Tests all workflows to identify production-ready issues
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

# Test data storage
test_results = []
test_data = {}

def log_result(module, workflow, status, details=""):
    """Log test result"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "module": module,
        "workflow": workflow,
        "status": status,
        "details": details
    }
    test_results.append(result)
    print(f"[{status}] {module} > {workflow}: {details}")

def test_authentication():
    """Test authentication workflow"""
    print("\n" + "="*60)
    print("TESTING: Authentication Workflow")
    print("="*60)
    
    # Test 1: Login with valid credentials
    login_data = {
        "username": "demo_admin",
        "password": "secure_password_123"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/token/", json=login_data, timeout=5)
        if response.status_code == 200:
            tokens = response.json()
            if "access" in tokens and "refresh" in tokens:
                test_data["access_token"] = tokens["access"]
                test_data["refresh_token"] = tokens["refresh"]
                log_result("Authentication", "login", "✓ PASS", "Valid credentials accepted")
            else:
                log_result("Authentication", "login", "✗ FAIL", "Tokens missing from response")
        else:
            log_result("Authentication", "login", "✗ FAIL", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        log_result("Authentication", "login", "✗ FAIL", str(e))

    # Test 2: Access protected endpoint with token
    if "access_token" in test_data:
        try:
            headers = {"Authorization": f"Bearer {test_data['access_token']}"}
            response = requests.get(f"{BASE_URL}/api/me/", headers=headers, timeout=5)
            if response.status_code == 200:
                user = response.json()
                if user.get("username") == "demo_admin":
                    log_result("Authentication", "token_validation", "✓ PASS", "Token grants access to protected endpoint")
                else:
                    log_result("Authentication", "token_validation", "✗ FAIL", f"Wrong user returned: {user}")
            else:
                log_result("Authentication", "token_validation", "✗ FAIL", f"Status {response.status_code}")
        except Exception as e:
            log_result("Authentication", "token_validation", "✗ FAIL", str(e))

    # Test 3: Reject request without token
    try:
        response = requests.get(f"{BASE_URL}/api/students/", timeout=5)
        if response.status_code == 401:
            log_result("Authentication", "unauthorized_access", "✓ PASS", "Endpoint requires authentication")
        else:
            log_result("Authentication", "unauthorized_access", "✗ FAIL", f"Expected 401, got {response.status_code}")
    except Exception as e:
        log_result("Authentication", "unauthorized_access", "✗ FAIL", str(e))

def test_health_check():
    """Test backend health"""
    print("\n" + "="*60)
    print("TESTING: Backend Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health/", timeout=5)
        if response.status_code == 200:
            health = response.json()
            if health.get("status") == "ok" and health.get("database") == "connected":
                log_result("System", "backend_health", "✓ PASS", "Backend and database operational")
            else:
                log_result("System", "backend_health", "✗ FAIL", f"Health check returned: {health}")
        else:
            log_result("System", "backend_health", "✗ FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_result("System", "backend_health", "✗ FAIL", str(e))

def test_student_endpoints():
    """Test student management endpoints"""
    print("\n" + "="*60)
    print("TESTING: Student Management Endpoints")
    print("="*60)
    
    if "access_token" not in test_data:
        log_result("Students", "endpoints", "✗ FAIL", "No authentication token available")
        return
    
    headers = {"Authorization": f"Bearer {test_data['access_token']}"}
    
    # Test GET /api/students/
    try:
        response = requests.get(f"{BASE_URL}/api/students/", headers=headers, timeout=5)
        if response.status_code == 200:
            students = response.json()
            if "results" in students or isinstance(students, list):
                log_result("Students", "list_students", "✓ PASS", f"Retrieved {len(students.get('results', students))} students")
            else:
                log_result("Students", "list_students", "✗ FAIL", "Unexpected response format")
        else:
            log_result("Students", "list_students", "✗ FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_result("Students", "list_students", "✗ FAIL", str(e))

def test_academic_endpoints():
    """Test academic structure endpoints"""
    print("\n" + "="*60)
    print("TESTING: Academic Structure Endpoints")
    print("="*60)
    
    if "access_token" not in test_data:
        log_result("Academics", "endpoints", "✗ FAIL", "No authentication token available")
        return
    
    headers = {"Authorization": f"Bearer {test_data['access_token']}"}
    
    # Test academic years
    try:
        response = requests.get(f"{BASE_URL}/api/academic-years/", headers=headers, timeout=5)
        if response.status_code == 200:
            log_result("Academics", "list_academic_years", "✓ PASS", f"Retrieved academic years")
        else:
            log_result("Academics", "list_academic_years", "✗ FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_result("Academics", "list_academic_years", "✗ FAIL", str(e))
    
    # Test grade levels
    try:
        response = requests.get(f"{BASE_URL}/api/grade-levels/", headers=headers, timeout=5)
        if response.status_code == 200:
            log_result("Academics", "list_grade_levels", "✓ PASS", f"Retrieved grade levels")
        else:
            log_result("Academics", "list_grade_levels", "✗ FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_result("Academics", "list_grade_levels", "✗ FAIL", str(e))
    
    # Test sections
    try:
        response = requests.get(f"{BASE_URL}/api/sections/", headers=headers, timeout=5)
        if response.status_code == 200:
            log_result("Academics", "list_sections", "✓ PASS", f"Retrieved sections")
        else:
            log_result("Academics", "list_sections", "✗ FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_result("Academics", "list_sections", "✗ FAIL", str(e))

def test_dashboard():
    """Test dashboard endpoints"""
    print("\n" + "="*60)
    print("TESTING: Dashboard Endpoints")
    print("="*60)
    
    if "access_token" not in test_data:
        log_result("Dashboard", "endpoints", "✗ FAIL", "No authentication token available")
        return
    
    headers = {"Authorization": f"Bearer {test_data['access_token']}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard-summary/", headers=headers, timeout=5)
        if response.status_code == 200:
            dashboard = response.json()
            if "results" in dashboard and len(dashboard["results"]) > 0:
                summary = dashboard["results"][0]
                if "summary" in summary:
                    log_result("Dashboard", "summary", "✓ PASS", "Dashboard returns metrics")
                else:
                    log_result("Dashboard", "summary", "✗ FAIL", "Missing summary in response")
            else:
                log_result("Dashboard", "summary", "✗ FAIL", f"Unexpected response: {dashboard}")
        else:
            log_result("Dashboard", "summary", "✗ FAIL", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        log_result("Dashboard", "summary", "✗ FAIL", str(e))

def test_predictions():
    """Test prediction endpoints"""
    print("\n" + "="*60)
    print("TESTING: Prediction Engine Endpoints")
    print("="*60)
    
    if "access_token" not in test_data:
        log_result("Predictions", "endpoints", "✗ FAIL", "No authentication token available")
        return
    
    headers = {"Authorization": f"Bearer {test_data['access_token']}"}
    
    # Test list predictions
    try:
        response = requests.get(f"{BASE_URL}/api/risk-predictions/", headers=headers, timeout=5)
        if response.status_code == 200:
            log_result("Predictions", "list_predictions", "✓ PASS", "Retrieved predictions")
        else:
            log_result("Predictions", "list_predictions", "✗ FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_result("Predictions", "list_predictions", "✗ FAIL", str(e))

def test_attendance():
    """Test attendance endpoints"""
    print("\n" + "="*60)
    print("TESTING: Attendance Endpoints")
    print("="*60)
    
    if "access_token" not in test_data:
        log_result("Attendance", "endpoints", "✗ FAIL", "No authentication token available")
        return
    
    headers = {"Authorization": f"Bearer {test_data['access_token']}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/attendance-records/", headers=headers, timeout=5)
        if response.status_code == 200:
            log_result("Attendance", "list_records", "✓ PASS", "Retrieved attendance records")
        else:
            log_result("Attendance", "list_records", "✗ FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_result("Attendance", "list_records", "✗ FAIL", str(e))

def test_reports():
    """Test report endpoints"""
    print("\n" + "="*60)
    print("TESTING: Report Endpoints")
    print("="*60)
    
    if "access_token" not in test_data:
        log_result("Reports", "endpoints", "✗ FAIL", "No authentication token available")
        return
    
    headers = {"Authorization": f"Bearer {test_data['access_token']}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/reports/center/", headers=headers, timeout=5)
        if response.status_code == 200:
            log_result("Reports", "center_report", "✓ PASS", "Report center endpoint accessible")
        else:
            log_result("Reports", "center_report", "✗ FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_result("Reports", "center_report", "✗ FAIL", str(e))

def generate_report():
    """Generate test report"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if "✓" in r["status"])
    failed = sum(1 for r in test_results if "✗" in r["status"])
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if failed > 0:
        print("\n" + "-"*60)
        print("FAILED TESTS:")
        print("-"*60)
        for r in test_results:
            if "✗" in r["status"]:
                print(f"  {r['module']} > {r['workflow']}: {r['details']}")
    
    # Write report to file
    with open("functional_test_report.json", "w") as f:
        json.dump(test_results, f, indent=2)
    print(f"\nReport saved to: functional_test_report.json")

if __name__ == "__main__":
    print("EDU ASSIST Functional Validation - STARTING")
    print(f"Backend URL: {BASE_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Run all tests
    test_health_check()
    test_authentication()
    test_student_endpoints()
    test_academic_endpoints()
    test_dashboard()
    test_predictions()
    test_attendance()
    test_reports()
    
    # Generate report
    generate_report()
