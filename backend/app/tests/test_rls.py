from pathlib import Path


def test_rls_policies_cover_user_owned_tables():
    migration = Path(__file__).parents[3] / "supabase" / "migrations" / "202606190007_rls_policies.sql"
    sql = migration.read_text()

    for table in [
        "user_preferences",
        "accounts",
        "account_connection_events",
        "transfer_groups",
        "transactions",
        "account_balance_snapshots",
        "reconciliation_adjustments",
    ]:
        assert f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;" in sql
        assert "auth.uid() = user_id" in sql

