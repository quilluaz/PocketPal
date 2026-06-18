CREATE TABLE IF NOT EXISTS public.transfer_groups (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  transfer_type VARCHAR NOT NULL CHECK (
    transfer_type IN ('same_currency', 'cross_currency')
  ),

  from_account_id UUID NOT NULL REFERENCES public.accounts(id),
  to_account_id UUID NOT NULL REFERENCES public.accounts(id),

  from_currency CHAR(3) NOT NULL REFERENCES public.currencies(code),
  to_currency CHAR(3) NOT NULL REFERENCES public.currencies(code),

  from_amount_minor BIGINT NOT NULL,
  to_amount_minor BIGINT NOT NULL,

  implied_rate NUMERIC(20, 10) NULL,
  market_rate NUMERIC(20, 10) NULL,

  spread_amount_minor_base BIGINT NULL,
  fee_amount_minor_base BIGINT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.transactions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  account_id UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
  transfer_group_id UUID NULL REFERENCES public.transfer_groups(id),

  currency CHAR(3) NOT NULL REFERENCES public.currencies(code),
  amount_minor BIGINT NOT NULL,

  base_currency CHAR(3) NOT NULL REFERENCES public.currencies(code),
  amount_minor_base BIGINT NULL,
  exchange_rate_to_base NUMERIC(20, 10) NULL,
  exchange_rate_source TEXT NULL,
  exchange_rate_as_of TIMESTAMPTZ NULL,
  fx_valuation_status VARCHAR NOT NULL CHECK (
    fx_valuation_status IN ('not_required', 'provisional', 'final', 'missing')
  ) DEFAULT 'not_required',

  source VARCHAR NOT NULL CHECK (
    source IN ('manual', 'sandbox_bank', 'system')
  ),

  provider_name TEXT NULL,
  external_transaction_id TEXT NULL,

  idempotency_key TEXT NULL,
  sync_batch_id UUID NULL,
  local_transaction_uuid UUID NULL,
  client_revision INTEGER NOT NULL DEFAULT 1 CHECK (client_revision > 0),

  ledger_status VARCHAR NOT NULL CHECK (
    ledger_status IN ('pending', 'cleared', 'adjusted')
  ),

  match_state VARCHAR NOT NULL CHECK (
    match_state IN ('not_required', 'match_pending', 'matched', 'unmatched_review')
  ) DEFAULT 'not_required',

  transaction_type VARCHAR NOT NULL CHECK (
    transaction_type IN (
      'income',
      'expense',
      'transfer',
      'reconciliation',
      'initial_balance'
    )
  ),

  category TEXT NULL,
  vendor TEXT NULL,
  description TEXT NULL,

  ledger_cutoff_at TIMESTAMPTZ NOT NULL,
  server_received_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  is_backfilled BOOLEAN NOT NULL DEFAULT FALSE,
  requires_reconciliation_review BOOLEAN NOT NULL DEFAULT FALSE,

  reversal_of_transaction_id UUID NULL REFERENCES public.transactions(id),
  reversed_at TIMESTAMPTZ NULL,
  superseded_by_transaction_id UUID NULL REFERENCES public.transactions(id),

  affects_ledger BOOLEAN NOT NULL DEFAULT TRUE,
  affects_analytics BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS transactions_idempotency_unique
ON public.transactions (user_id, source, idempotency_key)
WHERE idempotency_key IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS one_initial_balance_per_account
ON public.transactions (account_id)
WHERE transaction_type = 'initial_balance';

CREATE INDEX IF NOT EXISTS idx_transactions_user_account_cutoff
ON public.transactions (user_id, account_id, ledger_cutoff_at);

CREATE INDEX IF NOT EXISTS idx_transactions_user_analytics
ON public.transactions (user_id, affects_analytics, ledger_status, transaction_type);

CREATE INDEX IF NOT EXISTS idx_transactions_external_transaction
ON public.transactions (provider_name, external_transaction_id)
WHERE external_transaction_id IS NOT NULL;

CREATE TRIGGER set_transactions_updated_at
BEFORE UPDATE ON public.transactions
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

