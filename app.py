import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/processed/processed_data.csv")
        df.columns = df.columns.str.strip()
        
        # Verify we have required columns
        expected_columns = ['Amount', 'Type of Assistance', 'Request Status']
        for col in expected_columns:
            if col not in df.columns:
                st.error(f"Required column '{col}' not found in data")
                
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()  # Return empty dataframe to prevent crashes

df = load_data()
df.columns = df.columns.str.strip()  # Clean any whitespace in column names


def show_review_page():
    st.title("📋 Applications Ready for Review")
    
    # First check if the column exists
    if 'Request Status' not in df.columns:
        st.error(f"'Request Status' column not found. Available columns: {df.columns.tolist()}")
        return
    
    # Filter for ready for review applications
    ready_df = df[df['Request Status'] == 'Ready for Review']  

    signed_filter = st.selectbox(
        "Filter by Committee Signature:",
        ["All", "Signed", "Unsigned"]
    )

    if signed_filter == "Signed":
        ready_df = ready_df[ready_df['Application Signed?'] == 'Signed']
    elif signed_filter == "Unsigned":
        ready_df = ready_df[ready_df['Application Signed?'] == 'Unsigned']

    st.markdown(f"### Showing {len(ready_df)} applications ready for review")

    columns_to_show = ['Date', 'Type of Assistance', 'Amount', 'Gender', 'DOB', 'Request Status', 'Application Signed?']
    # Make sure all columns exist
    columns_to_show = [col for col in columns_to_show if col in df.columns]
    st.dataframe(ready_df[columns_to_show].sort_values(by='Date', ascending=False), use_container_width=True)


def show_demographics_page():
    st.title("📈 Support Breakdown by Demographics")

    st.markdown("Breakdown of **total and average support amounts** based on various demographics.")

    # Choose demographic category
    category = st.selectbox(
        "Select demographic category to analyze:",
        ["Gender", "Age", "Insurance Type"]
    )

    # Calculate age from DOB if age is selected
    if category == "Age":
        df['DOB'] = pd.to_datetime(df['DOB'], errors='coerce')
        current_year = pd.to_datetime('today').year
        df['Age'] = current_year - df['DOB'].dt.year
        category = 'Age'  # Now the category will be "Age"
    
    # Group and summarize
    demo_df = df.dropna(subset=[category, 'Amount'])

    summary = demo_df.groupby(category).agg(
        total_support=pd.NamedAgg(column="Amount", aggfunc="sum"),
        average_support=pd.NamedAgg(column="Amount", aggfunc="mean"),
        number_of_patients=pd.NamedAgg(column="Amount", aggfunc="count")
    ).reset_index()

    # Display chart
    st.bar_chart(summary.set_index(category)[["total_support", "average_support"]])

    # Show detailed table
    st.markdown("### 📋 Summary Table")
    st.dataframe(summary.style.format({"total_support": "${:,.0f}", "average_support": "${:,.0f}"}))


def show_processing_time_page():
    st.title("⏱️ Request Processing Time")

    st.markdown("""
        Analyze how long it takes between **request submission** and **support being provided**.
        This can help identify delays and improve service efficiency.
    """)

    # Try to calculate processing time (if both dates are available)
    if 'Payment Submitted?' in df.columns:
        df['Payment Submitted?'] = pd.to_datetime(df['Payment Submitted?'], errors='coerce')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['processing_time_days'] = (df['Payment Submitted?'] - df['Date']).dt.days
    else:
        # Placeholder if no explicit support date exists — simulate for now
        st.warning("Payment Submitted date not found — estimating processing time using placeholder logic.")
        df['processing_time_days'] = pd.Series([14 + i % 10 for i in range(len(df))])  # simulated range 14–24 days

    # Drop rows without request dates
    valid_df = df.dropna(subset=['processing_time_days'])

    # Show summary stats
    avg_days = valid_df['processing_time_days'].mean()
    max_days = valid_df['processing_time_days'].max()
    min_days = valid_df['processing_time_days'].min()

    st.metric("Average Processing Time (days)", f"{avg_days:.1f}")
    st.metric("Fastest Approval", f"{min_days} days")
    st.metric("Slowest Approval", f"{max_days} days")

    # Histogram
    st.markdown("### 📊 Distribution of Processing Times")
    st.bar_chart(valid_df['processing_time_days'].value_counts().sort_index())

    # Optional: Add time trend over months
    if 'Date' in df.columns:
        df['month'] = pd.to_datetime(df['Date']).dt.to_period('M')
        trend = df.groupby('month')['processing_time_days'].mean().reset_index()
        trend['month'] = trend['month'].astype(str)
        st.markdown("### 📈 Average Processing Time by Month")
        st.line_chart(trend.set_index('month'))


def show_grant_utilization_page():
    st.title("💸 Grant Utilization Analysis")
    
    st.markdown("""
    This page highlights grant utilization information. 
    Note: Financial data columns not found in current dataset.
    """)
    
    # Show what data we do have
    st.warning("Financial columns not available in current data. Showing available information:")
    
    # Display the columns we do have
    if 'descriptions' in df.columns:
        st.write("Descriptions of assistance:")
        st.write(df['descriptions'].value_counts())
    
    if 'application_signed' in df.columns:
        st.write("Application signing status:")
        st.write(df['application_signed'].value_counts())
    
    if 'status' in df.columns:
        st.write("Application status overview:")
        st.write(df['status'].value_counts())
    
    st.write("Full available columns:", df.columns.tolist())


def show_impact_summary_page():
    st.title("🌟 Annual Impact Summary")

    st.markdown("A snapshot of impact and outcomes from the past year.")

    # Filter by most recent calendar year
    if 'Date' not in df.columns:
        st.warning("Missing 'Date' — unable to filter by year.")
        return

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['year'] = df['Date'].dt.year
    latest_year = df['year'].dropna().max()
    current_year_df = df[df['year'] == latest_year]

    # Key metrics
    total_granted = current_year_df['Amount'].sum()
    total_patients = current_year_df.shape[0]
    avg_grant = current_year_df['Amount'].mean()

    st.metric("Total Support Distributed", f"${total_granted:,.0f}")
    st.metric("Patients Supported", f"{total_patients}")
    st.metric("Average Grant per Patient", f"${avg_grant:,.0f}")

    # Assistance type breakdown
    st.markdown("### 🧾 Grants by Assistance Type")
    assist_summary = current_year_df.groupby('Type of Assistance').agg(
        total_granted=('Amount', 'sum'),
        patient_count=('Amount', 'count')
    ).reset_index()

    st.dataframe(assist_summary.style.format({"total_granted": "${:,.0f}"}))

    # Monthly trend
    current_year_df['month'] = current_year_df['Date'].dt.strftime('%b')
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    trend = current_year_df.groupby('month')['Amount'].sum().reindex(month_order).fillna(0)

    st.markdown(f"### 📈 Monthly Grant Distribution - {latest_year}")
    st.bar_chart(trend)

# Sidebar navigation
page = st.sidebar.selectbox("📊 Select a Page", [
    "Applications Ready for Review",
    "Support Breakdown by Demographics",
    "Request Processing Time",
    "Grant Utilization Analysis",
    "Annual Impact Summary"
])

if page == "Applications Ready for Review":
    show_review_page()
elif page == "Support Breakdown by Demographics":
    show_demographics_page()
elif page == "Request Processing Time":
    show_processing_time_page()
elif page == "Grant Utilization Analysis":
    show_grant_utilization_page()
elif page == "Annual Impact Summary":
    show_impact_summary_page()
