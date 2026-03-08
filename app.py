import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="Substation Works Dashboard", page_icon="⚡", layout="wide")

# Custom CSS to match the clean, professional look of your first dashboard
st.markdown("""
    <style>
    .main-header {
        font-size: 32px;
        color: #1A365D; /* Dark Navy Blue */
        font-weight: bold;
        padding-bottom: 10px;
        border-bottom: 2px solid #1A365D;
        margin-bottom: 20px;
    }
    .kpi-card-total {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .kpi-card-verified {
        background-color: #f0fff4; /* Soft Green */
        border: 1px solid #9ae6b4;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .kpi-card-issues {
        background-color: #fff5f5; /* Soft Red/Pink */
        border: 1px solid #feb2b2;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .kpi-value {
        font-size: 36px;
        font-weight: bold;
        color: #2d3748;
    }
    .kpi-label {
        font-size: 16px;
        color: #4a5568;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING
# ==========================================

# @st.cache_data(ttl=600)
# def load_data():
#     # Your standard Google Sheets edit link
#     original_url = "https://docs.google.com/spreadsheets/d/1CvhgmGpnmTmisc1LRPqaXu7slMHExSFfQG7Uz6xXI3w/edit?gid=0#gid=0"
    
#     # 1. Convert the 'edit' link into a direct 'export CSV' link
#     csv_url = original_url.replace("/edit?gid=0#gid=0", "/export?format=csv&gid=0")
    
#     try:
#         # 2. Use header=2. This makes Row 3 the official column names and ignores Rows 1 & 2.
#         df = pd.read_csv(csv_url, header=2)
        
#         # 3. Drop the first row of data (which is Row 4, the "YES/NO" row). 
#         # iloc[1:] means "keep everything from index 1 onwards".
#         df = df.iloc[1:].reset_index(drop=True)
        
#         return df
        
#     except Exception as e:
#         st.error(f"Error loading data: {e}")
#         st.write("Please verify the link is accessible (Anyone with the link can view).")
#         return pd.DataFrame() 

# df = load_data()

# if df.empty or 'Zone' not in df.columns:
#     st.warning("⚠️ Data could not be loaded or is missing the 'Zone' column. Please check your CSV link and ensure the sheet format hasn't changed.")
#     st.stop()



# ==========================================
# 2. DATA LOADING
# ==========================================

@st.cache_data(ttl=5)
def load_data():
    original_url = "https://docs.google.com/spreadsheets/d/1CvhgmGpnmTmisc1LRPqaXu7slMHExSFfQG7Uz6xXI3w/edit?gid=0#gid=0"
    csv_url = original_url.replace("/edit?gid=0#gid=0", "/export?format=csv&gid=0")
    
    try:
        df = pd.read_csv(csv_url, header=2)
        df = df.iloc[1:].reset_index(drop=True)
        
        # --- NEW FIX FOR S. NO. DECIMALS ---
        # Forces the column to integers, drops decimals, and cleans up any blank rows
        df['S. No.'] = pd.to_numeric(df['S. No.'], errors='coerce').astype('Int64').astype(str).replace('<NA>', '')
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.write("Please verify the link is accessible (Anyone with the link can view).")
        return pd.DataFrame()

# ---> THESE ARE THE LINES I MISSED <---
df = load_data()

if df.empty or 'Zone' not in df.columns:
    st.warning("⚠️ Data could not be loaded or is missing the 'Zone' column. Please check your CSV link and ensure the sheet format hasn't changed.")
    st.stop()

# ==========================================
# 3. HEADER & GLOBAL FILTERS
# ==========================================
st.markdown('<div class="main-header">PSPCL Substation Works Progress Dashboard</div>', unsafe_allow_html=True)

# Top Filter Row
col1, col2, col3 = st.columns(3)
with col1:
    selected_zone = st.selectbox("Select Zone", ["All Zones"] + list(df['Zone'].unique()))
with col2:
    # Filter Circles based on selected Zone
    if selected_zone == "All Zones":
        circle_options = ["All Circles"] + list(df['Circle'].unique())
    else:
        circle_options = ["All Circles"] + list(df[df['Zone'] == selected_zone]['Circle'].unique())
    selected_circle = st.selectbox("Select Circle", circle_options)
with col3:
    selected_rdss = st.selectbox("RDSS Category", ["All Categories"] + list(df['RDSS / Non-RDSS'].unique()))

# Apply Filters
filtered_df = df.copy()
if selected_zone != "All Zones":
    filtered_df = filtered_df[filtered_df['Zone'] == selected_zone]
if selected_circle != "All Circles":
    filtered_df = filtered_df[filtered_df['Circle'] == selected_circle]
if selected_rdss != "All Categories":
    filtered_df = filtered_df[filtered_df['RDSS / Non-RDSS'] == selected_rdss]

# ==========================================
# 4. MACRO VIEW: KPI CARDS
# ==========================================
st.write("### Overall Status")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

total_projects = len(filtered_df)

# LOGIC FIX: Check if it starts with "Yes" (handles "Yes", "Yes (Lease)", etc.)
is_land_available = filtered_df['Land Acquired?'].astype(str).str.strip().str.upper().str.startswith('YES')
land_available_count = len(filtered_df[is_land_available])

# Pending lands are the ones that are NOT "Yes" (and aren't completely blank rows)
pending_land_df = filtered_df[~is_land_available & (filtered_df['Land Acquired?'].astype(str).str.strip() != "")]
land_issues = len(pending_land_df)

# Fixed logic to ensure we count "Yes" regardless of spacing or capitalization
civil_in_progress = len(filtered_df[(filtered_df['Civil Tender Awarded'].astype(str).str.strip().str.upper() == 'YES') & 
                                    (filtered_df['Final Handover'].astype(str).str.strip().str.upper() != 'YES')])
completed = len(filtered_df[filtered_df['Final Handover'].astype(str).str.strip().str.upper() == 'YES'])

with kpi1:
    st.markdown(f"""
        <div class="kpi-card-total">
            <div class="kpi-label">Total Substations</div>
            <div class="kpi-value">{total_projects}</div>
        </div>
    """, unsafe_allow_html=True)
with kpi2:
    st.markdown(f"""
        <div class="kpi-card-verified">
            <div class="kpi-label">Land Available</div>
            <div class="kpi-value" style="color: #276749;">{land_available_count}</div>
        </div>
    """, unsafe_allow_html=True)
with kpi3:
    st.markdown(f"""
        <div class="kpi-card-issues">
            <div class="kpi-label">Pending Land Approvals</div>
            <div class="kpi-value" style="color: #c53030;">{land_issues}</div>
        </div>
    """, unsafe_allow_html=True)
with kpi4:
    st.markdown(f"""
        <div class="kpi-card-total" style="background-color: #fffaf0; border-color: #fbd38d;">
            <div class="kpi-label">Active Civil Works</div>
            <div class="kpi-value">{civil_in_progress}</div>
        </div>
    """, unsafe_allow_html=True)
with kpi5:
    st.markdown(f"""
        <div class="kpi-card-verified" style="background-color: #ebf8ff; border-color: #90cdf4;">
            <div class="kpi-label">Completed / Handed Over</div>
            <div class="kpi-value">{completed}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)


