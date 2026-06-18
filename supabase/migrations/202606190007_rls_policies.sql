ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.account_connection_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transfer_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.account_balance_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reconciliation_adjustments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.currencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exchange_rates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Authenticated users can read currencies" ON public.currencies;
CREATE POLICY "Authenticated users can read currencies"
ON public.currencies
FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Authenticated users can read exchange rates" ON public.exchange_rates;
CREATE POLICY "Authenticated users can read exchange rates"
ON public.exchange_rates
FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Users can select own preferences" ON public.user_preferences;
CREATE POLICY "Users can select own preferences"
ON public.user_preferences
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own preferences" ON public.user_preferences;
CREATE POLICY "Users can insert own preferences"
ON public.user_preferences
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own preferences" ON public.user_preferences;
CREATE POLICY "Users can update own preferences"
ON public.user_preferences
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own preferences" ON public.user_preferences;
CREATE POLICY "Users can delete own preferences"
ON public.user_preferences
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can select own accounts" ON public.accounts;
CREATE POLICY "Users can select own accounts"
ON public.accounts
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own accounts" ON public.accounts;
CREATE POLICY "Users can insert own accounts"
ON public.accounts
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own accounts" ON public.accounts;
CREATE POLICY "Users can update own accounts"
ON public.accounts
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own accounts" ON public.accounts;
CREATE POLICY "Users can delete own accounts"
ON public.accounts
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can select own connection events" ON public.account_connection_events;
CREATE POLICY "Users can select own connection events"
ON public.account_connection_events
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own connection events" ON public.account_connection_events;
CREATE POLICY "Users can insert own connection events"
ON public.account_connection_events
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own connection events" ON public.account_connection_events;
CREATE POLICY "Users can update own connection events"
ON public.account_connection_events
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own connection events" ON public.account_connection_events;
CREATE POLICY "Users can delete own connection events"
ON public.account_connection_events
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can select own transfer groups" ON public.transfer_groups;
CREATE POLICY "Users can select own transfer groups"
ON public.transfer_groups
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own transfer groups" ON public.transfer_groups;
CREATE POLICY "Users can insert own transfer groups"
ON public.transfer_groups
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own transfer groups" ON public.transfer_groups;
CREATE POLICY "Users can update own transfer groups"
ON public.transfer_groups
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own transfer groups" ON public.transfer_groups;
CREATE POLICY "Users can delete own transfer groups"
ON public.transfer_groups
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can select own transactions" ON public.transactions;
CREATE POLICY "Users can select own transactions"
ON public.transactions
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own transactions" ON public.transactions;
CREATE POLICY "Users can insert own transactions"
ON public.transactions
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own transactions" ON public.transactions;
CREATE POLICY "Users can update own transactions"
ON public.transactions
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own transactions" ON public.transactions;
CREATE POLICY "Users can delete own transactions"
ON public.transactions
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can select own snapshots" ON public.account_balance_snapshots;
CREATE POLICY "Users can select own snapshots"
ON public.account_balance_snapshots
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own snapshots" ON public.account_balance_snapshots;
CREATE POLICY "Users can insert own snapshots"
ON public.account_balance_snapshots
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own snapshots" ON public.account_balance_snapshots;
CREATE POLICY "Users can update own snapshots"
ON public.account_balance_snapshots
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own snapshots" ON public.account_balance_snapshots;
CREATE POLICY "Users can delete own snapshots"
ON public.account_balance_snapshots
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can select own reconciliation adjustments" ON public.reconciliation_adjustments;
CREATE POLICY "Users can select own reconciliation adjustments"
ON public.reconciliation_adjustments
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own reconciliation adjustments" ON public.reconciliation_adjustments;
CREATE POLICY "Users can insert own reconciliation adjustments"
ON public.reconciliation_adjustments
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own reconciliation adjustments" ON public.reconciliation_adjustments;
CREATE POLICY "Users can update own reconciliation adjustments"
ON public.reconciliation_adjustments
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own reconciliation adjustments" ON public.reconciliation_adjustments;
CREATE POLICY "Users can delete own reconciliation adjustments"
ON public.reconciliation_adjustments
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

