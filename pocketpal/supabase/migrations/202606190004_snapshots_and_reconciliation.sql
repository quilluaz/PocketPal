CREATE TABLE IF NOT EXISTS public.account_balance_snapshots (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  account_id UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,

  currency CHAR(3) NOT NULL REFERENCES public.currencies(code),
  current_balance_minor BIGINT NOT NULL,
  available_balance_minor BIGINT NULL,

  base_currency CHAR(3) NOT NULL REFERENCES public.currencies(code),
  current_balance_minor_base BIGINT NULL,
  available_balance_minor_base BIGINT NULL,
  exchange_rate_to_base NUMERIC(20, 10) NULL,
  exchange_rate_as_of TIMESTAMPTZ NULL,

  provider_name TEXT NOT NULL,
  provider_snapshot_id TEXT NULL,
  idempotency_key TEXT NULL,

  as_of TIMESTAMPTZ NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (account_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_account_as_of
ON public.account_balance_snapshots (account_id, as_of DESC);

CREATE TABLE IF NOT EXISTS public.reconciliation_adjustments (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  account_id UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
  snapshot_id UUID NOT NULL REFERENCES public.account_balance_snapshots(id) ON DELETE CASCADE,

  adjustment_transaction_id UUID NOT NULL REFERENCES public.transactions(id),
  delta_amount_minor BIGINT NOT NULL,
  currency CHAR(3) NOT NULL REFERENCES public.currencies(code),

  status TEXT NOT NULL CHECK (
    status IN ('active', 'reversed', 'superseded')
  ) DEFAULT 'active',

  reversal_transaction_id UUID NULL REFERENCES public.transactions(id),

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (account_id, snapshot_id)
);

