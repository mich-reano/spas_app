import os
from io import BytesIO
import base64
import json
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing, Line

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="ReaMic Scholar", page_icon="./images/reamicscholar_minilogo.png", layout="wide")

# ---------------------------
# Grade and Subject Configuration
# ---------------------------
GRADES = {
    'Grade 4': ['MAT', 'ENG', 'KIS', 'SCI', 'SST', 'C/ARTS'],
    'Grade 5': ['MAT', 'ENG', 'KIS', 'SCI', 'SST', 'C/ARTS'],
    'Grade 6': ['MAT', 'ENG', 'KIS', 'SCI', 'SST', 'C/ARTS'],
    'Grade 7': ['MAT', 'ENG', 'KIS', 'PRET', 'SST', 'AGR/N', 'C/ARTS', 'CRE', 'INT/SCI'],
    'Grade 8': ['MAT', 'ENG', 'KIS', 'PRET', 'SST', 'AGR/N', 'C/ARTS', 'CRE', 'INT/SCI'],
    'Grade 9': ['MAT', 'ENG', 'KIS', 'PRET', 'SST', 'AGR/N', 'C/ARTS', 'CRE', 'INT/SCI'],
}

DATA_PATH = "data"
USERS_FILE = os.path.join(DATA_PATH, "users.json")
STUDENTS_FILE = os.path.join(DATA_PATH, "students.json")
MARKS_FILE = os.path.join(DATA_PATH, "marks.json")

# ---------------------------
# User Management Functions
# ---------------------------
def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                content = f.read().strip()
                if not content:  # Empty file
                    raise ValueError("Empty file")
                return json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            # File is corrupted or empty, create default
            st.warning(f"⚠️ users.json file was corrupted or empty. Creating new default admin user.")
            default_users = {
                "admin": {
                    "password": "admin123",
                    "role": "admin",
                    "name": "System Administrator"
                }
            }
            save_users(default_users)
            return default_users
    else:
        # Default admin user
        default_users = {
            "admin": {
                "password": "admin123",
                "role": "admin",
                "name": "System Administrator"
            }
        }
        save_users(default_users)
        return default_users

def save_users(users):
    """Save users to JSON file"""
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def authenticate_user(username, password):
    """Authenticate user credentials"""
    users = load_users()
    if username in users and users[username]['password'] == password:
        return users[username]
    return None

def add_teacher(username, password, name, assignments):
    """
    Add a new teacher to the system with specific grade-subject-stream assignments
    assignments: list of dicts like [{"grade": "Grade 4", "subject": "MAT", "stream": "H"}, ...]
    """
    users = load_users()
    if username in users:
        return False, "Username already exists"
    
    # Extract unique subjects and grades from assignments
    subjects = list(set([a['subject'] for a in assignments]))
    grades = list(set([a['grade'] for a in assignments]))
    
    users[username] = {
        "password": password,
        "role": "teacher",
        "name": name,
        "subjects": subjects,  # For backward compatibility
        "grades": grades,  # For backward compatibility
        "assignments": assignments  # New detailed assignment structure
    }
    save_users(users)
    return True, "Teacher added successfully"

def delete_teacher(username):
    """Delete a teacher from the system"""
    users = load_users()
    
    if username not in users:
        return False, "Teacher not found"
    
    if users[username]['role'] != 'teacher':
        return False, "User is not a teacher"
    
    if 'username' in st.session_state and st.session_state.username == username:
        return False, "Cannot delete currently logged-in user"
    
    teacher_name = users[username]['name']
    del users[username]
    save_users(users)
    
    return True, f"Teacher {teacher_name} (@{username}) deleted successfully"


# ---------------------------
# Student Management Functions
# ---------------------------
def load_students():
    """Load students from JSON file"""
    if os.path.exists(STUDENTS_FILE):
        try:
            with open(STUDENTS_FILE, 'r') as f:
                content = f.read().strip()
                if not content:  # Empty file
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            # File is corrupted, return empty and show warning
            st.warning(f"⚠️ students.json file was corrupted. Starting with empty student list. Error: {str(e)}")
            return {}
    return {}

def save_students(students):
    """Save students to JSON file"""
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(STUDENTS_FILE, 'w') as f:
        json.dump(students, f, indent=2)

def add_student(adm_no, name, gender, grade, stream):
    """Add a new student to the system"""
    students = load_students()
    
    # For grades 4-6, use initials as admission number if not provided
    if grade in ['Grade 4', 'Grade 5', 'Grade 6']:
        if not adm_no:
            # Generate admission number from name initials
            words = name.strip().split()
            initials = ''.join([word[0].upper() for word in words if word])
            
            # Make unique by adding stream and number if needed
            base_adm = f"{initials}-{stream}"
            adm_no = base_adm
            counter = 1
            
            # Check for duplicates and add number if needed
            while adm_no in students:
                adm_no = f"{base_adm}{counter}"
                counter += 1
        
        # Check if student with same name and grade exists
        for existing_adm, existing_data in students.items():
            if (existing_data['name'].lower() == name.lower() and 
                existing_data['grade'] == grade and 
                existing_data['stream'] == stream and
                existing_adm != adm_no):
                return False, "A student with this name already exists in this grade and stream"
    else:  # Grades 7-9 require admission number
        if not adm_no:
            return False, "Admission number is required for Junior Secondary (Grades 7-9)"
        
        if adm_no in students:
            return False, "Admission number already exists"
    
    students[adm_no] = {
        "name": name,
        "gender": gender,
        "grade": grade,
        "stream": stream,
        "created_at": datetime.now().isoformat()
    }
    save_students(students)
    return True, f"Student added successfully with admission number: {adm_no}"

def delete_student(adm_no):
    """Delete a student from the system"""
    students = load_students()
    
    if adm_no not in students:
        return False, "Student not found"
    
    student_name = students[adm_no]['name']
    del students[adm_no]
    save_students(students)
    
    marks = load_marks()
    marks_deleted = 0
    for exam_key in marks.keys():
        if adm_no in marks[exam_key]:
            del marks[exam_key][adm_no]
            marks_deleted += 1
    
    if marks_deleted > 0:
        save_marks(marks)
    
    return True, f"Student {student_name} (ADM NO: {adm_no}) deleted successfully. {marks_deleted} exam record(s) also removed."

# ---------------------------
# Marks Management Functions
# ---------------------------
def load_marks():
    """Load marks from JSON file"""
    if os.path.exists(MARKS_FILE):
        try:
            with open(MARKS_FILE, 'r') as f:
                content = f.read().strip()
                if not content:  # Empty file
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            # File is corrupted, return empty and show warning
            st.warning(f"⚠️ marks.json file was corrupted. Starting with empty marks. Error: {str(e)}")
            return {}
    return {}

def save_marks(marks):
    """Save marks to JSON file"""
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(MARKS_FILE, 'w') as f:
        json.dump(marks, f, indent=2)

def enter_marks(adm_no, subject, grade, term, year, exam_type, score, teacher_username):
    """Enter marks for a student"""
    marks = load_marks()
    
    # Create unique key for this exam instance
    exam_key = f"{grade}_{term}_{year}_{exam_type}"
    
    if exam_key not in marks:
        marks[exam_key] = {}
    
    if adm_no not in marks[exam_key]:
        marks[exam_key][adm_no] = {}
    
    marks[exam_key][adm_no][subject] = {
        "score": score,
        "entered_by": teacher_username,
        "entered_at": datetime.now().isoformat()
    }
    
    save_marks(marks)
    return True, "Marks entered successfully"

def get_exam_marks(grade, term, year, exam_type):
    """Get all marks for a specific exam"""
    marks = load_marks()
    exam_key = f"{grade}_{term}_{year}_{exam_type}"
    return marks.get(exam_key, {})

def get_marks_entry_progress(grade, term, year, exam_type):
    """Get progress of marks entry by teachers"""
    students = load_students()
    marks = load_marks()
    users = load_users()
    
    exam_key = f"{grade}_{term}_{year}_{exam_type}"
    exam_marks = marks.get(exam_key, {})
    
    # Get all students in this grade
    grade_students = {adm: data for adm, data in students.items() if data['grade'] == grade}
    
    # Get all teachers
    teachers = {username: data for username, data in users.items() if data['role'] == 'teacher' and grade in data.get('grades', [])}
    
    progress = {}
    for teacher_username, teacher_data in teachers.items():
        teacher_subjects = teacher_data.get('subjects', [])
        total_entries_needed = len(grade_students) * len([s for s in teacher_subjects if s in GRADES[grade]])
        entries_made = 0
        
        for adm_no in grade_students.keys():
            if adm_no in exam_marks:
                for subject in teacher_subjects:
                    if subject in exam_marks[adm_no]:
                        entries_made += 1
        
        progress[teacher_username] = {
            "name": teacher_data['name'],
            "subjects": teacher_subjects,
            "total_needed": total_entries_needed,
            "completed": entries_made,
            "percentage": (entries_made / total_entries_needed * 100) if total_entries_needed > 0 else 0
        }
    
    return progress

# ---------------------------
# Data Preparation Functions
# ---------------------------
def get_subject_performance_level(score):
    """Get performance level and points for individual subject (0-100 marks)"""
    try:
        s = float(score)
    except Exception:
        return 'BE2', 1
    
    if s >= 90:
        return 'EE1', 8
    elif s >= 78:
        return 'EE2', 7
    elif s >= 65:
        return 'ME1', 6
    elif s >= 52:
        return 'ME2', 5
    elif s >= 39:
        return 'AE1', 4
    elif s >= 26:
        return 'AE2', 3
    elif s >= 13:
        return 'BE1', 2
    else:
        return 'BE2', 1

def get_primary_performance_level(total_score):
    """Get performance level and points for Primary (Grade 4-6) - 6 subjects, max 600"""
    try:
        s = float(total_score)
    except Exception:
        return 'BE2', 1
    
    if s >= 532:
        return 'EE1', 8
    elif s >= 456:
        return 'EE2', 7
    elif s >= 380:
        return 'ME1', 6
    elif s >= 304:
        return 'ME2', 5
    elif s >= 228:
        return 'AE1', 4
    elif s >= 152:
        return 'AE2', 3
    elif s >= 76:
        return 'BE1', 2
    else:
        return 'BE2', 1

def get_junior_performance_level(total_score):
    """Get performance level and points for Junior Secondary (Grade 7-9) - 9 subjects, max 900"""
    try:
        s = float(total_score)
    except Exception:
        return 'BE2', 1
    
    if s >= 798:
        return 'EE1', 8
    elif s >= 684:
        return 'EE2', 7
    elif s >= 570:
        return 'ME1', 6
    elif s >= 456:
        return 'ME2', 5
    elif s >= 342:
        return 'AE1', 4
    elif s >= 228:
        return 'AE2', 3
    elif s >= 114:
        return 'BE1', 2
    else:
        return 'BE2', 1

