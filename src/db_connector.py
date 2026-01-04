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
# GENERIC REPOSITORY
# ============================================================

class SupabaseTable:
    """Generic wrapper for Supabase table operations with RLS."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name

    @property
    def query(self):
        """Get the query builder for this table using authenticated client."""
        return get_authenticated_client().table(self.table_name)

    def select(self, user_id: str, order_by: tuple[str, bool] = None, limit: int = None) -> list:
        """Select rows for a specific user."""
        q = self.query.select("*").eq("user_id", user_id)
        if order_by:
            col, desc = order_by
            q = q.order(col, desc=desc)
        if limit:
            q = q.limit(limit)
        return q.execute().data

    def insert(self, data: list | dict) -> list:
        """Insert data."""
        return self.query.insert(data).execute().data

    def update(self, record_id: str, updates: dict) -> list:
        """Update a record by ID."""
        return self.query.update(updates).eq("id", record_id).execute().data

    def delete(self, record_id: str) -> bool:
        """Delete a record by ID."""
        response = self.query.delete().eq("id", record_id).execute()
        return len(response.data) > 0


# ============================================================
# TRANSACTIONS CRUD
# ============================================================

def get_transactions(user_id: str, limit: int = 1000) -> list:
    """Fetch all transactions for a user."""
    return SupabaseTable("transactions").select(user_id, order_by=("date", True), limit=limit)


def insert_transactions(transactions: list) -> dict:
    """Insert multiple transactions."""
    return SupabaseTable("transactions").insert(transactions)


def delete_transaction(transaction_id: str) -> bool:
    """Delete a single transaction by ID."""
    return SupabaseTable("transactions").delete(transaction_id)


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
    return SupabaseTable("holdings").select(user_id)


def insert_holding(holding: dict) -> dict:
    """Insert a new holding."""
    return SupabaseTable("holdings").insert(holding)


def update_holding(holding_id: str, updates: dict) -> dict:
    """Update an existing holding."""
    return SupabaseTable("holdings").update(holding_id, updates)


def delete_holding(holding_id: str) -> bool:
    """Delete a holding by ID."""
    return SupabaseTable("holdings").delete(holding_id)


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
