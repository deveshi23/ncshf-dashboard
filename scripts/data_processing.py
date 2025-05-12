import pandas as pd
import os
from datetime import datetime

# Get the root directory regardless of where the script is run from
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DATA_PATH = os.path.join(ROOT_DIR, 'data', 'raw', 'UNO Service Learning Data Sheet De-Identified Version.xlsx')
PROCESSED_DATA_PATH = os.path.join(ROOT_DIR, 'data', 'processed', 'processed_data.csv')

# Check directory and file existence
print("Current Working Directory:", os.getcwd())
if not os.path.exists(os.path.dirname(RAW_DATA_PATH)):
    print("The 'data/raw' directory does not exist.")
else:
    print("Contents of 'data/raw':", os.listdir(os.path.dirname(RAW_DATA_PATH)))

def clean_data():
    df = pd.read_excel(RAW_DATA_PATH, engine='openpyxl')

    # --- Standardizing column names ---
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')

    # --- Renaming for clarity ---
    rename_map = {
        'grant_req_date': 'request_date',
        'application_signed?': 'application_signed',
        'request_status': 'status',
        'total_household_gross_monthly_income': 'monthly_income',
        'type_of_assistance_class': 'assistance_type',
        'amount': 'amount_granted',
        'dob': 'date_of_birth'
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    # --- Dropping completely empty rows ---
    df.dropna(how='all', inplace=True)

    # --- Handling key flags ---
    if 'application_signed' in df.columns:
        df['application_signed'] = df['application_signed'].fillna('Missing')
    else:
        df['application_signed'] = 'Missing'

    if 'status' in df.columns:
        df['status'] = df['status'].fillna('Unknown')
    else:
        df['status'] = 'Unknown'

    # --- Converting dates ---
    if 'request_date' in df.columns:
        df['request_date'] = pd.to_datetime(df['request_date'], errors='coerce')
    if 'date_of_birth' in df.columns:
        df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce')

    # --- Calculating age ---
    today = pd.to_datetime('today')
    if 'date_of_birth' in df.columns:
        df['age'] = df['date_of_birth'].apply(lambda dob: today.year - dob.year if pd.notnull(dob) else None)

    # --- Cleaning categorical fields ---
    if 'gender' in df.columns:
        df['gender'] = df['gender'].str.strip().str.capitalize()
    if 'insurance_type' in df.columns:
        df['insurance_type'] = df['insurance_type'].str.strip().str.title()

    # --- Grant usage calculation ---
    if 'amount_granted' in df.columns:
        df['amount_granted'] = pd.to_numeric(df['amount_granted'], errors='coerce')
    if 'remaining_balance' in df.columns:
        df['remaining_balance'] = pd.to_numeric(df['remaining_balance'], errors='coerce')
        df['amount_used'] = df['amount_granted'] - df['remaining_balance']
        df['full_grant_used'] = df['remaining_balance'] <= 0

    # --- Income bracket classification ---
    if 'monthly_income' in df.columns:
        df['income_bracket'] = pd.cut(df['monthly_income'], bins=[0, 2000, 4000, 6000, 10000, 100000],
                                      labels=['<2k', '2–4k', '4–6k', '6–10k', '10k+'])

    # --- Review-ready flag ---
    if 'status' in df.columns:
        df['ready_for_review'] = (df['status'].str.lower() == 'approved')

    # --- Application signed flag normalization ---
    if 'application_signed' in df.columns:
        df['signed_by_committee'] = df['application_signed'].str.lower().isin(['yes', 'signed'])

    # --- Save cleaned data ---
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    df.to_csv(PROCESSED_DATA_PATH, index=False)
    print("✅ Data has been cleaned and saved to:", PROCESSED_DATA_PATH)

# --- Run cleaning if processed file doesn't exist ---
if not os.path.exists(PROCESSED_DATA_PATH):
    clean_data()