import streamlit as st
import pandas as pd
from datetime import datetime

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("UNO Service Learning Data Sheet De-Identified Version.xlsx", sheet_name="PA Log Sheet")
        df.columns = df.columns.str.strip()
        print("Columns in data:", df.columns.tolist())
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_data()

st.sidebar.markdown("### Data Columns Available")
st.sidebar.write(df.columns.tolist())

def show_review_page():
    st.title("📋 Applications Ready for Review")
    
    status_cols = ['Request Status']
    status_col = next((col for col in status_cols if col in df.columns), None)
    
    if status_col is None:
        st.error("Couldn't find status column in data")
        st.write("Available columns:", df.columns.tolist())
        return
    
    try:
        ready_df = df[df[status_col].astype(str).str.contains('ready|review', case=False, na=False)]
        
        if len(ready_df) == 0:
            st.warning(f"No applications ready for review found in column '{status_col}'")
            st.write(f"Unique values in {status_col}:", df[status_col].unique())
            return
        
        sign_cols = ['Payment Submitted?']
        sign_col = next((col for col in sign_cols if col in df.columns), None)
        
        if sign_col:
            signed_filter = st.selectbox("Filter by Payment Submitted:", ["All", "Yes", "No"])
            if signed_filter == "Yes":
                ready_df = ready_df[df[sign_col].astype(str).str.lower() == "yes"]
            elif signed_filter == "No":
                ready_df = ready_df[df[sign_col].astype(str).str.lower() == "no"]
        
        st.markdown(f"### Showing {len(ready_df)} applications ready for review")
        
        cols_to_show = [col for col in ['Grant Req Date', 'Type of Assistance (CLASS)', 'Amount', 
                                        'Patient ID#', 'Description of Assistance', status_col, sign_col] 
                        if col in df.columns]
        
        st.dataframe(ready_df[cols_to_show].sort_values(
            by='Grant Req Date' if 'Grant Req Date' in df.columns else cols_to_show[0],
            ascending=False
        ), use_container_width=True)
        
    except Exception as e:
        st.error(f"Error filtering applications: {str(e)}")

def show_demographics_page():
    st.title("📈 Support Breakdown by Demographics")
    
    demo_cols = [col for col in ['Gender', 'Race', 'Hispanic/Latino', 'Insurance Type', 'Age'] if col in df.columns]
    
    if not demo_cols:
        st.error("No demographic columns found in data")
        st.write("Available columns:", df.columns.tolist())
        return
    
    category = st.selectbox("Select demographic category:", demo_cols)
    
    if category == 'Age' and 'DOB' in df.columns:
        try:
            df['DOB'] = pd.to_datetime(df['DOB'], errors='coerce')
            df['Age'] = (pd.to_datetime('today') - df['DOB']).dt.days // 365
            category = 'Age'
        except Exception as e:
            st.error(f"Couldn't calculate age from DOB: {str(e)}")
            return
    
    if 'Amount' not in df.columns:
        st.warning("No financial data available - showing counts only")
        st.bar_chart(df[category].value_counts())
        st.write("Value counts:", df[category].value_counts())
        return
    
    try:
        demo_df = df.dropna(subset=[category, 'Amount'])
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
    except Exception as e:
        st.error(f"Error generating demographics breakdown: {str(e)}")

def show_processing_time_page():
    st.title("⏱️ Request Processing Time")
    
    date_col = 'Grant Req Date'
    complete_col = 'Payment Submitted Date'
    
    if date_col not in df.columns:
        st.error("No request date column found")
        return
    
    if complete_col not in df.columns:
        st.warning("No completion date column found - using placeholder data")
        df['processing_days'] = pd.Series([7 + i % 14 for i in range(len(df))])
    else:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df[complete_col] = pd.to_datetime(df[complete_col], errors='coerce')
            df['processing_days'] = (df[complete_col] - df[date_col]).dt.days
        except Exception as e:
            st.error(f"Error calculating processing time: {str(e)}")
            return
    
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

def show_grant_utilization_page():
    st.title("💸 Grant Utilization Analysis")
    
    if 'Amount' not in df.columns:
        st.error("No financial data available")
        return
    
    util_col = 'Amount Paid'
    if util_col not in df.columns:
        st.warning("No utilization data found - assuming full utilization")
        df['Amount Utilized'] = df['Amount']
    else:
        df['Amount Utilized'] = df[util_col]
    
    df['Unused Amount'] = df['Amount'] - df['Amount Utilized']
    df['Fully Utilized'] = df['Unused Amount'] <= 0.01
    
    col1, col2 = st.columns(2)
    with col1:
        unused_count = (~df['Fully Utilized']).sum()
        st.metric("Not Fully Utilized", f"{unused_count} ({(unused_count/len(df))*100:.1f}%)")
    with col2:
        st.metric("Avg Unused Amount", f"${df['Unused Amount'].mean():,.2f}")
    
    type_col = 'Type of Assistance (CLASS)'
    if type_col in df.columns:
        by_type = df.groupby(type_col).agg(
            avg_grant=('Amount', 'mean'),
            avg_used=('Amount Utilized', 'mean'),
            avg_unused=('Unused Amount', 'mean'),
            count=('Amount', 'count')
        ).reset_index()
        
        st.bar_chart(by_type.set_index(type_col)[['avg_used', 'avg_unused']])
        st.dataframe(by_type.style.format({
            "avg_grant": "${:,.2f}",
            "avg_used": "${:,.2f}",
            "avg_unused": "${:,.2f}"
        }))

def show_impact_summary_page():
    st.title("🌟 Annual Impact Summary")
    
    date_col = 'Grant Req Date'
    if date_col not in df.columns:
        st.error("No date column available")
        return
    
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df['year'] = df[date_col].dt.year
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
        
        type_col = 'Type of Assistance (CLASS)'
        if type_col in df.columns:
            st.subheader("Support by Assistance Type")
            st.bar_chart(yearly_df[type_col].value_counts())
        
        yearly_df['month'] = yearly_df[date_col].dt.month_name()
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        monthly = yearly_df.groupby('month').size().reindex(month_order, fill_value=0)
        st.subheader(f"Monthly Distribution ({latest_year})")
        st.bar_chart(monthly)
        
    except Exception as e:
        st.error(f"Error generating impact summary: {str(e)}")

pages = {
    "Applications Ready for Review": show_review_page,
    "Support Breakdown by Demographics": show_demographics_page,
    "Request Processing Time": show_processing_time_page,
    "Grant Utilization Analysis": show_grant_utilization_page,
    "Annual Impact Summary": show_impact_summary_page
}

page = st.sidebar.selectbox("📊 Select a Page", list(pages.keys()))
pages[page]()
