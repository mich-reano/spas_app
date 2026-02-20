import os
from io import BytesIO
import base64
import json
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from psycopg2.extras import RealDictCursor

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
    'Grade 1': ['Maths', 'English', 'Kiswahili', 'Environmental', 'Creative Activities/CRE'],
    'Grade 2': ['Maths', 'English', 'Kiswahili', 'Environmental', 'Creative Activities/CRE'],
    'Grade 3': ['Maths', 'English', 'Kiswahili', 'Environmental', 'Creative Activities/CRE'],
    'Grade 4': ['MAT', 'ENG', 'KIS', 'SCI', 'SST', 'C/ARTS'],
    'Grade 5': ['MAT', 'ENG', 'KIS', 'SCI', 'SST', 'C/ARTS'],
    'Grade 6': ['MAT', 'ENG', 'KIS', 'SCI', 'SST', 'C/ARTS'],
    'Grade 7': ['MAT', 'ENG', 'KIS', 'PRET', 'SST', 'AGR/N', 'C/ARTS', 'CRE', 'INT/SCI'],
    'Grade 8': ['MAT', 'ENG', 'KIS', 'PRET', 'SST', 'AGR/N', 'C/ARTS', 'CRE', 'INT/SCI'],
    'Grade 9': ['MAT', 'ENG', 'KIS', 'PRET', 'SST', 'AGR/N', 'C/ARTS', 'CRE', 'INT/SCI'],
}

# Grades 1-3 have no streams
NO_STREAM_GRADES = ['Grade 1', 'Grade 2', 'Grade 3']

DATABASE_URL = os.getenv("DATABASE_URL")

# ---------------------------
# Database Connection
# ---------------------------
@st.cache_resource
def get_connection():
    return psycopg2.connect('postgresql://postgres.xmjtsttcnkbslbdzhctv:reamicinsti@aws-1-eu-west-1.pooler.supabase.com:6543/postgres')


def get_cursor():
    conn = get_connection()
    try:
        conn.isolation_level  # test if alive
    except Exception:
        conn = psycopg2.connect('postgresql://postgres.xmjtsttcnkbslbdzhctv:reamicinsti@aws-1-eu-west-1.pooler.supabase.com:6543/postgres')
        st.cache_resource.clear()
    return conn.cursor(cursor_factory=RealDictCursor)


