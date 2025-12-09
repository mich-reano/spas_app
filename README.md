<p align="center">
  <img src="images/lumetra_scholar.png" alt="Lumetra Scholar Logo" width="180"/>
</p>

<h1 align="center"> LumetraScholar</h1>
<h3 align="center">A Streamlit-Powered Academic Reporting & Insights Platform</h3>

---

##  Overview
The **LumetraScholar** is a professional, data-driven platform developed using **Streamlit** to support academic reporting, performance monitoring, and decision-making within schools.

It transforms raw CSV exam data into **interactive dashboards**, **individual student reports**, **subject analytics**, **stream comparisons**, and **exportable PDFs**, making it a powerful tool for teachers, administrators, and academic heads.

---

##  Key Features

###  1. Dashboard Overview
- Overall class and stream performance  
- Best and weakest subjects  
- Performance distribution charts  
- Clean KPIs and visual insights  

###  2. Student Reports
- Individualized student profiles  
- Total marks, mean score, position, and performance level  
- Radar charts and subject-wise breakdowns  
- Automatically generated performance commentary  

###  3. Class Analysis
- Class-wise and stream-wise averages  
- Pass rate and performance distribution  
- Top and bottom performers  
- Comparative visualizations  

###  4. Subject Analysis
- Subject averages per grade and per stream  
- Comparative bar charts  
- Identify strengths and learning gaps  

###  5. Stream Comparison
- Stream-versus-stream performance view  
- Subject-by-subject comparisons  
- Statistical insights for performance review meetings  

###  6. Export Reports
- Export individual student reports to PDF  
- Export class summaries  
- Download cleaned or processed CSV  

---

##  Data Requirements

Upload a CSV containing:(optional)

- **ADM NO.**  
- **NAME OF STUDENTS**  
- **STREAM**  
- **Subject columns (e.g., MAT, ENG, KIS, SST, SCI, AGR, etc.)**  

The system will automatically:

- Detect subject fields  
- Calculate totals, averages, grades, and ranks  
- Generate visual reports & tables  

---

##  How to Use the System

### **Step 1 – Upload Data**
1. Open the app  
2. Go to **Dashboard/Home**  
3. Upload your CSV file  
4. The system validates and loads it automatically  

### **Step 2 – Explore Dashboards**
- View overall performance  
- Inspect KPIs and summaries  

### **Step 3 – Generate Student Reports**
- Search/select a student  
- Instantly view a detailed report  

### **Step 4 – Analyze Classes & Subjects**
- View class performance  
- Explore subject trends  
- Compare streams visually  

### **Step 5 – Export**
- Generate PDF reports   

---

##  Technologies Used

- **Python 3.10+**  
- **Streamlit**  
- **Pandas / NumPy**  
- **Plotly / Altair / Matplotlib**  
- **FPDF / pdfkit** (for report exports)

---

##  Installation

```bash
git clone https://github.com/yourusername/SPAS.git
cd SPAS
pip install -r requirements.txt
streamlit run app.py
```
---

## **📞 Support / Contact**

- For improvements or support:
- Developed by: Michael Reagan
- Email: michaelreagan94@gmail.com
