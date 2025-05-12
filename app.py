import streamlit as st
import pandas as pd
from datetime import datetime

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/processed/processed_data.csv")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_data()

# Debugging - show available columns
if st.sidebar.checkbox("Show debug info"):
    st.sidebar.write("Available columns:", df.columns.tolist())
    st.sidebar.write("Sample data:", df.head())

def show_review_page():
    st.title("📋 Applications Ready for Review")
    
    # Find status column (adapt to your actual column names)
    status_col = next((col for col in ['ready_for_review', 'status', 'Request Status'] 
                      if col in df.columns), None)
    
    if not status_col:
        st.error("No status column found in data")
        return
    
    # Filter ready for review applications
    if 'ready_for_review' in df.columns:
        ready_df = df[df['ready_for_review'] == True]
    else:
        ready_df = df[df[status_col].str.contains('review|ready', case=False, na=False)]
    
    if len(ready_df) == 0:
        st.warning("No applications ready for review found")
        return

    # Signature filtering
    sign_col = next((col for col in ['application_signed', 'signed_by_committee', 'Application Signed?'] 
                    if col in df.columns), None)
    
    if sign_col:
        signed_filter = st.selectbox(
            "Filter by Committee Signature:",
            ["All", "Signed", "Unsigned"]
        )
        
        if signed_filter == "Signed":
            ready_df = ready_df[ready_df[sign_col] == 'Signed']
        elif signed_filter == "Unsigned":
            ready_df = ready_df[ready_df[sign_col] != 'Signed']
    
    st.markdown(f"### Showing {len(ready_df)} applications ready for review")
    
    # Display available columns
    cols_to_show = [col for col in ['Date', 'descriptions', 'Type of Assistance', 
                                   'Amount', status_col, sign_col] if col in df.columns]
    st.dataframe(ready_df[cols_to_show].sort_values(
        by='Date' if 'Date' in df.columns else cols_to_show[0], 
        ascending=False
    ), use_container_width=True)

def show_demographics_page():
    st.title("📈 Support Breakdown by Demographics")
    
    # Find available demographic columns
    demo_cols = [col for col in ['Gender', 'Race', 'Hispanic/Latino', 
                                'Sexual Orientation', 'Marital Status',
                                'Insurance Type', 'Household Size',
                                'Total Household Gross Monthly Income'] 
                if col in df.columns]
    
    if not demo_cols:
        st.error("No demographic columns found")
        return
    
    category = st.selectbox("Select demographic category:", demo_cols)
    
    # Check if we have financial data
    if 'Amount' not in df.columns:
        st.warning("No financial data available - showing count distribution only")
        st.bar_chart(df[category].value_counts())
        return
    
    # Calculate age if DOB available
    if category == 'Age' and 'DOB' in df.columns:
        df['DOB'] = pd.to_datetime(df['DOB'], errors='coerce')
        df['Age'] = (datetime.now() - df['DOB']).dt.days // 365
        category = 'Age'
    
    demo_df = df.dropna(subset=[category, 'Amount'])
    
    if len(demo_df) == 0:
        st.warning("No data available for selected category")
        return
    
    summary = demo_df.groupby(category).agg(
        total_support=('Amount', 'sum'),
        average_support=('Amount', 'mean'),
        count=('Amount', 'count')
    ).reset_index()
    
    st.bar_chart(summary.set_index(category)[['total_support', 'average_support']])
    st.dataframe(summary.style.format({
        "total_support": "${:,.2f}",
        "average_support": "${:,.2f}"
    }))

