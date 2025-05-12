import streamlit as st
import pandas as pd
import os

# Check current working directory
st.write("Current working directory:", os.getcwd())

# Define file path
file_path = "UNO Service Learning Data Sheet De-Identified Version.xlsx"

# Check if the file exists and load the data
@st.cache_data
def load_data(file=None):
    if file is not None:
        return pd.read_excel(file)
    elif os.path.exists(file_path):
        return pd.read_excel(file_path)
    else:
        st.error(f"File '{file_path}' not found!")
        return None

# Upload file or use default path
uploaded_file = st.file_uploader("Upload the Excel file", type="xlsx")
if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    df = load_data()

# Check if df was successfully loaded
if df is None:
    st.stop()  # Stop execution if file was not found

def show_demographics_page():
    if df is None:
        st.error("No data available. Please check if the file is loaded.")
        return

    st.title("📈 Support Breakdown by Demographics")
    demo_cols = ['Gender', 'Race', 'Ethnicity', 'Marital Status', 'Insurance Type', 'Household Size', 'Income']
    demo_cols = [col for col in demo_cols if col in df.columns]
    if not demo_cols:
        st.error("No demographic columns found in data.")
        return
    category = st.selectbox("Select demographic category:", demo_cols)
    if 'Amount Approved' not in df.columns:
        st.warning("No financial data available - showing counts only")
        st.bar_chart(df[category].value_counts())
        return
    demo_df = df.dropna(subset=[category, 'Amount Approved'])
    summary = demo_df.groupby(category).agg(
        total_support=('Amount Approved', 'sum'),
        average_support=('Amount Approved', 'mean'),
        count=('Amount Approved', 'count')
    ).reset_index()
    st.bar_chart(summary.set_index(category)[['total_support', 'average_support']])
    st.dataframe(summary.style.format({
        "total_support": "${:,.2f}",
        "average_support": "${:,.2f}"
    }))

def show_processing_time_page():
    if df is None:
        st.error("No data available. Please check if the file is loaded.")
        return

    st.title("⏱️ Request Processing Time")
    if 'Date Application Received' not in df.columns or 'Date Check Sent' not in df.columns:
        st.error("Required date columns not found.")
        return
    df['Date Application Received'] = pd.to_datetime(df['Date Application Received'], errors='coerce')
    df['Date Check Sent'] = pd.to_datetime(df['Date Check Sent'], errors='coerce')
    df['processing_days'] = (df['Date Check Sent'] - df['Date Application Received']).dt.days
    valid_df = df.dropna(subset=['processing_days'])
    if valid_df.empty:
        st.warning("No valid processing time data available.")
        return
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Days", f"{valid_df['processing_days'].mean():.1f}")
    with col2:
        st.metric("Fastest", f"{valid_df['processing_days'].min()} days")
    with col3:
        st.metric("Slowest", f"{valid_df['processing_days'].max()} days")
    st.bar_chart(valid_df['processing_days'].value_counts().sort_index())
    try:
        df['month'] = df['Date Application Received'].dt.to_period('M')
        trend = df.groupby('month')['processing_days'].mean().reset_index()
        trend['month'] = trend['month'].astype(str)
        st.line_chart(trend.set_index('month'))
    except Exception as e:
        st.error(f"Couldn't generate monthly trend: {str(e)}")

def show_grant_utilization_page():
    if df is None:
        st.error("No data available. Please check if the file is loaded.")
        return

    st.title("💸 Grant Utilization Analysis")
    if 'Amount Approved' not in df.columns:
        st.error("No financial data available.")
        return
    df['Amount Utilized'] = df.get('Amount Utilized', df['Amount Approved'])  # Assume full use if missing
    df['Unused Amount'] = df['Amount Approved'] - df['Amount Utilized']
    df['Fully Utilized'] = df['Unused Amount'] <= 0.01
    col1, col2 = st.columns(2)
    with col1:
        unused_count = (~df['Fully Utilized']).sum()
        st.metric("Not Fully Utilized", f"{unused_count} ({(unused_count/len(df))*100:.1f}%)")
    with col2:
        st.metric("Avg Unused Amount", f"${df['Unused Amount'].mean():,.2f}")
    if 'Type of Support Requested' in df.columns:
        by_type = df.groupby('Type of Support Requested').agg(
            avg_grant=('Amount Approved', 'mean'),
            avg_used=('Amount Utilized', 'mean'),
            avg_unused=('Unused Amount', 'mean'),
            count=('Amount Approved', 'count')
        ).reset_index()
        st.bar_chart(by_type.set_index('Type of Support Requested')[['avg_used', 'avg_unused']])
        st.dataframe(by_type.style.format({
            "avg_grant": "${:,.2f}",
            "avg_used": "${:,.2f}",
            "avg_unused": "${:,.2f}"
        }))

def show_impact_summary_page():
    if df is None:
        st.error("No data available. Please check if the file is loaded.")
        return

    st.title("🌟 Annual Impact Summary")
    if 'Date Application Received' not in df.columns:
        st.error("No date column available.")
        return
    df['Date Application Received'] = pd.to_datetime(df['Date Application Received'], errors='coerce')
    df['year'] = df['Date Application Received'].dt.year
    latest_year = df['year'].max()
    yearly_df = df[df['year'] == latest_year]
    if 'Amount Approved' in df.columns:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Support", f"${yearly_df['Amount Approved'].sum():,.0f}")
        with col2:
            st.metric("Patients Supported", len(yearly_df))
        with col3:
            st.metric("Average Grant", f"${yearly_df['Amount Approved'].mean():,.0f}")
    if 'Type of Support Requested' in df.columns:
        st.subheader("Support by Type")
        by_type = yearly_df['Type of Support Requested'].value_counts()
        st.bar_chart(by_type)
    yearly_df['month'] = yearly_df['Date Application Received'].dt.month_name()
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly = yearly_df.groupby('month').size().reindex(month_order, fill_value=0)
    st.subheader(f"Monthly Distribution ({latest_year})")
    st.bar_chart(monthly)

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "📈 Demographics",
    "⏱️ Processing Time",
    "💸 Grant Utilization",
    "🌟 Impact Summary"
])

if page == "📈 Demographics":
    show_demographics_page()
elif page == "⏱️ Processing Time":
    show_processing_time_page()
elif page == "💸 Grant Utilization":
    show_grant_utilization_page()
elif page == "🌟 Impact Summary":
    show_impact_summary_page()
