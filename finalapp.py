import streamlit as st
import datetime
import sys
import os
import importlib.util
import pandas as pd

# Import from your backend file (livedata Integeration.py)
def load_livedata_module():
    """Load the livedata Integeration.py module dynamically"""
    # Try multiple possible file paths
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "livedata Integeration.py"),
        os.path.join(os.getcwd(), "livedata Integeration.py"),
        "livedata Integeration.py"
    ]
    
    for file_path in possible_paths:
        if os.path.exists(file_path):
            print(f"Found backend file at: {file_path}")
            spec = importlib.util.spec_from_file_location("livedata_integration", file_path)
            livedata_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(livedata_module)
            return livedata_module
    
    raise FileNotFoundError(f"Could not find 'livedata Integeration.py' in any of these paths: {possible_paths}")

# Load the backend module
try:
    livedata = load_livedata_module()
    generate_response = livedata.generate_response
    is_sales_related_question = livedata.is_sales_related_question
    # Test if the function is working
    test_result = is_sales_related_question("test sales question")
    print(f"Backend module loaded successfully. Test result: {test_result}")
except Exception as e:
    print(f"Error loading backend module: {e}")
    st.error(f"Error loading backend module: {e}")
    # Fallback function if import fails
    def generate_response(question, history=None, followup_flag=False):
        return f"Error: Backend module could not be loaded. Error: {e}"
    def is_sales_related_question(question):
        return True

# --- Festival Data (Tamil/Indian festivals) ---
FESTIVALS = [
    {"name": "Pongal", "date": "2025-01-14"},
    {"name": "Thai Poosam", "date": "2025-01-24"},
    {"name": "Maha Shivaratri", "date": "2025-02-26"},
    {"name": "Ugadi", "date": "2025-03-30"},
    {"name": "Tamil New Year", "date": "2025-04-14"},
    {"name": "Ramzan (Eid-ul-Fitr)", "date": "2025-03-31"},
    {"name": "Aadi Perukku", "date": "2025-08-03"},
    {"name": "Vinayaka Chaturthi", "date": "2025-08-27"},
    {"name": "Navaratri", "date": "2025-09-22"},
    {"name": "Ayudha Pooja", "date": "2025-10-01"},
    {"name": "Vijayadashami", "date": "2025-10-02"},
    {"name": "Deepavali", "date": "2025-10-20"},
    {"name": "Karthigai Deepam", "date": "2025-12-05"},
    {"name": "Christmas", "date": "2025-12-25"},
    {"name": "Pongal", "date": "2025-07-28"},  # Added as requested
]

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Change this to a secure password in production

# --- Predefined Questions (from sales_chatbot.py) ---
PREDEFINED_QUESTIONS = [
    "What is the total revenue from all orders?",
    "What is the average order value?",
    "How much revenue did we generate this month?",
    "What is the total quantity sold this year?",
    "How many dress orders are confirmed?",
    "How many pending or cancelled orders do we have?",
    "What is the status breakdown of all orders?",
    "What is the average rate per meter?",
    "How many premium quality orders have been made?",
    "Predict sales for premium cotton dresses",
    "Show me top 5 performing agents",
    "What is the conversion rate of orders?",
    "Which composition material sells best?",
    "What is the average quantity per order?",
    "Show me daily weave analysis",
    "What is the weekly composition breakdown?",
    "Show me monthly quality analysis",
    "What is the yearly status breakdown?",
    "Show me leading customers by month",
    "Who are the top agents weekly?",
    "Daily customer analysis",
    "Weekly agent performance",
    "Monthly weave trends",
    "Yearly composition analysis"
]

# --- Notification Helper ---
def load_sales_data():
    # Replace with your actual data loading logic
    try:
        df = pd.read_csv('fabric_synthetic.csv')  # Update with your actual file
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception:
        return None

