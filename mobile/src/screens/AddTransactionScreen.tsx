import { ScrollView, StyleSheet, Text, View } from "react-native";

import { TransactionForm } from "../components/TransactionForm";
import { NewQueuedTransaction } from "../db/queue";
import { DashboardAccount } from "../types/dashboard";
import { CurrencyMeta } from "../types/money";

type Props = {
  accounts: DashboardAccount[];
  currencies: CurrencyMeta[];
  onSave: (transaction: NewQueuedTransaction) => Promise<void>;
};

export function AddTransactionScreen({ accounts, currencies, onSave }: Props) {
  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <View>
        <Text style={styles.eyebrow}>Ledger Entry</Text>
        <Text style={styles.title}>Add Transaction</Text>
      </View>
      {accounts.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No accounts</Text>
        </View>
      ) : (
        <TransactionForm accounts={accounts} currencies={currencies} onSubmit={onSave} />
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: 22,
    padding: 18,
    paddingBottom: 112
  },
  empty: {
    borderColor: "#253b32",
    borderRadius: 8,
    borderWidth: 1,
    padding: 18
  },
  emptyText: {
    color: "#c5d8cf",
    fontSize: 16,
    fontWeight: "800"
  },
  eyebrow: {
    color: "#70d6ff",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase"
  },
  title: {
    color: "#f7fff8",
    fontSize: 28,
    fontWeight: "900",
    lineHeight: 32
  }
});

