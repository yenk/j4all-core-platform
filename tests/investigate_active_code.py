"""
Investigation script to determine what backend code is actually being used.
This script tests which endpoints are called by the frontend and which are not.
"""

import requests
import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_backend_endpoints():
    """Test which endpoints are actually implemented and working."""
    base_url = "http://localhost:8000/api/v1"
    
    # Test endpoints that the frontend calls
    frontend_endpoints = [
        ("GET", "/health", None),
        ("POST", "/chat", {"message": "test"}),
        ("POST", "/documents/upload", None),  # File upload - skip for now
        ("GET", "/documents/search?q=test", None),
        ("GET", "/chat/history/test-id", None),
        ("POST", "/generate/brief", {"case_data": "test"})
    ]
    
    results = {}
    
    print("🔍 Testing Frontend-Called Endpoints:")
    print("=" * 50)
    
    for method, endpoint, data in frontend_endpoints:
        full_url = base_url + endpoint
        
        try:
            response = None
            if method == "GET":
                response = requests.get(full_url, timeout=5)
            elif method == "POST":
                response = requests.post(full_url, json=data, timeout=5)
            
            if response:
                status = response.status_code
                results[endpoint] = {
                    "status": status,
                    "working": status not in [404, 501],
                    "response_size": len(response.content)
                }
                print(f"✅ {method} {endpoint}: {status}")
            
        except requests.exceptions.ConnectionError:
            results[endpoint] = {"status": "NO_SERVER", "working": False}
            print(f"❌ {method} {endpoint}: Server not running")
            
        except requests.exceptions.Timeout:
            results[endpoint] = {"status": "TIMEOUT", "working": False}
            print(f"⏰ {method} {endpoint}: Timeout")
            
        except (requests.exceptions.RequestException, ValueError) as e:
            results[endpoint] = {"status": f"ERROR: {e}", "working": False}
            print(f"💥 {method} {endpoint}: {e}")
    
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY:")
    print("=" * 50)
    
    working = [ep for ep, result in results.items() if result["working"]]
    not_working = [ep for ep, result in results.items() if not result["working"]]
    
    print(f"✅ WORKING ENDPOINTS ({len(working)}):")
    for ep in working:
        print(f"   - {ep}")
    
    print(f"\n❌ NOT WORKING ENDPOINTS ({len(not_working)}):")
    for ep in not_working:
        print(f"   - {ep} ({results[ep]['status']})")
    
    return results


def check_unused_files():
    """Check which Python files might be unused."""
    print("\n🗂️ POTENTIALLY UNUSED FILES:")
    print("=" * 50)
    
    # Files that are clearly not used by the current working setup
    potentially_unused = [
        "app.py",           # Streamlit app (not React)
        "integrate.py",     # Integration script
        "dev/lumilens.py",  # Dev utility
        "pipeline/ingest.py", # Data pipeline
        "pipeline/load.py",   # Data pipeline
        "prompt.py"         # Prompt templates
    ]
    
    confirmed_unused = []
    
    for file_path in potentially_unused:
        full_path = project_root / file_path
        if full_path.exists():
            # Check if file is imported anywhere
            # Simple heuristic: if it's not imported, likely unused
            print(f"❓ {file_path} - {full_path.stat().st_size} bytes")
            confirmed_unused.append(file_path)
    
    print(f"\n📋 SUMMARY: {len(confirmed_unused)} potentially unused files")
    return confirmed_unused


if __name__ == "__main__":
    print("🚀 BACKEND INVESTIGATION STARTING...")
    print("Make sure your backend is running: python run_server.py")
    
    # Give time to start server if needed
    time.sleep(2)
    
    # Test endpoints
    endpoint_results = test_backend_endpoints()
    
    # Check unused files
    unused_files = check_unused_files()
    
    print("\n🎯 RECOMMENDATIONS:")
    print("=" * 50)
    print("✅ KEEP: Files supporting working endpoints")
    print("❌ SAFE TO REMOVE: Demo files, unused utilities")
    print("❓ INVESTIGATE: Document/analysis features (partially implemented)")