def get_performance_level_for_grade(total_score, grade):
    """Get appropriate performance level based on grade"""
    if grade in ['Grade 4', 'Grade 5', 'Grade 6']:
        return get_primary_performance_level(total_score)
    else:  # Grade 7, 8, 9
        return get_junior_performance_level(total_score)

def get_performance_level(score):
    """Legacy function for backwards compatibility - uses subject-level grading"""
    level, _ = get_subject_performance_level(score)
    return level

def get_performance_label(level):
    labels = {
        'EE1': 'Exceeding Expectation 1',
        'EE2': 'Exceeding Expectation 2',
        'ME1': 'Meeting Expectation 1',
        'ME2': 'Meeting Expectation 2',
        'AE1': 'Approaching Expectation 1',
        'AE2': 'Approaching Expectation 2',
        'BE1': 'Below Expectation 1',
        'BE2': 'Below Expectation 2',
        # Legacy support
        'EE': 'Exceeding Expectation',
        'ME': 'Meeting Expectation',
        'AE': 'Approaching Expectation',
        'BE': 'Below Expectation'
    }
    return labels.get(level, level)

def prepare_grade_data(grade, term, year, exam_type):
    """Prepare DataFrame from students and marks data"""
    students = load_students()
    marks = load_marks()
    
    exam_key = f"{grade}_{term}_{year}_{exam_type}"
    exam_marks = marks.get(exam_key, {})
    
    # Filter students for this grade
    grade_students = {adm: data for adm, data in students.items() if data['grade'] == grade}
    
    if not grade_students:
        return pd.DataFrame()
    
    subject_cols = GRADES[grade]
    
    # Build DataFrame
    rows = []
    for adm_no, student_data in grade_students.items():
        row = {
            'ADM NO.': adm_no,
            'NAME OF STUDENTS': student_data['name'],
            'GENDER': student_data['gender'],
            'STRM': student_data['stream']
        }
        
        # Add subject marks and calculate subject points
        subject_points_total = 0
        for subject in subject_cols:
            if adm_no in exam_marks and subject in exam_marks[adm_no]:
                score = float(exam_marks[adm_no][subject]['score'])
                row[subject] = score
                # Get subject-level points
                _, points = get_subject_performance_level(score)
                subject_points_total += points
            else:
                row[subject] = 0.0
                subject_points_total += 1  # BE2 default
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    if df.empty:
        return df
    
    # Calculate totals and rankings
    df['TOTAL'] = df[subject_cols].sum(axis=1)
    df['AVERAGE'] = df['TOTAL'] / len(subject_cols)
    
    # Get performance level and points based on total score and grade
    perf_data = df.apply(lambda row: get_performance_level_for_grade(row['TOTAL'], grade), axis=1)
    df['P.LEVEL'] = perf_data.apply(lambda x: x[0])
    df['POINTS'] = perf_data.apply(lambda x: x[1])
    
    # Legacy column for compatibility
    df['AV/LVL'] = df['P.LEVEL']
    
    df['RANK'] = df['TOTAL'].rank(ascending=False, method='dense').astype(int)
    
    return df

