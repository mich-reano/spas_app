# lumetra_scholar_final.py
import os
from io import BytesIO
import base64

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

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="LumetraScholar", page_icon="./images/lumetra_scholar.png", layout="wide")

# ---------------------------
# Your grade map (exact)
# ----------------------------
GRADES = {
    'Grade 4': ['MAT', 'ENG', 'KIS', 'SCI', 'SST', 'C/ARTS'],
    'Grade 5': ['MAT', 'ENG', 'KIS', 'SCI', 'SST', 'C/ARTS'],
    'Grade 6': ['MAT', 'ENG', 'KIS', 'SCI', 'SST', 'C/ARTS'],
    'Grade 7': ['MAT', 'ENG', 'KIS', 'PRET', 'SST', 'AGR/N', 'C/ARTS', 'CRE', 'INT/SCI'],
    'Grade 8': ['MAT', 'ENG', 'KIS', 'PRET', 'SST', 'AGR/N', 'C/ARTS', 'CRE', 'INT/SCI'],
    'Grade 9': ['MAT', 'ENG', 'KIS', 'PRET', 'SST', 'AGR/N', 'C/ARTS', 'CRE', 'INT/SCI'],
}

DATA_PATH = "data"

# ---------------------------
# Utility functions
# ---------------------------
def get_performance_level(score):
    try:
        s = float(score)
    except Exception:
        return 'BE'
    if s >= 75:
        return 'EE'
    if s >= 60:
        return 'ME'
    if s >= 40:
        return 'AE'
    return 'BE'


def get_performance_label(level):
    labels = {
        'EE': 'Exceeding Expectation',
        'ME': 'Meeting Expectation',
        'AE': 'Approaching Expectation',
        'BE': 'Below Expectation'
    }
    return labels.get(level, level)


