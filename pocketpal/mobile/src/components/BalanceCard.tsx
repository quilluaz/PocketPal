import Animated, { FadeIn, Layout } from "react-native-reanimated";
import { StyleSheet, Text, View } from "react-native";

import { Dashboard } from "../types/dashboard";
import { CurrencyMeta } from "../types/money";
import { formatMoney } from "../utils/money";
import { ReconnectBankBanner } from "./ReconnectBankBanner";

type Props = {
  dashboard: Dashboard | null;
  currencies: CurrencyMeta[];
  onReconnectPress: () => void;
};

export function BalanceCard({ dashboard, currencies, onReconnectPress }: Props) {
  const base = dashboard?.base_currency ?? "PHP";
  const needsReconnect = dashboard?.accounts.some((account) => account.action_required === "reconnect_bank");

  return (
    <Animated.View entering={FadeIn.duration(320)} layout={Layout.springify()} style={styles.card}>
      <Text style={styles.label}>Projected Balance</Text>
      <Text adjustsFontSizeToFit numberOfLines={1} style={styles.amount}>
        {formatMoney(dashboard?.projected_balance_minor_base ?? 0, base, currencies)}
      </Text>
      <View style={styles.row}>
        <Text style={styles.subValue}>
          Settled: {formatMoney(dashboard?.settled_balance_minor_base ?? 0, base, currencies)}
        </Text>
        <Text style={styles.dot}>|</Text>
        <Text style={styles.subValue}>
          Pending: {formatMoney(dashboard?.pending_manual_minor_base ?? 0, base, currencies)}
        </Text>
      </View>
      {needsReconnect ? (
        <View style={styles.bannerWrap}>
          <ReconnectBankBanner onPress={onReconnectPress} />
        </View>
      ) : null}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  amount: {
    color: "#f7fff8",
    fontSize: 42,
    fontWeight: "900",
    lineHeight: 48,
    marginTop: 8
  },
  bannerWrap: {
    marginTop: 18
  },
  card: {
    backgroundColor: "#102019",
    borderColor: "#24513f",
    borderRadius: 8,
    borderWidth: 1,
    padding: 20
  },
  dot: {
    color: "#7ad4a3",
    fontSize: 14,
    fontWeight: "800"
  },
  label: {
    color: "#7ad4a3",
    fontSize: 13,
    fontWeight: "800",
    textTransform: "uppercase"
  },
  row: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 10
  },
  subValue: {
    color: "#c2d8cc",
    fontSize: 13,
    fontWeight: "700"
  }
});