# ---------------------------
# PDF Functions (same as original)
# ---------------------------
def create_pdf_report(student, school_name, grade, term, year, exam_type, df,
                                    class_teacher, dhoi, hoi, subject_cols):
    """
    Create a professional, CBC-compliant report card
    Fits on one A4 page with proper formatting
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=30,
        bottomMargin=30
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ============================================
    # CUSTOM STYLES
    # ============================================
    
    school_name_style = ParagraphStyle(
        'SchoolName',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Times-Bold',
        textColor=colors.HexColor('#1a3a5c'),
        alignment=TA_CENTER,
        spaceAfter=2
    )
    
    school_info_style = ParagraphStyle(
        'SchoolInfo',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    title_bar_style = ParagraphStyle(
        'TitleBar',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Times-Bold',
        textColor=colors.white,
        alignment=TA_CENTER
    )
    
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Times-Bold',
        textColor=colors.HexColor('#1a3a5c'),
        spaceAfter=4,
        spaceBefore=6
    )
    
    body_text_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        textColor=colors.black
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    
    # ============================================
    # SCHOOL HEADER
    # ============================================
    
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(school_name.upper(), school_name_style))
    elements.append(Paragraph("P.O. Box 3-40308, SINDO, KENYA", school_info_style))
    elements.append(Paragraph("Tel: +254 710 302846 | Email: sindocomprehensive@gmail.com", school_info_style))
    
    # Blue title bar
    title_data = [[Paragraph("STUDENT PERFORMANCE REPORT", title_bar_style)]]
    title_table = Table(title_data, colWidths=[7.5*inch])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a3a5c')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 8))
    
    # ============================================
    # EXAM DETAILS & LEARNER INFO
    # ============================================
    
    info_data = [
        [Paragraph(f"<b>Term:</b> {term}", body_text_style),
         Paragraph(f"<b>Year:</b> {year}", body_text_style),
         Paragraph(f"<b>Examination:</b> {exam_type}", body_text_style)],
        [Paragraph(f"<b>Grade/Class:</b> {grade}", body_text_style),
         Paragraph(f"<b>Stream:</b> {'Heroes (H)' if student.get('STRM') == 'H' else 'Champions (C)'}", body_text_style),
         ""]
    ]
    
    info_table = Table(info_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6))
    
    # Separator
    sep1 = Drawing(7.5*inch, 1)
    sep1.add(Line(0, 0, 7.5*inch, 0, strokeColor=colors.HexColor('#1a3a5c'), strokeWidth=0.8))
    elements.append(sep1)
    elements.append(Spacer(1, 6))
    
    # Learner details
    learner_data = [
        [Paragraph("<b>Learner Name:</b>", body_text_style), 
         Paragraph(str(student.get('NAME OF STUDENTS', '')), body_text_style),
         Paragraph("<b>Admission No:</b>", body_text_style),
         Paragraph(str(student.get('ADM NO.', '')), body_text_style)],
        [Paragraph("<b>Gender:</b>", body_text_style),
         Paragraph(str(student.get('GENDER', '')), body_text_style),
         Paragraph("<b>Class Rank:</b>", body_text_style),
         Paragraph(f"{student.get('RANK', '')}/{len(df)}", body_text_style)]
    ]
    
    learner_table = Table(learner_data, colWidths=[1.3*inch, 2.45*inch, 1.3*inch, 2.45*inch])
    learner_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(learner_table)
    elements.append(Spacer(1, 8))
    
    # ============================================
    # LEARNING AREAS PERFORMANCE
    # ============================================
    
    elements.append(Paragraph("LEARNING AREAS PERFORMANCE", section_heading_style))
    
    perf_header = ['Learning Area', 'Score (%)', 'P.Level', 'Points']
    perf_data = [perf_header]
    
    for subj in subject_cols:
        score = float(student.get(subj, 0))
        perf_level, points = get_subject_performance_level(score)
        perf_data.append([subj, f"{score:.0f}", perf_level, str(points)])
    
    perf_table = Table(perf_data, colWidths=[3.2*inch, 1.4*inch, 1.4*inch, 1.5*inch])
    perf_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Data
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        # Styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(perf_table)
    elements.append(Spacer(1, 8))
    
    # ============================================
    # OVERALL PERFORMANCE SUMMARY
    # ============================================
    
    elements.append(Paragraph("OVERALL PERFORMANCE SUMMARY", section_heading_style))
    
    summary_data = [
        [Paragraph("<b>Total Score:</b>", body_text_style), 
         f"{student.get('TOTAL', 0):.0f}",
         Paragraph("<b>Average Score:</b>", body_text_style),
         f"{student.get('AVERAGE', 0):.1f}%"],
        [Paragraph("<b>Overall P.Level:</b>", body_text_style),
         student.get('P.LEVEL', 'N/A'),
         Paragraph("<b>Points:</b>", body_text_style),
         str(student.get('POINTS', 0))],
        [Paragraph("<b>Class Position:</b>", body_text_style),
         f"{student.get('RANK', '')}/{len(df)}",
         Paragraph("<b>Class Average:</b>", body_text_style),
         f"{df['AVERAGE'].mean():.1f}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[1.9*inch, 1.85*inch, 1.9*inch, 1.85*inch])
    summary_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 8))
    
    # ============================================
    # CLASS TEACHER'S COMMENT
    # ============================================
    
    elements.append(Paragraph("CLASS TEACHER'S COMMENT", section_heading_style))
    
    points_val = student.get('POINTS', 0)
    if points_val >= 7:
        comment = "Excellent performance! The learner demonstrates outstanding mastery of learning outcomes. Keep up the exceptional work."
    elif points_val >= 5:
        comment = "Good performance. The learner shows satisfactory understanding of key concepts. Continue working hard to excel further."
    elif points_val >= 3:
        comment = "Fair performance. The learner is making progress but needs more effort to fully grasp learning outcomes. Additional support recommended."
    else:
        comment = "The learner requires significant support to meet expected learning outcomes. Remedial assistance and closer monitoring advised."
    
    comment_para = Paragraph(comment, body_text_style)
    comment_data = [[comment_para]]
    comment_table = Table(comment_data, colWidths=[7.5*inch])
    comment_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(comment_table)
    elements.append(Spacer(1, 8))
    
    # ============================================
    # AUTHENTICATION & SIGN-OFF
    # ============================================
    
    elements.append(Paragraph("AUTHENTICATION", section_heading_style))
    
    auth_data = [
        [Paragraph("<b>Class Teacher:</b>", body_text_style), class_teacher,
         Paragraph("<b>Signature:</b>", body_text_style), "________________"],
        [Paragraph("<b>DHOI:</b>", body_text_style), dhoi,
         Paragraph("<b>Signature:</b>", body_text_style), "________________"],
        [Paragraph("<b>HOI:</b>", body_text_style), hoi,
         Paragraph("<b>Signature:</b>", body_text_style), "________________"],
        [Paragraph("<b>School Stamp:</b>", body_text_style), "",
         Paragraph("<b>Date:</b>", body_text_style), "________________"]
    ]
    
    auth_table = Table(auth_data, colWidths=[1.5*inch, 2.4*inch, 1.4*inch, 2.2*inch])
    auth_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(auth_table)
    elements.append(Spacer(1, 8))
    
    # ============================================
    # FOOTER
    # ============================================
    
    sep2 = Drawing(7.5*inch, 1)
    sep2.add(Line(0, 0, 7.5*inch, 0, strokeColor=colors.HexColor('#cccccc'), strokeWidth=0.5))
    elements.append(sep2)
    elements.append(Spacer(1, 3))
    
    elements.append(Paragraph(
        "Powered by ReaMic Institute for Applied Intelligence • Advancing Intelligence for Real world Impact.| +254 741 908009",
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
    return buffer

def create_class_list_pdf(df, school_name, grade, term, year, exam_type, class_teacher, subject_cols):
    """Create professional class list PDF in landscape orientation with matching header"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=25,
        bottomMargin=25
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ============================================
    # CUSTOM STYLES (matching student report)
    # ============================================
    
    school_name_style = ParagraphStyle(
        'SchoolName',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Times-Bold',
        textColor=colors.HexColor('#1a3a5c'),
        alignment=TA_CENTER,
        spaceAfter=2
    )
    
    school_info_style = ParagraphStyle(
        'SchoolInfo',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=4
    )
    
    title_bar_style = ParagraphStyle(
        'TitleBar',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Times-Bold',
        textColor=colors.white,
        alignment=TA_CENTER
    )
    
    body_text_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        textColor=colors.black
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=6,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    
    # ============================================
    # SCHOOL HEADER (matching student report)
    # ============================================
    
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(school_name.upper(), school_name_style))
    elements.append(Paragraph("P.O. Box 3-40308, SINDO, KENYA", school_info_style))
    elements.append(Paragraph("Tel: +254 710 302846 | Email: sindocomprehensive@gmail.com", school_info_style))
    
    # Blue title bar
    title_data = [[Paragraph("CLASS PERFORMANCE LIST", title_bar_style)]]
    title_table = Table(title_data, colWidths=[10.7*inch])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a3a5c')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 6))
    
    # ============================================
    # EXAM DETAILS
    # ============================================
    
    info_data = [
        [Paragraph(f"<b>Grade/Class:</b> {grade}", body_text_style),
         Paragraph(f"<b>Term:</b> {term}", body_text_style),
         Paragraph(f"<b>Year:</b> {year}", body_text_style),
         Paragraph(f"<b>Examination:</b> {exam_type}", body_text_style)]
    ]
    
    info_table = Table(info_data, colWidths=[2.7*inch, 2.7*inch, 2.7*inch, 2.6*inch])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4))
    
    # Separator
    sep1 = Drawing(10.7*inch, 1)
    sep1.add(Line(0, 0, 10.7*inch, 0, strokeColor=colors.HexColor('#1a3a5c'), strokeWidth=0.8))
    elements.append(sep1)
    elements.append(Spacer(1, 6))
    
    # ============================================
    # CLASS PERFORMANCE TABLE
    # ============================================
    
    sorted_df = df.sort_values('RANK')
    
    header = ['Rank', 'ADM NO.', 'Name', 'Gender', 'Strm'] + subject_cols + ['Total', 'Avg', 'P.Level', 'Pts']
    table_data = [header]
    
    for _, row in sorted_df.iterrows():
        perf_level = row.get('P.LEVEL', 'BE2')
        points = row.get('POINTS', 1)
        row_data = [
            str(row['RANK']), 
            str(row.get('ADM NO.', '')), 
            str(row.get('NAME OF STUDENTS', ''))[:25],
            str(row.get('GENDER', '')), 
            str(row.get('STRM', ''))
        ]
        for subj in subject_cols:
            row_data.append(f"{row.get(subj, 0):.0f}")
        row_data.extend([
            f"{row.get('TOTAL', 0):.0f}", 
            f"{row.get('AVERAGE', 0):.1f}", 
            perf_level, 
            str(points)
        ])
        table_data.append(row_data)
    
    # Calculate column widths
    num_subjects = len(subject_cols)
    base_widths = [0.3*inch, 0.6*inch, 1.5*inch, 0.3*inch, 0.3*inch]
    subject_widths = [0.4*inch] * num_subjects
    end_widths = [0.45*inch, 0.4*inch, 0.45*inch, 0.3*inch]
    col_widths = base_widths + subject_widths + end_widths
    
    class_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    class_table.setStyle(TableStyle([
        # Header row (matching blue color)
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        # Borders and alternating rows (matching student report)
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    
    elements.append(class_table)
    elements.append(Spacer(1, 8))
    
    # ============================================
    # CBC GRADING KEY
    # ============================================
    
    legend_title = Paragraph("<b> PERFORMANCE LEVEL KEY</b>", body_text_style)
    elements.append(legend_title)
    elements.append(Spacer(1, 3))
    
    legend_data = [
        ['EE1 (8pts)', 'EE2 (7pts)', 'ME1 (6pts)', 'ME2 (5pts)'],
        ['AE1 (4pts)', 'AE2 (3pts)', 'BE1 (2pts)', 'BE2 (1pt)']
    ]
    legend_table = Table(legend_data, colWidths=[2.7*inch, 2.7*inch, 2.7*inch, 2.6*inch])
    legend_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7), 
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
    ]))
    elements.append(legend_table)
    elements.append(Spacer(1, 8))
    
    # ============================================
    # CLASS SUMMARY & AUTHENTICATION
    # ============================================
    
    avg_points = df['POINTS'].mean() if 'POINTS' in df.columns else 0
    
    summary_data = [
        [Paragraph("<b>CLASS SUMMARY</b>", body_text_style), ""],
        [Paragraph(f"Total Students: {len(df)}", body_text_style), 
         Paragraph(f"Class Average: {df['AVERAGE'].mean():.1f}%", body_text_style)],
        [Paragraph(f"Average Points: {avg_points:.1f}", body_text_style),
         Paragraph(f"Highest: {df['TOTAL'].max():.0f} | Lowest: {df['TOTAL'].min():.0f}", body_text_style)]
    ]
    
    summary_table = Table(summary_data, colWidths=[5.35*inch, 5.35*inch])
    summary_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
        ('SPAN', (0, 0), (-1, 0)),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 8))
    
    # Authentication
    auth_data = [
        [Paragraph(f"<b>Class Teacher:</b> {class_teacher}", body_text_style),
         Paragraph("<b>Signature:</b> _______________", body_text_style),
         Paragraph("<b>Date:</b> _______________", body_text_style)]
    ]
    
    auth_table = Table(auth_data, colWidths=[3.5*inch, 3.6*inch, 3.6*inch])
    auth_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    elements.append(auth_table)
    elements.append(Spacer(1, 6))
    
    # ============================================
    # FOOTER
    # ============================================
    
    sep2 = Drawing(10.7*inch, 1)
    sep2.add(Line(0, 0, 10.7*inch, 0, strokeColor=colors.HexColor('#cccccc'), strokeWidth=0.5))
    elements.append(sep2)
    elements.append(Spacer(1, 2))
    
    elements.append(Paragraph(
        "Powered by ReaMic Institute for Applied Intelligence • Advancing Intelligence for Real World Impact. | +254 741 908009",
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---------------------------
# Login Page
# ---------------------------
def show_login():
    st.markdown("## 🔐 Login to ReaMic Scholar")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary", use_container_width=True):
            user = authenticate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_role = user['role']
                st.session_state.user_name = user['name']
                st.session_state.user_data = user
                st.success(f"Welcome, {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
        
        st.markdown("---")
        st.caption("Contact your system administrator if you need access")

# ---------------------------
# Admin Pages
# ---------------------------
def show_admin_dashboard():
    st.header("🎯 Admin Dashboard")
    st.markdown("*Complete system overview and management*")
    st.markdown("---")
    
    students = load_students()
    users = load_users()
    marks = load_marks()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Students", len(students))
    with col2:
        teacher_count = sum(1 for u in users.values() if u['role'] == 'teacher')
        st.metric("Total Teachers", teacher_count)
    with col3:
        st.metric("Total Exams", len(marks))
    with col4:
        total_entries = sum(len(exam_marks) for exam_marks in marks.values())
        st.metric("Total Entries", total_entries)
    
    st.markdown("---")
    
    # Students by grade
    st.subheader("📊 Students by Grade")
    grade_counts = {}
    for student in students.values():
        grade = student['grade']
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    
    if grade_counts:
        fig = px.bar(x=list(grade_counts.keys()), y=list(grade_counts.values()),
                     labels={'x': 'Grade', 'y': 'Number of Students'},
                     title="Student Distribution by Grade")
        fig.update_traces(marker_color='lightblue')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📚 No students registered yet")
        st.markdown("---")
        st.markdown("### 🚀 Quick Start Guide")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Option 1: Add Manually")
            st.markdown("""
            1. Go to **Manage Students** page
            2. Click **Add Student** tab
            3. Fill in student details
            4. Repeat for each student
            """)
        
        with col2:
            st.markdown("#### Option 2: Use Sample Data")
            st.markdown("""
            Run these scripts to populate with test data:
            
            **Grade 5 (20 students):**
            ```bash
            python generate_grade5_data.py
            ```
            
            **Grade 7 (40 students):**
            ```bash
            python generate_grade7_sample_data.py
            ```
            """)
        
        st.markdown("---")
        st.info("💡 **Tip:** Sample data scripts create students, teachers, and marks automatically - perfect for testing!")

def show_manage_students():
    st.header("👥 Manage Students")
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Student", "📋 View Students", "✏️ Edit Student", "🗑️ Delete Student"])
    
    with tab1:
        st.subheader("Add New Student")
        
        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox("Grade", list(GRADES.keys()), key="add_grade")
            
            # Admission number only required for grades 7-9
            if grade in ['Grade 7', 'Grade 8', 'Grade 9']:
                adm_no = st.text_input("Admission Number *", key="add_adm_junior", 
                                      help="Required for Junior Secondary")
            else:
                adm_no = st.text_input("Admission Number (Optional)", key="add_adm_primary",
                                      help="Leave blank to auto-generate from student's name initials (e.g., John Doe → JD-H)")
            
            name = st.text_input("Student Name *", key="add_name")
        
        with col2:
            gender = st.selectbox("Gender", ["M", "F"], key="add_gender")
            stream = st.selectbox("Stream", ["H", "C"], 
                                 format_func=lambda x: "Heroes (H)" if x == "H" else "Champions (C)",
                                 key="add_stream")
        
        if st.button("Add Student", type="primary"):
            # For grades 4-6, admission number is optional
            if grade in ['Grade 4', 'Grade 5', 'Grade 6']:
                if name and grade:
                    success, message = add_student(adm_no, name, gender, grade, stream)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Please fill in Student Name")
            else:  # Grades 7-9 require admission number
                if adm_no and name and grade:
                    success, message = add_student(adm_no, name, gender, grade, stream)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Please fill in all required fields (Admission Number and Name)")
    
    with tab2:
        st.subheader("All Students")
        students = load_students()
        
        if students:
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                filter_grade = st.selectbox("Filter by Grade", ["All"] + list(GRADES.keys()), key="filter_grade")
            with col2:
                filter_stream = st.text_input("Filter by Stream", key="filter_stream")
            
            # Convert to DataFrame
            students_list = []
            for adm, data in students.items():
                students_list.append({
                    'ADM NO.': adm,
                    'Name': data['name'],
                    'Gender': data['gender'],
                    'Grade': data['grade'],
                    'Stream': data['stream']
                })
            
            df = pd.DataFrame(students_list)
            
            # Apply filters
            if filter_grade != "All":
                df = df[df['Grade'] == filter_grade]
            if filter_stream:
                df = df[df['Stream'].str.contains(filter_stream, case=False)]
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(df)} students")
        else:
            st.info("No students registered yet")
    
    with tab3:
        st.subheader("Edit Student")
        students = load_students()
        
        if students:
            adm_select = st.selectbox("Select Student", list(students.keys()), key="edit_select")
            
            if adm_select:
                student = students[adm_select]
                
                col1, col2 = st.columns(2)
                with col1:
                    edit_name = st.text_input("Student Name", value=student['name'], key="edit_name")
                    edit_gender = st.selectbox("Gender", ["M", "F"], 
                                              index=0 if student['gender'] == 'M' else 1, 
                                              key="edit_gender")
                
                with col2:
                    edit_grade = st.selectbox("Grade", list(GRADES.keys()),
                                             index=list(GRADES.keys()).index(student['grade']),
                                             key="edit_grade")
                    current_stream = student['stream'] if student['stream'] in ['H', 'C'] else 'H'
                    edit_stream = st.selectbox("Stream", ["H", "C"],
                                              format_func=lambda x: "Heroes (H)" if x == "H" else "Champions (C)",
                                              index=0 if current_stream == 'H' else 1,
                                              key="edit_stream")
                
                if st.button("Update Student", type="primary"):
                    students[adm_select] = {
                        "name": edit_name,
                        "gender": edit_gender,
                        "grade": edit_grade,
                        "stream": edit_stream,
                        "created_at": student.get('created_at', datetime.now().isoformat())
                    }
                    save_students(students)
                    st.success("Student updated successfully!")
                    st.rerun()
        else:
            st.info("No students to edit")

    with tab4:
        st.subheader("Delete Student")
        st.warning("⚠️ **Warning:** Deleting a student will permanently remove their record and all associated exam marks. This action cannot be undone!")
        
        students = load_students()
        
        if students:
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                filter_grade_del = st.selectbox("Filter by Grade", ["All"] + list(GRADES.keys()), key="delete_filter_grade")
            with col2:
                filter_stream_del = st.text_input("Filter by Stream", key="delete_filter_stream")
            
            filtered_students = {}
            for adm, data in students.items():
                if filter_grade_del != "All" and data['grade'] != filter_grade_del:
                    continue
                if filter_stream_del and filter_stream_del.upper() not in data['stream'].upper():
                    continue
                filtered_students[adm] = data
            
            if filtered_students:
                st.markdown(f"**Found {len(filtered_students)} student(s)**")
                st.markdown("---")
                
                student_options = {}
                for adm, data in filtered_students.items():
                    display_name = f"{adm} - {data['name']} ({data['grade']}, Stream {data['stream']})"
                    student_options[display_name] = adm
                
                selected_student = st.selectbox(
                    "Select Student to Delete",
                    list(student_options.keys()),
                    key="delete_student_select"
                )
                
                if selected_student:
                    selected_adm = student_options[selected_student]
                    student_data = students[selected_adm]
                    
                    st.markdown("### Student Details")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"**Name:** {student_data['name']}")
                        st.info(f"**Gender:** {student_data['gender']}")
                    with col2:
                        st.info(f"**Admission No:** {selected_adm}")
                        st.info(f"**Grade:** {student_data['grade']}")
                    with col3:
                        st.info(f"**Stream:** {student_data['stream']}")
                        created = student_data.get('created_at', 'Unknown')
                        st.info(f"**Created:** {created[:10] if len(created) > 10 else created}")
                    
                    marks = load_marks()
                    exam_count = 0
                    for exam_key in marks.keys():
                        if selected_adm in marks[exam_key]:
                            exam_count += 1
                    
                    if exam_count > 0:
                        st.warning(f"⚠️ This student has marks recorded in **{exam_count} exam(s)**. All marks will be deleted.")
                    
                    st.markdown("---")
                    
                    confirm = st.checkbox(
                        f"I confirm that I want to permanently delete {student_data['name']} ({selected_adm})",
                        key="delete_confirm"
                    )
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button("🗑️ Delete Student", type="primary", disabled=not confirm, use_container_width=True):
                            success, message = delete_student(selected_adm)
                            if success:
                                st.success(message)
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(message)
                    
                    if not confirm:
                        st.caption("Please check the confirmation box above to enable deletion")
            else:
                st.info("No students found matching the filter criteria")
        else:
            st.info("No students to delete")
    
def show_manage_teachers():
    st.header("👨‍🏫 Manage Teachers")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Teacher", "📋 View Teachers", "🗑️ Delete Teacher"])
    
    with tab1:
        st.subheader("Add New Teacher")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            username = st.text_input("Username", key="teacher_username")
        with col2:
            password = st.text_input("Password", type="password", key="teacher_password")
        with col3:
            name = st.text_input("Full Name", key="teacher_name")
        
        st.markdown("---")
        st.markdown("### 📋 Teaching Assignments")
        st.info("**Important:** Assign specific Grade + Subject + Stream combinations. Each assignment is a complete teaching responsibility.")
        
        # Initialize session state for assignments
        if 'teacher_assignments' not in st.session_state:
            st.session_state.teacher_assignments = []
        
        # Add new assignment
        st.markdown("#### ➕ Add New Assignment")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            new_grade = st.selectbox("Grade", list(GRADES.keys()), key="new_assignment_grade")
        
        with col2:
            # Get subjects for selected grade
            grade_subjects = GRADES[new_grade]
            new_subject = st.selectbox("Subject", grade_subjects, key="new_assignment_subject")
        
        with col3:
            new_stream = st.selectbox("Stream", 
                                     ["H", "C", "BOTH"],
                                     format_func=lambda x: "Heroes" if x == "H" else ("Champions" if x == "C" else "Both Streams"),
                                     key="new_assignment_stream",
                                     help="Select specific stream or BOTH")
        
        with col4:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("➕ Add", type="primary", use_container_width=True):
                # Create assignment(s)
                if new_stream == "BOTH":
                    # Add two assignments (one for each stream)
                    assignment_h = {
                        "grade": new_grade,
                        "subject": new_subject,
                        "stream": "H"
                    }
                    assignment_c = {
                        "grade": new_grade,
                        "subject": new_subject,
                        "stream": "C"
                    }
                    
                    # Check for duplicates
                    if assignment_h not in st.session_state.teacher_assignments:
                        st.session_state.teacher_assignments.append(assignment_h)
                    if assignment_c not in st.session_state.teacher_assignments:
                        st.session_state.teacher_assignments.append(assignment_c)
                    
                    st.success(f"✓ Added: {new_grade} → {new_subject} → Both Streams")
                else:
                    assignment = {
                        "grade": new_grade,
                        "subject": new_subject,
                        "stream": new_stream
                    }
                    
                    if assignment not in st.session_state.teacher_assignments:
                        st.session_state.teacher_assignments.append(assignment)
                        stream_name = "Heroes" if new_stream == "H" else "Champions"
                        st.success(f"✓ Added: {new_grade} → {new_subject} → {stream_name}")
                    else:
                        st.warning("This assignment already exists")
                
                st.rerun()
        
        # Display current assignments
        if st.session_state.teacher_assignments:
            st.markdown("---")
            st.markdown("#### 📝 Current Assignments")
            
            # Group by grade for better display
            assignments_by_grade = {}
            for assignment in st.session_state.teacher_assignments:
                grade = assignment['grade']
                if grade not in assignments_by_grade:
                    assignments_by_grade[grade] = []
                assignments_by_grade[grade].append(assignment)
            
            for grade, assignments in sorted(assignments_by_grade.items()):
                with st.expander(f"**{grade}** ({len(assignments)} assignments)", expanded=True):
                    for idx, assignment in enumerate(assignments):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            stream_name = "Heroes (H)" if assignment['stream'] == "H" else "Champions (C)"
                            st.write(f"• {assignment['subject']} - {stream_name}")
                        with col2:
                            if st.button("🗑️", key=f"remove_{grade}_{idx}", help="Remove this assignment"):
                                st.session_state.teacher_assignments.remove(assignment)
                                st.rerun()
            
            st.markdown("---")
            st.markdown(f"**Total Assignments:** {len(st.session_state.teacher_assignments)}")
        else:
            st.warning("⚠️ No assignments added yet. Please add at least one assignment.")
        
        # Save teacher button
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("💾 Save Teacher", type="primary", use_container_width=True):
                if username and password and name:
                    if st.session_state.teacher_assignments:
                        success, message = add_teacher(username, password, name, st.session_state.teacher_assignments)
                        if success:
                            st.success(message)
                            # Show summary
                            st.markdown("**Assignment Summary:**")
                            for assignment in st.session_state.teacher_assignments:
                                stream_name = "Heroes" if assignment['stream'] == "H" else "Champions"
                                st.write(f"• {assignment['grade']} - {assignment['subject']} - {stream_name}")
                            # Clear assignments
                            st.session_state.teacher_assignments = []
                        else:
                            st.error(message)
                    else:
                        st.error("Please add at least one teaching assignment")
                else:
                    st.warning("Please fill in Username, Password, and Full Name")
        
        with col2:
            if st.button("🔄 Clear All", use_container_width=True):
                st.session_state.teacher_assignments = []
                st.rerun()
    
    with tab2:
        st.subheader("All Teachers")
        users = load_users()
        teachers = {u: data for u, data in users.items() if data['role'] == 'teacher'}
        
        if teachers:
            for username, teacher in teachers.items():
                with st.expander(f"👨‍🏫 {teacher['name']} (@{username})", expanded=False):
                    # Get assignments
                    assignments = teacher.get('assignments', [])
                    
                    if assignments:
                        # Group by grade
                        assignments_by_grade = {}
                        for assignment in assignments:
                            grade = assignment['grade']
                            if grade not in assignments_by_grade:
                                assignments_by_grade[grade] = []
                            assignments_by_grade[grade].append(assignment)
                        
                        st.markdown("**Teaching Assignments:**")
                        for grade in sorted(assignments_by_grade.keys()):
                            st.markdown(f"**{grade}:**")
                            grade_assignments = assignments_by_grade[grade]
                            
                            # Group by subject within grade
                            subject_streams = {}
                            for assignment in grade_assignments:
                                subj = assignment['subject']
                                stream = assignment['stream']
                                if subj not in subject_streams:
                                    subject_streams[subj] = []
                                subject_streams[subj].append(stream)
                            
                            for subj, streams in sorted(subject_streams.items()):
                                streams_set = set(streams)
                                if streams_set == {'H', 'C'}:
                                    st.write(f"  • {subj}: **Both Streams** (Heroes & Champions)")
                                elif 'H' in streams_set:
                                    st.write(f"  • {subj}: **Heroes (H)** only")
                                else:
                                    st.write(f"  • {subj}: **Champions (C)** only")
                        
                        st.caption(f"Total: {len(assignments)} assignment(s)")
                    else:
                        # Legacy teacher without assignments structure
                        st.markdown("**Subjects:**")
                        st.write(", ".join(teacher.get('subjects', [])))
                        st.markdown("**Grades:**")
                        st.write(", ".join(teacher.get('grades', [])))
                        st.warning("⚠️ Legacy teacher format - please re-add with specific assignments")
        else:
            st.info("No teachers registered yet")

    with tab3:
        st.subheader("Delete Teacher")
        st.warning("⚠️ **Warning:** Deleting a teacher will permanently remove their account. This action cannot be undone!")
        
        users = load_users()
        teachers = {u: data for u, data in users.items() if data['role'] == 'teacher'}
        
        if teachers:
            st.markdown("---")
            
            teacher_options = {}
            for username, teacher in teachers.items():
                display_name = f"{teacher['name']} (@{username})"
                teacher_options[display_name] = username
            
            selected_teacher = st.selectbox(
                "Select Teacher to Delete",
                list(teacher_options.keys()),
                key="delete_teacher_select"
            )
            
            if selected_teacher:
                selected_username = teacher_options[selected_teacher]
                teacher_data = teachers[selected_username]
                
                st.markdown("### Teacher Details")
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Name:** {teacher_data['name']}")
                    st.info(f"**Username:** {selected_username}")
                with col2:
                    st.info(f"**Subjects:** {', '.join(teacher_data.get('subjects', []))}")
                    st.info(f"**Grades:** {', '.join(teacher_data.get('grades', []))}")
                
                assignments = teacher_data.get('assignments', [])
                if assignments:
                    st.markdown("**Teaching Assignments:**")
                    for assignment in assignments[:5]:
                        st.write(f"• {assignment['grade']} - {assignment['subject']} - Stream {assignment['stream']}")
                    if len(assignments) > 5:
                        st.caption(f"... and {len(assignments) - 5} more assignments")
                
                st.markdown("---")
                
                if 'username' in st.session_state and st.session_state.username == selected_username:
                    st.error("❌ You cannot delete your own account while logged in!")
                else:
                    confirm = st.checkbox(
                        f"I confirm that I want to permanently delete {teacher_data['name']} (@{selected_username})",
                        key="delete_teacher_confirm"
                    )
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button("🗑️ Delete Teacher", type="primary", disabled=not confirm, use_container_width=True):
                            success, message = delete_teacher(selected_username)
                            if success:
                                st.success(message)
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(message)
                    
                    if not confirm:
                        st.caption("Please check the confirmation box above to enable deletion")
        else:
            st.info("No teachers to delete")
    
def show_marks_entry_progress():
    st.header("📊 Marks Entry Progress")
    st.markdown("*Track which teachers have completed their marks entry*")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        grade = st.selectbox("Select Grade", list(GRADES.keys()), key="progress_grade")
    with col2:
        term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="progress_term")
    with col3:
        year = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="progress_year")
    
    exam_type = st.selectbox("Examination Type",
                            ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
                            key="progress_exam")
    
    if st.button("Check Progress", type="primary"):
        progress = get_marks_entry_progress(grade, term, year, exam_type)
        
        if not progress:
            st.info("No teachers assigned to this grade or no students in this grade")
        else:
            st.markdown("---")
            st.subheader("📈 Progress Overview")
            
            # Summary metrics
            total_needed = sum(p['total_needed'] for p in progress.values())
            total_completed = sum(p['completed'] for p in progress.values())
            overall_percentage = (total_completed / total_needed * 100) if total_needed > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Entries Needed", total_needed)
            with col2:
                st.metric("Total Completed", total_completed)
            with col3:
                st.metric("Overall Progress", f"{overall_percentage:.1f}%")
            
            st.markdown("---")
            
            # Individual teacher progress
            for teacher_username, data in progress.items():
                percentage = data['percentage']
                
                # Color coding
                if percentage == 100:
                    status_color = "🟢"
                    status = "Complete"
                elif percentage >= 50:
                    status_color = "🟡"
                    status = "In Progress"
                else:
                    status_color = "🔴"
                    status = "Not Started" if percentage == 0 else "Behind"
                
                with st.expander(f"{status_color} {data['name']} - {percentage:.1f}% ({status})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Subjects:** {', '.join(data['subjects'])}")
                        st.write(f"**Completed:** {data['completed']} / {data['total_needed']}")
                    with col2:
                        st.progress(percentage / 100)
                        st.write(f"**Remaining:** {data['total_needed'] - data['completed']} entries")

