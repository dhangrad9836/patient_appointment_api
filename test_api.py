#!/usr/bin/env python
"""
Simple script to test the Patient Appointment API.
Demonstrates common API operations.
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api"

def print_response(response, title):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def test_list_patients():
    """Test listing all patients"""
    response = requests.get(f"{BASE_URL}/patients/")
    print_response(response, "LIST PATIENTS")
    return response.json()

def test_create_patient():
    """Test creating a new patient"""
    patient_data = {
        "patient_id": "PT9999",
        "first_name": "Test",
        "last_name": "Patient",
        "date_of_birth": "1990-01-01",
        "phone": "555-999-9999",
        "email": "test@example.com"
    }
    
    response = requests.post(
        f"{BASE_URL}/patients/",
        json=patient_data,
        headers={"Content-Type": "application/json"}
    )
    print_response(response, "CREATE PATIENT")
    return response.json() if response.status_code == 201 else None

def test_get_patient(patient_id):
    """Test getting patient details"""
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/")
    print_response(response, f"GET PATIENT {patient_id}")
    return response.json()

def test_create_appointment(patient_id_str):
    """Test creating an appointment"""
    # Schedule appointment for tomorrow at 2 PM
    tomorrow = datetime.now() + timedelta(days=1)
    appointment_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    
    appointment_data = {
        "patient_id": patient_id_str,
        "appointment_date": appointment_time.isoformat(),
        "exam_type": "MRI_BRAIN",
        "status": "SCHEDULED",
        "referring_physician": "Dr. Test",
        "clinical_indication": "API test appointment",
        "duration_minutes": 30
    }
    
    response = requests.post(
        f"{BASE_URL}/appointments/",
        json=appointment_data,
        headers={"Content-Type": "application/json"}
    )
    print_response(response, "CREATE APPOINTMENT")
    return response.json() if response.status_code == 201 else None

def test_get_todays_appointments():
    """Test getting today's appointments"""
    response = requests.get(f"{BASE_URL}/appointments/today/")
    print_response(response, "TODAY'S APPOINTMENTS")

def test_get_statistics():
    """Test getting appointment statistics"""
    response = requests.get(f"{BASE_URL}/appointments/statistics/")
    print_response(response, "APPOINTMENT STATISTICS")

def test_search_patients():
    """Test patient search"""
    response = requests.get(f"{BASE_URL}/patients/?search=Test")
    print_response(response, "SEARCH PATIENTS (search=Test)")

def test_filter_appointments():
    """Test filtering appointments"""
    response = requests.get(f"{BASE_URL}/appointments/?exam_type=MRI_BRAIN")
    print_response(response, "FILTER APPOINTMENTS (exam_type=MRI_BRAIN)")

def test_patient_appointments(patient_id):
    """Test getting patient's appointments"""
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/appointments/")
    print_response(response, f"PATIENT {patient_id} APPOINTMENTS")

def test_upcoming_appointments():
    """Test getting upcoming appointments"""
    response = requests.get(f"{BASE_URL}/appointments/upcoming/?days=7")
    print_response(response, "UPCOMING APPOINTMENTS (next 7 days)")

def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("PATIENT APPOINTMENT API - TEST SUITE")
    print("="*60)
    print("\nMake sure the Django server is running on localhost:8000")
    print("Press Enter to continue...")
    input()
    
    try:
        # Test 1: List existing patients
        patients = test_list_patients()
        
        # Test 2: Create a new patient
        new_patient = test_create_patient()
        
        if new_patient:
            patient_id = new_patient['id']
            patient_id_str = new_patient['patient_id']
            
            # Test 3: Get patient details
            test_get_patient(patient_id)
            
            # Test 4: Create appointment for new patient
            new_appointment = test_create_appointment(patient_id_str)
            
            # Test 5: Get patient's appointments
            test_patient_appointments(patient_id)
        
        # Test 6: Today's appointments
        test_get_todays_appointments()
        
        # Test 7: Appointment statistics
        test_get_statistics()
        
        # Test 8: Search patients
        test_search_patients()
        
        # Test 9: Filter appointments
        test_filter_appointments()
        
        # Test 10: Upcoming appointments
        test_upcoming_appointments()
        
        print("\n" + "="*60)
        print("API TESTING COMPLETE!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the API.")
        print("Make sure Django server is running: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()