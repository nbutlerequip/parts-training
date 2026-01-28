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

# =============================================================================
# STYLES
# =============================================================================

st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    header {{visibility: hidden;}}
    
    .main .block-container {{
        padding-top: 0;
        padding-bottom: 2rem;
        max-width: 900px;
    }}
    
    .header-bar {{
        background: {SE_MAROON};
        color: white;
        padding: 16px 24px;
        margin: -1rem -1rem 1.5rem -1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 15px;
    }}
    
    .header-title {{
        font-weight: 600;
        font-size: 18px;
    }}
    
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
        font-size: 13px;
        margin-bottom: 40px;
    }}
    
    .stButton > button {{
        background: {SE_MAROON};
        color: white;
        border: none;
        font-weight: 500;
    }}
    
    .stButton > button:hover {{
        background: #8a1a2d;
        color: white;
    }}
    
    .training-card {{
        border: 1px solid #ddd;
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
        font-size: 14px;
    }}
    
    .progress-text {{
        font-size: 13px;
        color: #888;
    }}
    
    .scenario-box {{
        background: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }}
    
    .situation-label {{
        font-size: 12px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }}
    
    .situation-text {{
        font-size: 14px;
        color: #555;
        margin-bottom: 16px;
    }}
    
    .customer-says {{
        font-size: 16px;
        font-style: italic;
        color: #333;
        padding: 12px 16px;
        background: white;
        border-left: 4px solid {SE_MAROON};
        margin-bottom: 8px;
    }}
    
    .choice-btn {{
        text-align: left;
        padding: 12px 16px;
        margin-bottom: 8px;
        border: 1px solid #ddd;
        border-radius: 6px;
        background: white;
        cursor: pointer;
        transition: all 0.2s;
    }}
    
    .choice-btn:hover {{
        border-color: {SE_MAROON};
        background: #fdf6f7;
    }}
    
    .feedback-box {{
        padding: 16px;
        border-radius: 8px;
        margin-top: 16px;
    }}
    
    .feedback-best {{
        background: #d4edda;
        border: 1px solid #c3e6cb;
    }}
    
    .feedback-better {{
        background: #cce5ff;
        border: 1px solid #b8daff;
    }}
    
    .feedback-good {{
        background: #fff3cd;
        border: 1px solid #ffeeba;
    }}
    
    .feedback-bad {{
        background: #f8d7da;
        border: 1px solid #f5c6cb;
    }}
    
    .key-insight {{
        background: #e8f4fd;
        border: 1px solid #bee5eb;
        padding: 12px 16px;
        border-radius: 6px;
        margin-top: 16px;
        font-size: 14px;
    }}
    
    .key-insight strong {{
        color: #0c5460;
    }}
    
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
    
    .footer {{
        text-align: center;
        color: #999;
        font-size: 11px;
        padding: 20px 0;
        border-top: 1px solid #eee;
        margin-top: 40px;
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
    
    # Summary stats
    st.markdown("### Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Completions", len(df))
    
    with col2:
        unique_people = df['Name'].nunique()
        st.metric("Unique Associates", unique_people)
    
    with col3:
        avg_score = df['Percent'].mean()
        st.metric("Average Score", f"{avg_score:.1f}%")
    
    with col4:
        avg_optimal = df['Optimal'].mean()
        st.metric("Avg Optimal Answers", f"{avg_optimal:.1f}")
    
    st.markdown("---")
    
    # By Branch
    st.markdown("### Results by Branch")
    branch_stats = df.groupby('Branch').agg({
        'Name': 'count',
        'Percent': 'mean',
        'Optimal': 'mean'
    }).round(1)
    branch_stats.columns = ['Completions', 'Avg Score %', 'Avg Optimal']
    branch_stats = branch_stats.sort_values('Completions', ascending=False)
    st.dataframe(branch_stats, use_container_width=True)
    
    st.markdown("---")
    
    # By Training
    st.markdown("### Results by Training")
    training_stats = df.groupby('Training').agg({
        'Name': 'count',
        'Percent': 'mean',
        'Optimal': 'mean'
    }).round(1)
    training_stats.columns = ['Completions', 'Avg Score %', 'Avg Optimal']
    st.dataframe(training_stats, use_container_width=True)
    
    st.markdown("---")
    
    # Individual Results
    st.markdown("### Individual Results")
    
    display_df = df[['Timestamp', 'Name', 'Branch', 'Training', 'Score', 'MaxScore', 'Percent', 'Optimal']].copy()
    display_df = display_df.sort_values('Timestamp', ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
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
        st.markdown("**What's your response?**")
        
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
        # Show feedback
        selected = st.session_state.selected_choice
        selected_score = scenario.get(f'choice_{selected}_score', '')
        selected_text = scenario.get(f'choice_{selected}_text', '')
        selected_explanation = scenario.get(f'choice_{selected}_explanation', '')
        
        # Determine feedback class
        feedback_class = {
            'best': 'feedback-best',
            'better': 'feedback-better',
            'good': 'feedback-good',
            'bad': 'feedback-bad'
        }.get(selected_score, 'feedback-good')
        
        score_label = {
            'best': 'Best Response',
            'better': 'Good Approach',
            'good': 'Okay, But...',
            'bad': 'Missed Opportunity'
        }.get(selected_score, selected_score)
        
        st.markdown(f"""
        <div class="feedback-box {feedback_class}">
            <strong>Your choice: {selected.upper()}</strong> - {score_label}<br><br>
            "{selected_text}"<br><br>
            {selected_explanation}
        </div>
        """, unsafe_allow_html=True)
        
        # Show the best answer if they didn't pick it
        if selected_score != 'best':
            for choice in choices:
                if scenario.get(f'choice_{choice}_score', '') == 'best':
                    best_text = scenario.get(f'choice_{choice}_text', '')
                    best_explanation = scenario.get(f'choice_{choice}_explanation', '')
                    st.markdown(f"""
                    <div class="feedback-box feedback-best">
                        <strong>Best response was {choice.upper()}:</strong><br><br>
                        "{best_text}"<br><br>
                        {best_explanation}
                    </div>
                    """, unsafe_allow_html=True)
                    break
        
        # Key insight
        st.markdown(f"""
        <div class="key-insight">
            <strong>Key Insight:</strong> {scenario['key_insight']}
        </div>
        """, unsafe_allow_html=True)
        
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