# ---------------------------
# Teacher Pages
# ---------------------------
def show_teacher_dashboard():
    st.header("👨‍🏫 Teacher Dashboard")
    st.markdown(f"*Welcome, {st.session_state.user_name}!*")
    st.markdown("---")
    
    user_data = st.session_state.user_data
    assignments = user_data.get('assignments', [])
    
    if assignments:
        # Group assignments by grade
        assignments_by_grade = {}
        for assignment in assignments:
            grade = assignment['grade']
            if grade not in assignments_by_grade:
                assignments_by_grade[grade] = []
            assignments_by_grade[grade].append(assignment)
        
        st.subheader("📋 Your Teaching Assignments")
        
        for grade in sorted(assignments_by_grade.keys()):
            with st.expander(f"**{grade}**", expanded=True):
                grade_assignments = assignments_by_grade[grade]
                
                # Group by subject
                subject_streams = {}
                for assignment in grade_assignments:
                    subj = assignment['subject']
                    stream = assignment['stream']
                    if subj not in subject_streams:
                        subject_streams[subj] = []
                    subject_streams[subj].append(stream)
                
                for subj, streams in sorted(subject_streams.items()):
                    streams_set = set(streams)
                    if streams_set == {'H', 'C'}:
                        st.write(f"• {subj}: Both Streams")
                    elif 'H' in streams_set:
                        st.write(f"• {subj}: Heroes (H)")
                    else:
                        st.write(f"• {subj}: Champions (C)")
        
        st.markdown("---")
        
        # Quick stats
        students = load_students()
        grades = list(set([a['grade'] for a in assignments]))
        subjects = list(set([a['subject'] for a in assignments]))
        
        # Count students in assigned grades and streams
        assigned_students = 0
        for assignment in assignments:
            assigned_students += sum(1 for s in students.values() 
                                   if s['grade'] == assignment['grade'] 
                                   and s['stream'] == assignment['stream'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Your Students", assigned_students)
        with col2:
            st.metric("Subjects", len(subjects))
        with col3:
            st.metric("Total Assignments", len(assignments))
    else:
        st.warning("No teaching assignments found. Please contact the administrator.")

def show_enter_marks():
    st.header("✏️ Enter Student Marks")
    
    user_data = st.session_state.user_data
    assignments = user_data.get('assignments', [])
    
    if not assignments:
        st.warning("No teaching assignments found. Please contact the administrator.")
        return
    
    # Exam selection
    col1, col2, col3 = st.columns(3)
    with col1:
        # Get unique grades from assignments
        teacher_grades = sorted(list(set([a['grade'] for a in assignments])))
        grade = st.selectbox("Select Grade", teacher_grades, key="enter_grade")
    with col2:
        term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="enter_term")
    with col3:
        year = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="enter_year")
    
    exam_type = st.selectbox("Examination Type",
                            ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
                            key="enter_exam")
    
    # Get assignments for selected grade
    grade_assignments = [a for a in assignments if a['grade'] == grade]
    
    # Subject selection
    col1, col2 = st.columns(2)
    with col1:
        # Get unique subjects for this grade
        available_subjects = sorted(list(set([a['subject'] for a in grade_assignments])))
        
        if not available_subjects:
            st.warning(f"No subjects assigned for {grade}")
            return
        
        subject = st.selectbox("Select Subject", available_subjects, key="enter_subject")
    
    # Get allowed streams for this grade+subject combination
    subject_assignments = [a for a in grade_assignments if a['subject'] == subject]
    allowed_streams = [a['stream'] for a in subject_assignments]
    
    with col2:
        # Get students in this grade filtered by allowed streams
        students = load_students()
        grade_students = {adm: data for adm, data in students.items() 
                         if data['grade'] == grade and data['stream'] in allowed_streams}
        
        if not grade_students:
            streams_text = "Heroes and Champions" if len(allowed_streams) == 2 else ("Heroes" if "H" in allowed_streams else "Champions")
            st.warning(f"No students in {grade} - {streams_text} stream(s) for {subject}")
            return
        
        # Show which streams are being displayed
        if len(allowed_streams) == 1:
            stream_name = "Heroes (H)" if "H" in allowed_streams else "Champions (C)"
            st.caption(f"📍 Showing: {stream_name} stream only")
        else:
            st.caption(f"📍 Showing: Both streams (Heroes & Champions)")
        
        # Format student options with stream indicator
        student_options = {}
        for adm, data in grade_students.items():
            stream_label = f"[{'H' if data['stream'] == 'H' else 'C'}]"
            student_options[f"{adm} - {data['name']} {stream_label}"] = adm
        
        selected_student = st.selectbox("Select Student", list(student_options.keys()), key="enter_student")
        adm_no = student_options[selected_student]
    
    # Score entry
    st.markdown("---")
    st.subheader("Enter Score")
    
    # Check if marks already exist
    marks = load_marks()
    exam_key = f"{grade}_{term}_{year}_{exam_type}"
    existing_score = None
    if exam_key in marks and adm_no in marks[exam_key] and subject in marks[exam_key][adm_no]:
        existing_score = marks[exam_key][adm_no][subject]['score']
        st.info(f"Current score: {existing_score} (You can update it below)")
    
    score = st.number_input("Score (0-100)", min_value=0.0, max_value=100.0, 
                           value=float(existing_score) if existing_score else 0.0,
                           step=0.5, key="enter_score")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Submit Score", type="primary", use_container_width=True):
            success, message = enter_marks(adm_no, subject, grade, term, year, exam_type, 
                                          score, st.session_state.username)
            if success:
                st.success(message)
                st.balloons()
            else:
                st.error(message)
    
    with col2:
        if st.button("Clear Form", use_container_width=True):
            st.rerun()

