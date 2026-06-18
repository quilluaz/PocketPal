import { applySyncResults, listSyncableTransactions, markTransactionsSyncing } from "../db/queue";
import { SyncResponse } from "../types/sync";
import { getDeviceTimezone } from "../utils/timezone";
import { uuid } from "../utils/ids";
import { apiFetch } from "./client";

export async function syncLocalQueue(): Promise<SyncResponse | null> {
  const entries = await listSyncableTransactions();
  if (entries.length === 0) {
    return null;
  }

  await markTransactionsSyncing(entries.map((entry) => entry.local_transaction_uuid));
  try {
    const response = await apiFetch<SyncResponse>("/sync", {
      method: "POST",
      body: JSON.stringify({
        sync_batch_id: uuid(),
        timezone: getDeviceTimezone(),
        entries: entries.map((entry) => ({
          local_transaction_uuid: entry.local_transaction_uuid,
          account_id: entry.account_id,
          client_revision: entry.client_revision,
          currency: entry.currency,
          amount_minor: entry.amount_minor,
          transaction_type: entry.transaction_type,
          category: entry.category,
          vendor: entry.vendor,
          description: entry.description,
          ledger_cutoff_at: entry.ledger_cutoff_at,
          match_state: "match_pending"
        }))
      })
    });
    await applySyncResults(response.results);
    return response;
  } catch (error) {
    await applySyncResults(
      entries.map((entry) => ({
        local_transaction_uuid: entry.local_transaction_uuid,
        status: "failed",
        error: error instanceof Error ? error.message : "sync_failed"
      }))
    );
    throw error;
  }
}

