import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Constants
PROCESSED_DATA_PATH = 'data/processed/processed_data.csv'

# Load the processed data into a pandas DataFrame
@st.cache_data  # Updated cache decorator for Streamlit
def load_data():
    df = pd.read_csv(PROCESSED_DATA_PATH)
    
    # Convert date columns to datetime (assuming these columns exist)
    date_cols = ['request_date', 'support_date', 'committee_review_date', 'application_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Calculate derived columns
    if 'request_date' in df.columns and 'support_date' in df.columns:
        df['days_to_support'] = (df['support_date'] - df['request_date']).dt.days
    
    if 'amount_granted' in df.columns and 'amount_used' in df.columns:
        df['remaining_balance'] = df['amount_granted'] - df['amount_used']
        df['full_grant_used'] = df['remaining_balance'] <= 0
    
    return df

# Function to display "Ready for Review" page
def display_ready_for_review(df):
    st.title("Applications Ready for Review")
    
    # Create filters
    col1, col2 = st.columns(2)
    with col1:
        show_signed = st.checkbox("Show only signed applications", value=True)
    with col2:
        show_unsigned = st.checkbox("Show only unsigned applications", value=False)
    
    # Filter data based on selections
    if show_signed and not show_unsigned:
        review_df = df[(df['ready_for_review'] == True) & (df['signed_by_committee'] == True)]
    elif show_unsigned and not show_signed:
        review_df = df[(df['ready_for_review'] == True) & (df['signed_by_committee'] == False)]
    else:
        review_df = df[df['ready_for_review'] == True]
    
    st.write(f"Found {len(review_df)} applications ready for review")
    
    # Display interactive table
    st.dataframe(review_df, use_container_width=True)
    
    # Download button
    st.download_button(
        label="Download Ready for Review Data",
        data=review_df.to_csv(index=False),
        file_name='ready_for_review_applications.csv',
        mime='text/csv'
    )

# Function to display "Support Breakdown" page
def display_support_by_demographics(df):
    st.title("Support Breakdown by Demographics")
    
    # Create filters
    st.sidebar.header("Filter Data")
    demographic = st.sidebar.selectbox(
        "Select Demographic to Analyze",
        ['location', 'gender', 'income_bracket', 'insurance_type', 'age_group']
    )
    
    # Calculate age groups if age data exists
    if 'age' in df.columns:
        bins = [0, 18, 30, 50, 65, 100]
        labels = ['0-18', '19-30', '31-50', '51-65', '65+']
        df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels)
    
    # Group by selected demographic
    support_by_demo = df.groupby(demographic)['amount_granted'].agg(['sum', 'count', 'mean'])
    support_by_demo.columns = ['Total Support', 'Number of Grants', 'Average Grant']
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Support Given", f"${support_by_demo['Total Support'].sum():,.2f}")
    col2.metric("Total Grants Awarded", support_by_demo['Number of Grants'].sum())
    col3.metric("Average Grant Amount", f"${support_by_demo['Average Grant'].mean():,.2f}")
    
    # Create visualizations
    tab1, tab2, tab3 = st.tabs(["Total Support", "Number of Grants", "Average Grant"])
    
    with tab1:
        fig = px.bar(
            support_by_demo,
            x=support_by_demo.index,
            y='Total Support',
            title=f"Total Support by {demographic.replace('_', ' ').title()}",
            labels={'index': demographic.replace('_', ' ').title(), 'Total Support': 'Total Support ($)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.pie(
            support_by_demo,
            names=support_by_demo.index,
            values='Number of Grants',
            title=f"Number of Grants by {demographic.replace('_', ' ').title()}"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = px.bar(
            support_by_demo,
            x=support_by_demo.index,
            y='Average Grant',
            title=f"Average Grant Amount by {demographic.replace('_', ' ').title()}",
            labels={'index': demographic.replace('_', ' ').title(), 'Average Grant': 'Average Grant ($)'}
        )
        st.plotly_chart(fig, use_container_width=True)

# Function to display "Time to Provide Support" page
def display_time_to_support(df):
    st.title("Time Between Request and Support")
    
    # Ensure we have the required columns
    if 'days_to_support' not in df.columns:
        st.error("Required date columns not found in data.")
        return
    
    # Display metrics
    avg_days = df['days_to_support'].mean()
    median_days = df['days_to_support'].median()
    
    col1, col2 = st.columns(2)
    col1.metric("Average Days to Support", f"{avg_days:.1f} days")
    col2.metric("Median Days to Support", f"{median_days:.1f} days")
    
    # Create time series analysis
    df['request_month'] = df['request_date'].dt.to_period('M').dt.to_timestamp()
    monthly_times = df.groupby('request_month')['days_to_support'].mean().reset_index()
    
    fig = px.line(
        monthly_times,
        x='request_month',
        y='days_to_support',
        title="Average Processing Time by Month",
        labels={'request_month': 'Month', 'days_to_support': 'Days to Support'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Show distribution
    fig = px.histogram(
        df,
        x='days_to_support',
        nbins=30,
        title="Distribution of Processing Times",
        labels={'days_to_support': 'Days to Support'}
    )
    st.plotly_chart(fig, use_container_width=True)

# Function to display "Unused Grant Amount" page
def display_unused_grant(df):
    st.title("Unused Grant Amount Analysis")
    
    # Ensure we have the required columns
    if 'remaining_balance' not in df.columns:
        st.error("Required grant amount columns not found in data.")
        return
    
    # Calculate metrics
    total_unused = df[df['remaining_balance'] > 0]['remaining_balance'].sum()
    pct_unused = (len(df[df['remaining_balance'] > 0]) / len(df)) * 100
    
    col1, col2 = st.columns(2)
    col1.metric("Total Unused Funds", f"${total_unused:,.2f}")
    col2.metric("Percentage of Grants with Unused Funds", f"{pct_unused:.1f}%")
    
    # Show by assistance type
    if 'assistance_type' in df.columns:
        unused_by_type = df[df['remaining_balance'] > 0].groupby('assistance_type')['remaining_balance'].agg(['sum', 'count'])
        unused_by_type.columns = ['Total Unused', 'Number of Grants']
        unused_by_type['Average Unused'] = unused_by_type['Total Unused'] / unused_by_type['Number of Grants']
        
        st.subheader("Unused Funds by Assistance Type")
        st.dataframe(unused_by_type.style.format("{:,.2f}"), use_container_width=True)
        
        fig = px.bar(
            unused_by_type,
            x=unused_by_type.index,
            y='Average Unused',
            title="Average Unused Amount by Assistance Type",
            labels={'index': 'Assistance Type', 'Average Unused': 'Average Unused ($)'}
        )
        st.plotly_chart(fig, use_container_width=True)

# Function to display high-level impact summary page
def display_impact_summary(df):
    st.title("Impact and Progress Summary")
    
    # Current year metrics
    current_year = datetime.now().year
    yearly_data = df[df['request_date'].dt.year == current_year]
    
    # Calculate metrics
    total_grants = len(yearly_data)
    total_support = yearly_data['amount_granted'].sum()
    avg_support = yearly_data['amount_granted'].mean()
    unique_families = yearly_data['family_id'].nunique()
    
    # Display KPIs
    st.subheader(f"Year {current_year} Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Grants Awarded", total_grants)
    col2.metric("Total Support Given", f"${total_support:,.2f}")
    col3.metric("Average Grant Amount", f"${avg_support:,.2f}")
    col4.metric("Unique Families Helped", unique_families)
    
    # Year-over-year comparison
    st.subheader("Year-over-Year Comparison")
    
    if 'request_date' in df.columns:
        df['year'] = df['request_date'].dt.year
        yearly_comparison = df.groupby('year').agg({
            'amount_granted': ['sum', 'mean', 'count'],
            'family_id': 'nunique'
        }).reset_index()
        
        yearly_comparison.columns = ['Year', 'Total Support', 'Average Grant', 'Number of Grants', 'Unique Families']
        
        # Create visualizations
        tab1, tab2, tab3 = st.tabs(["Total Support", "Number of Grants", "Average Grant"])
        
        with tab1:
            fig = px.line(
                yearly_comparison,
                x='Year',
                y='Total Support',
                title="Total Support by Year",
                labels={'Total Support': 'Total Support ($)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = px.bar(
                yearly_comparison,
                x='Year',
                y='Number of Grants',
                title="Number of Grants by Year"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            fig = px.line(
                yearly_comparison,
                x='Year',
                y='Average Grant',
                title="Average Grant Amount by Year",
                labels={'Average Grant': 'Average Grant ($)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(yearly_comparison.style.format({
            'Total Support': "${:,.2f}",
            'Average Grant': "${:,.2f}"
        }), use_container_width=True)

# Main function to update the dashboard
def update_dashboard():
    # Load the processed data
    try:
        df = load_data()
    except FileNotFoundError:
        st.error("Processed data file not found. Please ensure the data processing pipeline has run.")
        return
    
    # Sidebar for page navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select a page", (
        "Applications Ready for Review",
        "Support Breakdown by Demographics",
        "Time to Provide Support",
        "Unused Grant Amount",
        "Impact and Progress Summary"
    ))
    
    # Display last updated time
    if os.path.exists(PROCESSED_DATA_PATH):
        last_updated = datetime.fromtimestamp(os.path.getmtime(PROCESSED_DATA_PATH))
        st.sidebar.write(f"Data last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Display content based on selected page
    if page == "Applications Ready for Review":
        display_ready_for_review(df)
    elif page == "Support Breakdown by Demographics":
        display_support_by_demographics(df)
    elif page == "Time to Provide Support":
        display_time_to_support(df)
    elif page == "Unused Grant Amount":
        display_unused_grant(df)
    elif page == "Impact and Progress Summary":
        display_impact_summary(df)
    
    # Add footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This dashboard helps the Nebraska Cancer Specialists Hope Foundation "
        "track and analyze their support programs. Data updates automatically "
        "when new information is added to the system."
    )

if __name__ == "__main__":
    st.set_page_config(
        page_title="NCS Hope Foundation Dashboard",
        page_icon=":heart:",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    update_dashboard()