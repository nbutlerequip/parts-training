"""
Southeastern Equipment - Parts Sales Training
February 2026

Two core competencies:
1. Sales Skills - Ask questions before suggesting
2. Customer Care - Find solutions, take ownership
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

# =============================================================================
# CONFIG
# =============================================================================

st.set_page_config(
    page_title="SE Parts Training",
    page_icon="SE",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SE_MAROON = "#A41E35"
DASHBOARD_PASSWORD = "SEparts2026"

BRANCHES = {
    1: "Cambridge",
    2: "North Canton",
    3: "Gallipolis",
    4: "Dublin",
    5: "Monroe",
    6: "Burlington",
    7: "Perrysburg",
    9: "Brunswick",
    11: "Mentor",
    12: "Fort Wayne",
    13: "Indianapolis",
    14: "Mansfield",
    15: "Heath",
    16: "Marietta",
    17: "Evansville",
    19: "Holt",
    20: "Novi"
}

# Regional groupings (ROM assignments)
REGIONS = {
    "SE (Brian)": ["Cambridge", "Gallipolis", "Dublin", "Heath", "Marietta"],
    "NE (Matt)": ["North Canton", "Perrysburg", "Brunswick", "Mentor", "Mansfield"],
    "West (Carrie)": ["Monroe", "Burlington", "Fort Wayne", "Indianapolis", "Evansville", "Holt", "Novi"]
}

# Reverse lookup - branch to region
BRANCH_TO_REGION = {}
for region, branches in REGIONS.items():
    for branch in branches:
        BRANCH_TO_REGION[branch] = region

# Competencies by training
COMPETENCIES = {
    1: {  # Sales Skills
        "name": "Sales Skills",
        "competencies": [
            {"name": "Discovery Questions", "scenarios": [1, 2, 3, 4, 5], "description": "Asking about hours, job scope, and equipment before suggesting"},
            {"name": "Building the Order", "scenarios": [6, 7, 8, 9], "description": "Connecting related parts and identifying what's missing"},
            {"name": "Handling Price Objections", "scenarios": [10, 11, 12], "description": "Redirecting to value instead of discounting"},
            {"name": "Closing & Follow-up", "scenarios": [13, 14, 15], "description": "Capturing future business and building relationships"}
        ]
    },
    2: {  # Customer Care
        "name": "Customer Care",
        "competencies": [
            {"name": "Finding Solutions", "scenarios": [1, 2, 3, 4], "description": "Checking other branches, not giving up"},
            {"name": "Taking Ownership", "scenarios": [5, 6, 7, 8], "description": "Owning problems even when not your fault"},
            {"name": "Product Knowledge", "scenarios": [9, 10], "description": "Verifying information, not guessing"},
            {"name": "Building Relationships", "scenarios": [11, 12, 13, 14, 15], "description": "Going the extra mile, personal connection"}
        ]
    }
}

# Scoring levels
SCORE_LEVELS = [
    {"min": 90, "level": "Expert", "color": "#10b981"},
    {"min": 75, "level": "Proficient", "color": "#3b82f6"},
    {"min": 60, "level": "Competent", "color": "#eab308"},
    {"min": 0, "level": "Developing", "color": "#ef4444"}
]

def get_level(score):
    """Get level name and color based on score"""
    for level in SCORE_LEVELS:
        if score >= level["min"]:
            return level["level"], level["color"]
    return "Developing", "#ef4444"

# =============================================================================
# STYLES - Option A: Card Style with Better Colors
# =============================================================================

st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    header {{visibility: hidden;}}
    
    /* Base font size increase */
    html, body, .stApp {{
        font-size: 16px;
    }}
    
    .main .block-container {{
        padding-top: 0;
        padding-bottom: 2rem;
        max-width: 900px;
    }}
    
    /* Header Bar */
    .header-bar {{
        background: {SE_MAROON};
        color: white;
        padding: 14px 24px;
        margin: -1rem -1rem 1.5rem -1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 15px;
    }}
    
    .header-title {{
        font-weight: 600;
        font-size: 17px;
    }}
    
    /* Login/Home Screen */
    .login-container {{
        text-align: center;
        padding: 60px 20px;
    }}
    
    .login-title {{
        color: {SE_MAROON};
        font-size: 36px;
        font-weight: 600;
        margin-bottom: 8px;
    }}
    
    .login-subtitle {{
        color: #666;
        font-size: 18px;
        margin-bottom: 8px;
    }}
    
    .login-desc {{
        color: #888;
        font-size: 14px;
        margin-bottom: 40px;
    }}
    
    /* Buttons - Default styling for action buttons */
    .stButton > button {{
        background: white;
        color: #374151;
        border: 2px solid #e5e7eb;
        font-weight: 500;
        font-size: 15px;
        padding: 12px 20px;
        text-align: left;
        line-height: 1.5;
    }}
    
    .stButton > button:hover {{
        background: #f8f9fa;
        border-color: {SE_MAROON};
        color: #374151;
    }}
    
    /* Primary buttons (Start, Next, etc.) */
    .stButton > button[kind="primary"] {{
        background: {SE_MAROON};
        color: white;
        border: none;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background: #8a1a2d;
        color: white;
    }}
    
    /* Small action buttons */
    div[data-testid="stHorizontalBlock"] .stButton > button {{
        background: {SE_MAROON};
        color: white;
        border: none;
        text-align: center;
    }}
    
    /* Training Selection Cards */
    .training-card {{
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
        background: white;
    }}
    
    .training-card h3 {{
        margin: 0 0 8px 0;
        color: #333;
        font-size: 18px;
    }}
    
    .training-card p {{
        margin: 0 0 12px 0;
        color: #666;
        font-size: 15px;
    }}
    
    .progress-text {{
        font-size: 14px;
        color: #888;
    }}
    
    /* Scenario Card */
    .scenario-box {{
        background: #f8f9fa;
        border-radius: 8px;
        padding: 20px 24px;
        margin-bottom: 24px;
    }}
    
    .situation-label {{
        font-size: 11px;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }}
    
    .situation-text {{
        font-size: 15px;
        color: #374151;
        line-height: 1.6;
        margin-bottom: 16px;
    }}
    
    .customer-says {{
        font-size: 17px;
        font-style: italic;
        color: #111;
        padding: 14px 18px;
        background: white;
        border-left: 4px solid {SE_MAROON};
        border-radius: 0 8px 8px 0;
    }}
    
    /* Choice Buttons */
    .choices-label {{
        font-size: 15px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 12px;
    }}
    
    .choice-btn {{
        display: block;
        width: 100%;
        text-align: left;
        padding: 14px 18px;
        margin-bottom: 10px;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        background: white;
        font-size: 15px;
        color: #374151;
        cursor: pointer;
        transition: all 0.15s;
        line-height: 1.5;
    }}
    
    .choice-btn:hover {{
        border-color: {SE_MAROON};
        background: #fef2f2;
    }}
    
    .choice-letter {{
        font-weight: 600;
        color: {SE_MAROON};
        margin-right: 8px;
    }}
    
    /* Feedback Cards - Color Coded */
    .feedback-box {{
        padding: 16px 20px;
        border-radius: 8px;
        margin-bottom: 12px;
        border-width: 2px;
        border-style: solid;
    }}
    
    .feedback-best {{
        background: #ecfdf5;
        border-color: #10b981;
    }}
    
    .feedback-better {{
        background: #eff6ff;
        border-color: #3b82f6;
    }}
    
    .feedback-good {{
        background: #fefce8;
        border-color: #eab308;
    }}
    
    .feedback-bad {{
        background: #fef2f2;
        border-color: #ef4444;
    }}
    
    .feedback-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }}
    
    .feedback-letter {{
        font-weight: 700;
        font-size: 15px;
        color: #374151;
    }}
    
    .feedback-badge {{
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        text-transform: uppercase;
    }}
    
    .badge-best {{ background: #10b981; color: white; }}
    .badge-better {{ background: #3b82f6; color: white; }}
    .badge-good {{ background: #eab308; color: white; }}
    .badge-bad {{ background: #ef4444; color: white; }}
    .badge-yours {{ background: #333; color: white; }}
    
    .feedback-quote {{
        font-style: italic;
        color: #4b5563;
        margin-bottom: 10px;
        font-size: 14px;
        line-height: 1.5;
    }}
    
    .feedback-explanation {{
        font-size: 14px;
        color: #374151;
        line-height: 1.6;
    }}
    
    /* Key Insight */
    .key-insight {{
        background: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 20px;
    }}
    
    .key-insight-label {{
        font-weight: 600;
        color: #0369a1;
        font-size: 13px;
        margin-bottom: 4px;
    }}
    
    .key-insight-text {{
        font-size: 14px;
        color: #1e40af;
        line-height: 1.5;
    }}
    
    /* Results Screen */
    .score-display {{
        text-align: center;
        padding: 40px;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 20px 0;
    }}
    
    .score-number {{
        font-size: 48px;
        font-weight: 600;
        color: {SE_MAROON};
    }}
    
    .score-label {{
        font-size: 16px;
        color: #666;
    }}
    
    /* Footer */
    .footer {{
        text-align: center;
        color: #999;
        font-size: 12px;
        padding: 20px 0;
        border-top: 1px solid #eee;
        margin-top: 40px;
    }}
    
    /* Dashboard Tables */
    .dataframe {{
        font-size: 14px;
    }}
    
    /* Bullet Charts */
    .bullet-chart {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
        padding: 8px 0;
    }}
    
    .bullet-label {{
        width: 140px;
        font-size: 14px;
        font-weight: 500;
        color: #374151;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    .bullet-bar-container {{
        flex: 1;
        background: #e5e7eb;
        border-radius: 4px;
        height: 24px;
        position: relative;
        overflow: hidden;
    }}
    
    .bullet-bar {{
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }}
    
    .bullet-score {{
        width: 50px;
        text-align: right;
        font-size: 14px;
        font-weight: 600;
        color: #374151;
    }}
    
    .bullet-level {{
        width: 90px;
        text-align: center;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 4px;
        text-transform: uppercase;
    }}
    
    /* Region Section */
    .region-section {{
        background: #f8f9fa;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 20px;
    }}
    
    .region-title {{
        font-size: 16px;
        font-weight: 600;
        color: {SE_MAROON};
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid {SE_MAROON};
    }}
    
    /* Competency Grid */
    .competency-card {{
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }}
    
    .competency-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }}
    
    .competency-name {{
        font-weight: 600;
        font-size: 15px;
        color: #374151;
    }}
    
    .competency-score {{
        font-weight: 600;
        font-size: 14px;
        padding: 4px 10px;
        border-radius: 4px;
    }}
    
    .competency-desc {{
        font-size: 13px;
        color: #6b7280;
    }}
    
    /* Dashboard Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        padding: 10px 20px;
        font-size: 14px;
    }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA FUNCTIONS
# =============================================================================

@st.cache_data
def load_training_data():
    """Load training scenarios from CSV"""
    try:
        df = pd.read_csv('training_data.csv')
        return df
    except:
        return None

def get_trainings(df):
    """Get unique trainings from data"""
    trainings = df.groupby(['month', 'training_id', 'training_name', 'training_description']).size().reset_index()
    return trainings[['month', 'training_id', 'training_name', 'training_description']].drop_duplicates()

def get_scenarios(df, month, training_id):
    """Get scenarios for a specific training"""
    filtered = df[(df['month'] == month) & (df['training_id'] == training_id)]
    return filtered.to_dict('records')

def get_google_sheets_client():
    """Initialize Google Sheets client"""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        return gspread.authorize(creds)
    except Exception as e:
        return None

def get_or_create_worksheet(client, sheet_id):
    """Get Results worksheet, create if it doesn't exist"""
    try:
        spreadsheet = client.open_by_key(sheet_id)
        try:
            worksheet = spreadsheet.worksheet("Results")
        except WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title="Results", rows=1000, cols=10)
        
        # Check if headers exist
        try:
            first_row = worksheet.row_values(1)
        except:
            first_row = []
        
        headers = ["Timestamp", "Name", "Branch", "Training", "Score", "MaxScore", "Percent", "Optimal", "Completed", "Answers"]
        
        if not first_row or first_row[0] != "Timestamp":
            worksheet.insert_row(headers, 1)
        
        return worksheet
    except Exception as e:
        return None

