import streamlit as st
import requests
import pandas as pd
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from io import BytesIO
import openai
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px

# Set API key
openai.api_key = st.secrets["openai"]["api_key"]

# Adzuna credentials
APP_ID = "405c8afb"
APP_KEY = "62a942e1b43aa0c0676795f62c5181d1"
COUNTRY = "us"

# Job scraping function
def fetch_jobs(query, pages=1):
    all_jobs = []
    for page in range(1, pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page}"
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": query,
            "results_per_page": 50,
            "content-type": "application/json"
        }
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json()
            for job in data.get("results", []):
                all_jobs.append({
                    "Title": job.get("title"),
                    "Company": job.get("company", {}).get("display_name"),
                    "Location": job.get("location", {}).get("display_name"),
                    "Description": job.get("description"),
                    "URL": job.get("redirect_url")
                })
        else:
            st.error(f"Error {res.status_code}: {res.text}")
    return all_jobs

# Resume reading
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Resume rewriting with OpenAI
def rewrite_resume(original_resume, job_description):
    prompt = f"""You are a professional resume writer. Modify the following resume to better match the job description provided below. Keep the tone formal and highlight relevant experience.

Job Description:
{job_description}

Original Resume:
{original_resume}

Modified Resume:"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message["content"]

# Convert modified resume to PDF
def create_pdf_from_text(text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    lines = text.split("\n")
    y = 800
    for line in lines:
        if y < 50:
            c.showPage()
            y = 800
        c.drawString(50, y, line[:100])
        y -= 15
    c.save()
    buffer.seek(0)
    return buffer

# UI
st.title("🧠 Smart Job Scraper + Resume Tailor")

job_query = st.text_input("Search Job Title:", value="Software Engineer 2")
num_pages = st.slider("Pages to scrape", 1, 3, 1)

if st.button("🔍 Fetch Jobs"):
    results = fetch_jobs(job_query, pages=num_pages)
    if results:
        df = pd.DataFrame(results)
        st.success(f"✅ Found {len(df)} jobs.")

        # Job chart
        st.subheader("📊 Top Companies Hiring")
        chart = df["Company"].value_counts().reset_index()
        chart.columns = ["Company", "Job Count"]
        fig = px.bar(chart, x="Company", y="Job Count")
        st.plotly_chart(fig)

        # Data table
        st.subheader("📋 Job Listings")
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination()
        grid_options = gb.build()
        AgGrid(df, gridOptions=grid_options)

        # Download
        if st.button("📥 Export to Excel"):
            df.to_excel("jobs_output.xlsx", index=False)
            with open("jobs_output.xlsx", "rb") as f:
                st.download_button("Download Excel", f, file_name="jobs.xlsx")
    else:
        st.warning("⚠️ No jobs found.")

# Resume tailoring
st.header("✍️ Upload Resume to Tailor")

uploaded_resume = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
job_description = st.text_area("Paste job description here")

if uploaded_resume and job_description:
    if st.button("🚀 Rewrite Resume"):
        resume_text = extract_text_from_pdf(uploaded_resume)
        tailored_resume = rewrite_resume(resume_text, job_description)
        pdf_file = create_pdf_from_text(tailored_resume)
        st.success("✅ Resume rewritten successfully!")
        st.download_button("📄 Download Tailored Resume (PDF)", pdf_file, file_name="tailored_resume.pdf")