# ==========================================
# 5. PHASE PROGRESS GAUGES (Logical Color Coding)
# ==========================================
st.write("### State-Wide Phase Completion")
gauge1, gauge2, gauge3 = st.columns(3)

# Helper function to calculate 'Yes' percentage for a set of columns
def calc_phase_progress(df_subset, columns):
    if len(df_subset) == 0: return 0
    # Add a safety check to only use columns that actually exist in the dataframe
    valid_columns = [col for col in columns if col in df_subset.columns]
    if not valid_columns: return 0
    
    total_checks = len(df_subset) * len(valid_columns)
    yes_counts = df_subset[valid_columns].apply(lambda x: x.astype(str).str.strip().str.upper() == 'YES').sum().sum()
    return (yes_counts / total_checks) * 100

# EXACT matches to Row 3 of your Google Sheet
civil_cols = [
    'Land Handover by DS to Civil', 
    'Layout Plan Issued', 
    'Soil bearing capacity Test and Grading level done', 
    'Earth filling done (if required)',
    'Structural Dwgs Issued',
    'Civil Tender Awarded'
]
elec_cols = ['Material Tenders Floated', 'PO / Work Order Issued', 'PTF Dispatch to Site']
int_cols = ['Transformer Energized', 'Final Handover']

civil_prog = calc_phase_progress(filtered_df, civil_cols)
elec_prog = calc_phase_progress(filtered_df, elec_cols)
int_prog = calc_phase_progress(filtered_df, int_cols)

