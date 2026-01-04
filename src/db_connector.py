"""
Supabase database connector and query helpers.
"""
import streamlit as st
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """Initialize and return Supabase client from Streamlit secrets."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


def get_authenticated_client() -> Client:
    """
    Get a Supabase client authenticated with the current user's session.
    This ensures RLS policies are applied correctly.
    """
    client = get_supabase_client()
    
    if "access_token" in st.session_state:
        client.auth.set_session(
            access_token=st.session_state["access_token"],
            refresh_token=st.session_state.get("refresh_token", "")
        )
    
    return client


# ============================================================
# TRANSACTIONS CRUD
# ============================================================

def get_transactions(user_id: str, limit: int = 1000) -> list:
    """Fetch all transactions for a user."""
    client = get_authenticated_client()
    response = client.table("transactions") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("date", desc=True) \
        .limit(limit) \
        .execute()
    return response.data


def insert_transactions(transactions: list) -> dict:
    """
    Insert multiple transactions.
    Each transaction dict should have: date, description, amount, category, account_source, user_id
    """
    client = get_authenticated_client()
    response = client.table("transactions").insert(transactions).execute()
    return response.data


def delete_transaction(transaction_id: str) -> bool:
    """Delete a single transaction by ID."""
    client = get_authenticated_client()
    response = client.table("transactions").delete().eq("id", transaction_id).execute()
    return len(response.data) > 0


def check_duplicate_transaction(user_id: str, date: str, amount: float, description: str) -> bool:
    """Check if a transaction with same date, amount, description exists for user."""
    client = get_authenticated_client()
    response = client.table("transactions") \
        .select("id") \
        .eq("user_id", user_id) \
        .eq("date", date) \
        .eq("amount", amount) \
        .eq("description", description) \
        .limit(1) \
        .execute()
    return len(response.data) > 0


# ============================================================
# HOLDINGS CRUD
# ============================================================

def get_holdings(user_id: str) -> list:
    """Fetch all holdings for a user."""
    client = get_authenticated_client()
    response = client.table("holdings") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()
    return response.data


def insert_holding(holding: dict) -> dict:
    """
    Insert a new holding.
    holding dict should have: ticker, quantity, avg_cost (optional), user_id
    """
    client = get_authenticated_client()
    response = client.table("holdings").insert(holding).execute()
    return response.data


def update_holding(holding_id: str, updates: dict) -> dict:
    """Update an existing holding."""
    client = get_authenticated_client()
    response = client.table("holdings").update(updates).eq("id", holding_id).execute()
    return response.data


def delete_holding(holding_id: str) -> bool:
    """Delete a holding by ID."""
    client = get_authenticated_client()
    response = client.table("holdings").delete().eq("id", holding_id).execute()
    return len(response.data) > 0


# ============================================================
# PROFILE HELPERS
# ============================================================

def get_profile(user_id: str) -> dict:
    """Fetch user profile."""
    client = get_authenticated_client()
    response = client.table("profiles") \
        .select("*") \
        .eq("id", user_id) \
        .single() \
        .execute()
    return response.data
