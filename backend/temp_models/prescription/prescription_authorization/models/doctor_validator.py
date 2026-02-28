import pandas as pd

def validate_doctor(registration_number):
    try:
        registry = pd.read_csv('data/doctor_registry.csv')
        return registration_number in registry['registration_number'].values
    except Exception as e:
        raise RuntimeError(f"Doctor validation failed: {e}")