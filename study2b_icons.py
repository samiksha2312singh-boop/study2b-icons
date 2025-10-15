import streamlit as st
from openai import OpenAI
import random
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64

# Page config
st.set_page_config(page_title="Study 2b - Icons", layout="centered", initial_sidebar_state="collapsed")

# CSS
st.markdown("""<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}
div[data-testid="stToolbar"] {visibility: hidden;}
div[data-testid="stDecoration"] {display:none;}

.user-msg { 
    background-color: #1e3a5f !important;
    color: white !important;
    padding: 12px !important;
    border-radius: 10px !important;
    margin: 8px 0 !important;
}

.ai-msg-container {
    display: flex !important;
    align-items: flex-start !important;
    margin: 8px 0 !important;
}

.ai-icon {
    width: 32px;
    height: 32px;
    margin-right: 12px;
    flex-shrink: 0;
    background-color: white;
    padding: 4px;
    border-radius: 8px;
}

.ai-msg { 
    background-color: #2c2c2c !important;
    color: white !important;
    padding: 12px !important;
    border-radius: 10px !important;
    flex: 1;
}
</style>""", unsafe_allow_html=True)

# Initialize OpenAI
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

# Function to load and encode icon
@st.cache_data
def get_icon_base64(icon_path):
    """Load icon and convert to base64 for embedding in HTML"""
    try:
        with open(icon_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception as e:
        st.error(f"Error loading icon {icon_path}: {str(e)}")
        return None

# Google Sheets setup
@st.cache_resource
def get_google_sheet():
    """Connect to Google Sheets"""
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client_gspread = gspread.authorize(creds)
        
        # Open your Google Sheet - updated name for Study 2b
        sheet = client_gspread.open("Study2b_Conversations").sheet1
        
        # Add headers if empty
        if sheet.row_count == 0 or not sheet.cell(1, 1).value:
            sheet.append_row([
                'Session ID', 'Condition', 'Session Start', 'First Message', 
                'Last Message', 'Total Messages', 'Total Session Seconds', 
                'Active Chat Seconds', 'Message Number', 'Role', 'Content', 'Timestamp'
            ])
        
        return sheet
    except Exception as e:
        st.error(f"Google Sheets error: {str(e)}")
        return None

def save_to_google_sheets(session_id, condition, session_start, first_message, 
                          last_message, total_messages, total_session_seconds,
                          active_chat_seconds, message_number, role, content, timestamp):
    sheet = get_google_sheet()
    if sheet:
        try:
            sheet.append_row([
                session_id, condition, session_start, 
                first_message or "", last_message or "", 
                total_messages, total_session_seconds, active_chat_seconds, 
                message_number, role, content, timestamp
            ])
        except Exception as e:
            st.error(f"Error saving: {str(e)}")

def calculate_time_metrics():
    current_time = datetime.now()
    total_duration = current_time - st.session_state.session_start_time
    active_duration = None
    if st.session_state.first_message_time and st.session_state.last_message_time:
        active_duration = st.session_state.last_message_time - st.session_state.first_message_time
    
    return {
        "total_session_seconds": total_duration.total_seconds(),
        "active_chat_seconds": active_duration.total_seconds() if active_duration else 0,
        "session_start": st.session_state.session_start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "first_message": st.session_state.first_message_time.strftime('%Y-%m-%d %H:%M:%S') if st.session_state.first_message_time else None,
        "last_message": st.session_state.last_message_time.strftime('%Y-%m-%d %H:%M:%S') if st.session_state.last_message_time else None
    }

# Initialize session
if "condition" not in st.session_state:
    st.session_state.condition = random.choice(["Brain", "Chip", "No Icon"])
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
    st.session_state.session_start_time = datetime.now()
    st.session_state.first_message_time = None
    st.session_state.last_message_time = None

if "messages" not in st.session_state:
    # Same system prompt for all conditions - no name references
    system_prompt = "You are a helpful AI assistant. Be concise and friendly."
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# Load icons based on condition
icon_html = ""
if st.session_state.condition == "Brain":
    brain_icon = get_icon_base64(".icons/brain.png")
    if brain_icon:
        icon_html = f'<img src="data:image/png;base64,{brain_icon}" class="ai-icon" alt="Brain">'
elif st.session_state.condition == "Chip":
    chip_icon = get_icon_base64(".icons/chip.png")
    if chip_icon:
        icon_html = f'<img src="data:image/png;base64,{chip_icon}" class="ai-icon" alt="Chip">'

# Header
st.markdown("<h1 style='color: white;'>AI Chat Assistant</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color: #888;'>Study 2b - Icons | Condition: {st.session_state.condition}</p>", unsafe_allow_html=True)
st.markdown("---")

# Display chat
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg"><b>You:</b> {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        if st.session_state.condition != "No Icon" and icon_html:
            message_html = f'''<div class="ai-msg-container">
                {icon_html}
                <div class="ai-msg">{msg["content"]}</div>
            </div>'''
        else:
            message_html = f'<div class="ai-msg">{msg["content"]}</div>'
        st.markdown(message_html, unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    if st.session_state.first_message_time is None:
        st.session_state.first_message_time = datetime.now()
    
    current_time = datetime.now()
    message_number = len(st.session_state.messages)
    
    st.session_state.messages.append({
        "role": "user", 
        "content": user_input,
        "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    st.session_state.last_message_time = current_time
    
    try:
        with st.spinner("🤖 Getting response..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.messages,
                max_tokens=500,
                temperature=0.7
            )
        
        assistant_message = response.choices[0].message.content
        assistant_time = datetime.now()
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": assistant_message,
            "timestamp": assistant_time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        st.session_state.last_message_time = assistant_time
        
        time_metrics = calculate_time_metrics()
        
        # Save user message
        save_to_google_sheets(
            st.session_state.session_id, st.session_state.condition,
            time_metrics["session_start"], time_metrics["first_message"],
            time_metrics["last_message"], len(st.session_state.messages) - 1,
            time_metrics["total_session_seconds"], time_metrics["active_chat_seconds"],
            message_number, "user", user_input, current_time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Save assistant message
        save_to_google_sheets(
            st.session_state.session_id, st.session_state.condition,
            time_metrics["session_start"], time_metrics["first_message"],
            time_metrics["last_message"], len(st.session_state.messages) - 1,
            time_metrics["total_session_seconds"], time_metrics["active_chat_seconds"],
            message_number + 1, "assistant", assistant_message, assistant_time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    st.rerun()

# Survey link
SURVEY_URL = "https://your-survey-link.com"
if len(st.session_state.messages) >= 11:
    st.markdown("---")
    st.success("✅ Thank you for chatting!")
    st.markdown(f"""<div style='text-align: center;'>
        <a href='{SURVEY_URL}' target='_blank' 
           style='background-color: #0e4429; color: white; padding: 12px 24px; 
                  text-decoration: none; border-radius: 5px; font-weight: bold;'>
            Complete Survey →
        </a>
    </div>""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### Study Info")
st.sidebar.markdown(f"**Session:** `{st.session_state.session_id}`")
st.sidebar.markdown(f"**Condition:** {st.session_state.condition}")
st.sidebar.markdown(f"**Messages:** {len(st.session_state.messages) - 1}")
st.sidebar.success("📊 Data saving to Google Sheets!")
st.sidebar.info("✅ External storage - persists across restarts")

if st.sidebar.button("🔄 Reset"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()