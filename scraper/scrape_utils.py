import hashlib
import re
from datetime import datetime

medical_stop_words = [
    # Nursing-related terms
    "Nurse", "Nursing", "LPN", "Nurse Specialist",
    
    # Midwife-related terms
    "Midwife", "Midwives", "Midwifery",
    
    # Pharmacist-related terms
    "Pharmacist", "Pharmacists", "Pharmacy Technician", "Pharmacology", "Pharmacy Assistant", 
    "Pharmacy Dispenser", "Pharmacy Manager", "Pharmacy Intern",
    
    # Consultant-related terms
    "Consultant", "Consultants", "Medical Consultant", "Consulting", "Healthcare Consultant",
    
    # Therapist-related terms
    "Therapist", "Therapists", "Therapy", "Physical Therapist", "Occupational Therapist", 
    "Speech Therapist", "Respiratory Therapist", "Psychotherapist", "Psychotherapy", 
    "Rehabilitation Therapist", "Mental Health Therapist", "Massage Therapist", 
    "Cognitive Behavioral Therapist", "CBT Therapist", "Trauma Therapist",
    
    # Social care-related terms
    "Assistant", "Social care", "Social Worker", "Social Services", "Care Worker", "Support Worker", 
    "Residential Care", "Care Assistant", "Community Care Worker", "Elderly Care", 
    "Child Care Worker", "Home Care Worker", "Case Worker",
    
    # Technical-related terms
    "Technical", "Technician", "X-ray Technician", "MRI Technician", "Ultrasound Technician", 
    "Surgical Technician", "Imaging Technician", "Radiology Technician", "Anesthesia Technician", 
    "Dialysis Technician", "Pathology Technician",
    
    # Pet/Veterinary-related terms
    "Pet", "Pets", "Vet", "Veterinary", "Veterinarian", "Veterinary Technician", 
    "Animal Care", "Animal Hospital", "Animal Health Technician", "Veterinary Assistant", 
    "Vet Nurse", "Pet Care Specialist", "Pet Groomer",
    
    # Volunteer-related terms
    "Volunteer", "Volunteers", "Volunteering", "Volunteer Coordinator", "Voluntary Work", 
    "Volunteer Service", "Charity Volunteer", "Community Volunteer", "Nonprofit Volunteer", 
    "Hospital Volunteer", "Event Volunteer", "Volunteer Worker",
    
    # Dentist-related terms
    "Dental", "Dentist", "Hygienist", "Dental Assistant", "Dental Surgeon", 
    "Orthodontist", "Periodontist", "Oral Surgeon", "Endodontist", "Prosthodontist", 
    "Pediatric Dentist", "Dental Nurse",
    
    # Scientist-related terms
    "Scientist", "Medical Scientist", "Biomedical Scientist", "Laboratory Scientist", 
    "Geneticist", "Biochemist",
    
    # Radiography-related terms
    "Radiographer", "Radiologic Technologist", "Radiology Technician", "Radiologic Technician", 
    "Radiologic Specialist", "X-ray Technologist", "MRI Technologist", "CT Scan Technician", 
    "Diagnostic Radiographer",
    
    # Specialty-related terms
    "Specialty doctor", "Specialty grade doctor", "Specialist Doctor", "Consultant Specialist",
    
    # Psychologist-related terms
    "Psychologist", "Clinical Psychologist", "Counseling Psychologist", 
    "Educational Psychologist", "Neuropsychologist",
    
    # Medical education-related terms
    "Medical lecturer",
    
    # Specialty training-related terms
    "ST5", "ST6", "ST7", "ST8",
    
    # Additional terms
    "Band", "Secretary", "Mammographer", "Coordinator", "Co-ordinator", "Admin", 
    "Administrator", "Audiologist", "Officer", "Engineering", "Prescriber"
]


