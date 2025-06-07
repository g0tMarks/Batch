import openpyxl
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ExcelParsingError(Exception):
    """Custom exception for Excel parsing errors"""
    pass

def validate_student_data(student: Dict[str, Any]) -> bool:
    """
    Validate that a student record has all required fields and they are not empty
    
    Args:
        student: Dictionary containing student data
        
    Returns:
        bool: True if student data is valid, False otherwise
    """
    required_fields = [
        'student_name',
        'year',
        'gender',
        'adjectives',
        'academic_performance',
        'extracurricular_activities',
        'other',
        'sample_report'
    ]
    
    # Check if all required fields exist and are not empty
    for field in required_fields:
        if field not in student or not student[field]:
            logger.warning(f"Missing or empty required field '{field}' for student {student.get('student_name', 'unknown')}")
            return False
            
    # Validate year is a number
    try:
        year = int(student['year'])
        if year < 7 or year > 12:  # Assuming years 7-12
            logger.warning(f"Invalid year {year} for student {student['student_name']}")
            return False
    except (ValueError, TypeError):
        logger.warning(f"Year must be a number for student {student['student_name']}")
        return False
        
    # Validate gender is one of the expected values
    valid_genders = ['male', 'female', 'other']
    if student['gender'].lower() not in valid_genders:
        logger.warning(f"Invalid gender '{student['gender']}' for student {student['student_name']}")
        return False
        
    return True

def read_student_data_from_excel(file_path: str, sheet_name: str = "Sheet1") -> List[Dict[str, Any]]:
    """
    Read and validate student data from an Excel file
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet to read (default: "Sheet1")
        
    Returns:
        List[Dict[str, Any]]: List of valid student records
        
    Raises:
        ExcelParsingError: If there are issues reading or parsing the file
    """
    try:
        logger.info(f"Reading Excel file: {file_path}")
        workbook = openpyxl.load_workbook(file_path)
        
        if sheet_name not in workbook.sheetnames:
            raise ExcelParsingError(f"Sheet '{sheet_name}' not found in workbook")
            
        sheet = workbook[sheet_name]
        
        # Validate header row
        expected_headers = [
            'Student Name',
            'Year',
            'Gender',
            'Adjectives',
            'Academic Performance',
            'Extracurricular Activities',
            'Other',
            'Sample Report'
        ]
        
        headers = [cell.value for cell in sheet[1]]
        if headers != expected_headers:
            raise ExcelParsingError(f"Invalid headers. Expected: {expected_headers}, Got: {headers}")
        
        valid_students = []
        skipped_rows = []
        
        for row in range(2, sheet.max_row + 1):
            try:
                student = {
                    "student_name": sheet.cell(row=row, column=1).value,
                    "year": sheet.cell(row=row, column=2).value,
                    "gender": sheet.cell(row=row, column=3).value,
                    "adjectives": sheet.cell(row=row, column=4).value,
                    "academic_performance": sheet.cell(row=row, column=5).value,
                    "extracurricular_activities": sheet.cell(row=row, column=6).value,
                    "other": sheet.cell(row=row, column=7).value,
                    "sample_report": sheet.cell(row=row, column=8).value,
                }
                
                # Skip empty rows
                if all(value is None for value in student.values()):
                    logger.debug(f"Skipping empty row {row}")
                    continue
                    
                # Validate student data
                if validate_student_data(student):
                    valid_students.append(student)
                    logger.debug(f"Added valid student data for {student['student_name']}")
                else:
                    skipped_rows.append(row)
                    logger.warning(f"Skipping invalid student data in row {row}")
                    
            except Exception as e:
                logger.error(f"Error processing row {row}: {str(e)}")
                skipped_rows.append(row)
                
        if skipped_rows:
            logger.warning(f"Skipped {len(skipped_rows)} rows due to invalid data: {skipped_rows}")
            
        if not valid_students:
            raise ExcelParsingError("No valid student data found in the file")
            
        logger.info(f"Successfully parsed {len(valid_students)} valid student records")
        return valid_students
        
    except Exception as e:
        logger.error(f"Error reading Excel file: {str(e)}")
        raise ExcelParsingError(f"Failed to read Excel file: {str(e)}")