def create_gauge(val, title, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = val,
        # Reduced title font size slightly to fit longer words
        title = {'text': title, 'font': {'size': 16}}, 
        number = {'suffix': "%", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
        }
    ))
    # INCREASED height to 300, and top margin (t) to 50 
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig

with gauge1:
    st.plotly_chart(create_gauge(civil_prog, "Civil Works Phase", "#ECC94B"), use_container_width=True) # Yellow
with gauge2:
    st.plotly_chart(create_gauge(elec_prog, "Electrical/Equipment Phase", "#ED8936"), use_container_width=True) # Orange
with gauge3:
    st.plotly_chart(create_gauge(int_prog, "Integration & Handover Phase", "#48BB78"), use_container_width=True) # Green

st.markdown("<hr/>", unsafe_allow_html=True)
# # ==========================================
# # 6. ZONE-WISE SUMMARY (Cross-tab)
# # ==========================================
# st.write("### Zone-Wise Critical Milestones")
# # Create a summary dataframe
# if not filtered_df.empty:
#     summary_df = filtered_df.groupby('Zone').agg(
#         Total_Projects=('S. No.', 'count'),
#         Civil_Tender_Awarded=('Civil Tender Awarded', lambda x: (x == 'Yes').sum()),
#         Material_Tenders_Floated=('Material Tenders Floated', lambda x: (x == 'Yes').sum()),
#         Completed=('Final Handover', lambda x: (x == 'Yes').sum())
#     ).reset_index()
    
#     st.dataframe(summary_df, use_container_width=True, hide_index=True)
# else:
#     st.info("No data available for the selected filters.")

# st.markdown("<hr/>", unsafe_allow_html=True)

# ==========================================
# 6.5 PENDING LAND APPROVAL DETAILS
# ==========================================
st.write("### Pending Land Approvals")

if not pending_land_df.empty:
    # Filter only the relevant columns to show the explanations cleanly
    land_reasons_df = pending_land_df[['Zone', 'Circle', 'Name of 66 KV Substation', 'Land Acquired?']].copy()
    
    # Rename the column purely for visual clarity on the dashboard
    land_reasons_df.rename(columns={'Land Acquired?': 'Current Status / Reason for Delay'}, inplace=True)
    
    # Display it as a full-width table
    st.dataframe(land_reasons_df, use_container_width=True, hide_index=True)
else:
    st.success("✅ There are no pending land approvals in the selected criteria!")

st.markdown("<hr/>", unsafe_allow_html=True)


# ==========================================
# 7. DETAILED PROJECT LOG (Color-coded Pandas DataFrame)
# ==========================================
st.write("### Detailed Substation Works Log")

# Pandas styling function to color 'Yes' green and 'No' red
def color_status(val):
    if val == 'Yes':
        color = '#276749' # Dark green text
        bg_color = '#C6F6D5' # Light green bg
    elif val == 'No':
        color = '#9B2C2C' # Dark red text
        bg_color = '#FED7D7' # Light red bg
    elif isinstance(val, str) and 'Pending' in val:
        color = '#9C4221' # Dark orange text
        bg_color = '#FEEBC8' # Light orange bg
    else:
        return ''
    return f'color: {color}; background-color: {bg_color}; font-weight: bold;'

# Apply styling to the dataframe
# Apply styling to the dataframe using the exact Row 3 headers
columns_to_style = [
    'Land Acquired?', 
    'Land Handover by DS to Civil', 
    'Layout Plan Issued', 
    'Soil bearing capacity Test and Grading level done', 
    'Earth filling done (if required)',
    'Structural Dwgs Issued',
    'Civil Tender Awarded', 
    'Material Tenders Floated', 
    'PO / Work Order Issued', 
    'PTF Dispatch to Site', 
    'Transformer Energized', 
    'Final Handover'
]

# Only apply styling to columns that exist to prevent further KeyErrors
valid_style_columns = [col for col in columns_to_style if col in filtered_df.columns]

styled_df = filtered_df.style.map(color_status, subset=valid_style_columns)

st.dataframe(styled_df, use_container_width=True, height=400, hide_index=True)

