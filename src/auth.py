import streamlit as st
from src.db_connector import get_supabase_client


def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None
    if "refresh_token" not in st.session_state:
        st.session_state["refresh_token"] = None


def login(email: str, password: str) -> tuple[bool, str]:
    try:
        client = get_supabase_client()
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        st.session_state["authenticated"] = True
        st.session_state["user"] = response.user
        st.session_state["access_token"] = response.session.access_token
        st.session_state["refresh_token"] = response.session.refresh_token
        
        return True, "Login successful!"
    
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            return False, "Invalid email or password."
        elif "Email not confirmed" in error_msg:
            return False, "Please verify your email before logging in."
        else:
            return False, f"Login failed: {error_msg}"


def signup(email: str, password: str) -> tuple[bool, str]:
    try:
        client = get_supabase_client()
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            if response.user.confirmed_at:
                st.session_state["authenticated"] = True
                st.session_state["user"] = response.user
                st.session_state["access_token"] = response.session.access_token
                st.session_state["refresh_token"] = response.session.refresh_token
                return True, "Account created successfully!"
            else:
                return True, "Account created! Please check your email to verify."
        
        return False, "Signup failed. Please try again."
    
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            return False, "This email is already registered."
        elif "password" in error_msg.lower():
            return False, "Password must be at least 6 characters."
        else:
            return False, f"Signup failed: {error_msg}"


def reset_password(email: str) -> tuple[bool, str]:
    try:
        client = get_supabase_client()
        client.auth.reset_password_for_email(email)
        return True, "Password reset email sent! Check your inbox."
    except Exception as e:
        return False, f"Failed to send reset email: {str(e)}"


def logout():
    try:
        client = get_supabase_client()
        client.auth.sign_out()
    except Exception:
        pass
    
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["access_token"] = None
    st.session_state["refresh_token"] = None


def get_current_user_id() -> str | None:
    if st.session_state.get("user"):
        return st.session_state["user"].id
    return None


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def render_auth_page():
    # Initialize auth view state if not present
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"

    # Inject Custom CSS for Auth Page
    st.markdown("""
        <style>
            /* Hide Streamlit Input Instructions */
            div[data-testid="InputInstructions"] > span:nth-child(1) {
                display: none;
            }
            
            /* Center elements vertically in the main area */
            .main > div {
                justify-content: center;
            }
            
            /* -- BUTTON STYLING -- */
            
            /* Primary Button (Login, Sign Up, etc) */
            /* Aggressively target the form submit button */
            div[data-testid="stForm"] button,
            div[data-testid="stForm"] button:active,
            div.stButton > button[kind="primary"],
            div.stButton > button[kind="secondaryFormSubmit"] {
                background-color: #0d3b10 !important; /* Darker Green (Default) */
                border-color: #0d3b10 !important;
                color: white !important;
                transition: all 0.2s ease;
            }
            
            div[data-testid="stForm"] button:hover,
            div.stButton > button[kind="primary"]:hover,
            div.stButton > button[kind="secondaryFormSubmit"]:hover {
                background-color: #1B5E20 !important; /* Lighter Green (Hover) */
                border-color: #1B5E20 !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
                color: white !important;
            }
            
            div[data-testid="stForm"] button:focus,
            div.stButton > button[kind="primary"]:focus {
                box-shadow: 0 0 0 2px rgba(27, 94, 32, 0.4) !important;
                border-color: #1B5E20 !important;
                color: white !important;
            }
            
            /* Text Color override for button text elements if they exist */
            div[data-testid="stForm"] button p {
                color: white !important;
            }
            
            /* Secondary Button (Text Links) */
            button[kind="secondary"] {
                border: none !important;
                background: transparent !important;
                box-shadow: none !important;
                color: #CCCCCC !important; /* Lighter Gray */
                padding: 0 !important;
                margin: 0 auto !important;
                display: block !important;
                font-weight: normal !important;
                transition: color 0.2s ease;
            }
            
            button[kind="secondary"]:hover {
                color: #FFFFFF !important; /* White on hover */
                text-decoration: none !important; /* Clean look */
                border: none !important;
                background: transparent !important;
                text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
            }
            
            /* -- INPUT FIELD STYLING -- */
            
            /* Target the input container for border/box-shadow focus changes */
            div[data-baseweb="input"] {
                background-color: transparent !important;
                border-radius: 4px;
            }
            
            /* Aggressive fix for "Dark Spot" / Eye Icon Background */
            /* This targets the container holding the eye icon and the icon itself */
            div[data-baseweb="input"] > div:last-child,
            div[data-baseweb="input"] > div:last-child > div,
            div[data-baseweb="input"] button {
                background-color: transparent !important;
                border: none !important;
            }
            
            /* When the input is focused, change the border of the container */
            div[data-baseweb="input"]:focus-within {
                border-color: #1B5E20 !important;
                box-shadow: 0 0 0 1px #1B5E20 !important;
            }
            
            /* Also ensure the actual input element has no conflicting styles */
            div[data-testid="stTextInput"] input {
                color: inherit;
                background-color: transparent !important;
            }
            
            /* When the input is focused, change the border of the container */
            div[data-baseweb="input"]:focus-within {
                border-color: #1B5E20 !important;
                box-shadow: 0 0 0 1px #1B5E20 !important;
            }
            
            /* Also ensure the actual input element has no conflicting styles */
            div[data-testid="stTextInput"] input {
                color: inherit;
            }
            
            /* -- TYPOGRAPHY & SPACING -- */
            
            h3 {
                margin-top: 5px !important;
                margin-bottom: 25px !important;
                padding-top: 0 !important;
                font-weight: 500;
            }
            
            hr {
                margin-top: 15px !important;
                margin-bottom: 15px !important;
            }
            
        </style>
    """, unsafe_allow_html=True)

    # Simplified Layout
    _, col_modal, _ = st.columns([1, 2, 1])
    
    with col_modal:
        with st.container(border=True):
            # Vertical Padding (Top) - Approximate "half of side margins" feel
            st.markdown("<div style='padding-top: 2rem;'></div>", unsafe_allow_html=True)
            
            # Inner Container Spacing: Use columns to create left/right whitespace
            _, col_content, _ = st.columns([0.1, 0.8, 0.1])
            
            with col_content:
                view = st.session_state["auth_view"]
                
                if view == "login":
                    render_login_view()
                elif view == "signup":
                    render_signup_view()
                elif view == "reset":
                    render_reset_view()
            
            # Vertical Padding (Bottom)
            st.markdown("<div style='padding-bottom: 2rem;'></div>", unsafe_allow_html=True)


