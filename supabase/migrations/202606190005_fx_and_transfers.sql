INSERT INTO public.exchange_rates
(base_currency, quote_currency, rate, rate_date, source)
VALUES
('PHP', 'USD', 56.8500000000, CURRENT_DATE, 'seed'),
('PHP', 'JPY', 0.3900000000, CURRENT_DATE, 'seed'),
('PHP', 'KWD', 185.0000000000, CURRENT_DATE, 'seed'),
('PHP', 'PHP', 1.0000000000, CURRENT_DATE, 'seed')
ON CONFLICT DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_exchange_rates_lookup
ON public.exchange_rates (base_currency, quote_currency, rate_date DESC);

CREATE INDEX IF NOT EXISTS idx_transfer_groups_user_created
ON public.transfer_groups (user_id, created_at DESC);

