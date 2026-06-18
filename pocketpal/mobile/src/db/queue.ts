import { uuid } from "../utils/ids";
import { QueuedTransaction, SyncResult } from "../types/sync";
import { all, run } from "./sqlite";

export type NewQueuedTransaction = Omit<
  QueuedTransaction,
  "local_transaction_uuid" | "client_revision" | "sync_state" | "created_at" | "updated_at"
>;

export async function enqueueTransaction(input: NewQueuedTransaction): Promise<string> {
  const id = uuid();
  const now = new Date().toISOString();
  await run(
    `
    INSERT INTO local_transaction_queue (
      local_transaction_uuid, account_id, currency, amount_minor,
      transaction_type, category, vendor, description, ledger_cutoff_at,
      client_revision, sync_state, created_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'local_unsynced', ?, ?)
    `,
    [
      id,
      input.account_id,
      input.currency,
      input.amount_minor,
      input.transaction_type,
      input.category ?? null,
      input.vendor ?? null,
      input.description ?? null,
      input.ledger_cutoff_at,
      now,
      now
    ]
  );
  return id;
}

export async function listQueuedTransactions(): Promise<QueuedTransaction[]> {
  return all<QueuedTransaction>(`
    SELECT *
    FROM local_transaction_queue
    WHERE sync_state IN ('local_unsynced', 'failed', 'syncing')
    ORDER BY created_at DESC
  `);
}

export async function listSyncableTransactions(): Promise<QueuedTransaction[]> {
  return all<QueuedTransaction>(`
    SELECT *
    FROM local_transaction_queue
    WHERE sync_state IN ('local_unsynced', 'failed')
    ORDER BY created_at ASC
  `);
}

export async function markTransactionsSyncing(ids: string[]): Promise<void> {
  const now = new Date().toISOString();
  for (const id of ids) {
    await run(
      `
      UPDATE local_transaction_queue
      SET sync_state = 'syncing', last_error = NULL, updated_at = ?
      WHERE local_transaction_uuid = ?
      `,
      [now, id]
    );
  }
}

export async function applySyncResults(results: SyncResult[]): Promise<void> {
  const now = new Date().toISOString();
  for (const result of results) {
    if (["inserted", "updated", "already_synced"].includes(result.status)) {
      await run(
        "DELETE FROM local_transaction_queue WHERE local_transaction_uuid = ?",
        [result.local_transaction_uuid]
      );
      continue;
    }
    if (result.status === "stale_ignored") {
      await run(
        `
        UPDATE local_transaction_queue
        SET sync_state = 'failed', last_error = 'stale_ignored', updated_at = ?
        WHERE local_transaction_uuid = ?
        `,
        [now, result.local_transaction_uuid]
      );
      continue;
    }
    await run(
      `
      UPDATE local_transaction_queue
      SET sync_state = 'failed', last_error = ?, updated_at = ?
      WHERE local_transaction_uuid = ?
      `,
      [result.error ?? "sync_failed", now, result.local_transaction_uuid]
    );
  }
}

