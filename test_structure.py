#!/usr/bin/env python3
"""
Quick structure test for AlaeAutomates 2.0 Backend API
Tests basic imports and structure without requiring external dependencies
"""

import os
import sys

def test_structure():
    """Test the basic project structure"""
    print("🧪 Testing AlaeAutomates 2.0 Backend API Structure")
    print("=" * 50)
    
    # Check if we're in the right directory
    required_files = [
        'app.py',
        'requirements.txt',
        'railway.json',
        'Procfile',
        'README.md',
        'FRONTEND_GUIDE.md'
    ]
    
    required_dirs = [
        'app',
        'app/api',
        'app/modules', 
        'app/utils'
    ]
    
    # Check files
    print("📁 Checking required files...")
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
    
    # Check directories
    print("\n📂 Checking required directories...")
    for dir in required_dirs:
        if os.path.exists(dir):
            print(f"  ✅ {dir}/")
        else:
            print(f"  ❌ {dir}/ - MISSING")
    
    # Check API modules
    print("\n🔌 Checking API modules...")
    api_modules = [
        'app/api/monthly_statements.py',
        'app/api/invoices.py',
        'app/api/excel_macros.py',
        'app/api/cc_batch.py'
    ]
    
    for module in api_modules:
        if os.path.exists(module):
            print(f"  ✅ {module}")
        else:
            print(f"  ❌ {module} - MISSING")
    
    # Check utility modules
    print("\n🛠️  Checking utility modules...")
    util_modules = [
        'app/utils/security.py',
        'app/utils/cleanup_manager.py',
        'app/modules/statement_processor.py'
    ]
    
    for module in util_modules:
        if os.path.exists(module):
            print(f"  ✅ {module}")
        else:
            print(f"  ❌ {module} - MISSING")
    
    # Test basic Python syntax
    print("\n🐍 Testing Python syntax...")
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            compile(content, 'app.py', 'exec')
        print("  ✅ app.py - Valid Python syntax")
    except Exception as e:
        print(f"  ❌ app.py - Syntax error: {e}")
    
    # Check requirements.txt
    print("\n📦 Checking requirements...")
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
            essential_packages = ['Flask', 'Flask-CORS', 'openpyxl', 'pandas', 'gunicorn']
            for package in essential_packages:
                if package in requirements:
                    print(f"  ✅ {package}")
                else:
                    print(f"  ❌ {package} - MISSING")
    
    print("\n🚀 Structure Test Complete!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Test locally: python app.py")
    print("3. Deploy to Railway following README.md")
    print("4. Update frontend with your Railway URL")

if __name__ == "__main__":
    test_structure()