def save_to_google_sheets(name, branch, training_name, score, max_score, optimal_count, answers):
    """Save results to Google Sheets"""
    try:
        sheet_id = st.secrets.get("TRAINING_SHEET_ID")
        if not sheet_id:
            return False
        
        client = get_google_sheets_client()
        if not client:
            return False
        
        worksheet = get_or_create_worksheet(client, sheet_id)
        if not worksheet:
            return False
        
        percent = round((score / max_score) * 100, 1) if max_score > 0 else 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        row = [
            timestamp,
            name,
            branch,
            training_name,
            score,
            max_score,
            percent,
            optimal_count,
            len(answers),
            str(answers)
        ]
        
        worksheet.append_row(row)
        return True
    except Exception as e:
        return False

def load_dashboard_data():
    """Load results from Google Sheets for dashboard"""
    try:
        sheet_id = st.secrets.get("TRAINING_SHEET_ID")
        if not sheet_id:
            return None
        
        client = get_google_sheets_client()
        if not client:
            return None
        
        worksheet = get_or_create_worksheet(client, sheet_id)
        if not worksheet:
            return None
        
        data = worksheet.get_all_records()
        if not data:
            return None
        
        return pd.DataFrame(data)
    except:
        return None

# =============================================================================
# SESSION STATE
# =============================================================================

