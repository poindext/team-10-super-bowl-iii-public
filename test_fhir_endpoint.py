#!/usr/bin/env python3
"""
Test script to query FHIR endpoints from fhir_test_patients.csv
Uses basic authentication (username/password)

Usage:
    Interactive mode:
        python3 test_fhir_endpoint.py
    
    Non-interactive mode (with credentials):
        python3 test_fhir_endpoint.py --username USERNAME --password PASSWORD [--patient-index N]
    
    Using environment variables:
        export FHIR_USERNAME=your_username
        export FHIR_PASSWORD=your_password
        python3 test_fhir_endpoint.py --patient-index 1
"""

import csv
import requests
import json
import sys
import getpass
import os
import argparse
from requests.auth import HTTPBasicAuth


def read_patients_csv(csv_file='fhir_test_patients.csv'):
    """Read patient data from CSV file."""
    patients = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                patients.append({
                    'mpiid': row['MPIID'],
                    'name': row['Name'],
                    'endpoint': row['Endpoint']
                })
        return patients
    except FileNotFoundError:
        print(f"Error: {csv_file} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)


def test_fhir_endpoint(endpoint_url, username, password, timeout=30):
    """Test a FHIR endpoint with basic authentication."""
    print(f"\n{'='*80}")
    print(f"Testing FHIR Endpoint:")
    print(f"URL: {endpoint_url}")
    print(f"{'='*80}\n")
    
    try:
        # Make GET request with basic authentication
        response = requests.get(
            endpoint_url,
            auth=HTTPBasicAuth(username, password),
            headers={
                'Accept': 'application/fhir+json',
                'Content-Type': 'application/fhir+json'
            },
            timeout=timeout
        )
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        print(f"Status Text: {response.reason}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\n{'='*80}")
        print("Response Body:")
        print(f"{'='*80}\n")
        
        # Try to parse as JSON and pretty print
        if response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                json_data = response.json()
                print(json.dumps(json_data, indent=2))
            except json.JSONDecodeError:
                print("Response is not valid JSON:")
                print(response.text[:1000])  # Print first 1000 chars
        else:
            print(response.text[:2000])  # Print first 2000 chars if not JSON
        
        # Check for errors
        if response.status_code == 200:
            print(f"\n{'='*80}")
            print("✅ SUCCESS: Endpoint is accessible and returned data")
            print(f"{'='*80}\n")
            return True
        elif response.status_code == 401:
            print(f"\n{'='*80}")
            print("❌ ERROR: Authentication failed (401 Unauthorized)")
            print("Please check your username and password")
            print(f"{'='*80}\n")
            return False
        elif response.status_code == 404:
            print(f"\n{'='*80}")
            print("❌ ERROR: Resource not found (404)")
            print(f"{'='*80}\n")
            return False
        else:
            print(f"\n{'='*80}")
            print(f"⚠️  WARNING: Unexpected status code: {response.status_code}")
            print(f"{'='*80}\n")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n{'='*80}")
        print("❌ ERROR: Request timed out")
        print(f"{'='*80}\n")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n{'='*80}")
        print("❌ ERROR: Connection error - could not reach the endpoint")
        print(f"{'='*80}\n")
        return False
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        print(f"{'='*80}\n")
        return False


def main():
    """Main function to run the test."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Test FHIR endpoints from fhir_test_patients.csv',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive mode:
    python3 test_fhir_endpoint.py
  
  Non-interactive with credentials:
    python3 test_fhir_endpoint.py --username user --password pass --patient-index 1
  
  Using environment variables:
    export FHIR_USERNAME=user
    export FHIR_PASSWORD=pass
    python3 test_fhir_endpoint.py --patient-index 1
        """
    )
    parser.add_argument('--username', help='FHIR API username')
    parser.add_argument('--password', help='FHIR API password')
    parser.add_argument('--patient-index', type=int, help='Patient index (1-based) to test')
    parser.add_argument('--csv-file', default='fhir_test_patients.csv', help='CSV file with patient data')
    
    args = parser.parse_args()
    
    print("FHIR Endpoint Test Script")
    print("=" * 80)
    
    # Read patients from CSV
    patients = read_patients_csv(args.csv_file)
    
    if not patients:
        print("No patients found in CSV file.")
        sys.exit(1)
    
    # Display available patients
    print(f"\nFound {len(patients)} test patients:\n")
    for i, patient in enumerate(patients, 1):
        print(f"{i}. {patient['name']} (MPIID: {patient['mpiid']})")
    
    # Select patient
    if args.patient_index:
        selection = args.patient_index
        if selection < 1 or selection > len(patients):
            print(f"Invalid patient index {selection}. Using first patient.")
            selection = 1
    else:
        # Interactive selection
        print(f"\nSelect patient to test (1-{len(patients)}, default=1): ", end='')
        try:
            selection_input = input().strip()
            if not selection_input:
                selection = 1
            else:
                selection = int(selection_input)
            
            if selection < 1 or selection > len(patients):
                print(f"Invalid selection. Using first patient.")
                selection = 1
        except (ValueError, KeyboardInterrupt, EOFError):
            print("\nUsing first patient by default.")
            selection = 1
    
    selected_patient = patients[selection - 1]
    endpoint_url = selected_patient['endpoint']
    
    # Get credentials
    username = args.username or os.getenv('FHIR_USERNAME')
    password = args.password or os.getenv('FHIR_PASSWORD')
    
    if not username:
        try:
            username = input("\nEnter FHIR API username: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nError: Username is required. Use --username or set FHIR_USERNAME environment variable.")
            sys.exit(1)
    
    if not password:
        try:
            password = getpass.getpass("Enter FHIR API password: ")
        except (EOFError, KeyboardInterrupt):
            print("\nError: Password is required. Use --password or set FHIR_PASSWORD environment variable.")
            sys.exit(1)
    
    if not username or not password:
        print("Error: Both username and password are required.")
        sys.exit(1)
    
    # Test the endpoint
    success = test_fhir_endpoint(endpoint_url, username, password)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

