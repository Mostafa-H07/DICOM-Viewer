import pydicom
from pydicom.dataset import Dataset
import os

def anonymize_dicom(filepath, prefix):
    """
    Anonymizes a DICOM file by removing or modifying patient-specific information.
    
    Args:
        filepath (str): Path to the DICOM file to be anonymized.
        prefix (str): Prefix to use for anonymized patient information.
    
    Returns:
        bool: True if anonymization was successful, False otherwise.
    """
    try:
        # Read the DICOM file
        ds = pydicom.dcmread(filepath)
        
        # Anonymize patient information
        ds.PatientName = f"{prefix}_Anonymous"
        ds.PatientID = f"{prefix}_ID"
        ds.PatientBirthDate = "19000101"
        ds.PatientSex = "O"  # Other/Unknown
        
        # List of fields to anonymize
        fields_to_remove = [
            'InstitutionName',
            'ReferringPhysicianName',
            'StudyID',
            'AccessionNumber',
            'PhysiciansOfRecord',
            'PerformingPhysicianName',
            'OperatorsName'
        ]
        
        # Remove identifiable information
        for field in fields_to_remove:
            if hasattr(ds, field):
                delattr(ds, field)
        
        # Save the anonymized DICOM file
        anonymized_filepath = os.path.join(os.path.dirname(filepath), 
                                         f"anonymized_{os.path.basename(filepath)}")
        ds.save_as(anonymized_filepath)
        
        return True
    except Exception as e:
        print(f"Error anonymizing DICOM file: {str(e)}")
        return False