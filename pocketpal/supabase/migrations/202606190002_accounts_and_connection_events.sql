CREATE TABLE IF NOT EXISTS public.accounts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  account_name TEXT NOT NULL,
  account_type TEXT NOT NULL DEFAULT 'depository',
  currency CHAR(3) NOT NULL REFERENCES public.currencies(code),

  provider_name TEXT NOT NULL DEFAULT 'manual',
  provider_account_id TEXT NULL,

  oauth_status VARCHAR NOT NULL CHECK (
    oauth_status IN (
      'active',
      'reconnect_required',
      'pending_expiration',
      'disconnected',
      'sandbox_error'
    )
  ) DEFAULT 'active',

  oauth_error_code TEXT NULL,
  oauth_error_message TEXT NULL,
  oauth_last_failed_at TIMESTAMPTZ NULL,

  reconciliation_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  initialized_at TIMESTAMPTZ NULL,
  last_reconciled_snapshot_at TIMESTAMPTZ NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS accounts_provider_account_unique
ON public.accounts (user_id, provider_name, provider_account_id)
WHERE provider_account_id IS NOT NULL;

CREATE TRIGGER set_accounts_updated_at
BEFORE UPDATE ON public.accounts
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE IF NOT EXISTS public.account_connection_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  account_id UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,

  provider_name TEXT NOT NULL,
  event_type TEXT NOT NULL,
  provider_error_code TEXT NULL,
  provider_payload JSONB NOT NULL,

  handled BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

