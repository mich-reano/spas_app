"""
Lumetra Analytics - Contact Page
Built with Streamlit

A professional contact page showcasing services and contact information
for Lumetra Analytics educational technology solutions.
"""

import streamlit as st

# ========================================
# PAGE CONFIGURATION
# ========================================

st.set_page_config(
    page_title="Contact Us - Lumetra Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========================================
# CUSTOM CSS STYLING
# ========================================

st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }
    
    /* Remove default padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #1a3a5c 0%, #2c5282 100%);
        padding: 3rem 2rem;
        border-radius: 20px 20px 0 0;
        text-align: center;
        margin-bottom: 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }
    
    .logo {
        font-size: 3rem;
        font-weight: bold;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .tagline {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        letter-spacing: 2px;
        font-weight: 300;
    }
    
    /* Content container */
    .content-container {
        background: white;
        padding: 3rem 2rem;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }
    
    /* Service cards */
    .service-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        transition: transform 0.3s ease;
        height: 100%;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .service-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    }
    
    .service-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .service-title {
        font-size: 1.3rem;
        color: #1a3a5c;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    
    .service-description {
        color: #666;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    /* Contact section */
    .contact-box {
        background: #f8f9fa;
        padding: 2.5rem;
        border-radius: 12px;
        margin: 2rem 0;
    }
    
    .contact-item {
        text-align: center;
        padding: 1.5rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: transform 0.3s ease;
    }
    
    .contact-item:hover {
        transform: scale(1.05);
    }
    
    .contact-icon {
        font-size: 2.5rem;
        margin-bottom: 0.8rem;
    }
    
    .contact-label {
        font-size: 0.85rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .contact-value {
        font-size: 1.1rem;
        color: #1a3a5c;
        font-weight: 600;
    }
    
    /* Feature boxes */
    .feature-box {
        background: #f8f9fa;
        padding: 1.2rem;
        border-radius: 10px;
        display: flex;
        align-items: start;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    
    .feature-icon {
        font-size: 1.5rem;
        color: #667eea;
        flex-shrink: 0;
    }
    
    .feature-title {
        font-weight: 600;
        color: #1a3a5c;
        margin-bottom: 0.3rem;
    }
    
    .feature-description {
        font-size: 0.9rem;
        color: #666;
        line-height: 1.5;
    }
    
    /* Info box */
    .info-box {
        background: #fff3cd;
        padding: 2rem;
        border-radius: 12px;
        border-left: 5px solid #ffc107;
        margin: 2rem 0;
    }
    
    .info-title {
        color: #856404;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .info-list {
        color: #856404;
        line-height: 1.8;
    }
    
    /* CTA Button */
    .cta-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2.5rem;
        border-radius: 50px;
        font-size: 1.1rem;
        font-weight: 600;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: none;
        cursor: pointer;
    }
    
    .cta-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .logo {
            font-size: 2rem;
        }
        .tagline {
            font-size: 0.9rem;
        }
        .service-icon {
            font-size: 2.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# HEADER SECTION
# ========================================

st.markdown("""
<div class="header-container">
    <div class="logo">📊 Lumetra Analytics</div>
    <div class="tagline">EDUCATIONAL EXCELLENCE THROUGH DATA-DRIVEN INSIGHTS</div>
</div>
""", unsafe_allow_html=True)

# ========================================
# MAIN CONTENT
# ========================================

st.markdown('<div class="content-container">', unsafe_allow_html=True)

# Title and Introduction
st.markdown("<h1 style='text-align: center; color: #1a3a5c; font-size: 2.2rem; margin-bottom: 1rem;'>🚀 Transform Your School with Technology</h1>", unsafe_allow_html=True)

st.markdown("""
<p style='text-align: center; font-size: 1.1rem; color: #555; margin-bottom: 2.5rem; line-height: 1.8;'>
We specialize in CBC-compliant school management systems and educational technology solutions. 
Our flagship product, <strong>LumetraScholar</strong>, helps schools streamline operations, 
track student performance, and generate professional reports with ease.
</p>
""", unsafe_allow_html=True)

# ========================================
# SERVICES SECTION
# ========================================

st.markdown("<h2 style='text-align: center; color: #1a3a5c; margin: 2rem 0 1.5rem;'>Our Services</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="service-card">
        <div class="service-icon">🎓</div>
        <div class="service-title">School Management Systems</div>
        <div class="service-description">
            Complete CBC-compliant platforms for managing students, teachers, marks, and analytics
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="service-card" style="margin-top: 1.5rem;">
        <div class="service-icon">☁️</div>
        <div class="service-title">Cloud Deployment</div>
        <div class="service-description">
            Secure cloud hosting with 24/7 access from any device, anywhere
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="service-card">
        <div class="service-icon">📈</div>
        <div class="service-title">Performance Analytics</div>
        <div class="service-description">
            Advanced data visualization and reporting tools for informed decision-making
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="service-card" style="margin-top: 1.5rem;">
        <div class="service-icon">🎨</div>
        <div class="service-title">Custom Solutions</div>
        <div class="service-description">
            Tailored features and branding to match your school's unique needs
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="service-card">
        <div class="service-icon">📄</div>
        <div class="service-title">Automated Reporting</div>
        <div class="service-description">
            Professional PDF report cards, class lists, and performance reports generated automatically
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="service-card" style="margin-top: 1.5rem;">
        <div class="service-icon">🛠️</div>
        <div class="service-title">Training & Support</div>
        <div class="service-description">
            Comprehensive training for staff and ongoing technical support
        </div>
    </div>
    """, unsafe_allow_html=True)

# ========================================
# WHY CHOOSE US SECTION
# ========================================

st.markdown("<h2 style='text-align: center; color: #1a3a5c; margin: 3rem 0 1.5rem;'>Why Choose Lumetra Analytics?</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">✅</div>
        <div>
            <div class="feature-title">CBC Compliant</div>
            <div class="feature-description">Fully aligned with Kenya's CBC curriculum requirements</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">🔒</div>
        <div>
            <div class="feature-title">Secure & Reliable</div>
            <div class="feature-description">Bank-level encryption and regular backups</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">💰</div>
        <div>
            <div class="feature-title">Affordable Pricing</div>
            <div class="feature-description">Flexible plans to fit schools of all sizes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">⚡</div>
        <div>
            <div class="feature-title">Fast & Efficient</div>
            <div class="feature-description">Streamlined workflows save hours of administrative time</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">📱</div>
        <div>
            <div class="feature-title">Mobile Friendly</div>
            <div class="feature-description">Access from phones, tablets, or computers</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-box">
        <div class="feature-icon">🎯</div>
        <div>
            <div class="feature-title">Data-Driven Decisions</div>
            <div class="feature-description">Powerful analytics for better educational outcomes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ========================================
# CONTACT SECTION
# ========================================

st.markdown("""
<div class="contact-box">
    <h2 style='text-align: center; color: #1a3a5c; margin-bottom: 1.5rem;'>📞 Get In Touch</h2>
    <p style='text-align: center; margin-bottom: 2rem; color: #555; font-size: 1.05rem;'>
        Ready to transform your school's management system? We'd love to hear from you!
    </p>
</div>
""", unsafe_allow_html=True)

# Contact Methods
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="contact-item">
        <div class="contact-icon">📧</div>
        <div class="contact-label">Email Us</div>
        <div class="contact-value">info@lumetra<br>analytics.com</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="contact-item">
        <div class="contact-icon">📱</div>
        <div class="contact-label">Call/WhatsApp</div>
        <div class="contact-value">+254 700<br>000 000</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="contact-item">
        <div class="contact-icon">🌐</div>
        <div class="contact-label">Visit Website</div>
        <div class="contact-value">lumetra<br>analytics.com</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="contact-item">
        <div class="contact-icon">📍</div>
        <div class="contact-label">Location</div>
        <div class="contact-value">Nairobi,<br>Kenya</div>
    </div>
    """, unsafe_allow_html=True)

# CTA Button
st.markdown("<div style='text-align: center; margin: 2.5rem 0;'>", unsafe_allow_html=True)
if st.button("✉️ Send Us an Email", key="email_button", use_container_width=False):
    st.markdown("""
    <script>
        window.location.href = "mailto:info@lumetraanalytics.com?subject=Inquiry%20about%20LumetraScholar&body=Hello%20Lumetra%20Analytics%20Team,%0D%0A%0D%0AI%20am%20interested%20in%20learning%20more%20about%20your%20school%20management%20solutions.%0D%0A%0D%0ASchool%20Name:%20%0D%0AContact%20Person:%20%0D%0APhone%20Number:%20%0D%0ANumber%20of%20Students:%20%0D%0A%0D%0APlease%20contact%20me%20to%20discuss%20further.%0D%0A%0D%0AThank%20you!";
    </script>
    """, unsafe_allow_html=True)
    st.info("Opening your email client...")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<p style='text-align: center; margin-top: 1.5rem; font-size: 0.9rem; color: #888;'>
    We typically respond within 24 hours on business days
</p>
""", unsafe_allow_html=True)

# ========================================
# WHAT TO EXPECT SECTION
# ========================================

st.markdown("""
<div class="info-box">
    <div class="info-title">💡 What Happens Next?</div>
    <ol class="info-list" style="padding-left: 1.5rem; line-height: 1.8;">
        <li><strong>Free Consultation:</strong> We'll schedule a call to understand your school's needs</li>
        <li><strong>Live Demo:</strong> See LumetraScholar in action with sample school data</li>
        <li><strong>Custom Proposal:</strong> Receive a tailored solution with pricing options</li>
        <li><strong>Setup & Training:</strong> We'll deploy the system and train your staff</li>
        <li><strong>Ongoing Support:</strong> Continuous technical support and updates</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# ========================================
# CONTACT FORM (OPTIONAL)
# ========================================

st.markdown("<h2 style='text-align: center; color: #1a3a5c; margin: 3rem 0 1.5rem;'>📝 Quick Contact Form</h2>", unsafe_allow_html=True)

with st.form("contact_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Your Name *", placeholder="John Doe")
        email = st.text_input("Email Address *", placeholder="john@school.com")
        phone = st.text_input("Phone Number", placeholder="+254 700 000 000")
    
    with col2:
        school = st.text_input("School Name *", placeholder="ABC Academy")
        students = st.number_input("Number of Students", min_value=0, value=0, step=50)
        interest = st.selectbox("Primary Interest", [
            "Select an option...",
            "School Management System",
            "Performance Analytics",
            "PDF Report Generation",
            "Cloud Deployment",
            "Custom Solution",
            "General Inquiry"
        ])
    
    message = st.text_area("Message (Optional)", placeholder="Tell us about your needs...", height=100)
    
    submitted = st.form_submit_button("🚀 Submit Inquiry", use_container_width=True)
    
    if submitted:
        if name and email and school:
            st.success("✅ Thank you! We've received your inquiry and will respond within 24 hours.")
            st.balloons()
            
            # Display summary
            st.info(f"""
            **Inquiry Summary:**
            - Name: {name}
            - Email: {email}
            - School: {school}
            - Students: {students if students > 0 else "Not specified"}
            - Interest: {interest}
            
            We'll contact you at {email} shortly!
            """)
        else:
            st.error("❌ Please fill in all required fields (Name, Email, School Name)")

st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# FOOTER SECTION
# ========================================

st.markdown("""
<div style='background: #1a3a5c; color: white; padding: 2rem; text-align: center; margin-top: 3rem; border-radius: 20px;'>
    <div style='display: flex; justify-content: center; gap: 2rem; margin-bottom: 1rem; flex-wrap: wrap;'>
        <a href='mailto:info@lumetraanalytics.com' style='color: white; text-decoration: none; opacity: 0.8;'>Email</a>
        <a href='tel:+254700000000' style='color: white; text-decoration: none; opacity: 0.8;'>Call Us</a>
        <span style='color: white; opacity: 0.8;'>Features</span>
        <span style='color: white; opacity: 0.8;'>Services</span>
    </div>
    <p style='margin: 0.5rem 0;'>&copy; 2024 Lumetra Analytics. All rights reserved.</p>
    <p style='margin-top: 0.8rem; font-size: 0.85rem; opacity: 0.8;'>
        Educational Excellence Through Data-Driven Insights
    </p>
</div>
""", unsafe_allow_html=True)
