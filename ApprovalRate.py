import pandas as pd
import pycountry

# Convert country code to country name
def country_name(code):
    try:
        return pycountry.countries.get(alpha_2=code).name
    except:
        return None

# Load data from CSV file
data = pd.read_csv("/content/AllOrders.csv") # Double-check the file path

# Convert 'created_at' column to datetime format
data['created_at'] = pd.to_datetime(data['created_at'], errors='coerce')

# Filter data for specific partner_id or user_id
# partner_id = '01HW'
# data = data[data['partner_id'] == partner_id]

# Define provider variable
provider = None  # Change this to the desired provider ('worldpay', 'safecharge', or None for both)

if provider is not None:
    if provider == 'worldpay':
        data = data[data['provider'] == 'worldpay']
    elif provider == 'safecharge':
        data = data[data['provider'].str.contains('safecharge', case=False)]

# Exclude failed orders with "bad scoring" error
data['valid_failed'] = ~data['error'].str.contains("bad scoring", case=False, na=True)

# Remove duplicates based on user, partner, date, and error
data = data.drop_duplicates(subset=['user_id', 'partner_id', 'created_at', 'error'])

# Create 'date' column from 'created_at' for daily granularity
data['date'] = data['created_at'].dt.date

# Group and count Errors by User, Partner, Date, and Error Type
grouped_errors = data[data['valid_failed']].groupby(['user_id', 'partner_id', 'date', 'error']).size().reset_index(name='error_count')

# Exclude failed orders on the same day as successful orders
success_dates = data[data['status'] == 'success'][['user_id', 'partner_id', 'date']]
failed_filtered = grouped_errors.merge(success_dates, on=['user_id', 'partner_id', 'date'], how='left', indicator=True)
failed_filtered = failed_filtered[(failed_filtered['_merge'] == 'left_only') & (failed_filtered['error_count'] > 0)]

# Count successful and failed orders for each user-partner combination
successful_count = data[data['status'] == 'success'].groupby(['user_id', 'partner_id']).size().reset_index(name='successful_count')
failed_count = failed_filtered.groupby(['user_id', 'partner_id']).size().reset_index(name='failed_count')

# Merge successful and failed counts and calculate totals
combined_counts = successful_count.merge(failed_count, on=['user_id', 'partner_id'], how='outer').fillna(0)
combined_counts['total_transactions'] = combined_counts['successful_count'] + combined_counts['failed_count']

# Merge with country information and convert codes to names
country_data = data[['user_id', 'partner_id', 'country']].drop_duplicates()
country_data['country'] = country_data['country'].apply(country_name)
combined_counts = combined_counts.merge(country_data, on=['user_id', 'partner_id'], how='left')

# Calculate acceptance rate per country
country_summary = combined_counts.groupby('country').agg({
    'successful_count': 'sum',
    'failed_count': 'sum',
    'total_transactions': 'sum'
}).reset_index()
country_summary['acceptance_rate'] = (country_summary['successful_count'] / country_summary['total_transactions']) * 100

# Filter out countries with fewer than 50 transactions unless acceptance rate is 100%
country_summary = country_summary[(country_summary['total_transactions'] >= 50) | (country_summary['acceptance_rate'] == 100)]

# Format the numeric columns and sorting by country
country_summary = country_summary.round(0).astype({'successful_count': int, 'failed_count': int, 'total_transactions': int})
country_summary['acceptance_rate'] = country_summary['acceptance_rate'].astype(int).astype(str) + '%'
country_summary = country_summary.sort_values(by='country')

# Display the breakdown of successful and failed orders, total transactions, and acceptance rate per user by country
print("\nAcceptance rate breakdown by country for '{}':".format(provider if provider else 'worldpay and safecharge'))

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
country_summary.style.hide(axis='index')
