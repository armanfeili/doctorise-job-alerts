import hashlib
import re

# Enriched list of medical stop words
medical_stop_words = [
    # Nursing-related terms
    "Nurse", "Nurses", "Nursing", "Registered Nurse", "Staff Nurse", "Nurse Practitioner", "Nurse Manager",
    
    # Midwife-related terms
    "Midwife", "Midwives", "Midwifery",
    
    # Pharmacist-related terms
    "Pharmacist", "Pharmacists", "Pharmacy Technician", "Pharmaceutical", "Pharmacology", "Pharmacy Assistant",
    
    # Consultant-related terms
    "Consultant", "Consultants", "Medical Consultant", "Consulting",
    
    # Therapist-related terms
    "Therapist", "Therapists", "Therapy", "Physical Therapist", "Occupational Therapist", "Speech Therapist", 
    "Respiratory Therapist", "Psychotherapist", "Psychotherapy", "Rehabilitation Therapist",
    
    # Social care-related terms
    "Social care", "Social Worker", "Social Services", "Care Worker", "Support Worker", "Residential Care", "Care Assistant",
    
    # Technical-related terms
    "Technical", "Technician", "Biomedical Technician", "Medical Technician", "Laboratory Technician", "X-ray Technician", 
    "MRI Technician", "Ultrasound Technician", "Surgical Technician", "Imaging Technician",
    
    # Pet/Veterinary-related terms
    "Pet", "Pets", "Vet", "Veterinary", "Veterinarian", "Veterinary Technician", "Animal Care", "Animal Hospital",
    
    # Volunteer-related terms
    "Volunteer", "Volunteers", "Volunteering", "Volunteer Coordinator", "Voluntary Work", "Volunteer Service", "Charity Volunteer"
]

# Enriched Considerable words list
medical_considerable = [
    # Clinical Fellow (CT)
    "Clinical Fellow (CT)", "Clinical Fellow", "(CT)", "Junior Doctor", "Training Doctor", "Core Trainee", 
    "Medical Rotation", "Hospital Placement", "Foundation Training", "Postgraduate Medical Education", 
    "Clinical Trainee", "Clinical Training", "Clinical Doctor", "Foundation Doctor", 
    "Medical Foundation Trainee", "Training Fellowship", "CT Fellow", "CT Doctor",
    
    # Clinical Dev Fellow (FHO2)
    "Clinical Dev Fellow (FHO2)", "Clinical Dev Fellow", "FHO2", "Foundation Year 2", "FY2 Doctor", 
    "Junior Doctor", "Clinical Development", "Medical Trainee", "Postgraduate Training", 
    "Rotation Program", "Medical Education", "Foundation Year Doctor", "Clinical Fellow FY2", 
    "Foundation Trainee", "FHO2 Doctor", "Foundation Doctor FHO2",
    
    # Snr. Clinical Fellow (Spec Reg)
    "Snr. Clinical Fellow (Spec Reg)", "Snr. Clinical Fellow", "Spec Reg", "Specialist Registrar", 
    "Senior Doctor", "Postgraduate Training", "Registrar Grade", "Specialty Training", 
    "Higher Specialist Training", "Advanced Medical Practice", "Senior Specialist", 
    "Senior Registrar", "Clinical Specialty Registrar", "Senior Medical Fellow", 
    "Registrar in Training", "Registrar Fellowship", "Spec Reg Fellow", "Spec Reg Doctor", "Senior Specialty Registrar",
    
    # Clinical Fellow
    "Clinical Fellow", "Medical Fellow", "Hospital Doctor", "Postgraduate Training", 
    "Non-training Doctor", "Clinical Attachment", "Junior Doctor", "Medical Education", 
    "Clinical Fellow Training", "Medical Fellowship", "Hospital Fellowship", 
    "Clinical Doctor", "Fellowship Doctor", "Non-training Fellow", "Junior Medical Fellow",
    
    # Clinical Teaching Fellow
    "Clinical Teaching Fellow", "Medical Teaching Fellow", "Clinical Teaching", "Medical Teaching", 
    "Medical Educator", "Clinical Instructor", "Academic Fellow", "Clinical Tutor", 
    "Medical Instructor", "Medical Academic", "Medical Lecturer", "Teaching Fellow", 
    "Medical Teaching Instructor", "Clinical Education Fellow", "Teaching Medical Students", 
    "Clinical Training Educator", "Clinical Tutor Fellow", "Teaching Medical Fellow",
    
    # LAS - FY2 (Locum Appointment for Service - Foundation Year 2)
    "LAS - FY2 (Locum Appointment for Service - Foundation Year 2)", "LAS - FY2", 
    "Locum Appointment for Service", "Locum Appointment for Service - Foundation Year 2", 
    "Locum Doctor", "Temporary Doctor", "Junior Doctor", "Second Year Foundation", 
    "Clinical Rotation", "NHS Doctor", "Medical Placement", "Locum FY2 Doctor", 
    "Foundation Year Locum", "LAS Foundation Doctor", "LAS Locum Doctor", 
    "Locum Foundation Year 2", "Locum Medical Doctor", "Locum NHS Doctor", "Foundation Locum Doctor",
    
    # SHO (Senior House Officer)
    "SHO (Senior House Officer)", "SHO", "Senior House Officer", 
    "Junior Doctor", "Postgraduate Training", "Medical Resident", 
    "Hospital Doctor", "Medical Rotation", "Specialty Training", "Intermediate Training", 
    "SHO Doctor", "House Officer", "Senior House Officer Trainee", 
    "SHO Training", "Resident Medical Officer", "Medical House Officer", 
    "House Officer Doctor", "Senior House Officer Fellowship", "Hospital SHO"
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
