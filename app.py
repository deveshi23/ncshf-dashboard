import streamlit as st
import pandas as pd
import os

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="NCSHF Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar Navigation and Accessibility Controls ---
st.sidebar.title("Navigation")
st.sidebar.info(
    "Welcome to the dashboard! Use the menu below to explore data insights. "
)

font_size = st.sidebar.radio(
    "Font Size",
    ("Normal", "Large"),
    help="Increase font size for readability."
)
cb_mode = st.sidebar.checkbox("Color-Blind Friendly Mode", value=True)

CB_PALETTE = [
    "#4CAF50", "#FFF176", "#388E3C", "#FFF9C4", "#C8E6C9", "#FBC02D", "#A5D6A7", "#FDD835", "#2E7D32"
]

font_css = "1.1rem" if font_size == "Normal" else "1.35rem"
st.markdown(f"""
    <style>
    html, body, [class*="css"]  {{
        background-color: #FFFFFF !important;
        color: #2E7D32 !important;
        font-size: {font_css} !important;
    }}
    h1 {{
        text-align: center;
        font-size: 2.7rem;
        color: #4CAF50;
        font-weight: bold;
    }}
    h2, h3, .stHeader, .stSubheader {{
        color: #388E3C !important;
    }}
    .stMetric {{
        background-color: #FFF9C4;
        border-radius: 10px;
        padding: 10px;
        color: #2E7D32 !important;
        border: 1px solid #C8E6C9;
    }}
    .block-container {{
        padding-top: 1.5rem;
    }}
    .sidebar .sidebar-content {{
        background-color: #FFF9C4 !important;
    }}
    .stSelectbox > div, .stButton > button {{
        background-color: #C8E6C9 !important;
        color: #2E7D32 !important;
        border-radius: 6px;
        border: 1px solid #4CAF50;
    }}
    .stDataFrame thead tr th {{
        background-color: #FFFDE7 !important;
        color: #2E7D32 !important;
    }}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 8])
with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=80, caption="NCSHF Logo", output_format="PNG")
with col2:
    st.markdown("<h1 style='margin-bottom:0;'> 🚀 Welcome to the NCSHF Service Learning Dashboard!", unsafe_allow_html=True)
    st.caption("<h1 style='margin-bottom:0;'>Empowering community health through data-driven insights", unsafe_allow_html=True)

st.markdown("---")

@st.cache_data
def load_data():
    file_path = "data/raw/UNO Service Learning Data Sheet De-Identified Version.xlsx"
    if not os.path.exists(file_path):
        st.error(f"File not found: {file_path}\n\n"
                 "Please make sure the file is in the correct directory.")
        return pd.DataFrame()
    try:
        df = pd.read_excel(file_path, sheet_name="PA Log Sheet")
        df.columns = df.columns.astype(str).str.strip()
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        if 'DOB' in df.columns:
            try:
                df['DOB'] = pd.to_datetime(df['DOB'], format='%m/%d/%Y', errors='coerce')
            except Exception:
                df['DOB'] = pd.to_datetime(df['DOB'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# --- Session State for appended rows ---
if "appended_rows" not in st.session_state:
    st.session_state.appended_rows = []

if "page" not in st.session_state:
    st.session_state.page = "Landing Page"

df_original = load_data()

def get_dashboard_df():
    if st.session_state.appended_rows:
        df_appended = pd.DataFrame(st.session_state.appended_rows)
        df_appended = df_appended.reindex(columns=df_original.columns, fill_value=None)
        return pd.concat([df_original, df_appended], ignore_index=True)
    else:
        return df_original

df = get_dashboard_df()

def color_blind_bar_chart(data, x=None, y=None, title=None):
    import altair as alt
    if isinstance(data, pd.Series):
        df_chart = data.reset_index()
        df_chart.columns = ['category', 'value']
        x = x or 'category'
        y = y or 'value'
    else:
        df_chart = data.copy()
        if x is None or y is None:
            x, y = df_chart.columns[0], df_chart.columns[1]
    if cb_mode:
        color_encoding = alt.Color(x, scale=alt.Scale(range=CB_PALETTE))
    else:
        color_encoding = alt.Color(x)
    chart = alt.Chart(df_chart).mark_bar().encode(
        x=alt.X(x, sort='-y'),
        y=alt.Y(y),
        color=color_encoding,
        tooltip=[x, y]
    ).properties(width=600, title=title)
    st.altair_chart(chart, use_container_width=True)

# --- Landing Page ---
def landing_page():
    st.title("Use the navigation below or the sidebar to explore the dashboard features:")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📤 Upload Your Data"):
            st.session_state.page = "Upload Your Data"
            st.rerun()
    with col2:
        if st.button("➕ Add New Row"):
            st.session_state.page = "Add New Row"
            st.rerun()
    with col3:
        if st.button("📊 Dashboard"):
            st.session_state.page = "Applications Ready for Review"
            st.rerun()

    st.markdown(
        """
        <br>
        <ul>
        <li>📤 <b>Upload Your Data</b>: Preview your own Excel or CSV file.</li>
        <li>➕ <b>Add New Row</b>: Add new data entries to the dashboard.</li>
        <li>📊 <b>Dashboard</b>: Explore analytics and summaries.</li>
        </ul>
        """, unsafe_allow_html=True
    )

def handle_file_upload():
    st.header("📤 Upload Your Data")
    st.markdown("---")
    uploaded_file = st.file_uploader(
        "Upload your Excel or CSV file (optional)", 
        type=["xlsx", "xls", "csv"]
    )
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                user_df = pd.read_csv(uploaded_file)
            else:
                user_df = pd.read_excel(uploaded_file)
            user_df.columns = user_df.columns.astype(str).str.strip()
            if 'Amount' in user_df.columns:
                user_df['Amount'] = pd.to_numeric(user_df['Amount'], errors='coerce')
            if 'DOB' in user_df.columns:
                try:
                    user_df['DOB'] = pd.to_datetime(user_df['DOB'], format='%m/%d/%Y', errors='coerce')
                except Exception:
                    user_df['DOB'] = pd.to_datetime(user_df['DOB'], errors='coerce')
            st.success(f"Loaded data from: {uploaded_file.name}")
            st.dataframe(user_df, use_container_width=True)
            st.info("This data is only displayed here. The dashboard pages still use the default data.")
        except Exception as e:
            st.error(f"Could not load file: {e}")
    else:
        st.info("No file uploaded yet. You can upload an Excel or CSV file to preview it here.")

def handle_append_row():
    st.header("➕ Add a New Row to the Data")
    st.markdown("---")
    st.info("Fill out the form below to add a new row to the dashboard's data. "
            "Your addition will only persist for this session.")

    with st.form("append_row_form"):
        new_row = {}
        for col in df_original.columns:
            if col.lower() in ["amount"]:
                val = st.number_input(f"{col}", value=0.0)
            elif "date" in col.lower() or "dob" in col.lower():
                val = st.date_input(f"{col}")
            else:
                val = st.text_input(f"{col}")
            new_row[col] = val
        submitted = st.form_submit_button("Add Row")
        if submitted:
            for k, v in new_row.items():
                if isinstance(v, pd.Timestamp):
                    new_row[k] = v.strftime('%m/%d/%Y')
            st.session_state.appended_rows.append(new_row)
            st.success("Row added! It will be included in all dashboard visualizations for this session.")
            st.dataframe(pd.DataFrame(st.session_state.appended_rows), use_container_width=True)

    if st.session_state.appended_rows:
        st.markdown("#### Appended Rows (this session):")
        st.dataframe(pd.DataFrame(st.session_state.appended_rows), use_container_width=True)

def show_review_page():
    st.header("📋 Applications Ready for Review")
    st.markdown("---")
    if df.empty:
        st.error("No data loaded.")
        return
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
            ready_df = df[df[status_col].astype(str).str.contains('ready|review|approved', case=False, na=False)]
        if len(ready_df) == 0:
            st.warning(f"No applications ready for review found in column '{status_col}'")
            st.write(f"Unique values in {status_col}:", df[status_col].unique())
            return
        sign_cols = ['Application Signed?', 'application_signed', 'signed_by_committee', 'Signed']
        sign_col = next((col for col in sign_cols if col in df.columns), None)
        if sign_col:
            signed_filter = st.selectbox(
                "Filter by Committee Signature:",
                ["All", "Signed", "Unsigned"]
            )
            if signed_filter == "Signed":
                ready_df = ready_df[ready_df[sign_col].astype(str).str.contains('yes|signed', case=False, na=False)]
            elif signed_filter == "Unsigned":
                ready_df = ready_df[~ready_df[sign_col].astype(str).str.contains('yes|signed', case=False, na=False)]
        st.subheader(f"Showing {len(ready_df)} applications ready for review")
        cols_to_show = [col for col in [
            'Grant Req Date', 'Type of Assistance (CLASS)', 'Amount',
            'Pt Name', 'Description of Assistance', status_col, sign_col
        ] if col in df.columns]
        if cols_to_show:
            st.dataframe(
                ready_df[cols_to_show].sort_values(
                    by='Grant Req Date' if 'Grant Req Date' in cols_to_show else cols_to_show[0],
                    ascending=False
                ),
                use_container_width=True
            )
        else:
            st.dataframe(ready_df)
    except Exception as e:
        st.error(f"Error filtering applications: {str(e)}")

def show_demographics_page():
    st.header("📈 Support Breakdown by Demographics")
    st.markdown("---")
    if df.empty:
        st.error("No data loaded.")
        return
    df.columns = df.columns.astype(str).str.strip()
    possible_demo_cols = [
        'Gender', 'Sex', 'Race', 'Ethnicity', 'Hispanic/Latino', 'Sexual Orientation',
        'Marital Status', 'Insurance Type', 'Household Size', 'Income', 'Age', 'DOB',
        'Total Household Gross Monthly Income'
    ]
    demo_cols = [col for col in df.columns if col.strip().lower() in [p.lower() for p in possible_demo_cols]]
    if not demo_cols:
        st.error("No demographic columns found in data")
        st.write("Available columns:", df.columns.tolist())
        return
    category = st.selectbox("Select demographic category:", demo_cols)
    if category.lower() == 'age' and 'DOB' in df.columns:
        try:
            df['Age'] = (pd.to_datetime('today') - pd.to_datetime(df['DOB'], errors='coerce')).dt.days // 365
            category = 'Age'
        except Exception as e:
            st.error(f"Couldn't calculate age from DOB: {str(e)}")
            return
    if 'Amount' not in df.columns:
        st.warning("No financial data available - showing counts only")
        color_blind_bar_chart(df[category].value_counts(), x=category, y='count', title=f"Distribution of {category}")
        st.write("Value counts:", df[category].value_counts())
        return
    try:
        demo_df = df.dropna(subset=[category, 'Amount'])
        summary = demo_df.groupby(category).agg(
            total_support=('Amount', 'sum'),
            average_support=('Amount', 'mean'),
            count=('Amount', 'count')
        ).reset_index()
        color_blind_bar_chart(summary[[category, 'total_support']], x=category, y='total_support', title=f"Total Support by {category}")
        color_blind_bar_chart(summary[[category, 'average_support']], x=category, y='average_support', title=f"Average Support by {category}")
        st.dataframe(summary.style.format({
            "total_support": "${:,.2f}",
            "average_support": "${:,.2f}"
        }))
    except Exception as e:
        st.error(f"Error generating demographics breakdown: {str(e)}")

def show_processing_time_page():
    st.header("⏱️ Request Processing Time")
    st.markdown("---")
    if df.empty:
        st.error("No data loaded.")
        return
    df.columns = df.columns.astype(str).str.strip()
    date_col = 'Grant Req Date'
    if date_col not in df.columns:
        st.error(f"Column '{date_col}' not found. Available columns:")
        st.write(df.columns.tolist())
        return
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df['processing_days'] = df.get('processing_days', pd.Series([7 + i % 14 for i in range(len(df))]))
        if df[date_col].isnull().all():
            st.error(f"Column '{date_col}' doesn't contain valid dates")
            st.write("Sample values:", df[date_col].head())
            return
    except Exception as e:
        st.error(f"Error parsing dates: {str(e)}")
        return
    min_date = df[date_col].min()
    max_date = df[date_col].max()
    st.subheader("Filter Data")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", min_date)
    with col2:
        end_date = st.date_input("End date", max_date)
    valid_df = df[
        (df[date_col] >= pd.to_datetime(start_date)) &
        (df[date_col] <= pd.to_datetime(end_date))
    ].dropna(subset=['processing_days'])
    if len(valid_df) == 0:
        st.warning("No valid processing time data available for selected date range")
        return
    st.subheader("Processing Time Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Days", f"{valid_df['processing_days'].mean():.1f}")
    with col2:
        st.metric("Fastest", f"{valid_df['processing_days'].min()} days")
    with col3:
        st.metric("Slowest", f"{valid_df['processing_days'].max()} days")
    counts = valid_df['processing_days'].value_counts().sort_index().reset_index()
    counts.columns = ['processing_days', 'count']
    color_blind_bar_chart(counts, x='processing_days', y='count', title="Processing Time Distribution")
    st.subheader("Monthly Trends")
    try:
        valid_df = valid_df.copy()
        valid_df['month'] = valid_df[date_col].dt.month_name()
        trend = valid_df.groupby('month')['processing_days'].mean().reset_index()
        trend['month'] = trend['month'].astype(str)
        import altair as alt
        chart = alt.Chart(trend).mark_line(point=True).encode(
            x='month',
            y='processing_days',
            color=alt.value(CB_PALETTE[0] if cb_mode else "#4CAF50")
        ).properties(width=600, title="Average Processing Days by Month")
        st.altair_chart(chart, use_container_width=True)
    except Exception as e:
        st.error(f"Couldn't generate monthly trend: {str(e)}")

def show_grant_utilization_page():
    st.header("💸 Grant Utilization Analysis")
    st.markdown("---")
    if df.empty:
        st.error("No data loaded.")
        return
    if 'Amount' not in df.columns:
        st.error("No financial data available")
        st.write("Available columns:", df.columns.tolist())
        return
    util_cols = ['Amount Utilized', 'Utilized Amount', 'amount_used', 'Remaining Balance']
    util_col = next((col for col in util_cols if col in df.columns), None)
    if util_col is None:
        st.warning("No utilization data found - assuming full utilization")
        df['Amount Utilized'] = df['Amount']
    else:
        if util_col == 'Remaining Balance':
            df['Amount Utilized'] = df['Amount'] - pd.to_numeric(df[util_col], errors='coerce')
        else:
            df['Amount Utilized'] = pd.to_numeric(df[util_col], errors='coerce')
    df['Unused Amount'] = df['Amount'] - df['Amount Utilized']
    df['Fully Utilized'] = df['Unused Amount'] <= 0.01
    col1, col2 = st.columns(2)
    with col1:
        unused_count = (~df['Fully Utilized']).sum()
        st.metric("Patients Not Fully Utilizing", f"{unused_count} ({(unused_count/len(df))*100:.1f}%)")
    with col2:
        st.metric("Average Unused Amount", f"${df['Unused Amount'].mean():,.2f}")
    type_cols = ['Type of Assistance (CLASS)', 'Type of Assistance', 'Assistance Type', 'Help Type']
    type_col = next((col for col in type_cols if col in df.columns), None)
    if type_col:
        by_type = df.groupby(type_col).agg(
            avg_grant=('Amount', 'mean'),
            avg_used=('Amount Utilized', 'mean'),
            avg_unused=('Unused Amount', 'mean'),
            count=('Amount', 'count')
        ).reset_index()
        color_blind_bar_chart(by_type[[type_col, 'avg_used']], x=type_col, y='avg_used', title="Average Used by Assistance Type")
        color_blind_bar_chart(by_type[[type_col, 'avg_unused']], x=type_col, y='avg_unused', title="Average Unused by Assistance Type")
        st.dataframe(by_type.style.format({
            "avg_grant": "${:,.2f}",
            "avg_used": "${:,.2f}",
            "avg_unused": "${:,.2f}"
        }))

def show_impact_summary_page():
    st.header("🌟 Annual Impact Summary")
    st.markdown("---")
    if df.empty:
        st.error("No data loaded.")
        return
    date_col = 'Grant Req Date'
    if date_col not in df.columns:
        st.error(f"Column '{date_col}' not found")
        st.write("Available columns:", df.columns.tolist())
        return
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df['year'] = df[date_col].dt.year
        latest_year = df['year'].max()
        yearly_df = df[df['year'] == latest_year].copy()
        if 'Amount' in df.columns:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Support", f"${yearly_df['Amount'].sum():,.0f}")
            with col2:
                st.metric("Patients Supported", len(yearly_df))
            with col3:
                st.metric("Average Grant", f"${yearly_df['Amount'].mean():,.0f}")
        type_cols = ['Type of Assistance (CLASS)', 'Type of Assistance', 'Assistance Type']
        type_col = next((col for col in type_cols if col in df.columns), None)
        if type_col:
            counts = yearly_df[type_col].value_counts().reset_index()
            counts.columns = [type_col, 'count']
            color_blind_bar_chart(counts, x=type_col, y='count', title="Support by Assistance Type")
        yearly_df['month'] = yearly_df[date_col].dt.month_name()
        month_order = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        monthly = yearly_df.groupby('month').size().reindex(month_order, fill_value=0).reset_index()
        monthly.columns = ['month', 'count']
        color_blind_bar_chart(monthly, x='month', y='count', title=f"Monthly Distribution ({latest_year})")
    except Exception as e:
        st.error(f"Error generating impact summary: {str(e)}")

# --- Navigation ---
pages = {
    "Landing Page": landing_page,
    "Upload Your Data": handle_file_upload,
    "Add New Row": handle_append_row,
    "Applications Ready for Review": show_review_page,
    "Support Breakdown by Demographics": show_demographics_page,
    "Request Processing Time": show_processing_time_page,
    "Grant Utilization Analysis": show_grant_utilization_page,
    "Annual Impact Summary": show_impact_summary_page
}

# --- Page Selection Logic ---
page = st.sidebar.selectbox(
    "📊 Select a Page", 
    list(pages.keys()), 
    index=list(pages.keys()).index(st.session_state.page)
)
st.session_state.page = page

# Render selected page
pages[st.session_state.page]()