def show_teacher_progress():
    st.header("📊 My Progress")
    st.markdown("*Track your marks entry progress*")
    st.markdown("---")
    
    user_data = st.session_state.user_data
    teacher_grades = user_data.get('grades', [])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        grade = st.selectbox("Select Grade", teacher_grades, key="my_progress_grade")
    with col2:
        term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="my_progress_term")
    with col3:
        year = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="my_progress_year")
    
    exam_type = st.selectbox("Examination Type",
                            ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
                            key="my_progress_exam")
    
    if st.button("Check My Progress", type="primary"):
        progress = get_marks_entry_progress(grade, term, year, exam_type)
        
        username = st.session_state.username
        if username in progress:
            data = progress[username]
            percentage = data['percentage']
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Entries Needed", data['total_needed'])
            with col2:
                st.metric("Completed", data['completed'])
            with col3:
                st.metric("Progress", f"{percentage:.1f}%")
            
            st.progress(percentage / 100)
            
            if percentage == 100:
                st.success("🎉 Congratulations! You have completed all entries for this exam!")
            else:
                remaining = data['total_needed'] - data['completed']
                st.info(f"📝 You have {remaining} entries remaining")
            
            # Show subjects
            st.markdown("---")
            st.subheader("Your Subjects")
            st.write(", ".join(data['subjects']))
        else:
            st.warning("No progress data available for this exam")

