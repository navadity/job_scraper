import streamlit as st
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px

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
                    "URL": job.get("redirect_url"),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max")
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
            st.success(f"✅ Found {len(df)} jobs.")

            # Bar Chart: Job Count by Company
            st.subheader("📊 Job Count by Company")
            chart_data = df["Company"].value_counts().reset_index()
            chart_data.columns = ["Company", "Job Count"]
            fig = px.bar(chart_data, x="Company", y="Job Count", title="Top Hiring Companies")
            st.plotly_chart(fig, use_container_width=True)

            # Interactive Grid
            st.subheader("📋 Job Listings (Interactive Grid)")
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=False)
            grid_options = gb.build()
            AgGrid(df, gridOptions=grid_options, enable_enterprise_modules=True, fit_columns_on_grid_load=True)

            # Download button
            if st.button("📥 Export to Excel"):
                df.to_excel("jobs_output.xlsx", index=False)
                with open("jobs_output.xlsx", "rb") as f:
                    st.download_button("Download Excel", f, file_name="jobs.xlsx")

            # Salary Insights
            st.markdown("---")
            st.header("💰 Company & City Payscale Insights")
            df['MinSalary'] = pd.to_numeric(df['salary_min'], errors='coerce')
            df['MaxSalary'] = pd.to_numeric(df['salary_max'], errors='coerce')
            df['AvgSalary'] = df[['MinSalary', 'MaxSalary']].mean(axis=1)

            if "Company" in df.columns:
                st.subheader("🏢 Average Salary by Company (Top 10)")
                company_salary = df.groupby("Company")["AvgSalary"].mean().dropna().sort_values(ascending=False).head(10).reset_index()
                fig = px.bar(company_salary, x="Company", y="AvgSalary", title="Avg Salary by Company", labels={"AvgSalary": "Avg Salary (USD)"})
                st.plotly_chart(fig, use_container_width=True)

            if "Location" in df.columns:
                st.subheader("🌆 Average Salary by City (Top 10)")
                city_salary = df.groupby("Location")["AvgSalary"].mean().dropna().sort_values(ascending=False).head(10).reset_index()
                fig2 = px.bar(city_salary, x="Location", y="AvgSalary", title="Avg Salary by Location", labels={"AvgSalary": "Avg Salary (USD)"})
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("⚠️ No jobs found.")

# Company Search Section
st.markdown("---")
st.header("🏢 Company-Specific Job Scraper")
company_name = st.text_input("Enter company name (e.g., Microsoft)", value="")
company_pages = st.slider("Pages to fetch", 1, 5, 1, key="company_slider")

if st.button("🏢 Fetch Jobs for Company"):
    if company_name:
        with st.spinner(f"Fetching jobs for {company_name}..."):
            company_results = fetch_jobs(query=f'company:"{company_name}"', pages=company_pages)
            if company_results:
                df_company = pd.DataFrame(company_results)
                st.success(f"✅ Found {len(df_company)} jobs at {company_name}")

                # Chart
                st.subheader("📊 Locations of Jobs")
                chart = df_company["Location"].value_counts().reset_index()
                chart.columns = ["Location", "Job Count"]
                fig = px.bar(chart, x="Location", y="Job Count", title=f"Job Locations at {company_name}")
                st.plotly_chart(fig, use_container_width=True)

                # Grid display
                st.subheader("📋 Job Listings (Interactive Grid)")
                gb = GridOptionsBuilder.from_dataframe(df_company)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=False)
                grid_options = gb.build()
                AgGrid(df_company, gridOptions=grid_options, enable_enterprise_modules=True, fit_columns_on_grid_load=True)

                if st.button("📥 Export Company Jobs to Excel"):
                    df_company.to_excel("company_jobs.xlsx", index=False)
                    with open("company_jobs.xlsx", "rb") as f:
                        st.download_button("Download Excel", f, file_name=f"{company_name}_jobs.xlsx")
            else:
                st.warning(f"No jobs found for {company_name}.")
    else:
        st.warning("Please enter a company name.")
