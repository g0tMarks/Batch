import openpyxl

def read_student_data_from_excel(file_path, sheet_name="Sheet1"):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook[sheet_name]

    student_data = []

    for row in range(2, sheet.max_row + 1):
        student = {
            "student_name": sheet.cell(row=row, column=1).value,
            "year": sheet.cell(row=row, column=2).value,
            "gender": sheet.cell(row=row, column=3).value,
            "academic_performance": sheet.cell(row=row, column=4).value,
            "extracurricular_activities": sheet.cell(row=row, column=5).value,
            "other": sheet.cell(row=row, column=6).value,
            "sample_report": sheet.cell(row=row, column=7).value,
        }
        student_data.append(student)

    return student_data
