import streamlit as st
import requests
import pandas as pd

# Replace these with your free Adzuna credentials
APP_ID = "405c8afb"
APP_KEY = "62a942e1b43aa0c0676795f62c5181d1"
COUNTRY = "us"  # 'in' for India, 'us' for USA

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

# Streamlit UI
st.title("🧠 Smart Job Scraper (Adzuna + Streamlit)")

job_query = st.text_input("Search Job Title:", value="Software Engineer 2")
num_pages = st.slider("Number of pages to scrape", 1, 5, 1)

if st.button("🔍 Fetch Jobs"):
    with st.spinner("Fetching jobs..."):
        results = fetch_jobs(job_query, pages=num_pages)
        if results:
            df = pd.DataFrame(results)
            st.success(f"Found {len(df)} jobs.")
            st.dataframe(df)

            # Download as Excel
            if st.button("📥 Export to Excel"):
                df.to_excel("jobs_output.xlsx", index=False)
                with open("jobs_output.xlsx", "rb") as f:
                    st.download_button("Download Excel", f, file_name="jobs.xlsx")
        else:
            st.warning("No jobs found.")
