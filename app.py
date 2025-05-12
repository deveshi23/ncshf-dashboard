import streamlit as st
import pandas as pd
from datetime import datetime
import os

@st.cache_data
def load_data():
    try:
        # Try Excel first, fallback to CSV if not found
        file_paths = [
            "UNO Service Learning Data Sheet De-Identified Version.xlsx",
            "data/UNO Service Learning Data Sheet De-Identified Version.xlsx",
            "data/processed/processed_data.csv"
        ]

        for path in file_paths:
            if os.path.exists(path):
                if path.endswith('.xlsx'):
                    df = pd.read_excel(path)
                else:
                    df = pd.read_csv(path)
                df.columns = df.columns.str.strip()
                print("Columns in data:", df.columns.tolist())
                return df

        raise FileNotFoundError("No valid file found in expected paths.")

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_data()

# Show columns in sidebar for debugging
st.sidebar.markdown("### Data Columns Available")
st.sidebar.write(df.columns.tolist())

# ----------------------------
# Page 1: Applications Ready for Review
# ----------------------------
def show_review_page():
    st.title("📋 Applications Ready for Review")
    
    status_cols = ['ready_for_review', 'status', 'Request Status', 'Application Status']
    status_col = next((col for col in status_cols if col in df.columns), None)
    
    if status_col is None:
        st.error("Couldn't find status column in data")
        st.write("Available columns:", df.columns.tolist())
        return
    
    try:
        if status_col == 'ready_for_review':
            ready_df = df[df[status_col] == True]
        else:
            ready_df = df[df[status_col].astype(str).str.contains('ready|review', case=False, na=False)]
        
        if len(ready_df) == 0:
            st.warning(f"No applications ready for review found in column '{status_col}'")
            st.write(f"Unique values in {status_col}:", df[status_col].unique())
            return
            
        sign_cols = ['application_signed', 'signed_by_committee', 'Application Signed?', 'Signed']
        sign_col = next((col for col in sign_cols if col in df.columns), None)
        
        if sign_col:
            signed_filter = st.selectbox("Filter by Committee Signature:", ["All", "Signed", "Unsigned"])
            if signed_filter == "Signed":
                ready_df = ready_df[ready_df[sign_col].astype(str).str.contains('signed', case=False, na=False)]
            elif signed_filter == "Unsigned":
                ready_df = ready_df[~ready_df[sign_col].astype(str).str.contains('signed', case=False, na=False)]
        
        st.markdown(f"### Showing {len(ready_df)} applications ready for review")
        
        cols_to_show = [col for col in ['Date', 'Type of Assistance', 'Amount', 
                                        'Patient Name', 'Description', status_col] 
                        if col in ready_df.columns]
        if sign_col: cols_to_show.append(sign_col)

        st.dataframe(ready_df[cols_to_show].sort_values(
            by='Date' if 'Date' in ready_df.columns else cols_to_show[0],
            ascending=False
        ), use_container_width=True)
        
    except Exception as e:
        st.error(f"Error filtering applications: {str(e)}")

# ----------------------------
# Page 2: Support Breakdown by Demographics
# ----------------------------
def show_demographics_page():
    st.title("📈 Support Breakdown by Demographics")
    
    demo_cols = [col for col in ['Gender', 'gender', 'Sex', 'Race', 'Ethnicity',
                                 'Hispanic/Latino', 'Sexual Orientation', 
                                 'Marital Status', 'Insurance Type', 'insurance',
                                 'Household Size', 'Income', 'Age', 'DOB']
                if col in df.columns]
    
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

# ----------------------------
# Page 3: Request Processing Time
# ----------------------------
def show_processing_time_page():
    st.title("⏱️ Request Processing Time")
    
    date_cols = ['Date', 'date', 'Request Date', 'Application Date']
    date_col = next((col for col in date_cols if col in df.columns), None)
    
    if date_col is None:
        st.error("No request date column found")
        st.write("Available columns:", df.columns.tolist())
        return
    
    complete_cols = ['Payment Submitted?', 'Completion Date', 'Processed Date', 'payment_date']
    complete_col = next((col for col in complete_cols if col in df.columns), None)
    
    if complete_col is None:
        st.warning("No completion date column found - using placeholder data")
        df['processing_days'] = pd.Series([7 + i % 14 for i in range(len(df))])  # Simulated
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
    
    if date_col in df.columns:
        try:
            df['month'] = df[date_col].dt.to_period('M')
            trend = df.groupby('month')['processing_days'].mean().reset_index()
            trend['month'] = trend['month'].astype(str)
            st.line_chart(trend.set_index('month'))
        except Exception as e:
            st.error(f"Couldn't generate monthly trend: {str(e)}")

# ----------------------------
# Page 4: Grant Utilization Analysis
# ----------------------------
def show_grant_utilization_page():
    st.title("💸 Grant Utilization Analysis")
    
    if 'Amount' not in df.columns:
        st.error("No financial data available")
        st.write("Available columns:", df.columns.tolist())
        return
    
    util_cols = ['Amount Utilized', 'Utilized Amount', 'amount_used']
    util_col = next((col for col in util_cols if col in df.columns), None)
    
    if util_col is None:
        st.warning("No utilization data found - assuming full utilization")
        df['Amount Utilized'] = df['Amount']
    else:
        df['Amount Utilized'] = df[util_col]
    
    df['Unused Amount'] = df['Amount'] - df['Amount Utilized']
    df['Fully Utilized'] = df['Unused Amount'] <= 0.01
    
    col1, col2 = st.columns(2)
    with col1:
        unused_count = (~df['Fully Utilized']).sum()
        st.metric("Patients Not Fully Utilizing", f"{unused_count} ({(unused_count/len(df))*100:.1f}%)")
    with col2:
        st.metric("Average Unused Amount", f"${df['Unused Amount'].mean():,.2f}")
    
    type_cols = ['Type of Assistance', 'Assistance Type', 'Help Type']
    type_col = next((col for col in type_cols if col in df.columns), None)
    
    if type_col:
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

# ----------------------------
# Page 5: Annual Impact Summary
# ----------------------------
def show_impact_summary_page():
    st.title("🌟 Annual Impact Summary")
    
    date_cols = ['Date', 'date', 'Application Date']
    date_col = next((col for col in date_cols if col in df.columns), None)
    
    if date_col is None:
        st.error("No date column available")
        st.write("Available columns:", df.columns.tolist())
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
        
        type_cols = ['Type of Assistance', 'Assistance Type']
        type_col = next((col for col in type_cols if col in df.columns), None)
        
        if type_col:
            st.subheader("Support by Assistance Type")
            by_type = yearly_df[type_col].value_counts()
            st.bar_chart(by_type)
        
        yearly_df['month'] = yearly_df[date_col].dt.month_name()
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        monthly = yearly_df.groupby('month').size().reindex(month_order, fill_value=0)
        st.subheader(f"Monthly Distribution ({latest_year})")
        st.bar_chart(monthly)
        
    except Exception as e:
        st.error(f"Error generating impact summary: {str(e)}")

# ----------------------------
# Navigation
# ----------------------------
pages = {
    "Applications Ready for Review": show_review_page,
    "Support Breakdown by Demographics": show_demographics_page,
    "Request Processing Time": show_processing_time_page,
    "Grant Utilization Analysis": show_grant_utilization_page,
    "Annual Impact Summary": show_impact_summary_page
}

page = st.sidebar.selectbox("📊 Select a Page", list(pages.keys()))
pages[page]()
