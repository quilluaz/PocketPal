import streamlit as st
from supabase import create_client, Client


def get_supabase_client() -> Client:
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


class SupabaseTable:
    def __init__(self, table_name: str):
        self.table_name = table_name

    @property
    def query(self):
        return get_authenticated_client().table(self.table_name)

    def select(self, user_id: str, order_by: tuple[str, bool] = None, limit: int = None) -> list:
        q = self.query.select("*").eq("user_id", user_id)
        if order_by:
            col, desc = order_by
            q = q.order(col, desc=desc)
        if limit:
            q = q.limit(limit)
        return q.execute().data

    def insert(self, data: list | dict) -> list:
        return self.query.insert(data).execute().data

    def update(self, record_id: str, updates: dict) -> list:
        return self.query.update(updates).eq("id", record_id).execute().data

    def delete(self, record_id: str) -> bool:
        response = self.query.delete().eq("id", record_id).execute()
        return len(response.data) > 0


def get_transactions(user_id: str, limit: int = 1000) -> list:
    return SupabaseTable("transactions").select(user_id, order_by=("date", True), limit=limit)


def get_existing_signatures(user_id: str) -> set:
    """
    Fetch a set of (date, amount, description) tuples for existing transactions.
    Used for batch deduplication - O(1) lookup instead of N database queries.
    """
    client = get_authenticated_client()
    response = client.table("transactions") \
        .select("date, amount, description") \
        .eq("user_id", user_id) \
        .execute()
    
    return {
        (row['date'], float(row['amount']), row['description']) 
        for row in response.data
    }


def insert_transactions(transactions: list) -> dict:
    return SupabaseTable("transactions").insert(transactions)


def delete_transaction(transaction_id: str) -> bool:
    return SupabaseTable("transactions").delete(transaction_id)


def check_duplicate_transaction(user_id: str, date: str, amount: float, description: str) -> bool:
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


def get_holdings(user_id: str) -> list:
    return SupabaseTable("holdings").select(user_id)


def insert_holding(holding: dict) -> dict:
    return SupabaseTable("holdings").insert(holding)


def update_holding(holding_id: str, updates: dict) -> dict:
    return SupabaseTable("holdings").update(holding_id, updates)


def delete_holding(holding_id: str) -> bool:
    return SupabaseTable("holdings").delete(holding_id)


def get_profile(user_id: str) -> dict:
    client = get_authenticated_client()
    response = client.table("profiles") \
        .select("*") \
        .eq("id", user_id) \
        .single() \
        .execute()
    return response.data


def update_profile_currency(user_id: str, currency: str):
    client = get_authenticated_client()
    return client.table("profiles").update({"currency": currency}).eq("id", user_id).execute()
