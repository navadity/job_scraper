import streamlit as st
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px
import openai
from fpdf import FPDF
import PyPDF2
import io

# Load OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai_api_key"]

# Replace with your Adzuna credentials
APP_ID = "405c8afb"
APP_KEY = "62a942e1b43aa0c0676795f62c5181d1"
COUNTRY = "us"

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

def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def rewrite_resume(resume_text, job_description):
    prompt = f"""
You are a resume optimization assistant. Here is a user's current resume:

{resume_text}

And here is a job description they are targeting:

{job_description}

Rewrite the resume to highlight relevant skills, experiences, and keywords from the job description while keeping it professional and concise.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert resume editor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def save_to_pdf(text, filename="rewritten_resume.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

# UI starts here
st.title("🧠 Smart Job Scraper + Resume Rewriter")

job_query = st.text_input("🔍 Job Title to Search", value="Software Engineer 2")
num_pages = st.slider("Pages to scrape", 1, 5, 1)

if st.button("Fetch Jobs"):
    with st.spinner("Fetching jobs..."):
        jobs = fetch_jobs(job_query, pages=num_pages)
        if jobs:
            df = pd.DataFrame(jobs)
            st.success(f"✅ Found {len(df)} jobs")

            # Charts
            st.subheader("📊 Top Hiring Companies")
            chart_data = df["Company"].value_counts().reset_index()
            chart_data.columns = ["Company", "Job Count"]
            fig = px.bar(chart_data, x="Company", y="Job Count", title="Top Companies Hiring")
            st.plotly_chart(fig, use_container_width=True)

            # Interactive Grid
            st.subheader("📋 Job Listings")
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination()
            grid_options = gb.build()
            selected = AgGrid(df, gridOptions=grid_options, enable_enterprise_modules=True)

            # Resume Rewriter Section
            st.subheader("📝 Resume Rewriting Assistant")
            uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])
            if uploaded_file:
                resume_text = extract_text_from_pdf(uploaded_file)
                job_to_use = st.selectbox("Select Job for Tailoring Resume", df["Title"] + " @ " + df["Company"])
                selected_job_desc = df[df["Title"] + " @ " + df["Company"] == job_to_use]["Description"].values[0]

                if st.button("✏️ Rewrite Resume"):
                    with st.spinner("Rewriting your resume..."):
                        rewritten_text = rewrite_resume(resume_text, selected_job_desc)
                        pdf_path = save_to_pdf(rewritten_text)
                        with open(pdf_path, "rb") as f:
                            st.download_button("📥 Download Tailored Resume (PDF)", f, file_name="rewritten_resume.pdf")
        else:
            st.warning("⚠️ No jobs found.")
