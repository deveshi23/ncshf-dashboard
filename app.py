import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    return pd.read_csv("data/processed/processed_data.csv")

df = load_data()

def show_review_page():
    st.title("📋 Applications Ready for Review")

    ready_df = df[df['ready_for_review'] == True]

    signed_filter = st.selectbox(
        "Filter by Committee Signature:",
        ["All", "Signed", "Unsigned"]
    )

    if signed_filter == "Signed":
        ready_df = ready_df[ready_df['signed_by_committee'] == True]
    elif signed_filter == "Unsigned":
        ready_df = ready_df[ready_df['signed_by_committee'] == False]

    st.markdown(f"### Showing {len(ready_df)} applications ready for review")

    columns_to_show = ['request_date', 'assistance_type', 'amount_granted', 'gender', 'age', 'status', 'application_signed']
    st.dataframe(ready_df[columns_to_show].sort_values(by='request_date', ascending=False), use_container_width=True)

def show_demographics_page():
    st.title("📈 Support Breakdown by Demographics")

    st.markdown("Breakdown of **total and average support amounts** based on various demographics.")

    category = st.selectbox(
        "Select demographic category to analyze:",
        ["gender", "age", "income_bracket", "insurance_type"]
    )

    demo_df = df.dropna(subset=[category, 'amount_granted'])

    summary = demo_df.groupby(category).agg(
        total_support=pd.NamedAgg(column="amount_granted", aggfunc="sum"),
        average_support=pd.NamedAgg(column="amount_granted", aggfunc="mean"),
        number_of_patients=pd.NamedAgg(column="amount_granted", aggfunc="count")
    ).reset_index()

    st.bar_chart(summary.set_index(category)[["total_support", "average_support"]])

    st.markdown("### 📋 Summary Table")
    st.write(summary.style.format({"total_support": "${:,.0f}", "average_support": "${:,.0f}"}))

def show_processing_time_page():
    st.title("⏱️ Request Processing Time")

    st.markdown("""
        Analyze how long it takes between **request submission** and **support being provided**.
        This can help identify delays and improve service efficiency.
    """)

    if 'support_sent_date' in df.columns:
        df['support_sent_date'] = pd.to_datetime(df['support_sent_date'], errors='coerce')
        df['request_date'] = pd.to_datetime(df['request_date'], errors='coerce')
        df['processing_time_days'] = (df['support_sent_date'] - df['request_date']).dt.days
    else:
        st.warning("Support sent date not found — estimating processing time using placeholder logic.")
        df['processing_time_days'] = pd.Series([14 + i % 10 for i in range(len(df))])

    valid_df = df.dropna(subset=['processing_time_days'])

    avg_days = valid_df['processing_time_days'].mean()
    max_days = valid_df['processing_time_days'].max()
    min_days = valid_df['processing_time_days'].min()

    st.metric("Average Processing Time (days)", f"{avg_days:.1f}")
    st.metric("Fastest Approval", f"{min_days} days")
    st.metric("Slowest Approval", f"{max_days} days")

    st.markdown("### 📊 Distribution of Processing Times")
    st.bar_chart(valid_df['processing_time_days'].value_counts().sort_index())

    if 'request_date' in df.columns:
        df['month'] = pd.to_datetime(df['request_date']).dt.to_period('M')
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

    if 'amount_utilized' not in df.columns:
        st.warning("Column 'amount_utilized' not found — simulating usage based on granted amount.")
        df['amount_utilized'] = df['amount_granted'] * (0.6 + (df.index % 5) * 0.1)

    df['unused_amount'] = df['amount_granted'] - df['amount_utilized']
    df['fully_utilized'] = df['unused_amount'] <= 1e-2

    total_apps = len(df)
    unused_apps = (df['fully_utilized'] == False).sum()
    percent_unused = unused_apps / total_apps * 100

    st.metric("Patients NOT Fully Utilizing Grants", f"{unused_apps} ({percent_unused:.1f}%)")
    st.metric("Average Unused Amount", f"${df['unused_amount'].mean():,.2f}")

    usage_by_type = df.groupby('assistance_type').agg(
        avg_granted=('amount_granted', 'mean'),
        avg_utilized=('amount_utilized', 'mean'),
        avg_unused=('unused_amount', 'mean'),
        applications=('amount_granted', 'count')
    ).reset_index()

    st.markdown("### 📊 Average Usage by Assistance Type")
    st.write(usage_by_type.style.format({
        "avg_granted": "${:,.2f}",
        "avg_utilized": "${:,.2f}",
        "avg_unused": "${:,.2f}"
    }))

    st.bar_chart(usage_by_type.set_index('assistance_type')[['avg_utilized', 'avg_unused']])

def show_impact_summary_page():
    st.title("🌟 Annual Impact Summary")

    st.markdown("A snapshot of impact and outcomes from the past year.")

    if 'request_date' not in df.columns:
        st.warning("Missing 'request_date' — unable to filter by year.")
        return

    df['request_date'] = pd.to_datetime(df['request_date'], errors='coerce')
    df['year'] = df['request_date'].dt.year
    latest_year = df['year'].dropna().max()
    current_year_df = df[df['year'] == latest_year]

    total_granted = current_year_df['amount_granted'].sum()
    total_patients = current_year_df.shape[0]
    avg_grant = current_year_df['amount_granted'].mean()

    st.metric("Total Support Distributed", f"${total_granted:,.0f}")
    st.metric("Patients Supported", f"{total_patients}")
    st.metric("Average Grant per Patient", f"${avg_grant:,.0f}")

    st.markdown("### 🧾 Grants by Assistance Type")
    assist_summary = current_year_df.groupby('assistance_type').agg(
        total_granted=('amount_granted', 'sum'),
        patient_count=('amount_granted', 'count')
    ).reset_index()

    st.dataframe(assist_summary.style.format({"total_granted": "${:,.0f}"}))

    current_year_df['month'] = current_year_df['request_date'].dt.strftime('%b')
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    trend = current_year_df.groupby('month')['amount_granted'].sum().reindex(month_order).fillna(0)

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
