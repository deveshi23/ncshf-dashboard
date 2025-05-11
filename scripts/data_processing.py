import pandas as pd
import os
from datetime import datetime

RAW_DATA_PATH = 'data/raw/UNO Service Learning Data Sheet De-Identified Version.xlsx'
PROCESSED_DATA_PATH = 'data/processed/processed_data.csv'

def clean_data():
    df = pd.read_excel(RAW_DATA_PATH, engine='openpyxl')

    # --- Standardizing column names ---
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')

    # --- Renaming for clarity ---
    df.rename(columns={
        'grant_req_date': 'request_date',
        'application_signed?': 'application_signed',
        'request_status': 'status',
        'total_household_gross_monthly_income': 'monthly_income',
        'type_of_assistance_class': 'assistance_type',
        'amount': 'amount_granted',
        'dob': 'date_of_birth'
    }, inplace=True)

    # --- Droping completely empty rows ---
    df.dropna(how='all', inplace=True)

    # --- Filling in missing data in key flags ---
    df['application_signed'] = df['application_signed'].fillna('Missing')
    df['status'] = df['status'].fillna('Unknown')

    # --- Converting dates ---
    df['request_date'] = pd.to_datetime(df['request_date'], errors='coerce')
    df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce')

    # --- Calculating patient age ---
    today = pd.to_datetime('today')
    df['age'] = df['date_of_birth'].apply(lambda dob: today.year - dob.year if pd.notnull(dob) else None)

    # --- Demographic cleaning ---
    df['gender'] = df['gender'].str.strip().str.capitalize()
    df['insurance_type'] = df['insurance_type'].str.strip().str.title()

    # --- Calculating unused grant flag ---
    df['amount_granted'] = pd.to_numeric(df['amount_granted'], errors='coerce')
    df['remaining_balance'] = pd.to_numeric(df['remaining_balance'], errors='coerce')
    df['amount_used'] = df['amount_granted'] - df['remaining_balance']
    df['full_grant_used'] = df['remaining_balance'] <= 0

    # --- Income brackets for dashboard filters ---
    df['income_bracket'] = pd.cut(df['monthly_income'], bins=[0, 2000, 4000, 6000, 10000, 100000],
                                  labels=['<2k', '2–4k', '4–6k', '6–10k', '10k+'])

    # --- Adding review-ready flag ---
    df['ready_for_review'] = (df['status'].str.lower() == 'approved')

    # --- Cleaning application_signed flag for filter use ---
    df['signed_by_committee'] = df['application_signed'].str.lower().isin(['yes', 'signed'])

    # --- Saving processed data ---
    df.to_csv(PROCESSED_DATA_PATH, index=False)
    print("Data has been cleaned and saved to:", PROCESSED_DATA_PATH)

if __name__ == "__main__":
    clean_data()
