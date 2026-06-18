export type LocalSyncState = "local_unsynced" | "syncing" | "synced" | "failed";

export type QueuedTransaction = {
  local_transaction_uuid: string;
  account_id: string;
  currency: string;
  amount_minor: number;
  transaction_type: "income" | "expense" | "transfer";
  category?: string | null;
  vendor?: string | null;
  description?: string | null;
  ledger_cutoff_at: string;
  client_revision: number;
  sync_state: LocalSyncState;
  last_error?: string | null;
  created_at: string;
  updated_at: string;
};

export type SyncResult = {
  local_transaction_uuid: string;
  server_transaction_id?: string | null;
  status: "inserted" | "updated" | "stale_ignored" | "already_synced" | "failed";
  error?: string | null;
};

export type SyncResponse = {
  sync_batch_id: string;
  results: SyncResult[];
};

