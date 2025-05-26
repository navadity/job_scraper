import streamlit as st
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px

# Replace with your Adzuna credentials
APP_ID = "405c8afb"
APP_KEY = "62a942e1b43aa0c0676795f62c5181d1"
COUNTRY = "us"

def fetch_jobs(query, company_filter=None, pages=1):
    all_jobs = []
    for page in range(1, pages + 1):
        full_query = query
        if company_filter:
            full_query += f' company:"{company_filter}"'
        url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page}"
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": full_query,
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
                    "URL": job.get("redirect_url"),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max")
                })
        else:
            st.error(f"Error {res.status_code}: {res.text}")
    return all_jobs

# Unified Streamlit interface
st.title("🧠 Smart Job Scraper")

job_query = st.text_input("Search job title or keyword", value="Software Engineer 2")
company_filter = st.text_input("Optional: Filter by company (e.g., Microsoft)", value="")
num_pages = st.slider("Pages to scrape", 1, 5, 1)

if st.button("🔍 Fetch Jobs"):
    with st.spinner("Fetching jobs..."):
        results = fetch_jobs(query=job_query, company_filter=company_filter, pages=num_pages)
        if results:
            df = pd.DataFrame(results)
            st.success(f"✅ Found {len(df)} job listings.")

            df['MinSalary'] = pd.to_numeric(df['salary_min'], errors='coerce')
            df['MaxSalary'] = pd.to_numeric(df['salary_max'], errors='coerce')
            df['AvgSalary'] = df[['MinSalary', 'MaxSalary']].mean(axis=1)

            st.subheader("📍 Job Locations")
            loc_count = df["Location"].value_counts().reset_index()
            loc_count.columns = ["Location", "Job Count"]
            fig = px.bar(loc_count, x="Location", y="Job Count", title="Job Distribution by Location")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📊 Job Count by Company")
            company_chart = df["Company"].value_counts().reset_index()
            company_chart.columns = ["Company", "Job Count"]
            fig_company = px.bar(company_chart, x="Company", y="Job Count", title="Top Hiring Companies")
            st.plotly_chart(fig_company, use_container_width=True)

            st.subheader("📈 Salary Insights")
            company_salary = df.groupby("Company")["AvgSalary"].mean().dropna().sort_values(ascending=False).head(10).reset_index()
            fig_salary = px.bar(company_salary, x="Company", y="AvgSalary", title="Avg Salary by Company", labels={"AvgSalary": "Avg Salary (USD)"})
            st.plotly_chart(fig_salary, use_container_width=True)

            st.subheader("📋 Job Listings (Interactive Grid)")
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=False)
            grid_options = gb.build()
            AgGrid(df, gridOptions=grid_options, enable_enterprise_modules=True, fit_columns_on_grid_load=True)

            if st.button("📥 Export to Excel"):
                df.to_excel("combined_jobs.xlsx", index=False)
                with open("combined_jobs.xlsx", "rb") as f:
                    st.download_button("Download Excel", f, file_name="job_listings.xlsx")
        else:
            st.warning("⚠️ No jobs found. Try refining your search.")