def render_login_view():
    # Plain Div for "Welcome Back" to avoid Anchor links
    st.markdown("<div style='text-align: center; font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem;'>Welcome Back</div>", unsafe_allow_html=True)
    
    with st.form("login_form", border=False):
        # Using placeholders as requested
        email = st.text_input("Email", key="login_email", placeholder="Email", label_visibility="collapsed")
        password = st.text_input("Password", type="password", key="login_password", placeholder="Password", label_visibility="collapsed")
        
        st.write("") 
        
        # Primary Action
        submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                success, message = login(email, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    try:
                        st.error(message)
                    except:
                        pass
    
    # Text Links Stack
    # Forgot Password
    if st.button("Forgot Password?", type="secondary", use_container_width=True):
        st.session_state["auth_view"] = "reset"
        st.rerun()
        
    st.markdown("---")
    
    # New Here?
    if st.button("New here? Sign Up", type="secondary", use_container_width=True):
        st.session_state["auth_view"] = "signup"
        st.rerun()


def render_signup_view():
    st.markdown("<div style='text-align: center; font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem;'>Create Account</div>", unsafe_allow_html=True)
    
    with st.form("signup_form", border=False):
        email = st.text_input("Email", key="signup_email", placeholder="Email", label_visibility="collapsed")
        password = st.text_input("Password", type="password", key="signup_password", placeholder="Password", label_visibility="collapsed")
        password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm", placeholder="Confirm Password", label_visibility="collapsed")
        
        st.write("")
        
        submitted = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
        
        if submitted:
            if not email or not password:
                st.error("Please fill in all fields.")
            elif password != password_confirm:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                success, message = signup(email, password)
                if success:
                    st.success(message)
                    if st.session_state.get("authenticated"):
                        st.rerun()
                else:
                    st.error(message)
    
    st.markdown("---")
    
    if st.button("Already have an account? Log in", type="secondary", use_container_width=True):
        st.session_state["auth_view"] = "login"
        st.rerun()


def render_reset_view():
    st.markdown("<div style='text-align: center; font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem;'>Reset Password</div>", unsafe_allow_html=True)
    
    with st.form("reset_form", border=False):
        email = st.text_input("Email", key="reset_email", placeholder="Email", label_visibility="collapsed")
        
        st.write("")
        
        submitted = st.form_submit_button("Send Reset Link", type="primary", use_container_width=True)
        
        if submitted:
            if not email:
                st.error("Please enter your email.")
            else:
                success, message = reset_password(email)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    st.markdown("---")
    
    if st.button("Back to Login", type="secondary", use_container_width=True):
        st.session_state["auth_view"] = "login"
        st.rerun()