if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'user_name' not in st.session_state:
    st.session_state.user_name = ''
if 'branch' not in st.session_state:
    st.session_state.branch = ''
if 'current_training' not in st.session_state:
    st.session_state.current_training = None
if 'current_scenario' not in st.session_state:
    st.session_state.current_scenario = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'show_feedback' not in st.session_state:
    st.session_state.show_feedback = False
if 'selected_choice' not in st.session_state:
    st.session_state.selected_choice = None
if 'dashboard_auth' not in st.session_state:
    st.session_state.dashboard_auth = False

# =============================================================================
# HOME PAGE
# =============================================================================

def show_home():
    st.markdown("""
    <div class="login-container">
        <div class="login-title">Parts Sales Training</div>
        <div class="login-subtitle">February 2026</div>
        <div class="login-desc">Build your skills in sales and customer care</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        name = st.text_input("Your Name", value=st.session_state.user_name)
        
        options = ["Select your branch..."]
        for num, bname in sorted(BRANCHES.items()):
            options.append(f"{num} - {bname}")
        
        current_idx = 0
        if st.session_state.branch:
            for i, opt in enumerate(options):
                if st.session_state.branch in opt:
                    current_idx = i
                    break
        
        selected = st.selectbox("Branch", options, index=current_idx, label_visibility="visible")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Start Training", use_container_width=True, type="primary"):
                if name.strip() and selected != "Select your branch...":
                    st.session_state.user_name = name.strip()
                    st.session_state.branch = selected
                    st.session_state.page = 'select_training'
                    st.rerun()
                else:
                    st.warning("Please enter your name and select a branch")
        
        with col_b:
            if st.button("Dashboard", use_container_width=True):
                st.session_state.page = 'dashboard_login'
                st.rerun()
    
    st.markdown("""
    <div class="footer">
        Southeastern Equipment - Parts Department
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# DASHBOARD LOGIN
# =============================================================================

def show_dashboard_login():
    st.markdown("""
    <div class="login-container">
        <div class="login-title">Dashboard</div>
        <div class="login-subtitle">Manager Access</div>
        <div class="login-desc">View training results and analytics</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        password = st.text_input("Password", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Back", use_container_width=True):
                st.session_state.page = 'home'
                st.rerun()
        
        with col_b:
            if st.button("Login", use_container_width=True, type="primary"):
                if password == DASHBOARD_PASSWORD:
                    st.session_state.dashboard_auth = True
                    st.session_state.page = 'dashboard'
                    st.rerun()
                else:
                    st.error("Incorrect password")

# =============================================================================
# DASHBOARD
# =============================================================================

def show_dashboard():
    if not st.session_state.dashboard_auth:
        st.session_state.page = 'dashboard_login'
        st.rerun()
        return
    
    st.markdown(f"""
    <div class="header-bar">
        <span class="header-title">Training Dashboard</span>
        <span>Manager View</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Back to Home"):
            st.session_state.page = 'home'
            st.session_state.dashboard_auth = False
            st.rerun()
    
    df = load_dashboard_data()
    
    if df is None or len(df) == 0:
        st.info("No training results yet. Results will appear here as associates complete trainings.")
        return
    
    # Add region to dataframe
    def get_region(branch):
        # Extract branch name from "1 - Cambridge" format
        if " - " in str(branch):
            branch_name = str(branch).split(" - ")[1]
        else:
            branch_name = str(branch)
        return BRANCH_TO_REGION.get(branch_name, "Other")
    
    df['Region'] = df['Branch'].apply(get_region)
    
    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "By Region", "Competencies", "Individual Results"])
    
    # =========================================================================
    # TAB 1: OVERVIEW
    # =========================================================================
    with tab1:
        st.markdown("### Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Completions", len(df))
        
        with col2:
            unique_people = df['Name'].nunique()
            st.metric("Unique Associates", unique_people)
        
        with col3:
            avg_score = df['Percent'].mean()
            level, color = get_level(avg_score)
            st.metric("Average Score", f"{avg_score:.1f}%")
        
        with col4:
            avg_optimal = df['Optimal'].mean()
            st.metric("Avg Best Answers", f"{avg_optimal:.1f} of 15")
        
        st.markdown("---")
        
        # Score distribution by level
        st.markdown("### Score Distribution")
        
        level_counts = {"Expert": 0, "Proficient": 0, "Competent": 0, "Developing": 0}
        for _, row in df.iterrows():
            lvl, _ = get_level(row['Percent'])
            level_counts[lvl] += 1
        
        total = len(df)
        for level_name, count in level_counts.items():
            pct = (count / total * 100) if total > 0 else 0
            level_info = next((l for l in SCORE_LEVELS if l["level"] == level_name), SCORE_LEVELS[-1])
            color = level_info["color"]
            
            st.markdown(f"""
            <div class="bullet-chart">
                <div class="bullet-label">{level_name}</div>
                <div class="bullet-bar-container">
                    <div class="bullet-bar" style="width: {pct}%; background: {color};"></div>
                </div>
                <div class="bullet-score">{count}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # By Training
        st.markdown("### Results by Training")
        for training_id, comp_data in COMPETENCIES.items():
            training_name = comp_data["name"]
            training_df = df[df['Training'] == training_name]
            if len(training_df) > 0:
                avg = training_df['Percent'].mean()
                count = len(training_df)
                level, color = get_level(avg)
                
                st.markdown(f"""
                <div class="bullet-chart">
                    <div class="bullet-label">{training_name}</div>
                    <div class="bullet-bar-container">
                        <div class="bullet-bar" style="width: {avg}%; background: {color};"></div>
                    </div>
                    <div class="bullet-score">{avg:.0f}%</div>
                    <div class="bullet-level" style="background: {color}; color: white;">{level}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 2: BY REGION
    # =========================================================================
    with tab2:
        st.markdown("### Performance by Region")
        
        for region in REGIONS.keys():
            region_df = df[df['Region'] == region]
            
            if len(region_df) == 0:
                continue
            
            avg_score = region_df['Percent'].mean()
            level, color = get_level(avg_score)
            
            st.markdown(f"""
            <div class="region-section">
                <div class="region-title">{region}</div>
            """, unsafe_allow_html=True)
            
            # Get branches in this region with data
            branches_in_region = region_df['Branch'].unique()
            
            for branch in sorted(branches_in_region):
                branch_df = region_df[region_df['Branch'] == branch]
                branch_avg = branch_df['Percent'].mean()
                branch_count = len(branch_df)
                b_level, b_color = get_level(branch_avg)
                
                # Extract just branch name for display
                if " - " in str(branch):
                    display_name = str(branch).split(" - ")[1]
                else:
                    display_name = str(branch)
                
                st.markdown(f"""
                <div class="bullet-chart">
                    <div class="bullet-label">{display_name} ({branch_count})</div>
                    <div class="bullet-bar-container">
                        <div class="bullet-bar" style="width: {branch_avg}%; background: {b_color};"></div>
                    </div>
                    <div class="bullet-score">{branch_avg:.0f}%</div>
                    <div class="bullet-level" style="background: {b_color}; color: white;">{b_level}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 3: COMPETENCIES
    # =========================================================================
    with tab3:
        st.markdown("### Core Competencies Analysis")
        st.markdown("Understanding where associates need additional support.")
        st.markdown("")
        
        # Note about competency tracking
        st.info("Competency scores are calculated when detailed answer data is available. Below are the competency areas covered in each training.")
        
        for training_id, comp_data in COMPETENCIES.items():
            training_name = comp_data["name"]
            
            st.markdown(f"#### {training_name}")
            
            training_df = df[df['Training'] == training_name]
            if len(training_df) > 0:
                overall_avg = training_df['Percent'].mean()
                overall_level, overall_color = get_level(overall_avg)
                st.markdown(f"**Overall: {overall_avg:.0f}%** ({overall_level})")
            
            for comp in comp_data["competencies"]:
                scenario_list = ", ".join([str(s) for s in comp["scenarios"]])
                
                st.markdown(f"""
                <div class="competency-card">
                    <div class="competency-header">
                        <div class="competency-name">{comp["name"]}</div>
                        <div style="font-size: 12px; color: #6b7280;">Scenarios {scenario_list}</div>
                    </div>
                    <div class="competency-desc">{comp["description"]}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("")
        
        st.markdown("---")
        st.markdown("### Recommended Next Steps")
        
        # Calculate which training has lower scores
        sales_df = df[df['Training'] == 'Sales Skills']
        care_df = df[df['Training'] == 'Customer Care']
        
        sales_avg = sales_df['Percent'].mean() if len(sales_df) > 0 else 0
        care_avg = care_df['Percent'].mean() if len(care_df) > 0 else 0
        
        if sales_avg == 0 and care_avg == 0:
            st.write("Complete more trainings to see recommendations.")
        elif sales_avg < care_avg and sales_avg > 0:
            st.markdown(f"""
            **Focus Area: Sales Skills** ({sales_avg:.0f}% vs {care_avg:.0f}% Customer Care)
            
            Recommended actions:
            - Role-play discovery questions during team meetings
            - Review kit pricing and contents for quick recall
            - Practice "What are the hours?" question flow
            - Shadow top performers on upsell conversations
            """)
        elif care_avg < sales_avg and care_avg > 0:
            st.markdown(f"""
            **Focus Area: Customer Care** ({care_avg:.0f}% vs {sales_avg:.0f}% Sales Skills)
            
            Recommended actions:
            - Practice checking other branches before saying "no"
            - Role-play handling frustrated customers
            - Review F7 network inventory lookup
            - Emphasize personal ownership and follow-through
            """)
        else:
            st.markdown(f"""
            **Both areas performing similarly** (Sales: {sales_avg:.0f}%, Care: {care_avg:.0f}%)
            
            Continue balanced development in both competency areas.
            """)
    
    # =========================================================================
    # TAB 4: INDIVIDUAL RESULTS
    # =========================================================================
    with tab4:
        st.markdown("### Individual Results")
        
        # Add level to display
        display_df = df[['Timestamp', 'Name', 'Branch', 'Region', 'Training', 'Percent', 'Optimal']].copy()
        display_df['Level'] = display_df['Percent'].apply(lambda x: get_level(x)[0])
        display_df = display_df.sort_values('Timestamp', ascending=False)
        display_df.columns = ['Timestamp', 'Name', 'Branch', 'Region', 'Training', 'Score %', 'Best Answers', 'Level']
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            region_filter = st.selectbox("Filter by Region", ["All"] + list(REGIONS.keys()))
        
        with col2:
            training_filter = st.selectbox("Filter by Training", ["All", "Sales Skills", "Customer Care"])
        
        with col3:
            level_filter = st.selectbox("Filter by Level", ["All", "Expert", "Proficient", "Competent", "Developing"])
        
        # Apply filters
        filtered_df = display_df.copy()
        if region_filter != "All":
            filtered_df = filtered_df[filtered_df['Region'] == region_filter]
        if training_filter != "All":
            filtered_df = filtered_df[filtered_df['Training'] == training_filter]
        if level_filter != "All":
            filtered_df = filtered_df[filtered_df['Level'] == level_filter]
        
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        st.markdown(f"Showing {len(filtered_df)} of {len(display_df)} results")
        
        # Export
        st.markdown("---")
        csv = df.to_csv(index=False)
        st.download_button(
            "Export All Results",
            csv,
            f"training_results_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

# =============================================================================
# TRAINING SELECTION
# =============================================================================

def show_training_selection():
    st.markdown(f"""
    <div class="header-bar">
        <span class="header-title">Parts Sales Training</span>
        <span>{st.session_state.user_name} - {st.session_state.branch}</span>
    </div>
    """, unsafe_allow_html=True)
    
    df = load_training_data()
    
    if df is None:
        st.error("Training data not found. Please ensure training_data.csv is in the app folder.")
        if st.button("Back"):
            st.session_state.page = 'home'
            st.rerun()
        return
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Back"):
            st.session_state.page = 'home'
            st.rerun()
    
    st.markdown("### Select a Training")
    st.markdown("Each training has 15 scenarios. Pick the response you think works best, then see why each approach does or doesn't work.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    trainings = get_trainings(df)
    
    for _, training in trainings.iterrows():
        scenarios = get_scenarios(df, training['month'], training['training_id'])
        scenario_count = len(scenarios)
        
        # Check completion status
        completed = st.session_state.answers.get(f"{training['month']}_{training['training_id']}", {})
        completed_count = len(completed)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="training-card">
                <h3>Training {training['training_id']}: {training['training_name']}</h3>
                <p>{training['training_description']}</p>
                <div class="progress-text">{completed_count} of {scenario_count} completed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Start", key=f"start_{training['training_id']}", use_container_width=True):
                st.session_state.current_training = {
                    'month': training['month'],
                    'training_id': training['training_id'],
                    'training_name': training['training_name']
                }
                st.session_state.current_scenario = 0
                st.session_state.show_feedback = False
                st.session_state.selected_choice = None
                st.session_state.page = 'training'
                st.rerun()

# =============================================================================
# TRAINING PAGE
# =============================================================================

def show_training():
    df = load_training_data()
    
    if df is None or st.session_state.current_training is None:
        st.session_state.page = 'select_training'
        st.rerun()
        return
    
    training = st.session_state.current_training
    scenarios = get_scenarios(df, training['month'], training['training_id'])
    
    if not scenarios:
        st.error("No scenarios found for this training")
        return
    
    current_idx = st.session_state.current_scenario
    
    # Check if training is complete
    if current_idx >= len(scenarios):
        show_training_complete(training, scenarios)
        return
    
    scenario = scenarios[current_idx]
    
    # Header
    st.markdown(f"""
    <div class="header-bar">
        <span class="header-title">{training['training_name']}</span>
        <span>Scenario {current_idx + 1} of {len(scenarios)}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("Exit Training"):
        st.session_state.page = 'select_training'
        st.session_state.current_training = None
        st.session_state.current_scenario = 0
        st.session_state.show_feedback = False
        st.rerun()
    
    # Scenario
    st.markdown(f"""
    <div class="scenario-box">
        <div class="situation-label">Situation</div>
        <div class="situation-text">{scenario['situation']}</div>
        <div class="customer-says">"{scenario['customer_says']}"</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Choices
    choices = ['a', 'b', 'c', 'd']
    
    if not st.session_state.show_feedback:
        st.markdown('<div class="choices-label">What\'s your response?</div>', unsafe_allow_html=True)
        
        for choice in choices:
            choice_text = scenario.get(f'choice_{choice}_text', '')
            if choice_text:
                if st.button(f"{choice.upper()}: {choice_text}", key=f"choice_{choice}", use_container_width=True):
                    st.session_state.selected_choice = choice
                    st.session_state.show_feedback = True
                    
                    # Save answer
                    training_key = f"{training['month']}_{training['training_id']}"
                    if training_key not in st.session_state.answers:
                        st.session_state.answers[training_key] = {}
                    st.session_state.answers[training_key][current_idx] = choice
                    
                    st.rerun()
    else:
        # Show feedback for ALL answers using native Streamlit components
        selected = st.session_state.selected_choice
        
        score_labels = {
            'best': 'BEST RESPONSE',
            'better': 'GOOD APPROACH', 
            'good': 'OKAY, BUT...',
            'bad': 'MISSED OPPORTUNITY'
        }
        
        st.markdown("**Results**")
        st.markdown("---")
        
        # Show all 4 answers with explanations
        for choice in choices:
            choice_text = scenario.get(f'choice_{choice}_text', '')
            choice_score = scenario.get(f'choice_{choice}_score', '')
            choice_explanation = scenario.get(f'choice_{choice}_explanation', '')
            
            if not choice_text:
                continue
            
            score_label = score_labels.get(choice_score, choice_score.upper())
            yours_marker = " ← YOUR CHOICE" if choice == selected else ""
            
            # Use native Streamlit status components
            if choice_score == 'best':
                with st.container():
                    st.success(f"**{choice.upper()}: {score_label}{yours_marker}**")
                    st.write(f'*"{choice_text}"*')
                    st.write(choice_explanation)
            elif choice_score == 'better':
                with st.container():
                    st.info(f"**{choice.upper()}: {score_label}{yours_marker}**")
                    st.write(f'*"{choice_text}"*')
                    st.write(choice_explanation)
            elif choice_score == 'good':
                with st.container():
                    st.warning(f"**{choice.upper()}: {score_label}{yours_marker}**")
                    st.write(f'*"{choice_text}"*')
                    st.write(choice_explanation)
            else:  # bad
                with st.container():
                    st.error(f"**{choice.upper()}: {score_label}{yours_marker}**")
                    st.write(f'*"{choice_text}"*')
                    st.write(choice_explanation)
            
            st.markdown("")  # Spacing
        
        # Key insight
        st.markdown("---")
        st.info(f"**Key Insight:** {scenario['key_insight']}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Next button
        if current_idx < len(scenarios) - 1:
            if st.button("Next Scenario", type="primary", use_container_width=True):
                st.session_state.current_scenario += 1
                st.session_state.show_feedback = False
                st.session_state.selected_choice = None
                st.rerun()
        else:
            if st.button("See Results", type="primary", use_container_width=True):
                st.session_state.current_scenario += 1
                st.rerun()

# =============================================================================
# TRAINING COMPLETE
# =============================================================================

def show_training_complete(training, scenarios):
    st.markdown(f"""
    <div class="header-bar">
        <span class="header-title">{training['training_name']}</span>
        <span>Complete</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Calculate score
    training_key = f"{training['month']}_{training['training_id']}"
    answers = st.session_state.answers.get(training_key, {})
    
    score = 0
    max_score = 0
    optimal_count = 0
    
    score_values = {'best': 3, 'better': 2, 'good': 1, 'bad': 0}
    
    for idx, scenario in enumerate(scenarios):
        max_score += 3
        if idx in answers:
            choice = answers[idx]
            choice_score = scenario.get(f'choice_{choice}_score', 'bad')
            score += score_values.get(choice_score, 0)
            if choice_score == 'best':
                optimal_count += 1
    
    percent = round((score / max_score) * 100, 1) if max_score > 0 else 0
    
    # Display results
    st.markdown(f"""
    <div class="score-display">
        <div class="score-number">{percent}%</div>
        <div class="score-label">{score} of {max_score} points</div>
        <div class="score-label">{optimal_count} of {len(scenarios)} optimal answers</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Performance message
    if percent >= 80:
        st.success("Excellent work! You're demonstrating strong skills in this area.")
    elif percent >= 60:
        st.info("Good job! Review the scenarios you missed to strengthen your approach.")
    else:
        st.warning("Keep practicing! Consider reviewing this training to improve your skills.")
    
    # Save to Google Sheets
    saved = save_to_google_sheets(
        st.session_state.user_name,
        st.session_state.branch,
        training['training_name'],
        score,
        max_score,
        optimal_count,
        answers
    )
    
    if saved:
        st.success("Results saved!")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Review Answers", use_container_width=True):
            st.session_state.current_scenario = 0
            st.session_state.show_feedback = True
            st.rerun()
    
    with col2:
        if st.button("Back to Trainings", use_container_width=True, type="primary"):
            st.session_state.page = 'select_training'
            st.session_state.current_training = None
            st.session_state.current_scenario = 0
            st.session_state.show_feedback = False
            st.rerun()

# =============================================================================
# MAIN
# =============================================================================

if st.session_state.page == 'home':
    show_home()
elif st.session_state.page == 'dashboard_login':
    show_dashboard_login()
elif st.session_state.page == 'dashboard':
    show_dashboard()
elif st.session_state.page == 'select_training':
    show_training_selection()
elif st.session_state.page == 'training':
    show_training()
else:
    st.session_state.page = 'home'
    st.rerun()
