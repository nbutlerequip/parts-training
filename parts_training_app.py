"""
Parts Sales Training Tool - Southeastern Equipment
Streamlit app with Google Sheets integration for tracking results

To update training content, edit training_data.csv - no code changes needed.
"""

import streamlit as st
import pandas as pd
import gspread
from gspread.exceptions import WorksheetNotFound
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Parts Sales Training - SE",
    page_icon="🔧",
    layout="wide"
)

# App directory for data files
APP_DIR = Path(__file__).parent
DATA_FILE = APP_DIR / "training_data.csv"

# SE Branch list
SE_BRANCHES = [
    "",
    "1 - Cambridge",
    "2 - North Canton", 
    "3 - Gallipolis",
    "4 - Dublin",
    "5 - Monroe",
    "6 - Burlington",
    "7 - Perrysburg",
    "9 - Brunswick",
    "11 - Mentor",
    "12 - Fort Wayne",
    "13 - Indianapolis",
    "14 - Mansfield",
    "15 - Heath",
    "16 - Marietta",
    "17 - Evansville",
    "19 - Holt",
    "20 - Novi"
]

# =============================================================================
# LOAD TRAINING DATA FROM CSV
# =============================================================================

@st.cache_data
def load_training_data():
    """Load training scenarios from CSV file"""
    if not DATA_FILE.exists():
        st.error(f"Training data file not found: {DATA_FILE}")
        return None
    
    df = pd.read_csv(DATA_FILE)
    
    # Get unique month
    month = df['month'].iloc[0]
    
    # Build training structure from CSV
    trainings = []
    for training_id in df['training_id'].unique():
        training_df = df[df['training_id'] == training_id]
        
        training = {
            'id': int(training_id),
            'name': training_df['training_name'].iloc[0],
            'description': training_df['training_description'].iloc[0],
            'scenarios': []
        }
        
        for _, row in training_df.iterrows():
            scenario = {
                'id': int(row['scenario_id']),
                'situation': row['situation'],
                'customer_says': row['customer_says'],
                'key_insight': row['key_insight'],
                'choices': [
                    {
                        'letter': 'A',
                        'text': row['choice_a_text'],
                        'score': row['choice_a_score'],
                        'points': 3 if row['choice_a_score'] == 'best' else (2 if row['choice_a_score'] == 'better' else (1 if row['choice_a_score'] == 'good' else 0)),
                        'explanation': row['choice_a_explanation']
                    },
                    {
                        'letter': 'B',
                        'text': row['choice_b_text'],
                        'score': row['choice_b_score'],
                        'points': 3 if row['choice_b_score'] == 'best' else (2 if row['choice_b_score'] == 'better' else (1 if row['choice_b_score'] == 'good' else 0)),
                        'explanation': row['choice_b_explanation']
                    },
                    {
                        'letter': 'C',
                        'text': row['choice_c_text'],
                        'score': row['choice_c_score'],
                        'points': 3 if row['choice_c_score'] == 'best' else (2 if row['choice_c_score'] == 'better' else (1 if row['choice_c_score'] == 'good' else 0)),
                        'explanation': row['choice_c_explanation']
                    },
                    {
                        'letter': 'D',
                        'text': row['choice_d_text'],
                        'score': row['choice_d_score'],
                        'points': 3 if row['choice_d_score'] == 'best' else (2 if row['choice_d_score'] == 'better' else (1 if row['choice_d_score'] == 'good' else 0)),
                        'explanation': row['choice_d_explanation']
                    }
                ]
            }
            training['scenarios'].append(scenario)
        
        trainings.append(training)
    
    return {
        'month': month,
        'trainings': trainings
    }

# Load training data
TRAINING_DATA = load_training_data()

