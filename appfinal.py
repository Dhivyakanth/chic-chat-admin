import streamlit as st
import datetime
import sys
import os
import importlib.util
import pandas as pd

# Set page config first
st.set_page_config(
    page_title="Dress Sales Monitoring Chatbot", 
    page_icon="👗", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import from your backend file (livedata Integeration.py)
def load_livedata_module():
    """Load the livedata Integeration.py module dynamically"""
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
    test_result = is_sales_related_question("test sales question")
    print(f"Backend module loaded successfully. Test result: {test_result}")
except Exception as e:
    print(f"Error loading backend module: {e}")
    def generate_response(question, history=None, followup_flag=False):
        return f"Error: Backend module could not be loaded. Error: {e}"
    def is_sales_related_question(question):
        return True

# --- Constants ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Festival Data
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
]

# Predefined Questions
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

# --- Session State Initialization ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "notifications_shown" not in st.session_state:
    st.session_state.notifications_shown = False

# --- CSS Styling ---
def apply_css():
    st.markdown("""
    <style>
    /* Global Reset and Base Styles */
    * {
        box-sizing: border-box;
    }
    
    html, body {
        margin: 0;
        padding: 0;
        background-color: white;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    .main > div {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive Container */
    .main .block-container {
        max-width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 200px;
    }
    
    /* Chat Container - Responsive */
    .chat-container {
        background: white;
        height: 65vh;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        scroll-behavior: smooth;
    }
    
    /* Message Bubbles - ChatGPT Style Responsive */
    .message-user {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 18px 18px 4px 18px;
        margin-left: auto;
        margin-right: 0;
        max-width: 85%;
        word-wrap: break-word;
        align-self: flex-end;
        font-size: 0.95rem;
        line-height: 1.4;
        box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);
        position: relative;
        animation: slideInRight 0.3s ease-out;
    }
    
    .message-bot {
        background: #f8f9fa;
        color: #2d3748;
        padding: 0.75rem 1rem;
        border-radius: 18px 18px 18px 4px;
        margin-left: 0;
        margin-right: auto;
        max-width: 90%;
        word-wrap: break-word;
        align-self: flex-start;
        border: 1px solid #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.5;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        position: relative;
        animation: slideInLeft 0.3s ease-out;
    }
    
    /* Message animations */
    @keyframes slideInRight {
        from { transform: translateX(20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Input Container - Fixed Bottom with Responsive Padding */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 1rem;
        border-top: 1px solid #e2e8f0;
        z-index: 1000;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Predefined Questions - Responsive Grid */
    .questions-container {
        background: #f7fafc;
        padding: 0.75rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        border: 1px solid #e2e8f0;
        display: grid;
        gap: 0.5rem;
    }
    
    .question-btn {
        background: white;
        border: 1px solid #cbd5e0;
        padding: 0.5rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: left;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .question-btn:hover {
        background: #edf2f7;
        border-color: #007bff;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Login Form - Responsive */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem 1.5rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
    }
    
    /* Input Styling - Modern Look */
    .stTextInput > div > div > input {
        border-radius: 24px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.2s ease;
        background: white;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #007bff;
        box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
        outline: none;
    }
    
    /* Button Styling - Modern with Hover Effects */
    .stButton > button {
        border-radius: 24px;
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
        background: linear-gradient(135deg, #0056b3 0%, #004085 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Hide default text input label */
    .stTextInput label {
        display: none;
    }
    
    /* Responsive Breakpoints - Tablet */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            padding-bottom: 220px;
        }
        
        .chat-container {
            height: 60vh;
            padding: 0.75rem;
            border-radius: 8px;
            gap: 0.75rem;
        }
        
        .message-user, .message-bot {
            max-width: 95%;
            padding: 0.625rem 0.875rem;
            font-size: 0.9rem;
        }
        
        .message-user {
            border-radius: 16px 16px 4px 16px;
        }
        
        .message-bot {
            border-radius: 16px 16px 16px 4px;
        }
        
        .input-container {
            padding: 0.75rem;
        }
        
        .questions-container {
            padding: 0.5rem;
            gap: 0.375rem;
        }
        
        .question-btn {
            padding: 0.375rem 0.625rem;
            font-size: 0.8rem;
            border-radius: 16px;
        }
        
        .login-container {
            margin: 1rem;
            padding: 1.5rem 1rem;
            border-radius: 12px;
        }
        
        .stTextInput > div > div > input {
            padding: 0.625rem 0.875rem;
            font-size: 0.95rem;
            border-radius: 20px;
        }
        
        .stButton > button {
            padding: 0.625rem 1.25rem;
            font-size: 0.9rem;
            border-radius: 20px;
        }
    }
    
    /* Responsive Breakpoints - Mobile */
    @media (max-width: 480px) {
        .main .block-container {
            padding-left: 0.25rem;
            padding-right: 0.25rem;
            padding-bottom: 240px;
        }
        
        .chat-container {
            height: 55vh;
            padding: 0.5rem;
            border-radius: 6px;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }
        
        .message-user, .message-bot {
            max-width: 98%;
            padding: 0.5rem 0.75rem;
            font-size: 0.875rem;
            line-height: 1.3;
        }
        
        .message-user {
            border-radius: 14px 14px 4px 14px;
        }
        
        .message-bot {
            border-radius: 14px 14px 14px 4px;
        }
        
        .input-container {
            padding: 0.5rem;
        }
        
        .questions-container {
            padding: 0.375rem;
            gap: 0.25rem;
            grid-template-columns: 1fr;
        }
        
        .question-btn {
            padding: 0.375rem 0.5rem;
            font-size: 0.75rem;
            border-radius: 12px;
            white-space: normal;
            text-align: center;
        }
        
        .login-container {
            margin: 0.5rem;
            padding: 1rem 0.75rem;
            border-radius: 8px;
        }
        
        .stTextInput > div > div > input {
            padding: 0.5rem 0.75rem;
            font-size: 0.9rem;
            border-radius: 16px;
        }
        
        .stButton > button {
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
            border-radius: 16px;
        }
        
        /* Header text responsive */
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.25rem !important;
        }
        
        h3 {
            font-size: 1.125rem !important;
        }
    }
    
    /* Extra small devices */
    @media (max-width: 360px) {
        .chat-container {
            height: 50vh;
            padding: 0.375rem;
        }
        
        .message-user, .message-bot {
            padding: 0.375rem 0.625rem;
            font-size: 0.8rem;
        }
        
        .input-container {
            padding: 0.375rem;
        }
        
        .questions-container {
            padding: 0.25rem;
        }
        
        .question-btn {
            padding: 0.25rem 0.375rem;
            font-size: 0.7rem;
        }
    }
    
    /* Loading spinner customization */
    .stSpinner > div {
        border-top-color: #007bff !important;
    }
    
    /* Smooth scrolling for chat */
    .chat-container::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 6px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 6px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Notification Functions ---
def show_notifications():
    """Show festival notifications"""
    if st.session_state.notifications_shown:
        return
        
    today = datetime.date.today()
    notifications = []
    
    # Welcome message
    notifications.append("👋 Welcome, Admin! Ready to analyze your sales data?")
    
    # Festival notifications
    for festival in FESTIVALS:
        fest_date = datetime.datetime.strptime(festival["date"], "%Y-%m-%d").date()
        days_left = (fest_date - today).days
        
        if 0 <= days_left <= 7:
            notifications.append(f"🎊 {festival['name']} is in {days_left} days! Consider special promotions.")
        elif days_left == 0:
            notifications.append(f"🎉 Happy {festival['name']}! Great day for sales!")
    
    # Show notifications
    for notification in notifications:
        st.toast(notification, icon="🎊")
    
    st.session_state.notifications_shown = True

# --- Login Page ---
def login_page():
    apply_css()
    
    st.markdown("""
    <div style='text-align: center; margin-top: 100px;'>
        <h1 style='color: #007bff; margin-bottom: 10px;'>👗 Dress Sales Monitoring</h1>
        <h2 style='color: #6c757d; font-weight: 300; margin-bottom: 40px;'>Chatbot Admin Panel</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### 🔐 Admin Login")
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            login_button = st.form_submit_button("Login", use_container_width=True)
            
            if login_button:
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    st.session_state.logged_in = True
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Login hint
        st.markdown("""
        <div style='text-align: center; margin-top: 20px; color: #6c757d; font-size: 14px;'>
            <p>Default credentials: admin / admin123</p>
        </div>
        """, unsafe_allow_html=True)

# --- Chat Interface ---
def chat_interface():
    apply_css()
    show_notifications()
    
    # Header
    st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1 style='color: #007bff; margin: 0;'>👗 Sales Analytics Chatbot</h1>
        <p style='color: #6c757d; margin: 5px 0 0 0;'>Ask about sales trends, product performance, or request predictions!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button in top right
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🚪 Logout", key="logout"):
            st.session_state.logged_in = False
            st.session_state.chat_history = []
            st.session_state.messages = []
            st.session_state.notifications_shown = False
            st.rerun()
    
    # Chat messages display
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container" id="chat-container">', unsafe_allow_html=True)
        
        if not st.session_state.messages:
            st.markdown("""
            <div style='text-align: center; color: #6c757d; margin-top: 50px;'>
                <h3>👋 Hello! I'm your Sales Analytics Assistant</h3>
                <p>Ask me anything about your sales data, trends, or predictions!</p>
                <p>Try one of the suggested questions below to get started.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f'<div class="message-user">{message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="message-bot">{message["content"]}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Spacer to push input to bottom
    st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)
    
    # Fixed input container at bottom
    input_container = st.container()
    with input_container:
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        
        # Predefined questions
        st.markdown("**💡 Quick Questions:**")
        st.markdown('<div class="questions-container">', unsafe_allow_html=True)
        
        # Display questions in rows of 3
        for i in range(0, len(PREDEFINED_QUESTIONS), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(PREDEFINED_QUESTIONS):
                    question = PREDEFINED_QUESTIONS[i + j]
                    if col.button(question, key=f"q_{i+j}", help=question):
                        handle_user_input(question)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Text input with send button
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "message",
                placeholder="Type your question here...",
                key="user_input",
                label_visibility="collapsed"
            )
        with col2:
            send_button = st.button("Send", key="send", use_container_width=True)
        
        # Handle input submission
        if send_button and user_input.strip():
            handle_user_input(user_input)
            st.rerun()
        
        # Handle Enter key
        if user_input and user_input != st.session_state.get("last_input", ""):
            st.session_state.last_input = user_input
            handle_user_input(user_input)
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- Handle User Input ---
def handle_user_input(user_input):
    """Process user input and generate response"""
    if not user_input.strip():
        return
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Add to chat history for backend
    st.session_state.chat_history.append({
        "role": "user",
        "parts": [{"text": user_input}]
    })
    
    # Generate response using backend
    try:
        with st.spinner("🤖 Analyzing your question..."):
            # Determine if it's a follow-up
            followup_flag = user_input.lower().strip() in ["yes", "yeah", "ok", "sure", "go ahead"]
            
            # Call backend
            ai_response = generate_response(
                user_input, 
                st.session_state.chat_history, 
                followup_flag=followup_flag
            )
            
            # Add bot response
            st.session_state.messages.append({"role": "bot", "content": ai_response})
            
            # Add to chat history
            st.session_state.chat_history.append({
                "role": "model",
                "parts": [{"text": ai_response}]
            })
            
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        st.session_state.messages.append({"role": "bot", "content": error_msg})
    
    # Clear input
    if "user_input" in st.session_state:
        st.session_state.user_input = ""

# --- Auto-scroll JavaScript ---
def add_auto_scroll():
    """Add JavaScript to auto-scroll to bottom of chat"""
    st.markdown("""
    <script>
    function scrollToBottom() {
        var chatContainer = document.getElementById('chat-container');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    // Scroll to bottom when page loads
    window.onload = function() {
        setTimeout(scrollToBottom, 100);
    };
    
    // Scroll to bottom when new messages are added
    var observer = new MutationObserver(function(mutations) {
        scrollToBottom();
    });
    
    var chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        observer.observe(chatContainer, { childList: true, subtree: true });
    }
    </script>
    """, unsafe_allow_html=True)

# --- Main Application ---
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        chat_interface()
        add_auto_scroll()

if __name__ == "__main__":
    main()
