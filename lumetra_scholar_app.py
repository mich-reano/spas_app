<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Contact Lumetra Analytics for CBC-compliant school management solutions and educational technology services">
    <title>Contact Us - Lumetra Analytics | School Management Solutions</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            width: 100%;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
            animation: slideUp 0.6s ease-out;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .header {
            background: linear-gradient(135deg, #1a3a5c 0%, #2c5282 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
        }

        .logo {
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }

        .logo-subtitle {
            font-size: 18px;
            opacity: 0.9;
            font-weight: 300;
            letter-spacing: 2px;
        }

        .content {
            padding: 50px 40px;
        }

        h1 {
            color: #1a3a5c;
            font-size: 32px;
            margin-bottom: 20px;
            text-align: center;
        }

        .intro {
            text-align: center;
            font-size: 18px;
            color: #555;
            margin-bottom: 40px;
            line-height: 1.8;
        }

        .services {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin: 40px 0;
        }

        .service-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .service-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        }

        .service-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }

        .service-title {
            font-size: 20px;
            color: #1a3a5c;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .service-description {
            font-size: 14px;
            color: #666;
            line-height: 1.6;
        }

        .contact-section {
            background: #f8f9fa;
            padding: 40px;
            border-radius: 12px;
            margin: 30px 0;
        }

        .contact-title {
            text-align: center;
            color: #1a3a5c;
            font-size: 28px;
            margin-bottom: 30px;
        }

        .contact-methods {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }

        .contact-item {
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 10px;
            transition: transform 0.3s ease;
        }

        .contact-item:hover {
            transform: scale(1.05);
        }

        .contact-icon {
            font-size: 36px;
            margin-bottom: 10px;
        }

        .contact-label {
            font-size: 14px;
            color: #888;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .contact-value {
            font-size: 16px;
            color: #1a3a5c;
            font-weight: 600;
        }

        .contact-value a {
            color: #1a3a5c;
            text-decoration: none;
            transition: color 0.3s ease;
        }

        .contact-value a:hover {
            color: #667eea;
        }

        .cta-button {
            display: inline-block;
            padding: 15px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-size: 18px;
            font-weight: 600;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            margin: 20px auto;
            display: block;
            width: fit-content;
        }

        .cta-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }

        .feature {
            display: flex;
            align-items: start;
            gap: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }

        .feature-icon {
            font-size: 24px;
            color: #667eea;
            flex-shrink: 0;
        }

        .feature-text {
            flex: 1;
        }

        .feature-title {
            font-weight: 600;
            color: #1a3a5c;
            margin-bottom: 5px;
        }

        .feature-description {
            font-size: 14px;
            color: #666;
        }

        .footer {
            background: #1a3a5c;
            color: white;
            text-align: center;
            padding: 30px;
            font-size: 14px;
        }

        .footer-links {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }

        .footer-links a {
            color: white;
            text-decoration: none;
            opacity: 0.8;
            transition: opacity 0.3s ease;
        }

        .footer-links a:hover {
            opacity: 1;
        }

        @media (max-width: 768px) {
            .header {
                padding: 40px 20px;
            }

            .logo {
                font-size: 36px;
            }

            .content {
                padding: 30px 20px;
            }

            h1 {
                font-size: 24px;
            }

            .contact-section {
                padding: 25px;
            }

            .services {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="logo">📊 Lumetra Analytics</div>
            <div class="logo-subtitle">EDUCATIONAL EXCELLENCE THROUGH DATA-DRIVEN INSIGHTS</div>
        </div>

        <!-- Main Content -->
        <div class="content">
            <h1>🚀 Transform Your School with Technology</h1>
            <p class="intro">
                We specialize in CBC-compliant school management systems and educational technology solutions. 
                Our flagship product, <strong>LumetraScholar</strong>, helps schools streamline operations, 
                track student performance, and generate professional reports with ease.
            </p>

            <!-- Services -->
            <div class="services">
                <div class="service-card">
                    <div class="service-icon">🎓</div>
                    <div class="service-title">School Management Systems</div>
                    <div class="service-description">
                        Complete CBC-compliant platforms for managing students, teachers, marks, and analytics
                    </div>
                </div>

                <div class="service-card">
                    <div class="service-icon">📈</div>
                    <div class="service-title">Performance Analytics</div>
                    <div class="service-description">
                        Advanced data visualization and reporting tools for informed decision-making
                    </div>
                </div>

                <div class="service-card">
                    <div class="service-icon">📄</div>
                    <div class="service-title">Automated Reporting</div>
                    <div class="service-description">
                        Professional PDF report cards, class lists, and performance reports generated automatically
                    </div>
                </div>

                <div class="service-card">
                    <div class="service-icon">☁️</div>
                    <div class="service-title">Cloud Deployment</div>
                    <div class="service-description">
                        Secure cloud hosting with 24/7 access from any device, anywhere
                    </div>
                </div>

                <div class="service-card">
                    <div class="service-icon">🎨</div>
                    <div class="service-title">Custom Solutions</div>
                    <div class="service-description">
                        Tailored features and branding to match your school's unique needs
                    </div>
                </div>

                <div class="service-card">
                    <div class="service-icon">🛠️</div>
                    <div class="service-title">Training & Support</div>
                    <div class="service-description">
                        Comprehensive training for staff and ongoing technical support
                    </div>
                </div>
            </div>

            <!-- Features -->
            <h2 style="text-align: center; color: #1a3a5c; margin: 40px 0 20px;">Why Choose Lumetra Analytics?</h2>
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">✅</div>
                    <div class="feature-text">
                        <div class="feature-title">CBC Compliant</div>
                        <div class="feature-description">Fully aligned with Kenya's CBC curriculum requirements</div>
                    </div>
                </div>

                <div class="feature">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-text">
                        <div class="feature-title">Fast & Efficient</div>
                        <div class="feature-description">Streamlined workflows save hours of administrative time</div>
                    </div>
                </div>

                <div class="feature">
                    <div class="feature-icon">🔒</div>
                    <div class="feature-text">
                        <div class="feature-title">Secure & Reliable</div>
                        <div class="feature-description">Bank-level encryption and regular backups</div>
                    </div>
                </div>

                <div class="feature">
                    <div class="feature-icon">📱</div>
                    <div class="feature-text">
                        <div class="feature-title">Mobile Friendly</div>
                        <div class="feature-description">Access from phones, tablets, or computers</div>
                    </div>
                </div>

                <div class="feature">
                    <div class="feature-icon">💰</div>
                    <div class="feature-text">
                        <div class="feature-title">Affordable Pricing</div>
                        <div class="feature-description">Flexible plans to fit schools of all sizes</div>
                    </div>
                </div>

                <div class="feature">
                    <div class="feature-icon">🎯</div>
                    <div class="feature-text">
                        <div class="feature-title">Data-Driven Decisions</div>
                        <div class="feature-description">Powerful analytics for better educational outcomes</div>
                    </div>
                </div>
            </div>

            <!-- Contact Section -->
            <div class="contact-section">
                <h2 class="contact-title">📞 Get In Touch</h2>
                <p style="text-align: center; margin-bottom: 30px; color: #555;">
                    Ready to transform your school's management system? We'd love to hear from you!
                </p>

                <div class="contact-methods">
                    <div class="contact-item">
                        <div class="contact-icon">📧</div>
                        <div class="contact-label">Email Us</div>
                        <div class="contact-value">
                            <a href="mailto:info@lumetraanalytics.com">info@lumetraanalytics.com</a>
                        </div>
                    </div>

                    <div class="contact-item">
                        <div class="contact-icon">📱</div>
                        <div class="contact-label">Call/WhatsApp</div>
                        <div class="contact-value">
                            <a href="tel:+254700000000">+254 700 000 000</a>
                        </div>
                    </div>

                    <div class="contact-item">
                        <div class="contact-icon">🌐</div>
                        <div class="contact-label">Visit Website</div>
                        <div class="contact-value">
                            <a href="https://lumetraanalytics.com" target="_blank">lumetraanalytics.com</a>
                        </div>
                    </div>

                    <div class="contact-item">
                        <div class="contact-icon">📍</div>
                        <div class="contact-label">Location</div>
                        <div class="contact-value">
                            Nairobi, Kenya
                        </div>
                    </div>
                </div>

                <a href="mailto:info@lumetraanalytics.com?subject=Inquiry%20about%20LumetraScholar&body=Hello%20Lumetra%20Analytics%20Team,%0D%0A%0D%0AI%20am%20interested%20in%20learning%20more%20about%20your%20school%20management%20solutions.%0D%0A%0D%0ASchool%20Name:%20%0D%0AContact%20Person:%20%0D%0APhone%20Number:%20%0D%0ANumber%20of%20Students:%20%0D%0A%0D%0APlease%20contact%20me%20to%20discuss%20further.%0D%0A%0D%0AThank%20you!" class="cta-button">
                    ✉️ Send Us an Email
                </a>

                <p style="text-align: center; margin-top: 20px; font-size: 14px; color: #888;">
                    We typically respond within 24 hours on business days
                </p>
            </div>

            <!-- What to Expect -->
            <div style="background: #fff3cd; padding: 25px; border-radius: 12px; border-left: 5px solid #ffc107; margin: 30px 0;">
                <h3 style="color: #856404; margin-bottom: 15px;">💡 What Happens Next?</h3>
                <ol style="color: #856404; padding-left: 20px; line-height: 1.8;">
                    <li><strong>Free Consultation:</strong> We'll schedule a call to understand your school's needs</li>
                    <li><strong>Live Demo:</strong> See LumetraScholar in action with sample school data</li>
                    <li><strong>Custom Proposal:</strong> Receive a tailored solution with pricing options</li>
                    <li><strong>Setup & Training:</strong> We'll deploy the system and train your staff</li>
                    <li><strong>Ongoing Support:</strong> Continuous technical support and updates</li>
                </ol>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="footer-links">
                <a href="mailto:info@lumetraanalytics.com">Email</a>
                <a href="tel:+254700000000">Call Us</a>
                <a href="#features">Features</a>
                <a href="#services">Services</a>
            </div>
            <p>&copy; 2024 Lumetra Analytics. All rights reserved.</p>
            <p style="margin-top: 10px; font-size: 12px; opacity: 0.8;">
                Educational Excellence Through Data-Driven Insights
            </p>
        </div>
    </div>
</body>
</html>
