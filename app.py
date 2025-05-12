import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    return pd.read_csv("data/processed/processed_data.csv")

df = load_data()

def show_review_page():
    st.title("📋 Applications Ready for Review")

    ready_df = df[df['Request Status'] == 'Ready for Review']  # Filter for ready for review applications

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
    This page highlights how much of their granted funds patients actually used, broken down by assistance type.
    This informs future budget allocations.
    """)

    # Check if required columns exist
    if 'Amount Utilized' not in df.columns:
        st.warning("Column 'Amount Utilized' not found — simulating usage based on granted amount.")
        df['Amount Utilized'] = df['Amount'] * (0.6 + (df.index % 5) * 0.1)  # simulated values: 60%-100%

    # Calculate unused amount
    df['unused_amount'] = df['Amount'] - df['Amount Utilized']
    df['fully_utilized'] = df['unused_amount'] <= 1e-2  # small margin for rounding

    # Summary stats
    total_apps = len(df)
    unused_apps = (df['fully_utilized'] == False).sum()
    percent_unused = unused_apps / total_apps * 100

    st.metric("Patients NOT Fully Utilizing Grants", f"{unused_apps} ({percent_unused:.1f}%)")
    st.metric("Average Unused Amount", f"${df['unused_amount'].mean():,.2f}")

    # Average usage by assistance type
    usage_by_type = df.groupby('Type of Assistance').agg(
        avg_granted=('Amount', 'mean'),
        avg_utilized=('Amount Utilized', 'mean'),
        avg_unused=('unused_amount', 'mean'),
        applications=('Amount', 'count')
    ).reset_index()

    st.markdown("### 📊 Average Usage by Assistance Type")
    st.dataframe(usage_by_type.style.format({
        "avg_granted": "${:,.2f}",
        "avg_utilized": "${:,.2f}",
        "avg_unused": "${:,.2f}"
    }))

    st.bar_chart(usage_by_type.set_index('Type of Assistance')[['avg_utilized', 'avg_unused']])


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
