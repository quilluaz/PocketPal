import { ArrowUpRight, RefreshCw, WalletCards } from "lucide-react-native";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import Animated, { FadeInDown } from "react-native-reanimated";

import { BalanceCard } from "../components/BalanceCard";
import { Dashboard } from "../types/dashboard";
import { CurrencyMeta } from "../types/money";
import { formatMoney } from "../utils/money";

type Props = {
  dashboard: Dashboard | null;
  currencies: CurrencyMeta[];
  queueCount: number;
  syncing: boolean;
  onSync: () => void;
  onReconnect: () => void;
};

export function DashboardScreen({ dashboard, currencies, queueCount, syncing, onSync, onReconnect }: Props) {
  const base = dashboard?.base_currency ?? "PHP";

  return (
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <View>
          <Text style={styles.eyebrow}>PocketPal</Text>
          <Text style={styles.title}>Finance HQ</Text>
        </View>
        <Pressable onPress={onSync} style={styles.iconButton}>
          <RefreshCw color="#e9fff1" size={20} />
        </Pressable>
      </View>

      <BalanceCard dashboard={dashboard} currencies={currencies} onReconnectPress={onReconnect} />

      <View style={styles.kpiGrid}>
        <View style={styles.kpi}>
          <Text style={styles.kpiLabel}>Income</Text>
          <Text adjustsFontSizeToFit numberOfLines={1} style={styles.kpiValue}>
            {formatMoney(dashboard?.kpis.monthly_income_minor_base ?? 0, base, currencies)}
          </Text>
        </View>
        <View style={styles.kpi}>
          <Text style={styles.kpiLabel}>Expense</Text>
          <Text adjustsFontSizeToFit numberOfLines={1} style={styles.kpiValue}>
            {formatMoney(dashboard?.kpis.monthly_expense_minor_base ?? 0, base, currencies)}
          </Text>
        </View>
        <View style={styles.kpi}>
          <Text style={styles.kpiLabel}>Daily Burn</Text>
          <Text adjustsFontSizeToFit numberOfLines={1} style={styles.kpiValue}>
            {formatMoney(dashboard?.kpis.burn_rate_daily_minor_base ?? 0, base, currencies)}
          </Text>
        </View>
      </View>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Accounts</Text>
        <Text style={styles.queueText}>{syncing ? "Syncing" : `${queueCount} queued`}</Text>
      </View>

      <View style={styles.accounts}>
        {(dashboard?.accounts ?? []).map((account, index) => (
          <Animated.View
            entering={FadeInDown.delay(index * 70)}
            key={account.account_id}
            style={styles.account}
          >
            <View style={styles.accountIcon}>
              <WalletCards color="#7ad4a3" size={19} />
            </View>
            <View style={styles.accountBody}>
              <Text style={styles.accountName}>{account.account_name}</Text>
              <Text style={styles.accountMeta}>
                {account.oauth_status} | {account.currency}
              </Text>
            </View>
            <View style={styles.accountAmount}>
              <Text adjustsFontSizeToFit numberOfLines={1} style={styles.accountValue}>
                {formatMoney(account.projected_balance_minor_base, base, currencies)}
              </Text>
              {account.action_required ? <ArrowUpRight color="#f5b84b" size={16} /> : null}
            </View>
          </Animated.View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  account: {
    alignItems: "center",
    backgroundColor: "#111b18",
    borderColor: "#22372f",
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: "row",
    gap: 12,
    padding: 14
  },
  accountAmount: {
    alignItems: "flex-end",
    flexShrink: 1,
    gap: 4,
    maxWidth: "42%"
  },
  accountBody: {
    flex: 1
  },
  accountIcon: {
    alignItems: "center",
    backgroundColor: "#182d23",
    borderRadius: 8,
    height: 38,
    justifyContent: "center",
    width: 38
  },
  accountMeta: {
    color: "#82998f",
    fontSize: 12,
    fontWeight: "700",
    marginTop: 4
  },
  accountName: {
    color: "#eefcf2",
    fontSize: 15,
    fontWeight: "900"
  },
  accounts: {
    gap: 10
  },
  accountValue: {
    color: "#e8fff0",
    fontSize: 15,
    fontWeight: "900"
  },
  content: {
    gap: 18,
    padding: 18,
    paddingBottom: 112
  },
  eyebrow: {
    color: "#7ad4a3",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase"
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  iconButton: {
    alignItems: "center",
    backgroundColor: "#17261f",
    borderColor: "#2a463a",
    borderRadius: 8,
    borderWidth: 1,
    height: 44,
    justifyContent: "center",
    width: 44
  },
  kpi: {
    backgroundColor: "#101916",
    borderColor: "#23372f",
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    minWidth: 96,
    padding: 12
  },
  kpiGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10
  },
  kpiLabel: {
    color: "#88a096",
    fontSize: 11,
    fontWeight: "900",
    textTransform: "uppercase"
  },
  kpiValue: {
    color: "#e9fff1",
    fontSize: 16,
    fontWeight: "900",
    marginTop: 8
  },
  queueText: {
    color: "#70d6ff",
    fontSize: 12,
    fontWeight: "900"
  },
  sectionHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  sectionTitle: {
    color: "#f7fff8",
    fontSize: 18,
    fontWeight: "900"
  },
  title: {
    color: "#f7fff8",
    fontSize: 28,
    fontWeight: "900",
    lineHeight: 32
  }
});