# Custom CSS for SE branding
st.markdown("""
<style>
    .stApp {
        background-color: #fafafa;
    }
    .main-header {
        background-color: #A41E35;
        color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.5rem;
    }
    .scenario-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e5e5e5;
        margin-bottom: 1rem;
    }
    .customer-quote {
        font-size: 1.25rem;
        font-style: italic;
        color: #333;
        border-left: 4px solid #A41E35;
        padding-left: 1rem;
        margin: 1rem 0;
    }
    .insight-box {
        background: #1F4E79;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .optimal-answer {
        background: #e6f9ee;
        border-left: 4px solid #059669;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .other-answer {
        background: #f8f8f8;
        border-left: 4px solid #e5e5e5;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .result-optimal {
        background: #e6f9ee;
        color: #065f46;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .result-close {
        background: #e0f2fe;
        color: #0369a1;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .result-learning {
        background: #fef6e6;
        color: #92400e;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .progress-text {
        font-size: 0.9rem;
        color: #666;
    }
    div[data-testid="stRadio"] > label {
        background: white;
        padding: 0.75rem 1rem;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        cursor: pointer;
    }
    div[data-testid="stRadio"] > label:hover {
        border-color: #A41E35;
        background: #fef6f6;
    }
</style>
""", unsafe_allow_html=True)
# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    if 'user_branch' not in st.session_state:
        st.session_state.user_branch = ""
    if 'current_training' not in st.session_state:
        st.session_state.current_training = 1
    if 'current_scenario' not in st.session_state:
        st.session_state.current_scenario = 0
    if 'training_started' not in st.session_state:
        st.session_state.training_started = False
    if 'answers' not in st.session_state:
        st.session_state.answers = {1: [], 2: []}
    if 'points' not in st.session_state:
        st.session_state.points = {1: 0, 2: 0}
    if 'current_answer' not in st.session_state:
        st.session_state.current_answer = None
    if 'answer_submitted' not in st.session_state:
        st.session_state.answer_submitted = False
    if 'view' not in st.session_state:
        st.session_state.view = 'training'

init_session_state()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_training(training_id):
    return next(t for t in TRAINING_DATA['trainings'] if t['id'] == training_id)

def get_scenarios(training_id):
    return get_training(training_id)['scenarios']

def get_current_scenario():
    scenarios = get_scenarios(st.session_state.current_training)
    if st.session_state.current_scenario < len(scenarios):
        return scenarios[st.session_state.current_scenario]
    return None

def reset_for_new_scenario():
    st.session_state.current_answer = None
    st.session_state.answer_submitted = False

def get_or_create_worksheet(sheet):
    """Get Results worksheet, create it with headers if it doesn't exist"""
    HEADERS = ["Timestamp", "Name", "Branch", "Training", "Score", "MaxScore", "Percent", "Optimal", "Completed", "Answers"]
    
    try:
        worksheet = sheet.worksheet("Results")
        # Check if headers exist
        first_row = worksheet.row_values(1)
        if not first_row or first_row[0] != "Timestamp":
            worksheet.insert_row(HEADERS, 1)
    except WorksheetNotFound:
        worksheet = sheet.add_worksheet(title="Results", rows=1000, cols=10)
        worksheet.append_row(HEADERS)
    
    return worksheet

