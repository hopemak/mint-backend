"""
Test Runner - Run all tests
"""

import os
import sys
import subprocess

def run_tests():
    """Run all tests with coverage"""
    print("=" * 60)
    print("🧪 Running Test Suite")
    print("=" * 60)
    
    # Run pytest
    result = subprocess.run(
        ['pytest', '-v', '--cov=app', '--cov-report=term', '--cov-report=html'],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("✅ All tests passed!")
        print("📊 Coverage report: ./htmlcov/index.html")
    else:
        print("❌ Some tests failed!")
    
    print("=" * 60)
    return result.returncode

if __name__ == '__main__':
    sys.exit(run_tests())