# Remove Considerable
# Enriched Considerable words list
medical_considerable = [
    # Clinical Fellow (CT)
    "clinical", "medical", "doctor", "fellow", "Clinical Fellow", "(CT)", "Junior Doctor", "Training Doctor", "Core Trainee", 
    "Medical Rotation", "Hospital Placement", "Foundation Training", "Postgraduate Medical Education", 
    "Medical Foundation Trainee", "Training Fellowship", "CT Fellow", "CT Doctor", "Local Employed Doctor", 
    "LED", "Trust Doctor", "ST1/2", "ST1", "ST2", "CT1", "CT2", "FY2", "FY2/CT1", "Medical research", "Clinical research", 
    "Research Fellow",  "Clinical Research Fellow", "Research Clinical Fellow", "Clinical Trainee Fellow", 
    "Postgraduate Fellow", "Core Training Fellow", "Junior Foundation Fellow", "Medical Research Fellow", 
    "Medical Clinical Fellow", "Research Trainee Doctor", "Clinical Doctor Fellow", "ST Fellow", "CT Medical Fellow", 
    "Junior Training Doctor", "Postgraduate Clinical Trainee",

    # Clinical Dev Fellow (FHO2)
    "Clinical Dev Fellow (FHO2)", "Clinical Dev Fellow", "FHO2", "Foundation Year 2", "FY2 Doctor", 
    "Junior Doctor", "Clinical Development", "Medical Trainee", "Postgraduate Training", "Rotation Program", 
    "Medical Education", "Foundation Year Doctor", "Clinical Fellow FY2", "Foundation Trainee", 
    "FHO2 Doctor", "Foundation Doctor FHO2", "Clinical Development Fellow", "Junior Foundation Fellow", 
    "FY2 Trainee Doctor", "Postgraduate FY2 Doctor", "Clinical Doctor FY2", "Junior Medical Fellow", 
    "Clinical Training Fellow",

    # Snr. Clinical Fellow (Spec Reg)
    "Registrar", "training", "trainee", "locum", "non-training", "reg", "Snr. Clinical Fellow (Spec Reg)", 
    "Snr. Clinical Fellow", "Spec Reg", "Specialist Registrar", "Senior Doctor", "Postgraduate Training", 
    "Registrar Grade", "Specialty Training", "Advanced Medical Practice", "Senior Registrar", 
    "Clinical Specialty Registrar", "Senior Medical Fellow", "Registrar in Training", "Registrar Fellowship", 
    "Spec Reg Fellow", "Spec Reg Doctor", "Senior Specialty Registrar", "Senior Trainee Doctor", 
    "Specialty Registrar Fellow", "Senior Registrar Specialist", "Specialist Registrar Doctor", 
    "Higher Specialty Registrar", "ST3", "ST4", "Registrar Specialist", "Senior Clinical Registrar", 
    "Registrar Trainee Fellow", "Registrar Postgraduate Fellow",

    # Clinical Fellow
    "Medical Fellow", "Hospital Doctor", "Postgraduate Training", "Non-training Doctor", 
    "Clinical Attachment", "Junior Doctor", "Medical Education", "Clinical Fellow Training", 
    "Medical Fellowship", "Hospital Fellowship", "Clinical Doctor", "Fellowship Doctor", 
    "Non-training Fellow", "Junior Medical Fellow", "Postgraduate Medical Fellow", 
    "Clinical Doctor Fellow", "Non-trainee Fellow Doctor", "Junior Hospital Fellow", 
    "Postgraduate Clinical Fellow", "Junior Fellowship Doctor", "Training Medical Fellow", 
    "Non-specialty Medical Fellow", "Medical Fellow Trainee",

    # Clinical Teaching Fellow
    "Clinical Teaching Fellow", "Medical Teaching Fellow", "Clinical Teaching", "Medical Teaching", 
    "Medical Educator", "Clinical Instructor", "Academic Fellow", "Clinical Tutor", "Medical Instructor", 
    "Medical Academic", "Teaching Fellow", "Medical Teaching Instructor", "Clinical Education Fellow", 
    "Teaching Medical Students", "Clinical Training Educator", "Clinical Tutor Fellow", 
    "Teaching Medical Fellow", "Clinical Education Doctor", "Medical Educator Fellow", 
    "Academic Clinical Fellow", "Clinical Teaching Program", "Clinical Educator", "Medical Tutor", 
    "Clinical Tutor Doctor", "Clinical Tutor Trainee", "Academic Teaching Doctor", "Clinical Academic Fellow", 
    "Teaching Fellow Doctor", "Medical Academic Fellow", "Clinical Education Training Fellow", 
    "Medical Teaching Practitioner", "Tutor Fellow", "Clinical Teaching Trainee", "Clinical Tutor Instructor", 
    "Clinical Training Fellow", "Teaching Clinical Fellow", "Medical Clinical Educator", 
    "Clinical Lecturer in Medical Education", "Medical Education Fellow", "Medical Training Educator", 
    "Clinical Educator Fellow", "Tutor in Clinical Training", "Medical Education Tutor", 
    "Clinical Lecturer Fellow", "Clinical Tutor Instructor",

    # LAS - FY2 (Locum Appointment for Service - Foundation Year 2)
    "LAS - FY2 (Locum Appointment for Service - Foundation Year 2)", "LAS - FY2", "Locum Appointment for Service", 
    "Locum Appointment for Service - Foundation Year 2", "Locum Doctor", "Temporary Doctor", "Junior Doctor", 
    "Second Year Foundation", "Clinical Rotation", "NHS Doctor", "Medical Placement", "Locum FY2 Doctor", 
    "Foundation Year Locum", "LAS Foundation Doctor", "LAS Locum Doctor", "Locum Foundation Year 2", 
    "Locum Medical Doctor", "Locum NHS Doctor", "Foundation Locum Doctor", "Locum junior doctor", 
    "Locum Medical Fellow", "Junior Locum Doctor", "LAS NHS Doctor", "Locum Doctor FY2", 
    "Foundation Year Locum Doctor", "NHS Locum Doctor", "Temporary FY2 Doctor", "Locum Junior Doctor", 
    "Foundation Locum NHS Doctor", "Locum NHS FY2", "Junior Doctor Locum", "LAS Trainee Doctor", 
    "Foundation Year LAS Doctor", "NHS Junior Locum Doctor", "Locum Doctor in Training", "NHS LAS Trainee",

    # SHO (Senior House Officer)
    "SHO (Senior House Officer)", "SHO", "Senior House Officer", "Junior Doctor", "Postgraduate Training", 
    "Medical Resident", "Hospital Doctor", "Medical Rotation", "Specialty Training", "Intermediate Training", 
    "SHO Doctor", "House Officer", "Senior House Officer Trainee", "SHO Training", "Resident Medical Officer", 
    "Medical House Officer", "House Officer Doctor", "Senior House Officer Fellowship", "Hospital SHO", 
    "SHO Medical Fellow", "House Officer Fellow", "Junior SHO", "Junior House Officer", "SHO Trainee Doctor", 
    "SHO Residency Program", "Senior Hospital SHO", "Senior Resident SHO", "SHO Clinical Fellow", 
    "Postgraduate SHO Doctor", "Junior House Officer Doctor", "SHO Fellowship", "Resident House Officer", 
    "SHO Medical Trainee", "Medical Resident Fellow", "Intermediate SHO Trainee", "Resident SHO Doctor", 
    "Clinical SHO Doctor", "Junior Medical SHO", "Senior Resident Doctor", "Resident Doctor"
]