def save_to_google_sheets():
    """
    Save results to Google Sheets
    Auto-creates Results tab and headers if they don't exist.
    
    Setup:
    1. Create a blank Google Sheet
    2. Share it with your service account email
    3. Add TRAINING_SHEET_ID and gcp_service_account to Streamlit secrets
    """
    try:
        if 'gcp_service_account' in st.secrets:
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            gc = gspread.authorize(credentials)
            
            SHEET_ID = st.secrets.get("TRAINING_SHEET_ID", "")
            if not SHEET_ID:
                st.warning("TRAINING_SHEET_ID not configured in secrets")
                return False
                
            sheet = gc.open_by_key(SHEET_ID)
            worksheet = get_or_create_worksheet(sheet)
            
            # Save each completed training
            for training_id in [1, 2]:
                answers = st.session_state.answers[training_id]
                if not answers:
                    continue
                    
                training = get_training(training_id)
                scenarios = get_scenarios(training_id)
                points = st.session_state.points[training_id]
                max_points = len(scenarios) * 3
                optimal_count = sum(1 for a in answers if a['score'] == 'best')
                
                row = [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    st.session_state.user_name,
                    st.session_state.user_branch,
                    training['name'],
                    points,
                    max_points,
                    round(points / max_points * 100),
                    optimal_count,
                    len(answers),
                    json.dumps([a['answer'] for a in answers])
                ]
                
                worksheet.append_row(row)
            
            st.success("✓ Results saved!")
            return True
            
    except Exception as e:
        st.warning(f"Could not save to Google Sheets: {e}")
        return False
    
    return False

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_header():
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown('<div class="main-header"><h1>🔧 Southeastern Equipment - Parts Sales Training</h1></div>', unsafe_allow_html=True)
    with col2:
        if st.button("Training", type="primary" if st.session_state.view == 'training' else "secondary"):
            st.session_state.view = 'training'
            st.rerun()
    with col3:
        if st.button("Dashboard", type="primary" if st.session_state.view == 'dashboard' else "secondary"):
            st.session_state.view = 'dashboard'
            st.rerun()

def render_welcome():
    st.markdown("### February 2026 Training")
    st.markdown("""
    Each scenario shows a real customer interaction. Pick the response you think works best, 
    then see why each approach does or doesn't work.
    
    **Each training has 10 scenarios.** Take your time — this is about learning, not testing.
    """)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.user_name = st.text_input("Your Name", st.session_state.user_name)
    with col2:
        st.session_state.user_branch = st.selectbox("Branch", SE_BRANCHES, 
            index=SE_BRANCHES.index(st.session_state.user_branch) if st.session_state.user_branch in SE_BRANCHES else 0)
    
    st.divider()
    
    # Training cards
    col1, col2 = st.columns(2)
    
    for i, training in enumerate(TRAINING_DATA['trainings']):
        with col1 if i == 0 else col2:
            completed = len(st.session_state.answers[training['id']])
            total = len(training['scenarios'])
            progress = completed / total
            
            st.markdown(f"**Training {training['id']}**")
            st.markdown(f"**{training['name']}**")
            st.markdown(f"_{training['description']}_")
            st.progress(progress, text=f"{completed}/{total}")
    
    if st.button("Start Training", type="primary", disabled=not (st.session_state.user_name and st.session_state.user_branch)):
        st.session_state.training_started = True
        st.session_state.current_scenario = len(st.session_state.answers[st.session_state.current_training])
        st.rerun()