def prepare_grade_data(df, subject_cols):
    """Compute totals, average (0-100), rank, AV/LVL — only in memory."""
    df = df.copy()

    missing = [c for c in subject_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing subject columns: {missing}")

    # Ensure subject columns numeric
    df[subject_cols] = df[subject_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Compute TOTAL (in-memory) — won't overwrite CSV on disk
    df['TOTAL'] = df[subject_cols].sum(axis=1)

    # AVERAGE as mean per subject (0-100)
    n_sub = len(subject_cols)
    df['AVERAGE'] = df['TOTAL'] / n_sub  # each subject assumed out of 100

    # Performance label short and long
    df['AV/LVL'] = df['AVERAGE'].apply(get_performance_level)

    # RANK (dense; best = 1)
    df['RANK'] = df['TOTAL'].rank(ascending=False, method='dense').astype(int)

    # Safe defaults
    if 'GENDER' not in df.columns:
        df['GENDER'] = ''
    if 'NAME OF STUDENTS' not in df.columns:
        raise KeyError("Missing required column 'NAME OF STUDENTS'")
    if 'STRM' not in df.columns:
        df['STRM'] = ''

    return df


# ---------------------------
# PDF helpers (kept as in your original with fixes)
# ---------------------------
def create_pdf_report(student, school_name, grade, term, year, exam_type, df,
                      class_teacher, dhoi, hoi, subject_cols):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18,
                                 textColor=colors.HexColor('#1f4788'), spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold')
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=12,
                                   textColor=colors.HexColor('#2c5aa0'), spaceAfter=12, spaceBefore=12, fontName='Helvetica-Bold')
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)

    elements.append(Paragraph(school_name.upper(), title_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"{grade.upper()}", normal_style))
    elements.append(Paragraph(f"{term} - {year}", normal_style))
    elements.append(Paragraph(f"{exam_type}", normal_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("STUDENT PERFORMANCE REPORT", heading_style))
    elements.append(Spacer(1, 12))

    info_data = [
        ['Admission Number:', str(student.get('ADM NO.', '')), 'Stream:', str(student.get('STRM', ''))],
        ['Student Name:', str(student.get('NAME OF STUDENTS', '')), 'Gender:', str(student.get('GENDER', ''))],
        ['Class Rank:', f"{student.get('RANK', '')} / {len(df)}", 'Performance Level:', str(student.get('AV/LVL', ''))],
    ]

    info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1.2*inch, 1.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e8f4f8')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("SUBJECT PERFORMANCE", heading_style))
    elements.append(Spacer(1, 6))

    subject_data = [['Subject', 'Score', 'Class Average', 'Performance Level']]
    for subj in subject_cols:
        score = float(student.get(subj, 0))
        class_avg = float(df[subj].mean())
        perf_level = get_performance_level(score)
        subject_data.append([subj, f"{score:.0f}", f"{class_avg:.1f}", perf_level])

    subject_table = Table(subject_data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch])
    subject_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(subject_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("PERFORMANCE SUMMARY", heading_style))
    elements.append(Spacer(1, 6))

    summary_data = [
        ['Total Marks:', f"{student.get('TOTAL', 0):.0f}", 'Average Marks:', f"{student.get('AVERAGE', 0):.1f}"],
        ['Performance Level:', str(student.get('AV/LVL', '')), 'Class Average:', f"{df['TOTAL'].mean():.1f}"],
    ]

    summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e8f4f8')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Legend + remarks + signatures
    elements.append(Paragraph("PERFORMANCE LEVEL KEY", heading_style))
    elements.append(Spacer(1, 6))
    legend_data = [
        ['EE', 'Exceeding Expectation', '75-100'],
        ['ME', 'Meeting Expectation', '60-74'],
        ['AE', 'Approaching Expectation', '40-59'],
        ['BE', 'Below Expectation', '0-39']
    ]
    legend_table = Table(legend_data, colWidths=[1*inch, 2.5*inch, 1.5*inch])
    legend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(legend_table)
    elements.append(Spacer(1, 20))

    performance_level = "excellent" if student.get('AVERAGE', 0) >= 75 else "good" if student.get('AVERAGE', 0) >= 60 else "satisfactory" if student.get('AVERAGE', 0) >= 40 else "needs improvement"
    remarks_text = f"The student has demonstrated {performance_level} performance this term with a performance level of {student.get('AV/LVL','')}."
    elements.append(Paragraph("REMARKS", heading_style))
    elements.append(Paragraph(remarks_text, styles['Normal']))
    elements.append(Spacer(1, 30))

    signature_data = [
        ['Class Teacher:', class_teacher, 'Sign: _____________', 'Date: _____________'],
        ['DHOI:', dhoi, 'Sign: _____________', 'Date: _____________'],
        ['HOI:', hoi, 'Sign: _____________', 'Date: _____________']
    ]
    signature_table = Table(signature_data, colWidths=[1.2*inch, 2*inch, 1.5*inch, 1.3*inch])
    signature_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(signature_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def create_class_list_pdf(df, school_name, grade, term, year, exam_type, class_teacher, subject_cols):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30,
                           topMargin=30, bottomMargin=30)

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16,
                                 textColor=colors.HexColor('#1f4788'), spaceAfter=4, alignment=TA_CENTER, fontName='Helvetica-Bold')
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)

    elements.append(Paragraph(school_name.upper(), title_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"{grade}", normal_style))
    elements.append(Paragraph(f"{term} - {year}", normal_style))
    elements.append(Paragraph(f"{exam_type}", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("CLASS PERFORMANCE LIST", title_style))
    elements.append(Spacer(1, 15))

    sorted_df = df.sort_values('RANK')

    header = ['Rank', 'ADM NO.', 'Name', 'Gender', 'Strm'] + subject_cols + ['Total', 'Avg', 'Level']
    table_data = [header]

    for _, row in sorted_df.iterrows():
        perf_level = get_performance_level(row['AVERAGE'])
        row_data = [str(row['RANK']), str(row.get('ADM NO.', '')), str(row.get('NAME OF STUDENTS', ''))[:25],
                   str(row.get('GENDER', '')), str(row.get('STRM', ''))]
        for subj in subject_cols:
            row_data.append(f"{row.get(subj, 0):.0f}")
        row_data.extend([f"{row.get('TOTAL', 0):.0f}", f"{row.get('AVERAGE', 0):.1f}", perf_level])
        table_data.append(row_data)

    num_subjects = len(subject_cols)
    base_widths = [0.4*inch, 0.6*inch, 1.8*inch, 0.3*inch, 0.4*inch]
    subject_widths = [0.45*inch] * num_subjects
    end_widths = [0.5*inch, 0.5*inch, 0.4*inch]
    col_widths = base_widths + subject_widths + end_widths

    class_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    class_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))

    elements.append(class_table)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("PERFORMANCE LEVEL KEY", styles['Heading3']))
    elements.append(Spacer(1, 6))
    legend_data = [['EE - Exceeding Expectation (75-100)', 'ME - Meeting Expectation (60-74)',
                    'AE - Approaching Expectation (40-59)', 'BE - Below Expectation (0-39)']]
    legend_table = Table(legend_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch, 2.5*inch])
    legend_table.setStyle(TableStyle([('FONTSIZE', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    elements.append(legend_table)
    elements.append(Spacer(1, 15))

    summary_sig_data = [[
        f"CLASS SUMMARY: Total Students: {len(df)} | Class Average: {df['TOTAL'].mean():.2f} | Highest: {df['TOTAL'].max():.0f} | Lowest: {df['TOTAL'].min():.0f}",
        f"Class Teacher: {class_teacher}     Signature: ______________     Date: ______________"
    ]]
    summary_table = Table(summary_sig_data, colWidths=[5*inch, 5.5*inch])
    summary_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(summary_table)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ---------------------------
# Load data (auto) into session
# ---------------------------
def load_all_grade_data():
    if 'grade_data' not in st.session_state:
        st.session_state.grade_data = {}
    for grade in GRADES.keys():
        file_path = os.path.join(DATA_PATH, f"{grade}.csv")
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                st.session_state.grade_data[grade] = df
            except Exception as e:
                st.warning(f"Failed to load {file_path}: {e}")


def get_available_grades():
    if 'grade_data' not in st.session_state:
        return []
    return list(st.session_state.grade_data.keys())


def load_grade_data(grade):
    return st.session_state.grade_data.get(grade, pd.DataFrame()).copy()


def get_grade_df(grade):
    """Return uploaded override if present in session, else autoloaded."""
    key = f"uploaded_{grade}"
    if key in st.session_state and isinstance(st.session_state[key], pd.DataFrame):
        return st.session_state[key].copy()
    return st.session_state.get('grade_data', {}).get(grade, pd.DataFrame()).copy()


# ---------------------------
# UI: Home & Pages (using original styling/layout)
# ---------------------------
def show_home_page():
    st.markdown("## Your Trusted Academic Performance Intelligence Platform")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Primary Level")
        st.markdown("**At this level, every score tells a story of growing curiosity, early skills taking shape, and learners discovering their potential**")
        st.markdown("**LumetraScholar helps teachers follow these early progress patterns with clarity, ensuring that each child receives the encouragement and support they need as they build strong academic foundations.**")
        st.markdown("##### Small Steps, Big Growth : Every Learner Matters.")

    with col2:
        st.markdown("### Junior Secondary")
        st.markdown("**As learners advance, their academic journey becomes deeper, more defined, and increasingly skill-driven.**")
        st.markdown("**LumetraScholar provides thoughtful analytics that highlight strengths, track progress, and reveal areas needing targeted support.**")
        st.markdown("**With clear dashboards and comprehensive reports, teachers can guide students with precision and help them prepare for the next stage with confidence.**")
        st.markdown("##### Informed Teaching. Focused Support. Stronger Outcomes")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("")
    with col2:
        st.markdown("**Empowering learners with excellence, integrity, and purpose.**")
        st.image("./images/lumetra-logo.png", width=100)
        st.markdown("**LumetraScholar v1.0 | © 2025 Lumetra Analytics**")
    with col3:
        st.write("")

# Dashboard, Student Reports, Class Analysis, etc. — keep the layout/colors consistent with your original code
def show_dashboard(df, grade, subject_cols):
    st.header(f"Dashboard - {grade}")
    st.markdown("*Real-time insights and analytics*")
    st.markdown("---")

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

    st.subheader("Subject Statistics Summary")
    stats_df = pd.DataFrame({
        'Mean': df[subject_cols].mean(),
        'Max': df[subject_cols].max(),
        'Min': df[subject_cols].min(),
        'Std Dev': df[subject_cols].std()
    }).round(2)
    st.dataframe(stats_df, use_container_width=True)


def show_student_reports(df, grade, subject_cols):
    st.header("Student Reports")

    # Report configuration
    with st.expander("🔧 Report Configuration", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            school_name = st.text_input("School Name", "ABC SCHOOL")
            grade_text = st.text_input("Grade/Class", grade)
        with col2:
            term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"])
            year = st.number_input("Year", min_value=2020, max_value=2030, value=2024)
        with col3:
            exam_type = st.selectbox("Examination Type",
                                     ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"])

        st.markdown("**Staff Information**")
        col1, col2, col3 = st.columns(3)
        with col1:
            class_teacher = st.text_input("Class Teacher Name", "Mr./Mrs. Teacher")
        with col2:
            dhoi = st.text_input("DHOI Name", "Mr./Mrs. DHOI")
        with col3:
            hoi = st.text_input("HOI Name", "Mr./Mrs. HOI")

    st.markdown("---")

    search_type = st.radio("Search by:", ["ADM NO.", "Student Name"])

    if search_type == "ADM NO.":
        adm_no = st.selectbox("Select Admission Number", df['ADM NO.'].unique())
        student = df[df['ADM NO.'] == adm_no].iloc[0]
    else:
        name = st.selectbox("Select Student Name", df['NAME OF STUDENTS'].unique())
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

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Marks", f"{student['TOTAL']:.0f}")
    with col2:
        st.metric("Average", f"{student['AVERAGE']:.1f}")
    with col3:
        st.metric("Level", student['AV/LVL'])

    st.markdown("---")

    # Subject performance + radar side-by-side (restored original layout)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Subject Marks")
        marks_data = []
        for subj in subject_cols:
            marks_data.append({
                'Subject': subj,
                'Marks': student.get(subj, 0),
                'Performance': get_performance_level(student.get(subj, 0))
            })
        marks_df = pd.DataFrame(marks_data)

        fig = px.bar(marks_df, x='Subject', y='Marks',
                     title="Subject-wise Performance",
                     color='Performance',
                     color_discrete_map={'EE': '#00cc00', 'ME': '#3399ff',
                                        'AE': '#ffcc00', 'BE': '#ff6666'})
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
    # PDF
    st.subheader("📄 Generate PDF Report")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("Click the button below to generate and preview the PDF report")

    if st.button("Generate PDF Report", type="primary"):
        with st.spinner("Generating PDF report..."):
            pdf_buffer = create_pdf_report(student, school_name, grade_text, term, year,
                                           exam_type, df, class_teacher, dhoi, hoi, subject_cols)

            st.success("Done! Report generated successfully!")

            st.download_button(
                label="Download PDF Report",
                data=pdf_buffer,
                file_name=f"{student['NAME OF STUDENTS']}_Report_{term}_{year}.pdf",
                mime="application/pdf"
            )

            pdf_display = f'<iframe src="data:application/pdf;base64,{base64.b64encode(pdf_buffer.read()).decode()}" width="100%" height="800" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)


def show_class_analysis(df, grade, subject_cols):
    st.header("Class Analysis")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Class Average", f"{df['TOTAL'].mean():.1f}")
    with col2:
        st.metric("Median Score", f"{df['TOTAL'].median():.1f}")
    with col3:
        st.metric("Standard Deviation", f"{df['TOTAL'].std():.1f}")
    with col4:
        male_avg = df[df['GENDER'].str.upper() == 'M']['TOTAL'].mean()
        female_avg = df[df['GENDER'].str.upper() == 'F']['TOTAL'].mean()
        st.metric("Gender Gap", f"{abs(male_avg - female_avg):.1f}")

    st.markdown("---")

    st.subheader("Performance Level Distribution")
    df['PERF_LEVEL'] = df['AVERAGE'].apply(get_performance_level)
    perf_counts = df['PERF_LEVEL'].value_counts()

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(x=perf_counts.index, y=perf_counts.values,
                     labels={'x': 'Performance Level', 'y': 'Number of Students'},
                     title="Students by Performance Level",
                     color=perf_counts.index,
                     color_discrete_map={'EE': '#00cc00', 'ME': '#3399ff',
                                        'AE': '#ffcc00', 'BE': '#ff6666'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        perf_summary = []
        for level in ['EE', 'ME', 'AE', 'BE']:
            count = perf_counts.get(level, 0)
            percentage = (count / len(df)) * 100 if len(df) > 0 else 0
            perf_summary.append({
                'Level': level,
                'Description': get_performance_label(level),
                'Count': count,
                'Percentage': f"{percentage:.1f}%"
            })
        perf_df = pd.DataFrame(perf_summary)
        st.dataframe(perf_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Subject-wise Class Average")
    subject_avgs = df[subject_cols].mean().sort_values(ascending=False)
    fig = px.bar(x=subject_avgs.index, y=subject_avgs.values,
                 labels={'x': 'Subject', 'y': 'Average Score'},
                 title="Class Performance by Subject")
    fig.update_traces(marker_color='lightgreen')
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Top 10 Students")
        top_10 = df.nsmallest(10, 'RANK')[['RANK', 'NAME OF STUDENTS', 'GENDER', 'STRM', 'TOTAL', 'AVERAGE', 'AV/LVL']]
        st.dataframe(top_10, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Bottom 10 Students")
        bottom_10 = df.nlargest(10, 'RANK')[['RANK', 'NAME OF STUDENTS', 'GENDER', 'STRM', 'TOTAL', 'AVERAGE', 'AV/LVL']]
        st.dataframe(bottom_10, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Total Score Distribution")
    fig = px.histogram(df, x='TOTAL', nbins=20, color=df['GENDER'].str.upper(),
                      labels={'TOTAL': 'Total Score', 'count': 'Number of Students'},
                      title="Distribution of Total Scores by Gender",
                      color_discrete_map={'M': 'lightblue', 'F': 'lightpink'})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📄 Generate Class Performance List (PDF)")
    with st.expander("🔧 Class List Configuration", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            school_name_cl = st.text_input("School Name", "ABC SCHOOL", key="cl_school")
            grade_cl = st.text_input("Grade/Class", grade, key="cl_grade")
        with col2:
            term_cl = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="cl_term")
            year_cl = st.number_input("Year", min_value=2020, max_value=2030, value=2024, key="cl_year")
        with col3:
            exam_type_cl = st.selectbox("Examination Type",
                                        ["Opener Examinations", "Mid-Term Examinations", "End Term Examinations"],
                                        key="cl_exam")
            class_teacher_cl = st.text_input("Class Teacher Name", "Mr./Mrs. Teacher", key="cl_teacher")

    if st.button("Generate Class List PDF", type="primary"):
        with st.spinner("Generating class list PDF..."):
            pdf_buffer = create_class_list_pdf(df, school_name_cl, grade_cl, term_cl,
                                              year_cl, exam_type_cl, class_teacher_cl, subject_cols)

            st.success("Done! Class list generated successfully!")

            st.download_button(
                label="Download Class List PDF",
                data=pdf_buffer,
                file_name=f"Class_List_{grade_cl}_{term_cl}_{year_cl}.pdf",
                mime="application/pdf"
            )

            pdf_display = f'<iframe src="data:application/pdf;base64,{base64.b64encode(pdf_buffer.read()).decode()}" width="100%" height="800" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)


def show_subject_analysis(df, grade, subject_cols):
    st.header(" Subject Analysis")

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
    st.header("Stream Comparison")

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
    st.header("Gender Analysis")
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
# Main
# ---------------------------
def main():
    # your original CSS / style (restored)
    st.markdown("""
    <style>
        .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .block-container { background: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 2rem; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1); }
        h1 { color: #2c3e50; font-weight: 800; text-align: center; padding: 1rem 0; }
        h2 { color: #34495e; border-bottom: 3px solid #667eea; padding-bottom: 0.5rem; }
        [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: bold; color: #667eea; }
        .stButton>button { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; padding: 0.75rem 2rem; font-weight: 600; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%); }
        [data-testid="stSidebar"] .stMarkdown { color: white !important; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.write("")
    with col2:
        if os.path.exists("./images/lumetrascholar_full_logo.png"):
            st.image("./images/lumetrascholar_full_logo.png", width=700)
        else:
            st.title("LumetraScholar")
    with col3:
        st.write("")
    st.markdown("---")

    # load data
    load_all_grade_data()
    available_grades = list(GRADES.keys())

    # Sidebar
    st.sidebar.markdown("## 🎓 LumetraScholar")
    st.sidebar.markdown("*by Magollo M. Reagan @Lumetra Analytics*")
    st.sidebar.markdown("---")

    selected_grade = st.sidebar.selectbox(
        "Select Grade",
        options=["-- Select Grade --"] + available_grades,
        key="selected_grade_box"
    )

    st.sidebar.markdown("---")
    st.sidebar.header(" Navigation")
    page = st.sidebar.radio(
        "",
        ["Home", "Dashboard", "Student Reports", "Class Analysis",
         "Subject Analysis", "Stream Comparison", "Gender Analysis"],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**LumetraScholar v1.0**")
    
    # If no grade selected → home
    if selected_grade == "-- Select Grade --":
        show_home_page()
        return

    subject_cols = GRADES[selected_grade]

    # Allow upload override (session only)
    st.sidebar.markdown("**Upload CSV for this grade (optional)**")
    uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"], key=f"uploader_{selected_grade}")
    if uploaded:
        try:
            df_up = pd.read_csv(uploaded)
            st.session_state[f"uploaded_{selected_grade}"] = df_up
            st.sidebar.success("Upload loaded for this session")
        except Exception as e:
            st.sidebar.error(f"Upload failed: {e}")
    
    
    # Get df (uploaded override or auto-load)
    df = get_grade_df(selected_grade)

    # If empty, show message
    if df.empty:
        st.warning(f"No data available for {selected_grade}. Upload CSV in the sidebar to use this grade.")
        return

    # Validate subject columns
    missing = [c for c in subject_cols if c not in df.columns]
    if missing:
        st.error(f"Missing columns for {selected_grade}: {missing}")
        return

    # Prepare data (compute in-memory)
    try:
        df = prepare_grade_data(df, subject_cols)
    except Exception as e:
        st.error(f"Data preparation failed: {e}")
        return

    # route pages
    if page == "Home":
        show_home_page()
    elif page == "Dashboard":
        show_dashboard(df, selected_grade, subject_cols)
    elif page == "Student Reports":
        show_student_reports(df, selected_grade, subject_cols)
    elif page == "Class Analysis":
        show_class_analysis(df, selected_grade, subject_cols)
    elif page == "Subject Analysis":
        show_subject_analysis(df, selected_grade, subject_cols)
    elif page == "Stream Comparison":
        show_stream_comparison(df, selected_grade, subject_cols)
    elif page == "Gender Analysis":
        show_gender_analysis(df, subject_cols, selected_grade)


if __name__ == "__main__":
    main()

