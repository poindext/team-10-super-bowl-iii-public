"""
Utility module for reading patient data from CSV file.
"""

import csv
import os
from typing import Dict, Optional


def get_patient_endpoint(mpiid: str, csv_file: str = "fhir_test_patients.csv") -> Optional[Dict[str, str]]:
    """
    Get patient endpoint information from CSV file based on MPIID.
    
    Args:
        mpiid: Patient MPIID
        csv_file: Path to CSV file (default: fhir_test_patients.csv)
        
    Returns:
        Dictionary with 'mpiid', 'name', and 'endpoint' keys, or None if not found
    """
    # Get the project root directory (parent of src/)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(project_root, csv_file)
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['MPIID'] == mpiid:
                    return {
                        'mpiid': row['MPIID'],
                        'name': row['Name'],
                        'endpoint': row['Endpoint']
                    }
        return None
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None


def get_all_patients(csv_file: str = "fhir_test_patients.csv") -> list:
    """
    Get all patients from CSV file.
    
    Args:
        csv_file: Path to CSV file (default: fhir_test_patients.csv)
        
    Returns:
        List of dictionaries with patient information
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(project_root, csv_file)
    
    patients = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                patients.append({
                    'mpiid': row['MPIID'],
                    'name': row['Name'],
                    'endpoint': row['Endpoint']
                })
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    return patients

