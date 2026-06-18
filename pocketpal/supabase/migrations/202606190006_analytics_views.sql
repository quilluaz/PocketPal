CREATE OR REPLACE VIEW public.analytics_transactions
WITH (security_invoker = true) AS
SELECT
  id,
  user_id,
  account_id,
  currency,
  amount_minor,
  base_currency,
  amount_minor_base,
  ledger_cutoff_at,
  transaction_type,
  category,
  vendor,
  source
FROM public.transactions
WHERE affects_analytics = TRUE
  AND source <> 'system'
  AND transaction_type IN ('income', 'expense')
  AND ledger_status = 'cleared'
  AND amount_minor_base IS NOT NULL;

