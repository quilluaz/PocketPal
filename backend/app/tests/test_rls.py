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


def test_rls_keeps_canonical_ledger_writes_service_owned():
    migration = Path(__file__).parents[3] / "supabase" / "migrations" / "202606190007_rls_policies.sql"
    sql = migration.read_text()

    assert 'CREATE POLICY "Users can select own transactions"' in sql
    assert 'CREATE POLICY "Users can insert own transactions"' not in sql
    assert 'CREATE POLICY "Users can update own transactions"' not in sql
    assert 'CREATE POLICY "Users can delete own transactions"' not in sql

    for table in ["snapshots", "reconciliation adjustments"]:
        assert f'CREATE POLICY "Users can select own {table}"' in sql
        assert f'CREATE POLICY "Users can insert own {table}"' not in sql
        assert f'CREATE POLICY "Users can update own {table}"' not in sql
        assert f'CREATE POLICY "Users can delete own {table}"' not in sql
