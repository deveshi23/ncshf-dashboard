import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Grant Application Dashboard", layout="wide")

# Load processed data
df = pd.read_csv("processed_data.csv")
df.columns = df.columns.str.strip().str.lower()

# Sidebar for navigation
page = st.sidebar.selectbox("Select a Page:", [
    "Application Overview",
    "Demographics Analysis",
    "Processing Time Analysis",
    "Grant Utilization",
    "Annual Impact Summary"
])

if page == "Application Overview":
    st.title("📄 Application Overview")
    st.write("A snapshot of grant applications.")

    st.write("Available columns in loaded DataFrame:", df.columns.tolist())

    st.dataframe(df.head())

elif page == "Demographics Analysis":
    st.title("👥 Demographics Analysis")
    
    if 'gender' in df.columns and 'race' in df.columns:
        gender_counts = df['gender'].value_counts().reset_index()
        gender_counts.columns = ['Gender', 'Count']

        race_counts = df['race'].value_counts().reset_index()
        race_counts.columns = ['Race', 'Count']

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Gender Distribution")
            fig_gender = px.pie(gender_counts, names='Gender', values='Count', hole=0.4)
            st.plotly_chart(fig_gender)

        with col2:
            st.subheader("Race Distribution")
            fig_race = px.pie(race_counts, names='Race', values='Count', hole=0.4)
            st.plotly_chart(fig_race)
    else:
        st.warning("Gender or race columns not found in dataset.")

elif page == "Processing Time Analysis":
    st.title("⏱️ Processing Time Analysis")

    if 'request_date' in df.columns and 'check_mailed_date' in df.columns:
        df['request_date'] = pd.to_datetime(df['request_date'], errors='coerce')
        df['check_mailed_date'] = pd.to_datetime(df['check_mailed_date'], errors='coerce')
        df['processing_days'] = (df['check_mailed_date'] - df['request_date']).dt.days

        st.subheader("Processing Time Distribution")
        fig_processing = px.histogram(df, x='processing_days', nbins=30, title="Days Between Request and Check Mailed")
        st.plotly_chart(fig_processing)
    else:
        st.warning("Required date columns not found in dataset.")

elif page == "Grant Utilization":
    st.title("💰 Grant Utilization")

    if 'amount_granted' in df.columns:
        st.subheader("Grant Amount Distribution")
        fig_amount = px.histogram(df, x='amount_granted', nbins=40, title="Distribution of Grant Amounts")
        st.plotly_chart(fig_amount)

        st.subheader("Total Amount Granted")
        st.metric("Total Grants", f"${df['amount_granted'].sum():,.2f}")
    else:
        st.warning("Amount granted column not found in dataset.")

elif page == "Annual Impact Summary":
    st.title("📆 Annual Impact Summary")

    if 'request_date' in df.columns and 'amount_granted' in df.columns:
        df['year'] = pd.to_datetime(df['request_date'], errors='coerce').dt.year
        annual_summary = df.groupby('year')['amount_granted'].agg(['count', 'sum']).reset_index()
        annual_summary.columns = ['Year', 'Applications', 'Total_Granted']

        st.subheader("Yearly Summary")
        st.dataframe(annual_summary)

        st.subheader("Grants Over Time")
        fig_yearly = px.bar(annual_summary, x='Year', y='Total_Granted', text='Applications', title="Total Grants per Year")
        st.plotly_chart(fig_yearly)
    else:
        st.warning("Required columns for annual summary not found in dataset.")