# ---------------------------
# Shared Analysis Pages (accessible by both admin and teachers)
# ---------------------------
def show_dashboard(df, grade, subject_cols):
    st.header(f"📊 Dashboard - {grade}")
    st.markdown("*Real-time insights and analytics*")
    st.markdown("---")

    if df.empty:
        st.warning("No data available for analysis yet")
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Students", len(df))
    with col2:
        st.metric("Average Score", f"{df['TOTAL'].mean():.1f}")
    with col3:
        st.metric("Highest Score", f"{df['TOTAL'].max():.0f}")
    with col4:
        st.metric("Streams", df['STRM'].nunique())
    with col5:
        male_count = len(df[df['GENDER'].str.upper() == 'M'])
        female_count = len(df[df['GENDER'].str.upper() == 'F'])
        st.metric("M:F Ratio", f"{male_count}:{female_count}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Performance Level Distribution")
        df['PERF_LEVEL'] = df['AVERAGE'].apply(get_performance_level)
        perf_counts = df['PERF_LEVEL'].value_counts()
        fig = px.pie(values=perf_counts.values, names=perf_counts.index,
                     title="Students by Performance Level",
                     color=perf_counts.index,
                     color_discrete_map={'EE': '#00cc00', 'ME': '#3399ff', 'AE': '#ffcc00', 'BE': '#ff6666'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Gender Distribution")
        gender_counts = df['GENDER'].str.upper().value_counts()
        fig = px.pie(values=gender_counts.values, names=gender_counts.index,
                     title="Students by Gender",
                     color_discrete_map={'M': 'lightblue', 'F': 'lightpink'})
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Subject Averages")
        subject_avgs = df[subject_cols].mean().sort_values(ascending=False)
        fig = px.bar(x=subject_avgs.index, y=subject_avgs.values,
                     labels={'x': 'Subject', 'y': 'Average Score'},
                     title="Average Performance by Subject")
        fig.update_traces(marker_color='lightblue')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Performance by Gender")
        gender_perf = df.groupby(df['GENDER'].str.upper())['TOTAL'].mean()
        fig = px.bar(x=gender_perf.index, y=gender_perf.values,
                     labels={'x': 'Gender', 'y': 'Average Score'},
                     title="Average Score by Gender",
                     color=gender_perf.index,
                     color_discrete_map={'M': 'lightblue', 'F': 'lightpink'})
        st.plotly_chart(fig, use_container_width=True)

def show_student_reports(df, grade, subject_cols):
    st.header("📄 Student Reports")

    if df.empty:
        st.warning("No data available yet")
        return

    # Report configuration
    with st.expander("🔧 Report Configuration", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            school_name = st.text_input("School Name", "SINDO COMPREHENSIVE SCHOOL", key="report_school_name")
            grade_text = st.text_input("Grade/Class", grade, key="report_grade_text")
        with col2:
            term = st.text_input("Term", "Term 1", key="report_term")
            year = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="report_year")
        with col3:
            exam_type = st.text_input("Examination Type", "End Term Examinations", key="report_exam_type")

        st.markdown("**Staff Information**")
        col1, col2, col3 = st.columns(3)
        with col1:
            class_teacher = st.text_input("Class Teacher Name", "Mr./Mrs. Teacher", key="report_class_teacher")
        with col2:
            dhoi = st.text_input("DHOI Name", "Mr./Mrs. DHOI", key="report_dhoi")
        with col3:
            hoi = st.text_input("HOI Name", "Mr./Mrs. HOI", key="report_hoi")

    st.markdown("---")

    search_type = st.radio("Search by:", ["ADM NO.", "Student Name"], key="report_search_type")

    if search_type == "ADM NO.":
        adm_no = st.selectbox("Select Admission Number", df['ADM NO.'].unique(), key="report_select_adm")
        student = df[df['ADM NO.'] == adm_no].iloc[0]
    else:
        name = st.selectbox("Select Student Name", df['NAME OF STUDENTS'].unique(), key="report_select_name")
        student = df[df['NAME OF STUDENTS'] == name].iloc[0]

    # Student info
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Name", student['NAME OF STUDENTS'])
    with col2:
        st.metric("ADM NO.", student['ADM NO.'])
    with col3:
        st.metric("Gender", student['GENDER'])
    with col4:
        st.metric("Stream", student['STRM'])
    with col5:
        st.metric("Rank", f"{student['RANK']}/{len(df)}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Marks", f"{student['TOTAL']:.0f}")
    with col2:
        st.metric("Average", f"{student['AVERAGE']:.1f}")
    with col3:
        st.metric("P.Level", student.get('P.LEVEL', 'N/A'))
    with col4:
        st.metric("Points", student.get('POINTS', 'N/A'))

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Subject Marks")
        marks_data = []
        for subj in subject_cols:
            score = student.get(subj, 0)
            perf_level, points = get_subject_performance_level(score)
            marks_data.append({
                'Subject': subj,
                'Marks': score,
                'P.Level': perf_level,
                'Points': points
            })
        marks_df = pd.DataFrame(marks_data)

        # Create color mapping for CBC levels
        cbc_color_map = {
            'EE1': '#006400', 'EE2': '#00cc00',
            'ME1': '#0066cc', 'ME2': '#3399ff',
            'AE1': '#cc8800', 'AE2': '#ffcc00',
            'BE1': '#cc0000', 'BE2': '#ff6666'
        }

        fig = px.bar(marks_df, x='Subject', y='Marks',
                     title="Subject-wise Performance",
                     color='P.Level',
                     color_discrete_map=cbc_color_map,
                     hover_data=['Points'])
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(marks_df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Performance Radar")
        categories = subject_cols
        values = [student.get(subj, 0) for subj in subject_cols]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=student['NAME OF STUDENTS']
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📄 Generate PDF Report")

    if st.button("Generate PDF Report", type="primary"):
        with st.spinner("Generating professional report card..."):
            pdf_buffer = create_pdf_report(student, school_name, grade_text, term, year,
                                           exam_type, df, class_teacher, dhoi, hoi, subject_cols)

            st.success("✅ Report card generated successfully!")
            
            # Preview section
            st.markdown("---")
            st.subheader("📄 Report Preview")
            st.info("Preview the report card below before downloading")
            
            # Convert PDF to base64 for preview
            import base64
            pdf_bytes = pdf_buffer.read()
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_buffer.seek(0)  # Reset buffer for download
            
            # Display PDF in iframe
            pdf_display = f'''
                <iframe 
                    src="data:application/pdf;base64,{base64_pdf}" 
                    width="100%" 
                    height="800px" 
                    type="application/pdf"
                    style="border: 1px solid #ddd; border-radius: 4px;">
                </iframe>
            '''
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Download button
            st.download_button(
                label="📥 Download PDF Report Card",
                data=pdf_buffer,
                file_name=f"{student['NAME OF STUDENTS']}_Report_{term}_{year}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

def show_class_analysis(df, grade, subject_cols):
    st.header("📊 Class Analysis")

    if df.empty:
        st.warning("No data available yet")
        return
    
    # ============================================
    # STREAM FILTER
    # ============================================
    
    st.markdown("### 🎯 Select Class/Stream")
    
    # Get available streams
    available_streams = sorted(df['STRM'].unique().tolist())
    
    # Create filter options
    filter_options = [f"{grade} (All Streams)"]
    for stream in available_streams:
        stream_name = "Heroes" if stream == "H" else "Champions"
        filter_options.append(f"{grade} - {stream_name} ({stream})")
    
    selected_filter = st.selectbox(
        "Select class/stream to analyze:",
        filter_options,
        key="class_analysis_filter"
    )
    
    # Filter dataframe based on selection
    if "All Streams" in selected_filter:
        filtered_df = df.copy()
        display_name = f"{grade} (All Streams)"
    else:
        # Extract stream from selection
        stream = selected_filter.split("(")[-1].replace(")", "")
        filtered_df = df[df['STRM'] == stream].copy()
        stream_name = "Heroes" if stream == "H" else "Champions"
        display_name = f"{grade} - {stream_name}"
    
    st.info(f"📊 Analyzing: **{display_name}** | Students: **{len(filtered_df)}**")
    st.markdown("---")
    
    # ============================================
    # CLASS METRICS
    # ============================================

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Class Average", f"{filtered_df['TOTAL'].mean():.1f}")
    with col2:
        st.metric("Median Score", f"{filtered_df['TOTAL'].median():.1f}")
    with col3:
        st.metric("Standard Deviation", f"{filtered_df['TOTAL'].std():.1f}")
    with col4:
        male_avg = filtered_df[filtered_df['GENDER'].str.upper() == 'M']['TOTAL'].mean()
        female_avg = filtered_df[filtered_df['GENDER'].str.upper() == 'F']['TOTAL'].mean()
        st.metric("Gender Gap", f"{abs(male_avg - female_avg):.1f}")

    st.markdown("---")

    # ============================================
    # CBC PERFORMANCE LEVEL DISTRIBUTION (8 levels)
    # ============================================
    
    st.subheader(" Performance Level Distribution")
    
    # Count students by P.LEVEL (8-level CBC system)
    perf_counts = filtered_df['P.LEVEL'].value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Create ordered list of all 8 levels
        all_levels = ['EE1', 'EE2', 'ME1', 'ME2', 'AE1', 'AE2', 'BE1', 'BE2']
        level_counts = [perf_counts.get(level, 0) for level in all_levels]
        
        # Color mapping for 8 levels
        color_map = {
            'EE1': '#006400', 'EE2': '#00cc00',  # Dark green, Light green
            'ME1': '#0066cc', 'ME2': '#3399ff',  # Dark blue, Light blue
            'AE1': '#cc8800', 'AE2': '#ffcc00',  # Dark orange, Light orange
            'BE1': '#cc0000', 'BE2': '#ff6666'   # Dark red, Light red
        }
        
        fig = px.bar(
            x=all_levels, 
            y=level_counts,
            labels={'x': 'Performance Level', 'y': 'Number of Students'},
            title="Students by Performance Level (CBC 8-Level System)",
            color=all_levels,
            color_discrete_map=color_map
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Create detailed performance table
        perf_summary = []
        for level in all_levels:
            count = perf_counts.get(level, 0)
            percentage = (count / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
            
            # Get description
            descriptions = {
                'EE1': 'Exceeding Expectation 1',
                'EE2': 'Exceeding Expectation 2',
                'ME1': 'Meeting Expectation 1',
                'ME2': 'Meeting Expectation 2',
                'AE1': 'Approaching Expectation 1',
                'AE2': 'Approaching Expectation 2',
                'BE1': 'Below Expectation 1',
                'BE2': 'Below Expectation 2'
            }
            
            # Get points
            points_map = {
                'EE1': 8, 'EE2': 7, 'ME1': 6, 'ME2': 5,
                'AE1': 4, 'AE2': 3, 'BE1': 2, 'BE2': 1
            }
            
            perf_summary.append({
                'Level': level,
                'Description': descriptions[level],
                'Points': points_map[level],
                'Count': int(count),
                'Percentage': f"{percentage:.1f}%"
            })
        
        perf_df = pd.DataFrame(perf_summary)
        st.dataframe(perf_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    
    # ============================================
    # SUBJECT-WISE ANALYSIS
    # ============================================
    
    st.subheader("Subject-wise Class Average")
    subject_avgs = filtered_df[subject_cols].mean().sort_values(ascending=False)
    fig = px.bar(x=subject_avgs.index, y=subject_avgs.values,
                 labels={'x': 'Subject', 'y': 'Average Score'},
                 title="Class Performance by Subject")
    fig.update_traces(marker_color='lightgreen')
    st.plotly_chart(fig, use_container_width=True)

    # ============================================
    # TOP AND BOTTOM PERFORMERS
    # ============================================
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Top 10 Students")
        top_10 = filtered_df.nsmallest(10, 'RANK')[['RANK', 'NAME OF STUDENTS', 'GENDER', 'STRM', 'TOTAL', 'AVERAGE', 'P.LEVEL', 'POINTS']]
        st.dataframe(top_10, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("📉 Bottom 10 Students")
        bottom_10 = filtered_df.nlargest(10, 'RANK')[['RANK', 'NAME OF STUDENTS', 'GENDER', 'STRM', 'TOTAL', 'AVERAGE', 'P.LEVEL', 'POINTS']]
        st.dataframe(bottom_10, use_container_width=True, hide_index=True)

    st.markdown("---")
    
    # ============================================
    # SCORE DISTRIBUTION
    # ============================================
    
    st.subheader("Total Score Distribution")
    fig = px.histogram(filtered_df, x='TOTAL', nbins=20, color=filtered_df['GENDER'].str.upper(),
                      labels={'TOTAL': 'Total Score', 'count': 'Number of Students'},
                      title="Distribution of Total Scores by Gender",
                      color_discrete_map={'M': 'lightblue', 'F': 'lightpink'})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    # ============================================
    # PDF GENERATION (Stream-specific or All)
    # ============================================
    
    st.subheader("📄 Generate Class Performance List (PDF)")
    
    # Determine what to show in PDF title
    if "All Streams" in selected_filter:
        pdf_display_name = grade
    else:
        stream = selected_filter.split("(")[-1].replace(")", "")
        stream_name = "Heroes" if stream == "H" else "Champions"
        pdf_display_name = f"{grade} - {stream_name}"
    
    with st.expander("🔧 Class List Configuration", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            school_name_cl = st.text_input("School Name", "SINDO COMPREHENSIVE SCHOOL", key="cl_school")
            grade_cl = st.text_input("Grade/Class", pdf_display_name, key="cl_grade")
        with col2:
            term_cl = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="cl_term")
            year_cl = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="cl_year")
        with col3:
            exam_type_cl = st.selectbox("Examination Type",
                                        ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
                                        key="cl_exam")
            class_teacher_cl = st.text_input("Class Teacher Name", "Mr./Mrs. Teacher", key="cl_teacher")

    if st.button("Generate Class List PDF", type="primary", key="generate_class_pdf"):
        with st.spinner("Generating professional class list..."):
            # Use filtered_df for PDF generation
            pdf_buffer = create_class_list_pdf(filtered_df, school_name_cl, grade_cl, term_cl,
                                              year_cl, exam_type_cl, class_teacher_cl, subject_cols)

            st.success("✅ Class list generated successfully!")
            
            # Preview section
            st.markdown("---")
            st.subheader("📄 Class List Preview")
            st.info(f"Preview for: **{pdf_display_name}** | Students: **{len(filtered_df)}** (Landscape orientation)")
            
            # Convert PDF to base64 for preview
            pdf_bytes = pdf_buffer.read()
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_buffer.seek(0)  # Reset buffer for download
            
            # Display PDF in iframe
            pdf_display = f'''
                <iframe 
                    src="data:application/pdf;base64,{base64_pdf}" 
                    width="100%" 
                    height="800px" 
                    type="application/pdf"
                    style="border: 1px solid #ddd; border-radius: 4px;">
                </iframe>
            '''
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Download button with stream-specific filename
            filename_safe = pdf_display_name.replace(" ", "_").replace("-", "")
            st.download_button(
                label=f"📥 Download {pdf_display_name} Class List PDF",
                data=pdf_buffer,
                file_name=f"Class_List_{filename_safe}_{term_cl}_{year_cl}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )


def show_subject_analysis(df, grade, subject_cols):
    st.header("📚 Subject Analysis")

    if df.empty:
        st.warning("No data available yet")
        return

    subject_avgs = df[subject_cols].mean().sort_values(ascending=False)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Strongest Subject", subject_avgs.index[0])
        st.metric("Average Score", f"{subject_avgs.values[0]:.1f}")
    with col2:
        st.metric("Weakest Subject", subject_avgs.index[-1])
        st.metric("Average Score", f"{subject_avgs.values[-1]:.1f}")
    with col3:
        variance = df[subject_cols].std().max()
        st.metric("Highest Variance", f"{variance:.1f}")

    st.markdown("---")
    st.subheader("🏆 Top Performers by Subject")

    tabs = st.tabs(subject_cols)

    for idx, subj in enumerate(subject_cols):
        with tabs[idx]:
            top_students = df.nlargest(10, subj)[['RANK', 'NAME OF STUDENTS', 'GENDER', 'STRM', subj, 'TOTAL']]
            top_students = top_students.rename(columns={subj: f'{subj} Score'})

            col1, col2 = st.columns([2, 1])

            with col1:
                st.dataframe(top_students, use_container_width=True, hide_index=True)

            with col2:
                st.markdown("### 🥇 Top 3")
                for i, (_, student) in enumerate(top_students.head(3).iterrows()):
                    medal = ["🥇", "🥈", "🥉"][i]
                    st.markdown(f"{medal} **{student['NAME OF STUDENTS']}**")
                    st.markdown(f"Score: {student[f'{subj} Score']:.0f} | Stream: {student['STRM']}")
                    st.markdown("---")

    st.markdown("---")
    st.subheader("Subject Performance by Gender")
    gender_subject_avg = df.groupby(df['GENDER'].str.upper())[subject_cols].mean()

    fig = go.Figure()
    for gender in gender_subject_avg.index:
        color = 'lightblue' if gender == 'M' else 'lightpink'
        fig.add_trace(go.Bar(
            name=gender,
            x=subject_cols,
            y=gender_subject_avg.loc[gender],
            marker_color=color
        ))

    fig.update_layout(
        title="Average Scores by Subject and Gender",
        xaxis_title="Subject",
        yaxis_title="Average Score",
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Score Distribution by Subject")
    subject_data = []
    for subj in subject_cols:
        for idx, row in df.iterrows():
            subject_data.append({
                'Subject': subj,
                'Score': row[subj],
                'Gender': row['GENDER'].upper()
            })

    fig = px.box(pd.DataFrame(subject_data), x='Subject', y='Score', color='Gender',
                 title="Score Range and Distribution by Subject",
                 color_discrete_map={'M': 'lightblue', 'F': 'lightpink'})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Detailed Subject Statistics")

    best_students = []
    for subj in subject_cols:
        if subj in df and not df.empty:
            best_students.append(df.loc[df[subj].idxmax()]['NAME OF STUDENTS'])
        else:
            best_students.append('')

    stats_df = pd.DataFrame({
        'Average': df[subject_cols].mean(),
        'Median': df[subject_cols].median(),
        'Max': df[subject_cols].max(),
        'Min': df[subject_cols].min(),
        'Std Dev': df[subject_cols].std(),
        'Pass Rate (≥50)': [(df[subj] >= 50).sum() / len(df) * 100 for subj in subject_cols],
        'Best Student': best_students
    }).round(2)
    st.dataframe(stats_df, use_container_width=True)


def show_stream_comparison(df, grade, subject_cols):
    st.header("🏫 Stream Comparison")

    if df.empty:
        st.warning("No data available yet")
        return

    stream_avg = df.groupby('STRM')['TOTAL'].mean().sort_values(ascending=False)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Best Performing Stream", stream_avg.index[0] if len(stream_avg) > 0 else "")
    with col2:
        st.metric("Average Score", f"{stream_avg.values[0]:.1f}" if len(stream_avg) > 0 else "")
    with col3:
        st.metric("Total Streams", len(stream_avg))

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Stream Rankings")
        stream_rank_data = []
        for stream in stream_avg.index:
            stream_df = df[df['STRM'] == stream]
            male_count = len(stream_df[stream_df['GENDER'].str.upper() == 'M'])
            female_count = len(stream_df[stream_df['GENDER'].str.upper() == 'F'])
            stream_rank_data.append({
                'Stream': stream,
                'Average Score': stream_avg[stream],
                'Students': len(stream_df),
                'M:F': f"{male_count}:{female_count}"
            })
        stream_rank_df = pd.DataFrame(stream_rank_data)
        stream_rank_df.index += 1
        stream_rank_df.index.name = 'Rank'
        st.dataframe(stream_rank_df, use_container_width=True)

    with col2:
        st.subheader("Average Score by Stream")
        fig = px.bar(x=stream_avg.index, y=stream_avg.values,
                     labels={'x': 'Stream', 'y': 'Average Score'},
                     title="Stream Performance Comparison")
        fig.update_traces(marker_color='teal')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Subject-wise Stream Comparison")
    stream_subject_avg = df.groupby('STRM')[subject_cols].mean()

    fig = go.Figure()
    for stream in stream_subject_avg.index:
        fig.add_trace(go.Scatter(
            x=subject_cols,
            y=stream_subject_avg.loc[stream],
            mode='lines+markers',
            name=stream
        ))

    fig.update_layout(
        title="Stream Performance Across Subjects",
        xaxis_title="Subject",
        yaxis_title="Average Score",
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Gender Performance by Stream")
    stream_gender = df.groupby(['STRM', df['GENDER'].str.upper()])['TOTAL'].mean().reset_index()
    if not stream_gender.empty:
        fig = px.bar(stream_gender, x='STRM', y='TOTAL', color='GENDER',
                     labels={'TOTAL': 'Average Score', 'STRM': 'Stream'},
                     title="Average Score by Stream and Gender",
                     barmode='group',
                     color_discrete_map={'M': 'lightblue', 'F': 'lightpink'})
        st.plotly_chart(fig, use_container_width=True)


def show_gender_analysis(df, subject_cols, grade):
    st.header("⚥ Gender Analysis")
    
    if df.empty:
        st.warning("No data available yet")
        return
    
    male_df = df[df['GENDER'].str.upper() == 'M']
    female_df = df[df['GENDER'].str.upper() == 'F']

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Male Students", len(male_df))
        st.metric("Male Average", f"{male_df['TOTAL'].mean():.1f}" if len(male_df) > 0 else "0.0")
    with col2:
        st.metric("Female Students", len(female_df))
        st.metric("Female Average", f"{female_df['TOTAL'].mean():.1f}" if len(female_df) > 0 else "0.0")
    with col3:
        gap = male_df['TOTAL'].mean() - female_df['TOTAL'].mean() if len(male_df) > 0 and len(female_df) > 0 else 0.0
        st.metric("Performance Gap", f"{gap:.1f}")
        st.caption("(Male - Female)")
    with col4:
        male_top = len(male_df[male_df['RANK'] <= 10])
        female_top = len(female_df[female_df['RANK'] <= 10])
        st.metric("Top 10 Split", f"{male_top}:{female_top}")
        st.caption("(M:F)")

    st.markdown("---")
    st.subheader("Subject Performance by Gender")
    gender_subject_data = []
    for subj in subject_cols:
        gender_subject_data.append({
            'Subject': subj,
            'Male': male_df[subj].mean() if len(male_df) > 0 else 0,
            'Female': female_df[subj].mean() if len(female_df) > 0 else 0,
            'Gap': (male_df[subj].mean() - female_df[subj].mean()) if len(male_df) > 0 and len(female_df) > 0 else 0
        })

    gender_subj_df = pd.DataFrame(gender_subject_data)

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Male', x=gender_subj_df['Subject'], y=gender_subj_df['Male'], marker_color='lightblue'))
        fig.add_trace(go.Bar(name='Female', x=gender_subj_df['Subject'], y=gender_subj_df['Female'], marker_color='lightpink'))
        fig.update_layout(title="Average Scores by Gender", barmode='group', xaxis_title="Subject", yaxis_title="Average Score")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(gender_subj_df, x='Subject', y='Gap',
                     title="Performance Gap (Male - Female)",
                     labels={'Gap': 'Score Difference'},
                     color='Gap',
                     color_continuous_scale=['lightpink', 'white', 'lightblue'],
                     color_continuous_midpoint=0)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Detailed Gender Comparison")
    st.dataframe(gender_subj_df.round(2), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Score Distribution by Gender")
    fig = go.Figure()
    fig.add_trace(go.Box(y=male_df['TOTAL'], name='Male', marker_color='lightblue'))
    fig.add_trace(go.Box(y=female_df['TOTAL'], name='Female', marker_color='lightpink'))
    fig.update_layout(title="Total Score Distribution by Gender", yaxis_title="Total Score")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Top 10 Male Students")
        top_males = male_df.nlargest(10, 'TOTAL')[['RANK', 'NAME OF STUDENTS', 'STRM', 'TOTAL']]
        st.dataframe(top_males, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("🏆 Top 10 Female Students")
        top_females = female_df.nlargest(10, 'TOTAL')[['RANK', 'NAME OF STUDENTS', 'STRM', 'TOTAL']]
        st.dataframe(top_females, use_container_width=True, hide_index=True)

# ---------------------------
# Main App
# ---------------------------
def main():
    # Custom CSS
    st.markdown("""
    <style>
        .main { 
            background: linear-gradient(135deg, #003366 0%, #0099FF 100%); 
        }
        .block-container { 
            background: rgba(255, 255, 255, 0.98); 
            border-radius: 15px; 
            padding: 2rem; 
            box-shadow: 0 8px 32px rgba(0, 51, 102, 0.2); 
        }
        h1 { 
            color: #003366; 
            font-weight: 800; 
            text-align: center; 
            padding: 1rem 0; 
        }
        h2 { 
            color: #003366; 
            border-bottom: 3px solid #0099FF; 
            padding-bottom: 0.5rem; 
        }
        h3 {
            color: #003366;
        }
        [data-testid="stMetricValue"] { 
            font-size: 1.8rem; 
            font-weight: bold; 
            color: #0099FF; 
        }
        .stButton>button { 
            background: linear-gradient(90deg, #003366 0%, #0099FF 100%); 
            color: white; 
            border: none; 
            border-radius: 10px; 
            padding: 0.75rem 2rem; 
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            box-shadow: 0 4px 12px rgba(0, 153, 255, 0.4);
            transform: translateY(-2px);
        }
        [data-testid="stSidebar"] { 
            background: linear-gradient(180deg, #003366 0%, #002147 100%); 
        }
        [data-testid="stSidebar"] .stMarkdown { 
            color: white !important; 
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: white !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f2f6;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            color: #003366;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, #003366 0%, #0099FF 100%);
            color: white;
        }
        .stSelectbox [data-baseweb="select"] {
            border-color: #0099FF;
        }
        .stTextInput input {
            border-color: #0099FF;
        }
        .stTextInput input:focus {
            border-color: #003366;
            box-shadow: 0 0 0 0.2rem rgba(0, 153, 255, 0.25);
        }
    </style>
    """, unsafe_allow_html=True)


    # Header
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.write("")
    with col2:
        if os.path.exists("./images/reamicscholar_logo.png"):
            st.image("./images/reamicscholar_logo.png", width=700)
        else:
            st.title("ReaMic Scholar")
    with col3:
        st.write("")
    st.markdown("---")

    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # Check login status
    if not st.session_state.logged_in:
        show_login()
        return

    # Sidebar
    st.sidebar.markdown(f"## 👤 {st.session_state.user_name}")
    st.sidebar.markdown(f"*Role: {st.session_state.user_role.title()}*")
    st.sidebar.markdown("---")

    # Navigation based on role
    if st.session_state.user_role == 'admin':
        st.sidebar.header("🎯 Admin Menu")
        page = st.sidebar.radio(
            "",
            ["Admin Dashboard", "Manage Students", "Manage Teachers", "Marks Entry Progress",
             "View Analytics"],
            label_visibility="collapsed"
        )
    else:  # teacher
        st.sidebar.header("👨‍🏫 Teacher Menu")
        page = st.sidebar.radio(
            "",
            ["Teacher Dashboard", "Enter Marks", "My Progress"],
            label_visibility="collapsed"
        )

    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.session_state.user_data = None
        st.rerun()

    # Route pages based on role and selection
    if st.session_state.user_role == 'admin':
        if page == "Admin Dashboard":
            show_admin_dashboard()
        elif page == "Manage Students":
            show_manage_students()
        elif page == "Manage Teachers":
            show_manage_teachers()
        elif page == "Marks Entry Progress":
            show_marks_entry_progress()
        elif page == "View Analytics":
            # Analytics selector
            col1, col2, col3 = st.columns(3)
            with col1:
                grade = st.selectbox("Select Grade", list(GRADES.keys()), key="analytics_grade")
            with col2:
                term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="analytics_term")
            with col3:
                year = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="analytics_year")
            
            exam_type = st.selectbox("Examination Type",
                                    ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
                                    key="analytics_exam_type")
            
            subject_cols = GRADES[grade]
            df = prepare_grade_data(grade, term, year, exam_type)
            
            if not df.empty:
                analysis_page = st.selectbox("Select Analysis",
                                            ["Dashboard", "Student Reports", "Class Analysis", 
                                             "Subject Analysis", "Stream Comparison", "Gender Analysis"],
                                            key="analytics_page")
                
                if analysis_page == "Dashboard":
                    show_dashboard(df, grade, subject_cols)
                elif analysis_page == "Student Reports":
                    show_student_reports(df, grade, subject_cols)
                elif analysis_page == "Class Analysis":
                    show_class_analysis(df, grade, subject_cols)
                elif analysis_page == "Subject Analysis":
                    show_subject_analysis(df, grade, subject_cols)
                elif analysis_page == "Stream Comparison":
                    show_stream_comparison(df, grade, subject_cols)
                elif analysis_page == "Gender Analysis":
                    show_gender_analysis(df, subject_cols, grade)
            else:
                st.info("📊 No data available for the selected parameters")
                st.markdown("---")
                st.markdown("### 🚀 Getting Started")
                st.markdown("""
                To view analytics, you need to:
                
                1. **Add Students** (Manage Students page)
                   - Add students for the grade you want to analyze
                   
                2. **Add Teachers** (Manage Teachers page)  
                   - Add teachers and assign them subjects
                   
                3. **Enter Marks** (Teachers can enter marks, or Admin can use sample data scripts)
                   - Teachers: Login and use "Enter Marks" page
                   - Admin: Run sample data generators (e.g., `generate_grade5_data.py`)
                
                4. **Select the correct parameters** above:
                   - Grade, Term, Year, and Examination Type must match your entered data
                
                **Quick Start:** Run a sample data generator script to populate the system with test data!
                """)
                
                # Show helpful info about sample data
                st.markdown("---")
                st.markdown("### 📁 Sample Data Generators Available")
                col1, col2 = st.columns(2)
                with col1:
                    st.code("python generate_grade5_data.py", language="bash")
                    st.caption("Creates 20 Grade 5 students with marks")
                with col2:
                    st.code("python generate_grade7_sample_data.py", language="bash")
                    st.caption("Creates 40 Grade 7 students with marks")
    
    else:  # teacher
        if page == "Teacher Dashboard":
            show_teacher_dashboard()
        elif page == "Enter Marks":
            show_enter_marks()
        elif page == "My Progress":
            show_teacher_progress()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**ReaMic Scholar v1.0**")
    st.sidebar.markdown("*by ReaMic Institute for Applied Intelligence*")
    st.sidebar.markdown("------")


if __name__ == "__main__":
    main()
