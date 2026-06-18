export type DashboardAccount = {
  account_id: string;
  account_name: string;
  currency: string;
  oauth_status: string;
  reconciliation_enabled: boolean;
  projected_balance_minor_base: number;
  settled_balance_minor_base: number;
  pending_manual_minor_base: number;
  action_required: "reconnect_bank" | null;
};

export type Dashboard = {
  base_currency: string;
  projected_balance_minor_base: number;
  settled_balance_minor_base: number;
  pending_manual_minor_base: number;
  accounts: DashboardAccount[];
  kpis: {
    monthly_income_minor_base: number;
    monthly_expense_minor_base: number;
    burn_rate_daily_minor_base: number;
  };
};