def render_scenario():
    scenario = get_current_scenario()
    training = get_training(st.session_state.current_training)
    scenarios = get_scenarios(st.session_state.current_training)
    
    if not scenario:
        render_results()
        return
    
    # Header info
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**Scenario {st.session_state.current_scenario + 1} of {len(scenarios)}**")
    with col2:
        completed = len(st.session_state.answers[st.session_state.current_training])
        st.markdown(f"<span class='progress-text'>{completed} of {len(scenarios)} complete</span>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"**{training['name']}**")
    
    st.divider()
    
    # Scenario
    st.markdown(f"**{scenario['situation'].upper()}**")
    st.markdown(f'<div class="customer-quote">"{scenario["customer_says"]}"</div>', unsafe_allow_html=True)
    
    st.markdown("### What do you say?")
    
    if not st.session_state.answer_submitted:
        # Show choices as radio buttons
        choices = [f"{c['letter']}. {c['text']}" for c in scenario['choices']]
        selected = st.radio("Choose your response:", choices, index=None, label_visibility="collapsed")
        
        if selected:
            st.session_state.current_answer = selected[0]  # Get letter
        
        if st.button("Submit Answer", type="primary", disabled=st.session_state.current_answer is None):
            st.session_state.answer_submitted = True
            # Record answer
            answer_idx = ord(st.session_state.current_answer) - ord('A')
            choice = scenario['choices'][answer_idx]
            st.session_state.answers[st.session_state.current_training].append({
                'scenario_id': scenario['id'],
                'answer': st.session_state.current_answer,
                'score': choice['score'],
                'points': choice['points']
            })
            st.session_state.points[st.session_state.current_training] += choice['points']
            st.rerun()
    else:
        # Show feedback
        answer_idx = ord(st.session_state.current_answer) - ord('A')
        selected_choice = scenario['choices'][answer_idx]
        
        # Show all choices with optimal highlighted
        for choice in scenario['choices']:
            is_optimal = choice['score'] == 'best'
            is_selected = choice['letter'] == st.session_state.current_answer
            
            style = "optimal-answer" if is_optimal else "other-answer"
            badge = " ✓ Optimal" if is_optimal else ""
            selected_marker = " ← Your answer" if is_selected else ""
            
            st.markdown(f"""
            <div class="{style}">
                <strong>{choice['letter']}.{badge}</strong> {choice['text']}{selected_marker}
            </div>
            """, unsafe_allow_html=True)
        
        # Feedback message
        if selected_choice['score'] == 'best':
            st.markdown('<div class="result-optimal">✓ <strong>That\'s the optimal approach!</strong></div>', unsafe_allow_html=True)
        elif selected_choice['score'] == 'better':
            st.markdown('<div class="result-close">○ <strong>Good thinking!</strong> There\'s a slightly better option — see above.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="result-learning">○ <strong>Let\'s look at why a different approach works better here.</strong></div>', unsafe_allow_html=True)
        
        # Key insight
        st.markdown(f"""
        <div class="insight-box">
            <strong>💡 KEY INSIGHT</strong><br>
            {scenario['key_insight']}
        </div>
        """, unsafe_allow_html=True)
        
        # Explanations
        st.markdown("### Why Each Response Works (or Doesn't):")
        
        # Sort by points (best first)
        sorted_choices = sorted(scenario['choices'], key=lambda x: x['points'], reverse=True)
        for choice in sorted_choices:
            is_optimal = choice['score'] == 'best'
            style = "optimal-answer" if is_optimal else "other-answer"
            badge = " Optimal" if is_optimal else ""
            
            st.markdown(f"""
            <div class="{style}">
                <strong>{choice['letter']}.{badge}</strong><br>
                {choice['explanation']}
            </div>
            """, unsafe_allow_html=True)
        
        # Next button
        if st.session_state.current_scenario < len(scenarios) - 1:
            if st.button("Next Scenario →", type="primary"):
                st.session_state.current_scenario += 1
                reset_for_new_scenario()
                st.rerun()
        else:
            if st.button("See Results →", type="primary"):
                st.session_state.current_scenario += 1
                reset_for_new_scenario()
                st.rerun()

def render_results():
    training = get_training(st.session_state.current_training)
    scenarios = get_scenarios(st.session_state.current_training)
    answers = st.session_state.answers[st.session_state.current_training]
    points = st.session_state.points[st.session_state.current_training]
    
    # Count optimal answers
    optimal_count = sum(1 for a in answers if a['score'] == 'best')
    
    st.markdown(f"## {training['name']} Complete! 🎉")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Scenarios Completed", len(scenarios))
    with col2:
        st.metric("Optimal Answers", f"{optimal_count} of {len(scenarios)}")
    
    if optimal_count >= 8:
        st.success(f"Excellent! You got {optimal_count} out of {len(scenarios)} optimal answers.")
    elif optimal_count >= 5:
        st.info(f"Good work! You got {optimal_count} optimal answers. Review the others to strengthen your skills.")
    else:
        st.warning(f"You completed all {len(scenarios)} scenarios. Review them to see the optimal approaches.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Review Answers"):
            st.session_state.current_scenario = 0
            st.rerun()
    with col2:
        if st.session_state.current_training == 1:
            if st.button("Start Training 2 →", type="primary"):
                st.session_state.current_training = 2
                st.session_state.current_scenario = 0
                reset_for_new_scenario()
                st.rerun()
        else:
            st.success("You've completed both trainings!")
            # Save results
            save_to_google_sheets()

def render_sidebar():
    with st.sidebar:
        st.markdown(f"### {TRAINING_DATA['month']}")
        
        for training in TRAINING_DATA['trainings']:
            completed = len(st.session_state.answers[training['id']])
            total = len(training['scenarios'])
            is_current = training['id'] == st.session_state.current_training
            
            st.markdown(f"**Training {training['id']}: {training['name']}**")
            st.progress(completed / total, text=f"{completed}/{total}")
            
            if is_current and st.session_state.training_started:
                # Show scenario list
                scenarios = get_scenarios(training['id'])
                for i, scenario in enumerate(scenarios):
                    answer = next((a for a in st.session_state.answers[training['id']] if a['scenario_id'] == scenario['id']), None)
                    if answer:
                        icon = "✓" if answer['score'] == 'best' else "●"
                    else:
                        icon = ""
                    
                    is_selected = i == st.session_state.current_scenario
                    style = "→ " if is_selected else "  "
                    st.markdown(f"{style}Scenario {i+1} {icon}")
            
            st.divider()

def render_dashboard():
    st.markdown("## Training Dashboard")
    st.markdown("_Aggregate results across all associates_")
    
    # Try to load data from Google Sheets
    results_data = None
    try:
        if 'gcp_service_account' in st.secrets:
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            gc = gspread.authorize(credentials)
            SHEET_ID = st.secrets.get("TRAINING_SHEET_ID", "")
            if SHEET_ID:
                sheet = gc.open_by_key(SHEET_ID)
                worksheet = get_or_create_worksheet(sheet)
                results_data = worksheet.get_all_records()
    except Exception as e:
        st.warning(f"Could not load data: {e}")
    
    if results_data:
        df = pd.DataFrame(results_data)
        
        # Top-level stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            unique_associates = df['Name'].nunique()
            st.metric("Associates Trained", unique_associates)
        with col2:
            avg_pct = df['Percent'].mean()
            st.metric("Avg Score", f"{avg_pct:.0f}%")
        with col3:
            total_optimal = df['Optimal'].sum()
            total_completed = df['Completed'].sum()
            optimal_rate = (total_optimal / total_completed * 100) if total_completed > 0 else 0
            st.metric("Optimal Rate", f"{optimal_rate:.0f}%")
        with col4:
            # How many completed both trainings
            both_complete = df.groupby('Name')['Training'].nunique()
            completed_both = (both_complete == 2).sum()
            st.metric("Completed Both", completed_both)
        
        st.divider()
        
        # Results by branch
        st.markdown("### Results by Branch")
        branch_stats = df.groupby('Branch').agg({
            'Name': 'nunique',
            'Percent': 'mean',
            'Optimal': 'sum',
            'Completed': 'sum'
        }).round(1)
        branch_stats.columns = ['Associates', 'Avg Score %', 'Optimal Answers', 'Total Completed']
        st.dataframe(branch_stats, use_container_width=True)
        
        st.divider()
        
        # Individual results
        st.markdown("### Individual Results")
        individual = df[['Timestamp', 'Name', 'Branch', 'Training', 'Score', 'MaxScore', 'Optimal']].copy()
        individual = individual.sort_values('Timestamp', ascending=False)
        st.dataframe(individual.head(50), use_container_width=True)
        
    else:
        st.info("Dashboard will show results once Google Sheets is configured. See TRAINING_APP_SETUP.md for instructions.")
        
        # Show placeholder stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Associates Trained", "—")
        with col2:
            st.metric("Avg Score", "—")
        with col3:
            st.metric("Optimal Rate", "—")
        with col4:
            st.metric("Completed Both", "—")

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    render_header()
    
    if st.session_state.view == 'dashboard':
        render_dashboard()
    else:
        if st.session_state.training_started:
            render_sidebar()
            render_scenario()
        else:
            render_welcome()

if __name__ == "__main__":
    main()