def show_festival_notifications():
    today = datetime.date.today()
    notified = st.session_state.get('notified_festival', False)
    if notified:
        return
    st.toast("👋 Welcome, Admin! Wishing you a productive day!", icon="👋")
    for fest in FESTIVALS:
        fest_date = datetime.datetime.strptime(fest["date"], "%Y-%m-%d").date()
        days_left = (fest_date - today).days
        if 0 <= days_left <= 10:
            offer_msg = f"Upcoming Festival: {fest['name']} on {fest_date.strftime('%b %d, %Y')} ({days_left} days left)."
            msg = (
                f"🎊 {offer_msg} {fest['name']} is coming! Consider giving a discount."
            )
            st.toast(msg, icon="🎊")
    st.session_state['notified_festival'] = True

# --- Streamlit App ---
st.set_page_config(page_title="Dress Sales Monitoring Chatbot", page_icon="👗", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_response" not in st.session_state:
    st.session_state.current_response = ""

# --- Login Page ---
def login_page():
    st.markdown("""
        <div style='text-align:center; margin-top: 80px;'>
            <h1 style='color:#6C3483;'>👗 Dress Sales Monitoring Chatbot</h1>
            <h3 style='color:#2874A6;'>Admin Login</h3>
        </div>
    """, unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        # The form_submit_button will submit on Enter in any field by default
        login_submit = st.form_submit_button("Login", use_container_width=True, type="primary")
    if login_submit:
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.just_logged_in = True  # set a flag
        else:
            st.error("Invalid credentials. Please try again.")
    # After the button, outside the if-block:
    if st.session_state.get("just_logged_in"):
        st.success("Login successful! Redirecting to chat...")
        st.session_state.just_logged_in = False

# --- Chat Page ---
def chat_page():
    st.markdown("""
        <style>
        .chat-bubble-user {
            background: #e0e7ff;
            color: #222;
            border-radius: 16px 16px 4px 16px;
            padding: 12px 16px;
            margin: 8px 0 8px 40px;
            max-width: 70%;
            align-self: flex-end;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .chat-bubble-bot {
            background: #fff;
            color: #000;
            border-radius: 16px 16px 16px 4px;
            padding: 12px 16px;
            margin: 8px 40px 8px 0;
            max-width: 70%;
            align-self: flex-start;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .chat-container {
            display: flex;
            flex-direction: column;
            min-height: 300px;
        }
        .predefined-bar {
            background: #fff !important;
            padding: 16px 0 8px 0;
            border-radius: 8px;
            margin-bottom: 16px;
        }
        button[data-testid^="baseButton"] {
            background: #222 !important;
            color: #fff !important;
            border: 1px solid #e0e0e0 !important;
            font-weight: 500;
            font-size: 1rem;
        }
        button[data-testid^="baseButton"]:hover {
            background: #444 !important;
            color: #fff !important;
        }
        .prompt-bar {
            background: #fff !important;
            box-shadow: 0 -2px 8px rgba(0,0,0,0.05);
            border-top: 1px solid #e0e0e0;
        }
        section[data-testid="stTextInput"] input {
            background: #fff !important;
            color: #000 !important;
            border: 1px solid #e0e0e0 !important;
        }
        button[kind="primary"], button[data-testid="baseButton-primary"] {
            background: #222 !important;
            color: #fff !important;
            border: 1px solid #e0e0e0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("👗 Dress Sales Monitoring Chatbot")
    st.caption("Ask about sales trends, product performance, or request predictions!")
    
    # Debug information (can be removed later)
    with st.expander("🔧 Debug Info"):
        st.write(f"Backend module loaded: {generate_response.__module__ if hasattr(generate_response, '__module__') else 'Unknown'}")
        st.write(f"Current working directory: {os.getcwd()}")
        if st.button("Test Backend Connection"):
            test_response = generate_response("What is the total revenue from all orders?", [], False)
            st.write("Test Response:", test_response[:200] + "..." if len(test_response) > 200 else test_response)

    # Festival notifications
    show_festival_notifications()

    # Predefined questions
    st.markdown('<div class="predefined-bar">', unsafe_allow_html=True)
    st.markdown("**Quick Questions:**")
    q_cols = st.columns(3)
    for i, question in enumerate(PREDEFINED_QUESTIONS):
        if q_cols[i % 3].button(question, key=f"predef_{i}"):
            st.session_state.chat_history.append({
                "role": "user",
                "parts": [{"text": question}]
            })
            with st.spinner("AI is thinking..."):
                # Use the backend function with proper parameters
                ai_response = generate_response(question, st.session_state.chat_history, followup_flag=False)
            st.session_state.chat_history.append({
                "role": "model",
                "parts": [{"text": ai_response}]
            })
            st.session_state.current_response = ai_response
            st.session_state.last_bot_prompt = ai_response  # Save for context
            st.session_state.last_user_input = question
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat input with Enter key functionality
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "Type your question...",
            key="chat_input",
            value="",
            label_visibility="collapsed",
            on_change=None  # We'll handle Enter below
        )
    with col2:
        send = st.button("Send", use_container_width=True, key="send_btn")

    # Detect if the last bot message is a confirmation prompt
    def bot_asked_confirmation():
        last_bot = st.session_state.get("last_bot_prompt", "")
        return any(phrase in last_bot.lower() for phrase in ["can i do", "would you like me to", "should i proceed", "do you want me to"])  # Add more as needed

    # Handle 'Yes' button for confirmation
    yes_clicked = False
    if bot_asked_confirmation():
        if st.button("Yes", key="yes_btn", use_container_width=True):
            yes_clicked = True
            user_input = "yes"  # Simulate user input as 'yes'
            send = True

    # Handle Enter key and Send button or Yes button
    # If user_input is not empty and has changed, treat as Enter pressed
    enter_pressed = False
    if user_input.strip() and user_input != st.session_state.get("last_input", "") and not send and not yes_clicked:
        enter_pressed = True

    if (send and user_input.strip()) or yes_clicked or enter_pressed:
        st.session_state.last_input = user_input
        # Only store in history if the question is related to the dataset (with fuzzy match)
        if is_sales_related_question(user_input):
            st.session_state.chat_history.append({
                "role": "user",
                "parts": [{"text": user_input}]
            })
        # Pass a flag for follow-up if 'yes' or similar
        followup_flag = False
        if user_input.strip().lower() in ["yes", "do it", "change it", "ok", "go ahead"]:
            followup_flag = True
        with st.spinner("AI is thinking..."):
            try:
                # Debug: Show what we're calling
                st.write(f"Debug: Calling generate_response with question: '{user_input}'")
                ai_response = generate_response(user_input, st.session_state.chat_history, followup_flag=followup_flag)
                st.write(f"Debug: Received response length: {len(ai_response)} characters")
            except Exception as e:
                ai_response = f"Error occurred: {str(e)}"
                st.error(f"Error calling backend: {e}")
        # Only store bot response if user input was stored
        if is_sales_related_question(user_input):
            st.session_state.chat_history.append({
                "role": "model",
                "parts": [{"text": ai_response}]
            })
        st.session_state.current_response = ai_response
        st.session_state.last_bot_prompt = ai_response
        st.session_state.last_user_input = user_input
        st.rerun()

    # Display previous user question (if any), then latest exchange
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    # Show previous user question if available
    if len(st.session_state.chat_history) >= 3:
        # Find the previous user message (before the last one)
        prev_user = None
        for msg in reversed(st.session_state.chat_history[:-2]):
            if msg.get("role") == "user":
                prev_user = msg["parts"][0]["text"]
                break
        if prev_user:
            st.markdown(f"<div class='chat-bubble-user' style='opacity:0.7;'><b>Previous You:</b> {prev_user}</div>", unsafe_allow_html=True)
    if st.session_state.get("last_user_input"):
        st.markdown(f"<div class='chat-bubble-user'><b>You:</b> {st.session_state['last_user_input']}</div>", unsafe_allow_html=True)
    if st.session_state.current_response:
        st.markdown(f"<div class='chat-bubble-bot'><b>AI:</b> {st.session_state.current_response}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Main App Logic ---
if not st.session_state.logged_in:
    login_page()
else:
    chat_page() 