# Define the array of months
months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Helper functions
def clean_text(text):
    """Cleans and normalizes a text by stripping extra spaces."""
    return ' '.join(text.split()).strip() if text else 'N/A'

def clean_list(text):
    """Converts a block of text into a list of bullet points."""
    if not text:
        return 'N/A'
    # Handle abbreviations with periods correctly
    text = re.sub(r'\b(?:e\.g|i\.e|etc|Dr|Mr|Mrs|Ms|Jr|Sr|vs|Inc|Ltd|Co|Prof|PhD|M\.D|B\.Sc)\.', 
                  lambda m: m.group(0).replace('.', '[DOT]'), text)
    # Create bullet points for each sentence
    return '\n'.join(f"- {sentence.strip()}." for sentence in text.split('.') if sentence.strip()).replace('[DOT]', '.')

# Function to generate a unique ID if reference_number doesn't exist
def generate_unique_id(job_posting):
    """Generates a unique identifier for a job posting."""
    identifier_str = f"{job_posting.title}_{job_posting.employer_name}_{job_posting.location}"
    return hashlib.sha256(identifier_str.encode('utf-8')).hexdigest()

# Function to check if a title contains any stop words
def contains_word(title, words):
    """Returns True if any stop word is found in the title."""
    return any(word.lower() in title.lower() for word in words)

# Function to convert various date formats into the standard format '23 October 2024'
def convert_to_standard_date(date_str):
    """Converts date from various formats (dd/mm/yyyy, '23 October 2024') to '23 October 2024'."""
    try:
        # Handle the case where the date_str is 'N/A' or empty
        if not date_str or date_str == "N/A":
            return "N/A"
        
        # Case 1: Handle dates in format 'dd/mm/yyyy' or 'dd/mm/yyyy hh:mm'
        if '/' in date_str:
            # Remove the time part if it exists
            date_str = date_str.split()[0]
            # Parse the date
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            return date_obj.strftime(f'%-d {months[date_obj.month - 1]} %Y')

        # Case 2: Handle dates in format '23 October 2024'
        elif any(month in date_str for month in months):
            # If the format is already like '23 October 2024', just return it
            return date_str

        else:
            return date_str
    
    except Exception as e:
        print(f"Error: {e}")
        return None
