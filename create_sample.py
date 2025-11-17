import pandas as pd
from datetime import datetime

# Create sample data with EXACT column order as specified
data = {
    'current_class_sec': ['Class 9-A', 'Class 10-B', 'Class 8-C'],
    'gr_no': ['2024001', '2024002', '2024003'],
    'student_name': ['Ahmed Ali', 'Fatima Khan', 'Hassan Raza'],
    'father_name': ['Ali Ahmed', 'Muhammad Khan', 'Raza Hussain'],
    'address': ['123 Main St, Karachi', '456 Park Ave, Lahore', '789 School Rd, Islamabad'],
    'contact_number_resident': ['0300-1234567', '0321-9876543', '0333-5555555'],
    'contact_number_neighbour': ['0301-1111111', '0322-2222222', '0334-3333333'],
    'contact_number_relative': ['0302-4444444', '0323-5555555', '0335-6666666'],
    'contact_number_other1': ['', '', ''],
    'contact_number_other2': ['', '', ''],
    'contact_number_other3': ['', '', ''],
    'contact_number_other4': ['', '', ''],
    'date_of_birth': ['2008-01-15', '2007-05-20', '2009-03-10'],
    'joining_date': ['2023-04-01', '2022-08-15', '2024-01-10']
}

df = pd.DataFrame(data)
df.to_excel('student_sample.xlsx', index=False, engine='openpyxl')
print("✓ Sample Excel file created successfully!")
print("\n📋 Columns in exact order:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")
print("\n✅ father_name is column #4, right after student_name")
