import { run } from "./sqlite";

export async function migrateLocalDatabase(): Promise<void> {
  await run(`
    CREATE TABLE IF NOT EXISTS local_transaction_queue (
      local_transaction_uuid TEXT PRIMARY KEY,
      account_id TEXT NOT NULL,
      currency TEXT NOT NULL,
      amount_minor INTEGER NOT NULL,
      transaction_type TEXT NOT NULL,
      category TEXT,
      vendor TEXT,
      description TEXT,
      ledger_cutoff_at TEXT NOT NULL,
      client_revision INTEGER NOT NULL DEFAULT 1,
      sync_state TEXT NOT NULL DEFAULT 'local_unsynced',
      last_error TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
  `);
  await run(`
    CREATE INDEX IF NOT EXISTS idx_local_transaction_queue_state
    ON local_transaction_queue (sync_state, updated_at);
  `);
}