def show_processing_time_page():
    st.title("⏱️ Request Processing Time")
    
    if 'Date' not in df.columns:
        st.error("No date column found - cannot calculate processing time")
        return
    
    # Try to find completion date column
    complete_col = next((col for col in ['Payment Submitted?', 'completed_date', 'payment_date'] 
                        if col in df.columns), None)
    
    if not complete_col:
        st.warning("No completion date column found - using placeholder data")
        df['processing_days'] = pd.Series([14 + i % 10 for i in range(len(df))])
    else:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df[complete_col] = pd.to_datetime(df[complete_col], errors='coerce')
        df['processing_days'] = (df[complete_col] - df['Date']).dt.days
    
    valid_df = df.dropna(subset=['processing_days'])
    
    if len(valid_df) == 0:
        st.warning("No valid processing time data available")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Days", f"{valid_df['processing_days'].mean():.1f}")
    with col2:
        st.metric("Fastest", f"{valid_df['processing_days'].min()} days")
    with col3:
        st.metric("Slowest", f"{valid_df['processing_days'].max()} days")
    
    st.bar_chart(valid_df['processing_days'].value_counts().sort_index())
    
    # Monthly trend if date available
    if 'Date' in df.columns:
        df['month'] = df['Date'].dt.to_period('M')
        trend = df.groupby('month')['processing_days'].mean().reset_index()
        trend['month'] = trend['month'].astype(str)
        st.line_chart(trend.set_index('month'))

def show_grant_utilization_page():
    st.title("💸 Grant Utilization Analysis")
    
    if 'Amount' not in df.columns:
        st.error("No financial data available for utilization analysis")
        return
    
    # Check for utilization data
    if 'Amount Utilized' not in df.columns:
        st.warning("Assuming full utilization (Amount Utilized column not found)")
        df['Amount Utilized'] = df['Amount']
    
    df['Unused Amount'] = df['Amount'] - df['Amount Utilized']
    df['Fully Utilized'] = df['Unused Amount'] <= 0.01  # Tolerance for rounding
    
    col1, col2 = st.columns(2)
    with col1:
        unused_count = (~df['Fully Utilized']).sum()
        st.metric("Patients Not Fully Utilizing", f"{unused_count} ({(unused_count/len(df))*100:.1f}%)")
    with col2:
        st.metric("Average Unused Amount", f"${df['Unused Amount'].mean():,.2f}")
    
    if 'Type of Assistance' in df.columns:
        by_type = df.groupby('Type of Assistance').agg(
            avg_grant=('Amount', 'mean'),
            avg_used=('Amount Utilized', 'mean'),
            avg_unused=('Unused Amount', 'mean'),
            count=('Amount', 'count')
        ).reset_index()
        
        st.bar_chart(by_type.set_index('Type of Assistance')[['avg_used', 'avg_unused']])
        st.dataframe(by_type.style.format({
            "avg_grant": "${:,.2f}",
            "avg_used": "${:,.2f}",
            "avg_unused": "${:,.2f}"
        }))

def show_impact_summary_page():
    st.title("🌟 Annual Impact Summary")
    
    if 'Date' not in df.columns:
        st.error("No date column available for annual summary")
        return
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['year'] = df['Date'].dt.year
    latest_year = df['year'].max()
    yearly_df = df[df['year'] == latest_year]
    
    if 'Amount' in df.columns:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Support", f"${yearly_df['Amount'].sum():,.0f}")
        with col2:
            st.metric("Patients Supported", len(yearly_df))
        with col3:
            st.metric("Average Grant", f"${yearly_df['Amount'].mean():,.0f}")
    
    if 'Type of Assistance' in df.columns:
        st.subheader("Support by Assistance Type")
        by_type = yearly_df['Type of Assistance'].value_counts()
        st.bar_chart(by_type)
    
    # Monthly trend
    if 'Date' in df.columns:
        yearly_df['month'] = yearly_df['Date'].dt.month_name()
        monthly = yearly_df.groupby('month').size()
        st.subheader(f"Monthly Distribution ({latest_year})")
        st.bar_chart(monthly)

# Sidebar navigation
pages = {
    "Applications Ready for Review": show_review_page,
    "Support Breakdown by Demographics": show_demographics_page,
    "Request Processing Time": show_processing_time_page,
    "Grant Utilization Analysis": show_grant_utilization_page,
    "Annual Impact Summary": show_impact_summary_page
}

page = st.sidebar.selectbox("📊 Select a Page", list(pages.keys()))
pages[page]()