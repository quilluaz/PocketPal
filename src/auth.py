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
                # Auto-confirmed (if email confirmation is disabled)
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
    st.title("🏦 Personal Finance HQ")
    st.markdown("---")
    
    tab_login, tab_signup, tab_reset = st.tabs(["Login", "Sign Up", "Reset Password"])
    
    with tab_login:
        st.subheader("Welcome Back")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    success, message = login(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    with tab_signup:
        st.subheader("Create Account")
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
            submitted = st.form_submit_button("Sign Up", use_container_width=True)
            
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
    
    with tab_reset:
        st.subheader("Reset Password")
        with st.form("reset_form"):
            email = st.text_input("Email", key="reset_email")
            submitted = st.form_submit_button("Send Reset Link", use_container_width=True)
            
            if submitted:
                if not email:
                    st.error("Please enter your email.")
                else:
                    success, message = reset_password(email)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