def execute_query(query, params=None, fetch=None):
    """
    Execute a SQL query.
    fetch: None (no result), 'one', 'all'
    Returns fetched rows or None.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch == 'one':
                result = cur.fetchone()
            elif fetch == 'all':
                result = cur.fetchall()
            else:
                result = None
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        st.error(f"Database error: {e}")
        return None


# ---------------------------
# Database Initialisation
# ---------------------------
def init_db():
    """Create tables if they don't exist."""
    queries = [
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'teacher',
            name TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS teacher_assignments (
            id SERIAL PRIMARY KEY,
            username TEXT REFERENCES users(username) ON DELETE CASCADE,
            grade TEXT NOT NULL,
            subject TEXT NOT NULL,
            stream TEXT  -- NULL for grades 1-3
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS students (
            adm_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            grade TEXT NOT NULL,
            stream TEXT,  -- NULL for grades 1-3
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS marks (
            id SERIAL PRIMARY KEY,
            adm_no TEXT REFERENCES students(adm_no) ON DELETE CASCADE,
            grade TEXT NOT NULL,
            term TEXT NOT NULL,
            year INTEGER NOT NULL,
            exam_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            score NUMERIC(5,2) NOT NULL DEFAULT 0,
            entered_by TEXT REFERENCES users(username),
            entered_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (adm_no, grade, term, year, exam_type, subject)
        )
        """,
    ]
    for q in queries:
        execute_query(q)

    # Seed default admin if not exists
    existing = execute_query(
        "SELECT username FROM users WHERE username = %s", ('admin',), fetch='one'
    )
    if not existing:
        execute_query(
            "INSERT INTO users (username, password, role, name) VALUES (%s,%s,%s,%s)",
            ('admin', 'admin123', 'admin', 'System Administrator')
        )


# ---------------------------
# User Management
# ---------------------------
def authenticate_user(username, password):
    row = execute_query(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password), fetch='one'
    )
    return dict(row) if row else None


def load_users():
    rows = execute_query("SELECT * FROM users", fetch='all')
    return {r['username']: dict(r) for r in rows} if rows else {}


def add_teacher(username, password, name, assignments):
    existing = execute_query("SELECT username FROM users WHERE username=%s", (username,), fetch='one')
    if existing:
        return False, "Username already exists"

    execute_query(
        "INSERT INTO users (username, password, role, name) VALUES (%s,%s,%s,%s)",
        (username, password, 'teacher', name)
    )
    for a in assignments:
        execute_query(
            "INSERT INTO teacher_assignments (username, grade, subject, stream) VALUES (%s,%s,%s,%s)",
            (username, a['grade'], a['subject'], a.get('stream'))
        )
    return True, "Teacher added successfully"


def get_teacher_assignments(username):
    rows = execute_query(
        "SELECT grade, subject, stream FROM teacher_assignments WHERE username=%s",
        (username,), fetch='all'
    )
    return [dict(r) for r in rows] if rows else []


def delete_teacher(username):
    row = execute_query("SELECT * FROM users WHERE username=%s", (username,), fetch='one')
    if not row:
        return False, "Teacher not found"
    if row['role'] != 'teacher':
        return False, "User is not a teacher"
    if st.session_state.get('username') == username:
        return False, "Cannot delete currently logged-in user"
    name = row['name']
    execute_query("DELETE FROM users WHERE username=%s", (username,))
    return True, f"Teacher {name} (@{username}) deleted successfully"


# ---------------------------
# Admin User Management
# ---------------------------
def add_admin(username, password, name):
    """Add a new admin user."""
    existing = execute_query(
        "SELECT username FROM users WHERE username=%s", (username,), fetch='one'
    )
    if existing:
        return False, "Username already exists"
    execute_query(
        "INSERT INTO users (username, password, role, name) VALUES (%s,%s,%s,%s)",
        (username, password, 'admin', name)
    )
    return True, f"Admin '{name}' (@{username}) added successfully"


def delete_admin(username):
    """Delete an admin user (cannot delete yourself)."""
    row = execute_query("SELECT * FROM users WHERE username=%s", (username,), fetch='one')
    if not row:
        return False, "User not found"
    if row['role'] != 'admin':
        return False, "User is not an admin"
    if st.session_state.get('username') == username:
        return False, "You cannot delete your own account"
    # Prevent deleting last admin
    count_row = execute_query(
        "SELECT COUNT(*) AS cnt FROM users WHERE role='admin'", fetch='one'
    )
    if count_row and count_row['cnt'] <= 1:
        return False, "Cannot delete the last admin account"
    name = row['name']
    execute_query("DELETE FROM users WHERE username=%s", (username,))
    return True, f"Admin '{name}' (@{username}) deleted successfully"




# ---------------------------
# Student Management
# ---------------------------
def load_students(grade_filter=None, stream_filter=None):
    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if grade_filter:
        query += " AND grade=%s"
        params.append(grade_filter)
    if stream_filter:
        query += " AND stream=%s"
        params.append(stream_filter)
    query += " ORDER BY name"
    rows = execute_query(query, params or None, fetch='all')
    return {r['adm_no']: dict(r) for r in rows} if rows else {}


def add_student(adm_no, name, gender, grade, stream):
    # Grades 1-3: no stream, auto-generate adm_no if blank
    if grade in NO_STREAM_GRADES:
        stream = None
        if not adm_no:
            words = name.strip().split()
            initials = ''.join([w[0].upper() for w in words if w])
            base = initials
            adm_no = base
            counter = 1
            while execute_query("SELECT adm_no FROM students WHERE adm_no=%s", (adm_no,), fetch='one'):
                adm_no = f"{base}{counter}"
                counter += 1
        # Check duplicate name in same grade
        dup = execute_query(
            "SELECT adm_no FROM students WHERE LOWER(name)=%s AND grade=%s",
            (name.lower(), grade), fetch='one'
        )
        if dup and dup['adm_no'] != adm_no:
            return False, "A student with this name already exists in this grade"
    elif grade in ['Grade 4', 'Grade 5', 'Grade 6']:
        if not adm_no:
            words = name.strip().split()
            initials = ''.join([w[0].upper() for w in words if w])
            base = f"{initials}-{stream}"
            adm_no = base
            counter = 1
            while execute_query("SELECT adm_no FROM students WHERE adm_no=%s", (adm_no,), fetch='one'):
                adm_no = f"{base}{counter}"
                counter += 1
        dup = execute_query(
            "SELECT adm_no FROM students WHERE LOWER(name)=%s AND grade=%s AND stream=%s",
            (name.lower(), grade, stream), fetch='one'
        )
        if dup and dup['adm_no'] != adm_no:
            return False, "A student with this name already exists in this grade and stream"
    else:
        if not adm_no:
            return False, "Admission number is required for Junior Secondary (Grades 7-9)"
        if execute_query("SELECT adm_no FROM students WHERE adm_no=%s", (adm_no,), fetch='one'):
            return False, "Admission number already exists"

    execute_query(
        "INSERT INTO students (adm_no, name, gender, grade, stream) VALUES (%s,%s,%s,%s,%s)",
        (adm_no, name, gender, grade, stream)
    )
    return True, f"Student added successfully with admission number: {adm_no}"


def delete_student(adm_no):
    row = execute_query("SELECT * FROM students WHERE adm_no=%s", (adm_no,), fetch='one')
    if not row:
        return False, "Student not found"
    name = row['name']
    execute_query("DELETE FROM students WHERE adm_no=%s", (adm_no,))
    return True, f"Student {name} (ADM NO: {adm_no}) deleted successfully."


# ---------------------------
# Marks Management
# ---------------------------
def get_exam_marks(grade, term, year, exam_type):
    """Return dict: {adm_no: {subject: score}}"""
    rows = execute_query(
        "SELECT adm_no, subject, score FROM marks WHERE grade=%s AND term=%s AND year=%s AND exam_type=%s",
        (grade, term, year, exam_type), fetch='all'
    )
    result = {}
    if rows:
        for r in rows:
            adm = r['adm_no']
            if adm not in result:
                result[adm] = {}
            result[adm][r['subject']] = float(r['score'])
    return result


def upsert_marks_bulk(records, teacher_username):
    """
    Upsert a list of marks.
    records: list of (adm_no, grade, term, year, exam_type, subject, score)

    Score = 0 is treated as "not entered" (blank/missing):
      - If a non-zero record already exists in the DB, it is LEFT UNCHANGED
        when the teacher submits 0 (prevents accidental erasure).
      - If no record exists yet, a 0 is simply not written.
    Only scores > 0 are upserted as valid marks.
    """
    for rec in records:
        adm_no, grade, term, year, exam_type, subject, score = rec
        if float(score) == 0:
            # Skip: 0 means "not yet entered"; preserve any existing valid score
            continue
        execute_query(
            """
            INSERT INTO marks (adm_no, grade, term, year, exam_type, subject, score, entered_by, entered_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (adm_no, grade, term, year, exam_type, subject)
            DO UPDATE SET score=EXCLUDED.score, entered_by=EXCLUDED.entered_by, entered_at=EXCLUDED.entered_at
            """,
            (adm_no, grade, term, year, exam_type, subject, score, teacher_username, datetime.now())
        )



# ---------------------------
# Marks Entry Progress Helper
# ---------------------------
def get_marks_entry_progress(grade, term, year, exam_type):
    """
    Return per-teacher progress for a given exam.
    A score of 0 is treated as NOT entered (blank/missing).
    Only scores > 0 count as valid entries.

    Returns a list of dicts:
    {
        username, name,
        assignments: [{grade, subject, stream, total_students,
                        entered, missing, pct,
                        missing_students: [{adm_no, name}]}]
        overall_total, overall_entered, overall_missing, overall_pct
    }
    """
    users = load_users()
    teachers = {u: d for u, d in users.items() if d['role'] == 'teacher'
                and any(a['grade'] == grade
                        for a in get_teacher_assignments(u))}

    # Pull all marks for this exam in one query — score > 0 only
    rows = execute_query(
        """SELECT adm_no, subject, score
           FROM marks
           WHERE grade=%s AND term=%s AND year=%s AND exam_type=%s
             AND score > 0""",
        (grade, term, year, exam_type), fetch='all'
    ) or []

    entered_set = {}          # {(adm_no, subject): score}
    for r in rows:
        entered_set[(r['adm_no'], r['subject'])] = float(r['score'])

    results = []
    for uname, udata in teachers.items():
        assignments = [a for a in get_teacher_assignments(uname)
                       if a['grade'] == grade]
        if not assignments:
            continue

        teacher_total = 0
        teacher_entered = 0
        assignment_detail = []

        for a in assignments:
            students = load_students(
                grade_filter=grade,
                stream_filter=a.get('stream')
            )
            total = len(students)
            entered_here = sum(
                1 for adm in students
                if (adm, a['subject']) in entered_set
            )
            missing_students = [
                {"adm_no": adm, "name": sdata['name']}
                for adm, sdata in students.items()
                if (adm, a['subject']) not in entered_set
            ]
            pct = (entered_here / total * 100) if total > 0 else 0

            assignment_detail.append({
                "grade": a['grade'],
                "subject": a['subject'],
                "stream": a.get('stream') or '—',
                "total_students": total,
                "entered": entered_here,
                "missing": total - entered_here,
                "pct": pct,
                "missing_students": missing_students,
            })
            teacher_total += total
            teacher_entered += entered_here

        overall_pct = (teacher_entered / teacher_total * 100) if teacher_total > 0 else 0
        results.append({
            "username": uname,
            "name": udata['name'],
            "assignments": assignment_detail,
            "overall_total": teacher_total,
            "overall_entered": teacher_entered,
            "overall_missing": teacher_total - teacher_entered,
            "overall_pct": overall_pct,
        })

    # Sort: incomplete first, then by name
    results.sort(key=lambda x: (x['overall_pct'] == 100, x['name']))
    return results


# ---------------------------
# Marks Entry Progress Helper
# ---------------------------
def get_marks_entry_progress(grade, term, year, exam_type):
    """
    Return per-teacher progress for a given exam.
    A score of 0 is treated as NOT entered (blank/missing).
    Only scores > 0 count as valid entries.

    Returns a list of dicts:
    {
        username, name,
        assignments: [{grade, subject, stream, total_students,
                        entered, missing, pct,
                        missing_students: [{adm_no, name}]}]
        overall_total, overall_entered, overall_missing, overall_pct
    }
    """
    users = load_users()
    teachers = {u: d for u, d in users.items() if d['role'] == 'teacher'
                and any(a['grade'] == grade
                        for a in get_teacher_assignments(u))}

    # Pull all marks for this exam in one query — score > 0 only
    rows = execute_query(
        """SELECT adm_no, subject, score
           FROM marks
           WHERE grade=%s AND term=%s AND year=%s AND exam_type=%s
             AND score > 0""",
        (grade, term, year, exam_type), fetch='all'
    ) or []

    entered_set = {}          # {(adm_no, subject): score}
    for r in rows:
        entered_set[(r['adm_no'], r['subject'])] = float(r['score'])

    results = []
    for uname, udata in teachers.items():
        assignments = [a for a in get_teacher_assignments(uname)
                       if a['grade'] == grade]
        if not assignments:
            continue

        teacher_total = 0
        teacher_entered = 0
        assignment_detail = []

        for a in assignments:
            students = load_students(
                grade_filter=grade,
                stream_filter=a.get('stream')
            )
            total = len(students)
            entered_here = sum(
                1 for adm in students
                if (adm, a['subject']) in entered_set
            )
            missing_students = [
                {"adm_no": adm, "name": sdata['name']}
                for adm, sdata in students.items()
                if (adm, a['subject']) not in entered_set
            ]
            pct = (entered_here / total * 100) if total > 0 else 0

            assignment_detail.append({
                "grade": a['grade'],
                "subject": a['subject'],
                "stream": a.get('stream') or '—',
                "total_students": total,
                "entered": entered_here,
                "missing": total - entered_here,
                "pct": pct,
                "missing_students": missing_students,
            })
            teacher_total += total
            teacher_entered += entered_here

        overall_pct = (teacher_entered / teacher_total * 100) if teacher_total > 0 else 0
        results.append({
            "username": uname,
            "name": udata['name'],
            "assignments": assignment_detail,
            "overall_total": teacher_total,
            "overall_entered": teacher_entered,
            "overall_missing": teacher_total - teacher_entered,
            "overall_pct": overall_pct,
        })

    # Sort: incomplete first, then by name
    results.sort(key=lambda x: (x['overall_pct'] == 100, x['name']))
    return results

# ---------------------------
# Performance Level Functions
# ---------------------------
def get_subject_performance_level(score):
    try:
        s = float(score)
    except Exception:
        return 'BE2', 1
    if s >= 90: return 'EE1', 8
    elif s >= 78: return 'EE2', 7
    elif s >= 65: return 'ME1', 6
    elif s >= 52: return 'ME2', 5
    elif s >= 39: return 'AE1', 4
    elif s >= 26: return 'AE2', 3
    elif s >= 13: return 'BE1', 2
    else: return 'BE2', 1


def get_primary_performance_level(total_score):
    # Grade 4-6: 6 subjects, max 600
    try: s = float(total_score)
    except: return 'BE2', 1
    if s >= 532: return 'EE1', 8
    elif s >= 456: return 'EE2', 7
    elif s >= 380: return 'ME1', 6
    elif s >= 304: return 'ME2', 5
    elif s >= 228: return 'AE1', 4
    elif s >= 152: return 'AE2', 3
    elif s >= 76: return 'BE1', 2
    else: return 'BE2', 1


def get_lower_primary_performance_level(total_score):
    # Grade 1-3: 5 subjects, max 500
    try: s = float(total_score)
    except: return 'BE2', 1
    if s >= 443: return 'EE1', 8
    elif s >= 380: return 'EE2', 7
    elif s >= 317: return 'ME1', 6
    elif s >= 254: return 'ME2', 5
    elif s >= 190: return 'AE1', 4
    elif s >= 127: return 'AE2', 3
    elif s >= 64: return 'BE1', 2
    else: return 'BE2', 1


def get_junior_performance_level(total_score):
    # Grade 7-9: 9 subjects, max 900
    try: s = float(total_score)
    except: return 'BE2', 1
    if s >= 798: return 'EE1', 8
    elif s >= 684: return 'EE2', 7
    elif s >= 570: return 'ME1', 6
    elif s >= 456: return 'ME2', 5
    elif s >= 342: return 'AE1', 4
    elif s >= 228: return 'AE2', 3
    elif s >= 114: return 'BE1', 2
    else: return 'BE2', 1


def get_performance_level_for_grade(total_score, grade):
    if grade in NO_STREAM_GRADES:
        return get_lower_primary_performance_level(total_score)
    elif grade in ['Grade 4', 'Grade 5', 'Grade 6']:
        return get_primary_performance_level(total_score)
    else:
        return get_junior_performance_level(total_score)


def get_performance_level(score):
    level, _ = get_subject_performance_level(score)
    return level


def get_performance_label(level):
    labels = {
        'EE1': 'Exceeding Expectation 1', 'EE2': 'Exceeding Expectation 2',
        'ME1': 'Meeting Expectation 1', 'ME2': 'Meeting Expectation 2',
        'AE1': 'Approaching Expectation 1', 'AE2': 'Approaching Expectation 2',
        'BE1': 'Below Expectation 1', 'BE2': 'Below Expectation 2',
    }
    return labels.get(level, level)


# ---------------------------
# Data Preparation
# ---------------------------
def prepare_grade_data(grade, term, year, exam_type):
    students = load_students(grade_filter=grade)
    if not students:
        return pd.DataFrame()

    exam_marks = get_exam_marks(grade, term, year, exam_type)
    subject_cols = GRADES[grade]

    rows = []
    for adm_no, student_data in students.items():
        row = {
            'ADM NO.': adm_no,
            'NAME OF STUDENTS': student_data['name'],
            'GENDER': student_data['gender'],
            'STRM': student_data.get('stream') or 'N/A',
        }
        for subject in subject_cols:
            if adm_no in exam_marks and subject in exam_marks[adm_no]:
                row[subject] = float(exam_marks[adm_no][subject])
            else:
                row[subject] = 0.0
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df['TOTAL'] = df[subject_cols].sum(axis=1)
    df['AVERAGE'] = df['TOTAL'] / len(subject_cols)

    perf_data = df.apply(lambda r: get_performance_level_for_grade(r['TOTAL'], grade), axis=1)
    df['P.LEVEL'] = perf_data.apply(lambda x: x[0])
    df['POINTS'] = perf_data.apply(lambda x: x[1])
    df['AV/LVL'] = df['P.LEVEL']
    df['RANK'] = df['TOTAL'].rank(ascending=False, method='dense').astype(int)

    return df


# ---------------------------
# PDF Functions
# ---------------------------
def create_pdf_report(student, school_name, grade, term, year, exam_type, df,
                      class_teacher, dhoi, hoi, subject_cols):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    school_name_style = ParagraphStyle('SchoolName', parent=styles['Normal'],
        fontSize=14, fontName='Times-Bold', textColor=colors.HexColor('#1a3a5c'),
        alignment=TA_CENTER, spaceAfter=2)
    school_info_style = ParagraphStyle('SchoolInfo', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica', textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER, spaceAfter=6)
    title_bar_style = ParagraphStyle('TitleBar', parent=styles['Normal'],
        fontSize=11, fontName='Times-Bold', textColor=colors.white, alignment=TA_CENTER)
    section_heading_style = ParagraphStyle('SectionHeading', parent=styles['Normal'],
        fontSize=9, fontName='Times-Bold', textColor=colors.HexColor('#1a3a5c'),
        spaceAfter=4, spaceBefore=6)
    body_text_style = ParagraphStyle('BodyText', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica', textColor=colors.black)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#666666'), alignment=TA_CENTER)

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(school_name.upper(), school_name_style))
    elements.append(Paragraph("P.O. Box 3-40308, SINDO, KENYA", school_info_style))
    elements.append(Paragraph("Tel: +254 710 302846 | Email: sindocomprehensive@gmail.com", school_info_style))

    title_data = [[Paragraph("STUDENT PERFORMANCE REPORT", title_bar_style)]]
    title_table = Table(title_data, colWidths=[7.5*inch])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1a3a5c')),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 8))

    stream_val = student.get('STRM', 'N/A')
    stream_display = ('Heroes (H)' if stream_val == 'H' else
                      'Champions (C)' if stream_val == 'C' else 'N/A')

    info_data = [
        [Paragraph(f"<b>Term:</b> {term}", body_text_style),
         Paragraph(f"<b>Year:</b> {year}", body_text_style),
         Paragraph(f"<b>Examination:</b> {exam_type}", body_text_style)],
        [Paragraph(f"<b>Grade/Class:</b> {grade}", body_text_style),
         Paragraph(f"<b>Stream:</b> {stream_display}", body_text_style), ""]
    ]
    info_table = Table(info_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    info_table.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),3), ('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    elements.append(info_table)
    elements.append(Spacer(1, 6))

    sep1 = Drawing(7.5*inch, 1)
    sep1.add(Line(0, 0, 7.5*inch, 0, strokeColor=colors.HexColor('#1a3a5c'), strokeWidth=0.8))
    elements.append(sep1)
    elements.append(Spacer(1, 6))

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
    learner_table.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),3), ('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    elements.append(learner_table)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("LEARNING AREAS PERFORMANCE", section_heading_style))
    perf_header = ['Learning Area', 'Score (%)', 'P.Level', 'Points']
    perf_data = [perf_header]
    for subj in subject_cols:
        score = float(student.get(subj, 0))
        perf_level, points = get_subject_performance_level(score)
        perf_data.append([subj, f"{score:.0f}", perf_level, str(points)])

    perf_table = Table(perf_data, colWidths=[3.2*inch, 1.4*inch, 1.4*inch, 1.5*inch])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a3a5c')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8), ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,1), (-1,-1), 8),
        ('ALIGN', (0,1), (0,-1), 'LEFT'), ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(perf_table)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("OVERALL PERFORMANCE SUMMARY", section_heading_style))
    summary_data = [
        [Paragraph("<b>Total Score:</b>", body_text_style), f"{student.get('TOTAL', 0):.0f}",
         Paragraph("<b>Average Score:</b>", body_text_style), f"{student.get('AVERAGE', 0):.1f}%"],
        [Paragraph("<b>Overall P.Level:</b>", body_text_style), student.get('P.LEVEL', 'N/A'),
         Paragraph("<b>Points:</b>", body_text_style), str(student.get('POINTS', 0))],
        [Paragraph("<b>Class Position:</b>", body_text_style), f"{student.get('RANK', '')}/{len(df)}",
         Paragraph("<b>Class Average:</b>", body_text_style), f"{df['AVERAGE'].mean():.1f}%"]
    ]
    summary_table = Table(summary_data, colWidths=[1.9*inch, 1.85*inch, 1.9*inch, 1.85*inch])
    summary_table.setStyle(TableStyle([
        ('FONTSIZE',(0,0),(-1,-1),8),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f9f9f9')),
        ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('ALIGN',(1,0),(1,-1),'CENTER'), ('ALIGN',(3,0),(3,-1),'CENTER'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 8))

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

    comment_table = Table([[Paragraph(comment, body_text_style)]], colWidths=[7.5*inch])
    comment_table.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
        ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),6), ('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))
    elements.append(comment_table)
    elements.append(Spacer(1, 8))

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
        ('FONTSIZE',(0,0),(-1,-1),7),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
        ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    elements.append(auth_table)
    elements.append(Spacer(1, 8))

    sep2 = Drawing(7.5*inch, 1)
    sep2.add(Line(0, 0, 7.5*inch, 0, strokeColor=colors.HexColor('#cccccc'), strokeWidth=0.5))
    elements.append(sep2)
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(
        "Powered by ReaMic Institute for Applied Intelligence • Advancing Intelligence for Real world Impact.| +254 741 908009",
        footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def create_class_list_pdf(df, school_name, grade, term, year, exam_type, class_teacher, subject_cols):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=25)
    elements = []
    styles = getSampleStyleSheet()

    school_name_style = ParagraphStyle('SchoolName', parent=styles['Normal'],
        fontSize=14, fontName='Times-Bold', textColor=colors.HexColor('#1a3a5c'),
        alignment=TA_CENTER, spaceAfter=2)
    school_info_style = ParagraphStyle('SchoolInfo', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica', textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER, spaceAfter=4)
    title_bar_style = ParagraphStyle('TitleBar', parent=styles['Normal'],
        fontSize=11, fontName='Times-Bold', textColor=colors.white, alignment=TA_CENTER)
    body_text_style = ParagraphStyle('BodyText', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica', textColor=colors.black)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
        fontSize=6, fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#666666'), alignment=TA_CENTER)

    elements.append(Spacer(1, 5))
    elements.append(Paragraph(school_name.upper(), school_name_style))
    elements.append(Paragraph("P.O. Box 3-40308, SINDO, KENYA", school_info_style))
    elements.append(Paragraph("Tel: +254 710 302846 | Email: sindocomprehensive@gmail.com", school_info_style))

    title_data = [[Paragraph("CLASS PERFORMANCE LIST", title_bar_style)]]
    title_table = Table(title_data, colWidths=[10.7*inch])
    title_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#1a3a5c')),
        ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 6))

    info_data = [[
        Paragraph(f"<b>Grade/Class:</b> {grade}", body_text_style),
        Paragraph(f"<b>Term:</b> {term}", body_text_style),
        Paragraph(f"<b>Year:</b> {year}", body_text_style),
        Paragraph(f"<b>Examination:</b> {exam_type}", body_text_style)
    ]]
    info_table = Table(info_data, colWidths=[2.7*inch, 2.7*inch, 2.7*inch, 2.6*inch])
    info_table.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),2), ('BOTTOMPADDING',(0,0),(-1,-1),2)]))
    elements.append(info_table)
    elements.append(Spacer(1, 4))

    sep1 = Drawing(10.7*inch, 1)
    sep1.add(Line(0, 0, 10.7*inch, 0, strokeColor=colors.HexColor('#1a3a5c'), strokeWidth=0.8))
    elements.append(sep1)
    elements.append(Spacer(1, 6))

    sorted_df = df.sort_values('RANK')
    is_no_stream = grade in NO_STREAM_GRADES
    if is_no_stream:
        header = ['Rank', 'ADM NO.', 'Name', 'Gender'] + subject_cols + ['Total', 'Avg', 'P.Level', 'Pts']
    else:
        header = ['Rank', 'ADM NO.', 'Name', 'Gender', 'Strm'] + subject_cols + ['Total', 'Avg', 'P.Level', 'Pts']
    table_data = [header]

    for _, row in sorted_df.iterrows():
        if is_no_stream:
            row_data = [str(row['RANK']), str(row.get('ADM NO.','')),
                        str(row.get('NAME OF STUDENTS',''))[:25], str(row.get('GENDER',''))]
        else:
            row_data = [str(row['RANK']), str(row.get('ADM NO.','')),
                        str(row.get('NAME OF STUDENTS',''))[:25],
                        str(row.get('GENDER','')), str(row.get('STRM',''))]
        for subj in subject_cols:
            row_data.append(f"{row.get(subj, 0):.0f}")
        row_data.extend([f"{row.get('TOTAL',0):.0f}", f"{row.get('AVERAGE',0):.1f}",
                         row.get('P.LEVEL','BE2'), str(row.get('POINTS',1))])
        table_data.append(row_data)

    num_subjects = len(subject_cols)
    if is_no_stream:
        base_widths = [0.3*inch, 0.6*inch, 1.7*inch, 0.35*inch]
    else:
        base_widths = [0.3*inch, 0.6*inch, 1.5*inch, 0.3*inch, 0.3*inch]
    subject_widths = [0.4*inch] * num_subjects
    end_widths = [0.45*inch, 0.4*inch, 0.45*inch, 0.3*inch]
    col_widths = base_widths + subject_widths + end_widths

    class_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    class_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1a3a5c')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0),7), ('FONTSIZE',(0,1),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),3), ('TOPPADDING',(0,0),(-1,-1),3),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(class_table)
    elements.append(Spacer(1, 8))

    legend_title = Paragraph("<b>PERFORMANCE LEVEL KEY</b>", body_text_style)
    elements.append(legend_title)
    elements.append(Spacer(1, 3))
    legend_data = [
        ['EE1 (8pts)', 'EE2 (7pts)', 'ME1 (6pts)', 'ME2 (5pts)'],
        ['AE1 (4pts)', 'AE2 (3pts)', 'BE1 (2pts)', 'BE2 (1pt)']
    ]
    legend_table = Table(legend_data, colWidths=[2.7*inch, 2.7*inch, 2.7*inch, 2.6*inch])
    legend_table.setStyle(TableStyle([
        ('FONTSIZE',(0,0),(-1,-1),7), ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('TOPPADDING',(0,0),(-1,-1),3), ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f9f9f9')),
    ]))
    elements.append(legend_table)
    elements.append(Spacer(1, 8))

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
        ('FONTSIZE',(0,0),(-1,-1),7), ('TOPPADDING',(0,0),(-1,-1),3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f9f9f9')),
        ('SPAN',(0,0),(-1,0)), ('ALIGN',(0,0),(-1,0),'CENTER'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 8))

    auth_data = [[
        Paragraph(f"<b>Class Teacher:</b> {class_teacher}", body_text_style),
        Paragraph("<b>Signature:</b> _______________", body_text_style),
        Paragraph("<b>Date:</b> _______________", body_text_style)
    ]]
    auth_table = Table(auth_data, colWidths=[3.5*inch, 3.6*inch, 3.6*inch])
    auth_table.setStyle(TableStyle([
        ('FONTSIZE',(0,0),(-1,-1),7), ('TOPPADDING',(0,0),(-1,-1),3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
    ]))
    elements.append(auth_table)
    elements.append(Spacer(1, 6))

    sep2 = Drawing(10.7*inch, 1)
    sep2.add(Line(0, 0, 10.7*inch, 0, strokeColor=colors.HexColor('#cccccc'), strokeWidth=0.5))
    elements.append(sep2)
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(
        "Powered by ReaMic Institute for Applied Intelligence • Advancing Intelligence for Real World Impact. | +254 741 908009",
        footer_style))

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

    all_students = load_students()
    users = load_users()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Students", len(all_students))
    with col2:
        teacher_count = sum(1 for u in users.values() if u['role'] == 'teacher')
        st.metric("Total Teachers", teacher_count)
    with col3:
        grade_counts = {}
        for s in all_students.values():
            grade_counts[s['grade']] = grade_counts.get(s['grade'], 0) + 1
        st.metric("Grades Active", len(grade_counts))

    st.markdown("---")
    st.subheader("📊 Students by Grade")
    if grade_counts:
        fig = px.bar(x=list(grade_counts.keys()), y=list(grade_counts.values()),
                     labels={'x': 'Grade', 'y': 'Number of Students'},
                     title="Student Distribution by Grade")
        fig.update_traces(marker_color='lightblue')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📚 No students registered yet")


def show_manage_students():
    st.header("👥 Manage Students")
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Student", "📋 View Students", "✏️ Edit Student", "🗑️ Delete Student"])

    with tab1:
        st.subheader("Add New Student")
        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox("Grade", list(GRADES.keys()), key="add_grade")
            no_stream = grade in NO_STREAM_GRADES

            if grade in ['Grade 7', 'Grade 8', 'Grade 9']:
                adm_no = st.text_input("Admission Number *", key="add_adm_junior",
                                       help="Required for Junior Secondary")
            else:
                adm_no = st.text_input("Admission Number (Optional)", key="add_adm_primary",
                                       help="Leave blank to auto-generate from name initials")
            name = st.text_input("Student Name *", key="add_name")

        with col2:
            gender = st.selectbox("Gender", ["M", "F"], key="add_gender")
            if no_stream:
                st.info("ℹ️ Grades 1–3 have no streams")
                stream = None
            else:
                stream = st.selectbox("Stream", ["H", "C"],
                                      format_func=lambda x: "Heroes (H)" if x == "H" else "Champions (C)",
                                      key="add_stream")

        if st.button("Add Student", type="primary"):
            if name and grade:
                success, message = add_student(adm_no, name, gender, grade, stream)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("Please fill in Student Name")

    with tab2:
        st.subheader("All Students")
        col1, col2 = st.columns(2)
        with col1:
            filter_grade = st.selectbox("Filter by Grade", ["All"] + list(GRADES.keys()), key="filter_grade")
        with col2:
            filter_stream = st.text_input("Filter by Stream (H/C)", key="filter_stream")

        students = load_students(
            grade_filter=filter_grade if filter_grade != "All" else None,
            stream_filter=filter_stream.upper() if filter_stream else None
        )

        if students:
            students_list = [{'ADM NO.': a, 'Name': d['name'], 'Gender': d['gender'],
                               'Grade': d['grade'], 'Stream': d.get('stream') or '—'}
                             for a, d in students.items()]
            df = pd.DataFrame(students_list)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(df)} students")
        else:
            st.info("No students found")

    with tab3:
        st.subheader("Edit Student")
        all_students = load_students()
        if all_students:
            # Build a readable label list for the selectbox
            adm_labels = {
                adm: f"{adm} — {d['name']} ({d['grade']}{'/' + d['stream'] if d.get('stream') else ''})"
                for adm, d in all_students.items()
            }
            adm_select = st.selectbox(
                "Select Student by ADM NO.",
                list(adm_labels.keys()),
                format_func=lambda k: adm_labels[k],
                key="edit_select"
            )

            if adm_select:
                student = all_students[adm_select]

                # ── Confirmation card (read-only) ──────────────────────────
                st.markdown("#### 📋 Current Student Record")
                st.info(
                    f"**Name:** {student['name']}  |  "
                    f"**Gender:** {student['gender']}  |  "
                    f"**Grade:** {student['grade']}  |  "
                    f"**Stream:** {student.get('stream') or '—'}  |  "
                    f"**ADM NO.:** {adm_select}"
                )
                st.caption("Confirm this is the correct student before making changes below.")
                st.markdown("---")

                # ── Editable form ──────────────────────────────────────────
                st.markdown("#### ✏️ Make Changes")
                col1, col2 = st.columns(2)
                with col1:
                    edit_name = st.text_input(
                        "Student Name", value=student['name'], key="edit_name"
                    )
                    edit_gender = st.selectbox(
                        "Gender", ["M", "F"],
                        index=0 if student['gender'] == 'M' else 1,
                        key="edit_gender"
                    )
                with col2:
                    edit_grade = st.selectbox(
                        "Grade", list(GRADES.keys()),
                        index=list(GRADES.keys()).index(student['grade']),
                        key="edit_grade"
                    )
                    if edit_grade not in NO_STREAM_GRADES:
                        current_stream = student.get('stream') or 'H'
                        edit_stream = st.selectbox(
                            "Stream", ["H", "C"],
                            format_func=lambda x: "Heroes (H)" if x == "H" else "Champions (C)",
                            index=0 if current_stream == 'H' else 1,
                            key="edit_stream"
                        )
                    else:
                        edit_stream = None
                        st.info("ℹ️ Grades 1–3 have no streams")

                # Show a diff preview so the admin sees exactly what changes
                changes = []
                if edit_name != student['name']:
                    changes.append(f"**Name:** ~~{student['name']}~~ → {edit_name}")
                if edit_gender != student['gender']:
                    changes.append(f"**Gender:** ~~{student['gender']}~~ → {edit_gender}")
                if edit_grade != student['grade']:
                    changes.append(f"**Grade:** ~~{student['grade']}~~ → {edit_grade}")
                cur_stream = student.get('stream') or '—'
                new_stream_disp = edit_stream or '—'
                if new_stream_disp != cur_stream:
                    changes.append(f"**Stream:** ~~{cur_stream}~~ → {new_stream_disp}")

                if changes:
                    st.markdown("**Changes to be saved:**")
                    for c in changes:
                        st.markdown(f"  • {c}")
                else:
                    st.caption("No changes detected yet.")

                if st.button("💾 Update Student", type="primary"):
                    execute_query(
                        "UPDATE students SET name=%s, gender=%s, grade=%s, stream=%s WHERE adm_no=%s",
                        (edit_name, edit_gender, edit_grade, edit_stream, adm_select)
                    )
                    st.success(f"✅ Student **{edit_name}** updated successfully!")
                    st.rerun()
        else:
            st.info("No students to edit")

    with tab4:
        st.subheader("Delete Student")
        st.warning("⚠️ **Warning:** Deleting a student will permanently remove their record and all associated marks.")
        all_students = load_students()
        if all_students:
            col1, col2 = st.columns(2)
            with col1:
                del_grade = st.selectbox("Filter by Grade", ["All"] + list(GRADES.keys()), key="del_filter_grade")
            with col2:
                del_stream = st.text_input("Filter by Stream", key="del_filter_stream")

            filtered = load_students(
                grade_filter=del_grade if del_grade != "All" else None,
                stream_filter=del_stream.upper() if del_stream else None
            )

            if filtered:
                options = {f"{a} - {d['name']} ({d['grade']})": a for a, d in filtered.items()}
                selected = st.selectbox("Select Student to Delete", list(options.keys()), key="del_student_select")
                if selected:
                    sel_adm = options[selected]
                    sd = filtered[sel_adm]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Name:** {sd['name']}")
                        st.info(f"**Grade:** {sd['grade']}")
                    with col2:
                        st.info(f"**ADM NO.:** {sel_adm}")
                        st.info(f"**Stream:** {sd.get('stream') or '—'}")

                    confirm = st.checkbox(f"I confirm deletion of {sd['name']} ({sel_adm})", key="del_confirm")
                    if st.button("🗑️ Delete Student", type="primary", disabled=not confirm):
                        success, message = delete_student(sel_adm)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            else:
                st.info("No students match the filter")
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

        if 'teacher_assignments' not in st.session_state:
            st.session_state.teacher_assignments = []

        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            new_grade = st.selectbox("Grade", list(GRADES.keys()), key="new_assignment_grade")
        with col2:
            new_subject = st.selectbox("Subject", GRADES[new_grade], key="new_assignment_subject")
        with col3:
            if new_grade in NO_STREAM_GRADES:
                st.info("No streams for this grade")
                new_stream = None
            else:
                new_stream = st.selectbox("Stream", ["H", "C", "BOTH"],
                                          format_func=lambda x: "Heroes" if x == "H" else ("Champions" if x == "C" else "Both Streams"),
                                          key="new_assignment_stream")
        with col4:
            st.write("")
            st.write("")
            if st.button("➕ Add", type="primary", use_container_width=True):
                if new_grade in NO_STREAM_GRADES:
                    a = {"grade": new_grade, "subject": new_subject, "stream": None}
                    if a not in st.session_state.teacher_assignments:
                        st.session_state.teacher_assignments.append(a)
                        st.success(f"Added: {new_grade} → {new_subject}")
                    else:
                        st.warning("Assignment already exists")
                elif new_stream == "BOTH":
                    for s in ["H", "C"]:
                        a = {"grade": new_grade, "subject": new_subject, "stream": s}
                        if a not in st.session_state.teacher_assignments:
                            st.session_state.teacher_assignments.append(a)
                    st.success(f"Added: {new_grade} → {new_subject} → Both Streams")
                else:
                    a = {"grade": new_grade, "subject": new_subject, "stream": new_stream}
                    if a not in st.session_state.teacher_assignments:
                        st.session_state.teacher_assignments.append(a)
                        st.success(f"Added: {new_grade} → {new_subject} → {new_stream}")
                    else:
                        st.warning("Assignment already exists")
                st.rerun()

        if st.session_state.teacher_assignments:
            st.markdown("#### 📝 Current Assignments")
            for idx, a in enumerate(st.session_state.teacher_assignments):
                col1, col2 = st.columns([4, 1])
                with col1:
                    stream_lbl = ("Heroes (H)" if a.get('stream') == "H" else
                                  "Champions (C)" if a.get('stream') == "C" else "No Stream")
                    st.write(f"• {a['grade']} → {a['subject']} → {stream_lbl}")
                with col2:
                    if st.button("🗑️", key=f"rm_{idx}"):
                        st.session_state.teacher_assignments.pop(idx)
                        st.rerun()

        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("💾 Save Teacher", type="primary", use_container_width=True):
                if username and password and name and st.session_state.teacher_assignments:
                    success, message = add_teacher(username, password, name, st.session_state.teacher_assignments)
                    if success:
                        st.success(message)
                        st.session_state.teacher_assignments = []
                    else:
                        st.error(message)
                else:
                    st.warning("Fill in all fields and add at least one assignment")
        with col2:
            if st.button("🔄 Clear All", use_container_width=True):
                st.session_state.teacher_assignments = []
                st.rerun()

    with tab2:
        st.subheader("All Teachers")
        users = load_users()
        teachers = {u: d for u, d in users.items() if d['role'] == 'teacher'}
        if teachers:
            for uname, teacher in teachers.items():
                assignments = get_teacher_assignments(uname)
                with st.expander(f"👨‍🏫 {teacher['name']} (@{uname})", expanded=False):
                    if assignments:
                        for a in assignments:
                            s = a.get('stream') or 'No Stream'
                            st.write(f"• {a['grade']} → {a['subject']} → {s}")
                    else:
                        st.write("No assignments")
        else:
            st.info("No teachers registered yet")

    with tab3:
        st.subheader("Delete Teacher")
        st.warning("⚠️ Deleting a teacher removes their account permanently.")
        users = load_users()
        teachers = {u: d for u, d in users.items() if d['role'] == 'teacher'}
        if teachers:
            options = {f"{d['name']} (@{u})": u for u, d in teachers.items()}
            selected = st.selectbox("Select Teacher", list(options.keys()), key="del_teacher_select")
            if selected:
                sel_uname = options[selected]
                td = teachers[sel_uname]
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Name:** {td['name']}")
                with col2:
                    st.info(f"**Username:** {sel_uname}")
                if st.session_state.get('username') == sel_uname:
                    st.error("❌ Cannot delete your own account!")
                else:
                    confirm = st.checkbox(f"Confirm deletion of {td['name']}", key="del_teacher_confirm")
                    if st.button("🗑️ Delete Teacher", type="primary", disabled=not confirm):
                        success, message = delete_teacher(sel_uname)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("No teachers to delete")




def show_manage_admins():
    st.header("🔑 Manage Admin Users")
    st.markdown("*Add or remove admin accounts. You cannot delete your own account or the last remaining admin.*")
    st.markdown("---")

    tab1, tab2 = st.tabs(["➕ Add Admin", "🗑️ Remove Admin"])

    with tab1:
        st.subheader("Add New Admin")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_username = st.text_input("Username", key="admin_new_username")
        with col2:
            new_password = st.text_input("Password", type="password", key="admin_new_password")
        with col3:
            new_name = st.text_input("Full Name", key="admin_new_name")

        st.caption("⚠️ Passwords are stored as plain text — advise new admins to use a unique password.")

        if st.button("➕ Create Admin Account", type="primary", use_container_width=True):
            if new_username and new_password and new_name:
                success, message = add_admin(new_username, new_password, new_name)
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)
            else:
                st.warning("Please fill in all three fields.")

    with tab2:
        st.subheader("Remove Admin")
        st.warning("⚠️ This action is permanent. You cannot remove yourself or the last admin.")

        users = load_users()
        admins = {u: d for u, d in users.items()
                  if d['role'] == 'admin' and u != st.session_state.get('username')}

        if not admins:
            st.info("No other admin accounts to remove.")
        else:
            options = {f"{d['name']} (@{u})": u for u, d in admins.items()}
            selected = st.selectbox("Select Admin to Remove", list(options.keys()),
                                    key="del_admin_select")
            if selected:
                sel_uname = options[selected]
                sel_data = admins[sel_uname]

                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Name:** {sel_data['name']}")
                with col2:
                    st.info(f"**Username:** {sel_uname}")

                confirm = st.checkbox(
                    f"I confirm I want to permanently delete admin @{sel_uname}",
                    key="del_admin_confirm"
                )
                if st.button("🗑️ Delete Admin", type="primary", disabled=not confirm,
                             use_container_width=True):
                    success, message = delete_admin(sel_uname)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        st.markdown("---")
        st.subheader("Current Admin Accounts")
        all_admins = {u: d for u, d in load_users().items() if d['role'] == 'admin'}
        admin_rows = [
            {"Username": u,
             "Name": d['name'],
             "You": "👈 (you)" if u == st.session_state.get('username') else ""}
            for u, d in all_admins.items()
        ]
        import pandas as pd
        st.dataframe(pd.DataFrame(admin_rows), use_container_width=True, hide_index=True)




def show_marks_entry_progress():
    st.header("📋 Marks Entry Progress")
    st.markdown("*Track how far each teacher has gone with entering marks. Only scores > 0 count as entered — zeros are flagged as missing.*")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        grade = st.selectbox("Grade", list(GRADES.keys()), key="mep_grade")
    with col2:
        term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="mep_term")
    with col3:
        year = st.number_input("Year", min_value=2020, max_value=2030,
                               value=datetime.now().year, key="mep_year")

    exam_type = st.selectbox(
        "Examination Type",
        ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
        key="mep_exam"
    )

    if st.button("🔍 Check Progress", type="primary", use_container_width=True):
        with st.spinner("Calculating progress…"):
            results = get_marks_entry_progress(grade, term, year, exam_type)

        if not results:
            st.warning("No teachers are assigned to this grade, or no students exist yet.")
            return

        st.markdown("---")

        # ── Summary metrics ───────────────────────────────────────────────────
        grand_total    = sum(r['overall_total']   for r in results)
        grand_entered  = sum(r['overall_entered'] for r in results)
        grand_missing  = sum(r['overall_missing'] for r in results)
        grand_pct      = (grand_entered / grand_total * 100) if grand_total > 0 else 0
        complete_count = sum(1 for r in results if r['overall_pct'] == 100)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Entry Slots", grand_total)
        with col2:
            st.metric("✅ Entered (score > 0)", grand_entered)
        with col3:
            st.metric("⚠️ Missing / Zero", grand_missing)
        with col4:
            st.metric("Overall Progress", f"{grand_pct:.1f}%")

        # Overall progress bar
        bar_color = "green" if grand_pct == 100 else ("orange" if grand_pct >= 50 else "red")
        st.progress(grand_pct / 100)

        if complete_count == len(results):
            st.success("🎉 All teachers have completed marks entry!")
        else:
            pending = len(results) - complete_count
            st.info(f"⏳ {pending} teacher(s) still have pending entries.")

        st.markdown("---")

        # ── Per-teacher breakdown ─────────────────────────────────────────────
        st.subheader("👨‍🏫 Per-Teacher Breakdown")

        for r in results:
            pct = r['overall_pct']
            if pct == 100:
                icon, status = "🟢", "Complete"
            elif pct >= 75:
                icon, status = "🟡", "Almost Done"
            elif pct >= 25:
                icon, status = "🟠", "In Progress"
            else:
                icon, status = "🔴", "Barely Started" if pct > 0 else "Not Started"

            header_label = (
                f"{icon} **{r['name']}** (@{r['username']})  —  "
                f"{r['overall_entered']}/{r['overall_total']} entered  "
                f"({pct:.1f}%)  [{status}]"
            )

            with st.expander(header_label, expanded=(pct < 100)):
                st.progress(pct / 100)

                # ── Per-assignment table ──────────────────────────────────────
                import pandas as pd
                assign_rows = []
                for a in r['assignments']:
                    a_pct = a['pct']
                    if a_pct == 100:
                        a_status = "✅ Complete"
                    elif a_pct > 0:
                        a_status = f"⏳ {a_pct:.0f}%"
                    else:
                        a_status = "❌ Not Started"

                    assign_rows.append({
                        "Subject": a['subject'],
                        "Stream": a['stream'],
                        "Students": a['total_students'],
                        "Entered": a['entered'],
                        "Missing": a['missing'],
                        "Status": a_status,
                    })

                assign_df = pd.DataFrame(assign_rows)

                # Color the Status column via styling
                def color_status(val):
                    if val.startswith("✅"):
                        return "background-color: #d4edda; color: #155724;"
                    elif val.startswith("❌"):
                        return "background-color: #f8d7da; color: #721c24;"
                    else:
                        return "background-color: #fff3cd; color: #856404;"

                styled = assign_df.style.applymap(color_status, subset=["Status"])
                st.dataframe(styled, use_container_width=True, hide_index=True)

                # ── Missing students drill-down ───────────────────────────────
                missing_assignments = [a for a in r['assignments'] if a['missing'] > 0]
                if missing_assignments:
                    st.markdown("**⚠️ Missing / Zero-Score Students:**")
                    for a in missing_assignments:
                        if a['missing_students']:
                            st.markdown(
                                f"<div style='"
                                f"background:#fff3cd;border-left:4px solid #ffc107;"
                                f"padding:6px 10px;margin:6px 0;border-radius:4px;"
                                f"font-weight:600;'>"
                                f"Subject: {a['subject']} | Stream: {a['stream']} | "
                                f"{a['missing']} student(s) missing"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                            miss_df = pd.DataFrame(a['missing_students'])
                            miss_df.columns = ["ADM NO.", "Student Name"]
                            st.dataframe(miss_df, use_container_width=True, hide_index=True)
                else:
                    st.success("All students have valid scores for this teacher's subjects.")

        st.markdown("---")

        # ── Subject-level summary table ───────────────────────────────────────
        st.subheader("📚 Subject-Level Summary")
        subject_summary = {}
        for r in results:
            for a in r['assignments']:
                key = f"{a['subject']} (Stream: {a['stream']})"
                if key not in subject_summary:
                    subject_summary[key] = {
                        "Subject": a['subject'],
                        "Stream": a['stream'],
                        "Teacher": r['name'],
                        "Total": a['total_students'],
                        "Entered": a['entered'],
                        "Missing": a['missing'],
                        "Progress": f"{a['pct']:.1f}%",
                    }

        if subject_summary:
            subj_df = pd.DataFrame(list(subject_summary.values()))
            subj_df = subj_df.sort_values("Missing", ascending=False)
            st.dataframe(subj_df, use_container_width=True, hide_index=True)




def show_marks_entry_progress():
    st.header("📋 Marks Entry Progress")
    st.markdown("*Track how far each teacher has gone with entering marks. Only scores > 0 count as entered — zeros are flagged as missing.*")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        grade = st.selectbox("Grade", list(GRADES.keys()), key="mep_grade")
    with col2:
        term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="mep_term")
    with col3:
        year = st.number_input("Year", min_value=2020, max_value=2030,
                               value=datetime.now().year, key="mep_year")

    exam_type = st.selectbox(
        "Examination Type",
        ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
        key="mep_exam"
    )

    if st.button("🔍 Check Progress", type="primary", use_container_width=True):
        with st.spinner("Calculating progress…"):
            results = get_marks_entry_progress(grade, term, year, exam_type)

        if not results:
            st.warning("No teachers are assigned to this grade, or no students exist yet.")
            return

        st.markdown("---")

        # ── Summary metrics ───────────────────────────────────────────────────
        grand_total    = sum(r['overall_total']   for r in results)
        grand_entered  = sum(r['overall_entered'] for r in results)
        grand_missing  = sum(r['overall_missing'] for r in results)
        grand_pct      = (grand_entered / grand_total * 100) if grand_total > 0 else 0
        complete_count = sum(1 for r in results if r['overall_pct'] == 100)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Entry Slots", grand_total)
        with col2:
            st.metric("✅ Entered (score > 0)", grand_entered)
        with col3:
            st.metric("⚠️ Missing / Zero", grand_missing)
        with col4:
            st.metric("Overall Progress", f"{grand_pct:.1f}%")

        # Overall progress bar
        bar_color = "green" if grand_pct == 100 else ("orange" if grand_pct >= 50 else "red")
        st.progress(grand_pct / 100)

        if complete_count == len(results):
            st.success("🎉 All teachers have completed marks entry!")
        else:
            pending = len(results) - complete_count
            st.info(f"⏳ {pending} teacher(s) still have pending entries.")

        st.markdown("---")

        # ── Per-teacher breakdown ─────────────────────────────────────────────
        st.subheader("👨‍🏫 Per-Teacher Breakdown")

        for r in results:
            pct = r['overall_pct']
            if pct == 100:
                icon, status = "🟢", "Complete"
            elif pct >= 75:
                icon, status = "🟡", "Almost Done"
            elif pct >= 25:
                icon, status = "🟠", "In Progress"
            else:
                icon, status = "🔴", "Barely Started" if pct > 0 else "Not Started"

            header_label = (
                f"{icon} **{r['name']}** (@{r['username']})  —  "
                f"{r['overall_entered']}/{r['overall_total']} entered  "
                f"({pct:.1f}%)  [{status}]"
            )

            with st.expander(header_label, expanded=(pct < 100)):
                st.progress(pct / 100)

                # ── Per-assignment table ──────────────────────────────────────
                import pandas as pd
                assign_rows = []
                for a in r['assignments']:
                    a_pct = a['pct']
                    if a_pct == 100:
                        a_status = "✅ Complete"
                    elif a_pct > 0:
                        a_status = f"⏳ {a_pct:.0f}%"
                    else:
                        a_status = "❌ Not Started"

                    assign_rows.append({
                        "Subject": a['subject'],
                        "Stream": a['stream'],
                        "Students": a['total_students'],
                        "Entered": a['entered'],
                        "Missing": a['missing'],
                        "Status": a_status,
                    })

                assign_df = pd.DataFrame(assign_rows)

                # Color the Status column via styling
                def color_status(val):
                    if val.startswith("✅"):
                        return "background-color: #d4edda; color: #155724;"
                    elif val.startswith("❌"):
                        return "background-color: #f8d7da; color: #721c24;"
                    else:
                        return "background-color: #fff3cd; color: #856404;"

                styled = assign_df.style.applymap(color_status, subset=["Status"])
                st.dataframe(styled, use_container_width=True, hide_index=True)

                # ── Missing students drill-down ───────────────────────────────
                missing_assignments = [a for a in r['assignments'] if a['missing'] > 0]
                if missing_assignments:
                    st.markdown("**⚠️ Missing / Zero-Score Students:**")
                    for a in missing_assignments:
                        if a['missing_students']:
                            st.markdown(
                                "<div style='"
                                "background:#fff3cd;"
                                "border-left:4px solid #ffc107;"
                                "padding:6px 12px;"
                                "margin:6px 0;"
                                "border-radius:4px;"
                                "font-weight:600;'>"
                                f"Subject: {a['subject']} &nbsp;|&nbsp; "
                                f"Stream: {a['stream']} &nbsp;|&nbsp; "
                                f"{a['missing']} student(s) missing"
                                "</div>",
                                unsafe_allow_html=True
                            )
                            miss_df = pd.DataFrame(a['missing_students'])
                            miss_df.columns = ["ADM NO.", "Student Name"]
                            st.dataframe(miss_df, use_container_width=True, hide_index=True)
                else:
                    st.success("All students have valid scores for this teacher's subjects.")

        st.markdown("---")

        # ── Subject-level summary table ───────────────────────────────────────
        st.subheader("📚 Subject-Level Summary")
        subject_summary = {}
        for r in results:
            for a in r['assignments']:
                key = f"{a['subject']} (Stream: {a['stream']})"
                if key not in subject_summary:
                    subject_summary[key] = {
                        "Subject": a['subject'],
                        "Stream": a['stream'],
                        "Teacher": r['name'],
                        "Total": a['total_students'],
                        "Entered": a['entered'],
                        "Missing": a['missing'],
                        "Progress": f"{a['pct']:.1f}%",
                    }

        if subject_summary:
            subj_df = pd.DataFrame(list(subject_summary.values()))
            subj_df = subj_df.sort_values("Missing", ascending=False)
            st.dataframe(subj_df, use_container_width=True, hide_index=True)



# ---------------------------
# Teacher Pages
# ---------------------------
def show_teacher_dashboard():
    st.header("👨‍🏫 Teacher Dashboard")
    st.markdown(f"*Welcome, {st.session_state.user_name}!*")
    st.markdown("---")

    assignments = get_teacher_assignments(st.session_state.username)
    if assignments:
        st.subheader("📋 Your Teaching Assignments")
        by_grade = {}
        for a in assignments:
            by_grade.setdefault(a['grade'], []).append(a)
        for grade in sorted(by_grade.keys()):
            with st.expander(f"**{grade}**", expanded=True):
                for a in by_grade[grade]:
                    s = a.get('stream') or 'No Stream'
                    st.write(f"• {a['subject']} — {s}")

        students = load_students()
        assigned_students = sum(
            1 for s in students.values()
            for a in assignments
            if s['grade'] == a['grade'] and (
                a.get('stream') is None or s.get('stream') == a.get('stream')
            )
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Your Students (approx)", assigned_students)
        with col2:
            subjects = list(set(a['subject'] for a in assignments))
            st.metric("Subjects", len(subjects))
        with col3:
            st.metric("Total Assignments", len(assignments))
    else:
        st.warning("No teaching assignments found. Please contact the administrator.")


def show_enter_marks():
    """
    Bulk marks entry: teacher picks grade/stream/subject/exam, sees ALL students in a table,
    enters/updates marks and submits in one go.
    """
    st.header("✏️ Enter / Update Student Marks")
    st.markdown("*Enter marks for all students at once using the table below.*")
    st.markdown("---")

    assignments = get_teacher_assignments(st.session_state.username)
    if not assignments:
        st.warning("No teaching assignments found. Contact administrator.")
        return

    # -- Exam selection --
    col1, col2, col3 = st.columns(3)
    with col1:
        teacher_grades = sorted(list(set(a['grade'] for a in assignments)))
        grade = st.selectbox("Grade", teacher_grades, key="enter_grade")
    with col2:
        term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="enter_term")
    with col3:
        year = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="enter_year")

    exam_type = st.selectbox("Examination Type",
                             ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
                             key="enter_exam")

    grade_assignments = [a for a in assignments if a['grade'] == grade]

    col1, col2 = st.columns(2)
    with col1:
        available_subjects = sorted(list(set(a['subject'] for a in grade_assignments)))
        subject = st.selectbox("Subject", available_subjects, key="enter_subject")

    # streams allowed for this grade+subject
    subj_assignments = [a for a in grade_assignments if a['subject'] == subject]
    allowed_streams = [a.get('stream') for a in subj_assignments]

    with col2:
        if grade in NO_STREAM_GRADES:
            st.info("📍 Grade has no streams")
            stream_filter = None
        elif len(allowed_streams) == 1 and allowed_streams[0] is not None:
            stream_filter = allowed_streams[0]
            sn = "Heroes (H)" if stream_filter == "H" else "Champions (C)"
            st.info(f"📍 Stream: {sn}")
        else:
            # Teacher can teach both streams
            stream_choice = st.selectbox(
                "Stream",
                ["All", "H", "C"],
                format_func=lambda x: "All Streams" if x == "All" else ("Heroes (H)" if x == "H" else "Champions (C)"),
                key="enter_stream_choice"
            )
            stream_filter = None if stream_choice == "All" else stream_choice

    # -- Load students --
    students = load_students(grade_filter=grade, stream_filter=stream_filter)
    if not students:
        st.warning("No students found for these parameters.")
        return

    st.markdown("---")
    st.subheader(f"📝 Marks Entry — {grade} | {subject} | {exam_type}")

    # Load existing marks
    existing_marks = get_exam_marks(grade, term, year, exam_type)

    # Build initial data for the editor
    rows = []
    for adm_no, sdata in sorted(students.items(), key=lambda x: x[1]['name']):
        existing_score = None
        if adm_no in existing_marks and subject in existing_marks[adm_no]:
            existing_score = existing_marks[adm_no][subject]
        rows.append({
            "ADM NO.": adm_no,
            "Student Name": sdata['name'],
            "Gender": sdata['gender'],
            "Stream": sdata.get('stream') or '—',
            "Score (0–100)": float(existing_score) if existing_score is not None else 0.0,
        })

    df_input = pd.DataFrame(rows)

    st.info(f"📊 {len(df_input)} student(s) loaded. Edit the **Score** column and click **Submit Marks**.")

    # Show editable table
    edited_df = st.data_editor(
        df_input,
        column_config={
            "ADM NO.": st.column_config.TextColumn("ADM NO.", disabled=True),
            "Student Name": st.column_config.TextColumn("Student Name", disabled=True),
            "Gender": st.column_config.TextColumn("Gender", disabled=True),
            "Stream": st.column_config.TextColumn("Stream", disabled=True),
            "Score (0–100)": st.column_config.NumberColumn(
                "Score (0–100)",
                min_value=0.0,
                max_value=100.0,
                step=0.5,
                format="%.1f",
            ),
        },
        use_container_width=True,
        hide_index=True,
        key="bulk_marks_editor",
    )

    col1, col2 = st.columns([2, 4])
    with col1:
        if st.button("✅ Submit Marks", type="primary", use_container_width=True):
            records = []
            for _, row in edited_df.iterrows():
                score = row["Score (0–100)"]
                if score < 0:
                    score = 0.0
                if score > 100:
                    score = 100.0
                records.append((
                    row["ADM NO."], grade, term, int(year), exam_type, subject, float(score)
                ))
            upsert_marks_bulk(records, st.session_state.username)
            st.success(f"✅ Marks submitted for {len(records)} student(s)!")
            st.balloons()

    with col2:
        # Show quick summary of what's been entered vs not
        entered = sum(1 for _, r in edited_df.iterrows() if r["Score (0–100)"] > 0)
        not_entered = len(edited_df) - entered
        st.info(f"Scores entered: **{entered}** | Blank (0): **{not_entered}**")

    # -- Preview of current marks from DB --
    with st.expander("🔍 View Current Saved Marks", expanded=False):
        saved_marks = get_exam_marks(grade, term, year, exam_type)
        saved_rows = []
        for adm_no, sdata in sorted(students.items(), key=lambda x: x[1]['name']):
            sc = saved_marks.get(adm_no, {}).get(subject)
            saved_rows.append({
                "ADM NO.": adm_no,
                "Student Name": sdata['name'],
                "Saved Score": float(sc) if sc is not None else "—",
            })
        st.dataframe(pd.DataFrame(saved_rows), use_container_width=True, hide_index=True)


def show_teacher_progress():
    st.header("📊 My Progress")
    st.markdown("---")

    assignments = get_teacher_assignments(st.session_state.username)
    if not assignments:
        st.warning("No assignments found.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        teacher_grades = sorted(list(set(a['grade'] for a in assignments)))
        grade = st.selectbox("Grade", teacher_grades, key="prog_grade")
    with col2:
        term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="prog_term")
    with col3:
        year = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="prog_year")

    exam_type = st.selectbox("Examination Type",
                             ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
                             key="prog_exam")

    if st.button("Check Progress", type="primary"):
        grade_assignments = [a for a in assignments if a['grade'] == grade]
        exam_marks = get_exam_marks(grade, term, year, exam_type)

        total_needed = 0
        total_done = 0

        for a in grade_assignments:
            students = load_students(grade_filter=grade, stream_filter=a.get('stream'))
            needed = len(students)
            done = sum(1 for adm in students if a['subject'] in exam_marks.get(adm, {}))
            total_needed += needed
            total_done += done
            pct = (done / needed * 100) if needed > 0 else 0
            st.write(f"**{a['subject']}** (Stream: {a.get('stream') or 'N/A'}): {done}/{needed} — {pct:.0f}%")
            st.progress(pct / 100)

        st.markdown("---")
        overall = (total_done / total_needed * 100) if total_needed > 0 else 0
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Needed", total_needed)
        with col2:
            st.metric("Completed", total_done)
        with col3:
            st.metric("Overall Progress", f"{overall:.1f}%")

        if overall == 100:
            st.success("🎉 All entries complete!")


# ---------------------------
# Shared Analytics Pages
# ---------------------------
def show_dashboard(df, grade, subject_cols):
    st.header(f"📊 Dashboard — {grade}")
    if df.empty:
        st.warning("No data available")
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Total Students", len(df))
    with col2: st.metric("Average Score", f"{df['TOTAL'].mean():.1f}")
    with col3: st.metric("Highest Score", f"{df['TOTAL'].max():.0f}")
    with col4:
        if grade not in NO_STREAM_GRADES:
            st.metric("Streams", df['STRM'].nunique())
        else:
            st.metric("Streams", "N/A")
    with col5:
        m = len(df[df['GENDER'].str.upper() == 'M'])
        f = len(df[df['GENDER'].str.upper() == 'F'])
        st.metric("M:F Ratio", f"{m}:{f}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        perf_counts = df['P.LEVEL'].value_counts()
        fig = px.pie(values=perf_counts.values, names=perf_counts.index,
                     title="Students by Performance Level")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        gender_counts = df['GENDER'].str.upper().value_counts()
        fig = px.pie(values=gender_counts.values, names=gender_counts.index,
                     title="Students by Gender",
                     color_discrete_map={'M': 'lightblue', 'F': 'lightpink'})
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        subject_avgs = df[subject_cols].mean().sort_values(ascending=False)
        fig = px.bar(x=subject_avgs.index, y=subject_avgs.values,
                     labels={'x': 'Subject', 'y': 'Average Score'},
                     title="Average Performance by Subject")
        fig.update_traces(marker_color='lightblue')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
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
        st.warning("No data available")
        return

    with st.expander("🔧 Report Configuration", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            school_name = st.text_input("School Name", "SINDO COMPREHENSIVE SCHOOL", key="rep_school")
            grade_text = st.text_input("Grade/Class", grade, key="rep_grade")
        with col2:
            term = st.text_input("Term", "Term 1", key="rep_term")
            year = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="rep_year")
        with col3:
            exam_type = st.text_input("Exam Type", "End Term Examinations", key="rep_exam")
        col1, col2, col3 = st.columns(3)
        with col1:
            class_teacher = st.text_input("Class Teacher", "Mr./Mrs. Teacher", key="rep_teacher")
        with col2:
            dhoi = st.text_input("DHOI", "Mr./Mrs. DHOI", key="rep_dhoi")
        with col3:
            hoi = st.text_input("HOI", "Mr./Mrs. HOI", key="rep_hoi")

    st.markdown("---")
    search_type = st.radio("Search by:", ["ADM NO.", "Student Name"], key="rep_search")
    if search_type == "ADM NO.":
        adm_no = st.selectbox("Select ADM NO.", df['ADM NO.'].unique(), key="rep_adm")
        student = df[df['ADM NO.'] == adm_no].iloc[0]
    else:
        name = st.selectbox("Select Student", df['NAME OF STUDENTS'].unique(), key="rep_name")
        student = df[df['NAME OF STUDENTS'] == name].iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Name", student['NAME OF STUDENTS'])
    with col2: st.metric("ADM NO.", student['ADM NO.'])
    with col3: st.metric("Gender", student['GENDER'])
    with col4: st.metric("Stream", student['STRM'])
    with col5: st.metric("Rank", f"{student['RANK']}/{len(df)}")

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total", f"{student['TOTAL']:.0f}")
    with col2: st.metric("Average", f"{student['AVERAGE']:.1f}")
    with col3: st.metric("P.Level", student.get('P.LEVEL', 'N/A'))
    with col4: st.metric("Points", student.get('POINTS', 'N/A'))

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        marks_data = []
        for subj in subject_cols:
            score = student.get(subj, 0)
            pl, pts = get_subject_performance_level(score)
            marks_data.append({'Subject': subj, 'Marks': score, 'P.Level': pl, 'Points': pts})
        mdf = pd.DataFrame(marks_data)
        fig = px.bar(mdf, x='Subject', y='Marks', title="Subject-wise Performance",
                     color='P.Level', hover_data=['Points'])
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(mdf, use_container_width=True, hide_index=True)
    with col2:
        values = [student.get(subj, 0) for subj in subject_cols]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=values, theta=subject_cols, fill='toself',
                                      name=student['NAME OF STUDENTS']))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📄 Generate PDF Report")
    if st.button("Generate PDF Report", type="primary"):
        with st.spinner("Generating report card..."):
            pdf_buffer = create_pdf_report(student, school_name, grade_text, term, year,
                                           exam_type, df, class_teacher, dhoi, hoi, subject_cols)
            st.success("✅ Report generated!")
            pdf_bytes = pdf_buffer.read()
            b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_buffer.seek(0)
            st.markdown(f'''<iframe src="data:application/pdf;base64,{b64}"
                width="100%" height="800px" type="application/pdf"
                style="border:1px solid #ddd; border-radius:4px;"></iframe>''',
                unsafe_allow_html=True)
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
        st.warning("No data available")
        return

    st.markdown("### 🎯 Select Class/Stream")
    if grade in NO_STREAM_GRADES:
        filtered_df = df.copy()
        display_name = grade
        st.info(f"📊 Analyzing: **{display_name}** | Students: **{len(filtered_df)}**")
    else:
        available_streams = sorted(df['STRM'].unique().tolist())
        filter_options = [f"{grade} (All Streams)"] + [
            f"{grade} - {'Heroes' if s == 'H' else 'Champions'} ({s})" for s in available_streams
        ]
        selected_filter = st.selectbox("Select class/stream:", filter_options, key="class_filter")
        if "All Streams" in selected_filter:
            filtered_df = df.copy()
            display_name = f"{grade} (All Streams)"
        else:
            stream = selected_filter.split("(")[-1].replace(")", "")
            filtered_df = df[df['STRM'] == stream].copy()
            stream_name = "Heroes" if stream == "H" else "Champions"
            display_name = f"{grade} - {stream_name}"
        st.info(f"📊 Analyzing: **{display_name}** | Students: **{len(filtered_df)}**")

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Class Average", f"{filtered_df['TOTAL'].mean():.1f}")
    with col2: st.metric("Median Score", f"{filtered_df['TOTAL'].median():.1f}")
    with col3: st.metric("Std Deviation", f"{filtered_df['TOTAL'].std():.1f}")
    with col4:
        m_avg = filtered_df[filtered_df['GENDER'].str.upper() == 'M']['TOTAL'].mean()
        f_avg = filtered_df[filtered_df['GENDER'].str.upper() == 'F']['TOTAL'].mean()
        st.metric("Gender Gap", f"{abs(m_avg - f_avg):.1f}" if pd.notna(m_avg) and pd.notna(f_avg) else "N/A")

    st.markdown("---")
    st.subheader("Performance Level Distribution")
    all_levels = ['EE1', 'EE2', 'ME1', 'ME2', 'AE1', 'AE2', 'BE1', 'BE2']
    perf_counts = filtered_df['P.LEVEL'].value_counts()
    col1, col2 = st.columns(2)
    with col1:
        level_counts = [perf_counts.get(lv, 0) for lv in all_levels]
        fig = px.bar(x=all_levels, y=level_counts,
                     labels={'x': 'Performance Level', 'y': 'Students'},
                     title="Students by CBC Performance Level")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        points_map = {'EE1':8,'EE2':7,'ME1':6,'ME2':5,'AE1':4,'AE2':3,'BE1':2,'BE2':1}
        descs = {'EE1':'Exceeding Expectation 1','EE2':'Exceeding Expectation 2',
                 'ME1':'Meeting Expectation 1','ME2':'Meeting Expectation 2',
                 'AE1':'Approaching Expectation 1','AE2':'Approaching Expectation 2',
                 'BE1':'Below Expectation 1','BE2':'Below Expectation 2'}
        perf_summary = [{'Level': lv, 'Description': descs[lv], 'Points': points_map[lv],
                         'Count': int(perf_counts.get(lv, 0)),
                         'Percentage': f"{(perf_counts.get(lv,0)/len(filtered_df)*100):.1f}%"}
                        for lv in all_levels]
        st.dataframe(pd.DataFrame(perf_summary), use_container_width=True, hide_index=True)

    st.markdown("---")
    subject_avgs = filtered_df[subject_cols].mean().sort_values(ascending=False)
    fig = px.bar(x=subject_avgs.index, y=subject_avgs.values,
                 labels={'x': 'Subject', 'y': 'Average'},
                 title="Class Average by Subject")
    fig.update_traces(marker_color='lightgreen')
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Top 10 Students")
        top_10 = filtered_df.nsmallest(10, 'RANK')[['RANK', 'NAME OF STUDENTS', 'GENDER', 'STRM', 'TOTAL', 'AVERAGE', 'P.LEVEL', 'POINTS']]
        st.dataframe(top_10, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("📉 Bottom 10 Students")
        bot_10 = filtered_df.nlargest(10, 'RANK')[['RANK', 'NAME OF STUDENTS', 'GENDER', 'STRM', 'TOTAL', 'AVERAGE', 'P.LEVEL', 'POINTS']]
        st.dataframe(bot_10, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📄 Generate Class Performance List PDF")
    pdf_display_name = display_name
    with st.expander("🔧 Class List Config", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            school_cl = st.text_input("School Name", "SINDO COMPREHENSIVE SCHOOL", key="cl_school")
            grade_cl = st.text_input("Grade/Class", pdf_display_name, key="cl_grade")
        with col2:
            term_cl = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="cl_term")
            year_cl = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="cl_year")
        with col3:
            exam_cl = st.selectbox("Exam Type",
                                   ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
                                   key="cl_exam")
            teacher_cl = st.text_input("Class Teacher", "Mr./Mrs. Teacher", key="cl_teacher")

    if st.button("Generate Class List PDF", type="primary", key="gen_class_pdf"):
        with st.spinner("Generating class list..."):
            pdf_buffer = create_class_list_pdf(filtered_df, school_cl, grade_cl, term_cl,
                                               year_cl, exam_cl, teacher_cl, subject_cols)
            st.success("✅ Class list generated!")
            pdf_bytes = pdf_buffer.read()
            b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_buffer.seek(0)
            st.markdown(f'''<iframe src="data:application/pdf;base64,{b64}"
                width="100%" height="800px" type="application/pdf"
                style="border:1px solid #ddd; border-radius:4px;"></iframe>''',
                unsafe_allow_html=True)
            fname = pdf_display_name.replace(" ", "_").replace("-", "")
            st.download_button(
                label=f"📥 Download {pdf_display_name} PDF",
                data=pdf_buffer,
                file_name=f"Class_List_{fname}_{term_cl}_{year_cl}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )


def show_subject_analysis(df, grade, subject_cols):
    st.header("📚 Subject Analysis")
    if df.empty:
        st.warning("No data available")
        return

    subject_avgs = df[subject_cols].mean().sort_values(ascending=False)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Strongest Subject", subject_avgs.index[0])
        st.metric("Avg Score", f"{subject_avgs.values[0]:.1f}")
    with col2:
        st.metric("Weakest Subject", subject_avgs.index[-1])
        st.metric("Avg Score", f"{subject_avgs.values[-1]:.1f}")
    with col3:
        st.metric("Highest Std Dev", f"{df[subject_cols].std().max():.1f}")

    st.markdown("---")
    st.subheader("🏆 Top Performers by Subject")
    tabs = st.tabs(subject_cols)
    for idx, subj in enumerate(subject_cols):
        with tabs[idx]:
            top = df.nlargest(10, subj)[['RANK', 'NAME OF STUDENTS', 'GENDER', 'STRM', subj, 'TOTAL']]
            top = top.rename(columns={subj: f'{subj} Score'})
            col1, col2 = st.columns([2, 1])
            with col1:
                st.dataframe(top, use_container_width=True, hide_index=True)
            with col2:
                for i, (_, student) in enumerate(top.head(3).iterrows()):
                    medal = ["🥇", "🥈", "🥉"][i]
                    st.markdown(f"{medal} **{student['NAME OF STUDENTS']}**")
                    st.markdown(f"Score: {student[f'{subj} Score']:.0f}")

    st.markdown("---")
    st.subheader("Detailed Subject Statistics")
    stats_df = pd.DataFrame({
        'Average': df[subject_cols].mean(),
        'Median': df[subject_cols].median(),
        'Max': df[subject_cols].max(),
        'Min': df[subject_cols].min(),
        'Std Dev': df[subject_cols].std(),
        'Pass Rate (≥50)': [(df[subj] >= 50).sum() / len(df) * 100 for subj in subject_cols],
    }).round(2)
    st.dataframe(stats_df, use_container_width=True)


def show_stream_comparison(df, grade, subject_cols):
    st.header("🏫 Stream Comparison")
    if df.empty:
        st.warning("No data available")
        return
    if grade in NO_STREAM_GRADES:
        st.info("Stream comparison is not applicable for Grades 1–3 (no streams).")
        return

    stream_avg = df.groupby('STRM')['TOTAL'].mean().sort_values(ascending=False)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Stream Rankings")
        stream_rank = []
        for stream in stream_avg.index:
            sdf = df[df['STRM'] == stream]
            m = len(sdf[sdf['GENDER'].str.upper() == 'M'])
            f = len(sdf[sdf['GENDER'].str.upper() == 'F'])
            stream_rank.append({'Stream': stream, 'Average': stream_avg[stream],
                                 'Students': len(sdf), 'M:F': f"{m}:{f}"})
        st.dataframe(pd.DataFrame(stream_rank), use_container_width=True, hide_index=True)
    with col2:
        fig = px.bar(x=stream_avg.index, y=stream_avg.values,
                     labels={'x': 'Stream', 'y': 'Average'}, title="Stream Performance")
        fig.update_traces(marker_color='teal')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Subject-wise Stream Comparison")
    stream_subject_avg = df.groupby('STRM')[subject_cols].mean()
    fig = go.Figure()
    for stream in stream_subject_avg.index:
        fig.add_trace(go.Scatter(x=subject_cols, y=stream_subject_avg.loc[stream],
                                  mode='lines+markers', name=stream))
    fig.update_layout(title="Stream Performance Across Subjects",
                      xaxis_title="Subject", yaxis_title="Average")
    st.plotly_chart(fig, use_container_width=True)


def show_gender_analysis(df, subject_cols, grade):
    st.header("⚥ Gender Analysis")
    if df.empty:
        st.warning("No data available")
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
        gap = (male_df['TOTAL'].mean() - female_df['TOTAL'].mean()
               if len(male_df) > 0 and len(female_df) > 0 else 0.0)
        st.metric("Performance Gap", f"{gap:.1f}")
    with col4:
        mt = len(male_df[male_df['RANK'] <= 10])
        ft = len(female_df[female_df['RANK'] <= 10])
        st.metric("Top 10 M:F", f"{mt}:{ft}")

    st.markdown("---")
    gender_subj = []
    for subj in subject_cols:
        gender_subj.append({
            'Subject': subj,
            'Male': male_df[subj].mean() if len(male_df) > 0 else 0,
            'Female': female_df[subj].mean() if len(female_df) > 0 else 0,
        })
    gsdf = pd.DataFrame(gender_subj)
    gsdf['Gap'] = gsdf['Male'] - gsdf['Female']

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Male', x=gsdf['Subject'], y=gsdf['Male'], marker_color='lightblue'))
        fig.add_trace(go.Bar(name='Female', x=gsdf['Subject'], y=gsdf['Female'], marker_color='lightpink'))
        fig.update_layout(title="Average Scores by Gender", barmode='group')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(gsdf, x='Subject', y='Gap', title="Performance Gap (Male - Female)",
                     color='Gap', color_continuous_scale=['lightpink', 'white', 'lightblue'],
                     color_continuous_midpoint=0)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(gsdf.round(2), use_container_width=True, hide_index=True)


# ---------------------------
# Main App
# ---------------------------
def main():
    # Init DB on every run (idempotent)
    init_db()

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

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        if os.path.exists("./images/reamicscholar_logo.png"):
            st.image("./images/reamicscholar_logo.png", width=700)
        else:
            st.title("ReaMic Scholar")
    st.markdown("---")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        show_login()
        return

    st.sidebar.markdown(f"## 👤 {st.session_state.user_name}")
    st.sidebar.markdown(f"*Role: {st.session_state.user_role.title()}*")
    st.sidebar.markdown("---")

    if st.session_state.user_role == 'admin':
        st.sidebar.header("🎯 Admin Menu")
        page = st.sidebar.radio("", [
            "Admin Dashboard", "Manage Students", "Manage Teachers", "Marks Entry Progress", "View Analytics",
            "Manage Admins"
        ], label_visibility="collapsed")
    else:
        st.sidebar.header("👨‍🏫 Teacher Menu")
        page = st.sidebar.radio("", [
            "Teacher Dashboard", "Enter Marks", "My Progress"
        ], label_visibility="collapsed")

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        for key in ['logged_in', 'username', 'user_role', 'user_name', 'user_data']:
            st.session_state[key] = None
        st.session_state.logged_in = False
        st.rerun()

    if st.session_state.user_role == 'admin':
        if page == "Admin Dashboard":
            show_admin_dashboard()
        elif page == "Manage Students":
            show_manage_students()
        elif page == "Manage Teachers":
            show_manage_teachers()
        elif page == "Manage Admins":
            show_manage_admins()
        elif page == "Marks Entry Progress":
            show_marks_entry_progress()
        elif page == "View Analytics":
            col1, col2, col3 = st.columns(3)
            with col1:
                grade = st.selectbox("Grade", list(GRADES.keys()), key="ana_grade")
            with col2:
                term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="ana_term")
            with col3:
                year = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="ana_year")
            exam_type = st.selectbox("Examination Type",
                                     ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
                                     key="ana_exam")
            subject_cols = GRADES[grade]
            df = prepare_grade_data(grade, term, year, exam_type)

            if not df.empty:
                analysis_page = st.selectbox("Select Analysis", [
                    "Dashboard", "Student Reports", "Class Analysis",
                    "Subject Analysis", "Stream Comparison", "Gender Analysis"
                ], key="ana_page")
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
                st.info("📊 No data for the selected parameters. Add students and enter marks first.")
    else:
        if page == "Teacher Dashboard":
            show_teacher_dashboard()
        elif page == "Enter Marks":
            show_enter_marks()
        elif page == "My Progress":
            show_teacher_progress()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**ReaMic Scholar v2.0**")
    st.sidebar.markdown("*by ReaMic Institute for Applied Intelligence*")


if __name__ == "__main__":
    main()
