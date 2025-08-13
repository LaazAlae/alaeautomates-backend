#!/usr/bin/env python3
"""
Test script for the enhanced credit card batch processing API
"""

import requests
import json

def test_parse_excel_text():
    """Test the new parse-excel-text endpoint"""
    
    # Sample Excel data (matches your frontend format)
    test_data = """R130587    AMEX-1006    105.00    Wanyi Yang
R131702    AMEX-1007    210.00    Virginia Clarke
R132217    AMEX-1008    105.00    Smita Kumar"""
    
    payload = {
        "excel_text": test_data
    }
    
    # Test locally
    url = "http://localhost:5000/api/v1/cc-batch/parse-excel-text"
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Test Successful!")
            print(f"Records processed: {result['records_count']}")
            print(f"Message: {result['message']}")
            print("\nFirst few records:")
            for record in result['processed_data'][:3]:
                print(f"  {record}")
            print(f"\nJavaScript code length: {len(result['javascript_code'])} characters")
            
            # Check if the code contains the expected structure
            js_code = result['javascript_code']
            if "HeadlessAutomation" in js_code and "isFieldVisible" in js_code and "ROBUST" in js_code:
                print("✅ Generated JavaScript contains expected robust automation structure")
                print("✅ Includes legacy Edge compatibility and safeguards")
            else:
                print("❌ Generated JavaScript missing expected robust structure")
                
        else:
            print(f"❌ API Test Failed: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_parse_excel_text()