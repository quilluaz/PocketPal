import { Clock3, TriangleAlert } from "lucide-react-native";
import { StyleSheet, Text, View } from "react-native";

import { QueuedTransaction } from "../types/sync";
import { CurrencyMeta } from "../types/money";
import { formatMoney } from "../utils/money";

type Props = {
  items: QueuedTransaction[];
  currencies: CurrencyMeta[];
};

export function PendingQueueList({ items, currencies }: Props) {
  if (items.length === 0) {
    return (
      <View style={styles.empty}>
        <Clock3 color="#70d6ff" size={24} />
        <Text style={styles.emptyText}>Queue clear</Text>
      </View>
    );
  }

  return (
    <View style={styles.list}>
      {items.map((item) => (
        <View key={item.local_transaction_uuid} style={styles.row}>
          <View style={styles.rowTop}>
            <Text style={styles.vendor}>{item.vendor || item.category || item.transaction_type}</Text>
            <Text style={styles.amount}>{formatMoney(item.amount_minor, item.currency, currencies)}</Text>
          </View>
          <View style={styles.rowBottom}>
            <Text style={styles.meta}>{item.sync_state}</Text>
            {item.last_error ? (
              <View style={styles.error}>
                <TriangleAlert color="#ff9b8f" size={13} />
                <Text style={styles.errorText}>{item.last_error}</Text>
              </View>
            ) : null}
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  amount: {
    color: "#f6fff8",
    fontSize: 16,
    fontWeight: "900"
  },
  empty: {
    alignItems: "center",
    borderColor: "#20332c",
    borderRadius: 8,
    borderWidth: 1,
    gap: 8,
    padding: 22
  },
  emptyText: {
    color: "#b7c9c0",
    fontSize: 14,
    fontWeight: "800"
  },
  error: {
    alignItems: "center",
    flexDirection: "row",
    gap: 4
  },
  errorText: {
    color: "#ff9b8f",
    fontSize: 12,
    fontWeight: "700"
  },
  list: {
    gap: 10
  },
  meta: {
    color: "#7f9990",
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase"
  },
  row: {
    backgroundColor: "#111b18",
    borderColor: "#22372f",
    borderRadius: 8,
    borderWidth: 1,
    padding: 14
  },
  rowBottom: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 10
  },
  rowTop: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12,
    justifyContent: "space-between"
  },
  vendor: {
    color: "#dff7e8",
    flex: 1,
    fontSize: 15,
    fontWeight: "800"
  }
});

