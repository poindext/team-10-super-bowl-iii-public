#!/usr/bin/env python3
"""
Simple test script for search_trials_tool.
Run this to test the REST API call with authentication.
"""

import os
import sys
from search_trials_tool import search_trials_tool, _get_auth


def test_auth_configuration():
    """Test that authentication is configured correctly."""
    print("=" * 60)
    print("Testing Authentication Configuration")
    print("=" * 60)

    auth = _get_auth()
    if auth is None:
        print("⚠️  WARNING: No authentication configured!")
        print("\nSet one of these environment variables:")
        print("  - IRIS_USERNAME and IRIS_PASSWORD (Basic Auth)")
        print("  - IRIS_BEARER_TOKEN (Bearer Token)")
        print("  - IRIS_API_KEY (API Key)")
        print("\nExample:")
        print("  export IRIS_USERNAME=myuser")
        print("  export IRIS_PASSWORD=mypass")
        return False
    else:
        if isinstance(auth, dict):
            if "Authorization" in auth:
                print("✓ Bearer Token authentication configured")
            elif "X-API-Key" in auth:
                print("✓ API Key authentication configured")
        else:
            print("✓ Basic Authentication configured")
        return True


def test_search_trials():
    """Test the search_trials_tool function."""
    print("\n" + "=" * 60)
    print("Testing search_trials_tool")
    print("=" * 60)

    # Test query
    test_query = "diabetes treatment"
    print(f"\nTest query: '{test_query}'")
    print(f"Max rows: 5")

    try:
        result = search_trials_tool(test_query, maxRows=5)
        print("\n✓ Request successful!")
        print(f"\nResponse type: {type(result)}")
        if isinstance(result, dict):
            print(f"Response keys: {list(result.keys())}")
        elif isinstance(result, list):
            print(f"Response length: {len(result)}")
            if len(result) > 0:
                print(f"First item keys: {list(result[0].keys()) if isinstance(result[0], dict) else 'N/A'}")
        print(f"\nResponse preview:")
        print(str(result)[:500] + "..." if len(str(result)) > 500 else str(result))
        return True
    except Exception as e:
        print(f"\n✗ Request failed: {type(e).__name__}")
        print(f"  Error: {str(e)}")
        if hasattr(e, 'response'):
            print(f"  Status code: {e.response.status_code}")
            print(f"  Response: {e.response.text[:200]}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("IRIS VectorTrialSearch API Test")
    print("=" * 60)

    # Check authentication
    auth_ok = test_auth_configuration()

    if not auth_ok:
        response = input("\nContinue without authentication? (y/n): ")
        if response.lower() != 'y':
            print("\nExiting. Please configure authentication first.")
            sys.exit(1)

    # Test the API call
    success = test_search_trials()

    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Tests failed. Check the error messages above.")
    print("=" * 60 + "\n")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

