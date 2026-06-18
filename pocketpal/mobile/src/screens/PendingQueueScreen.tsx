import { RefreshCw } from "lucide-react-native";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { PendingQueueList } from "../components/PendingQueueList";
import { CurrencyMeta } from "../types/money";
import { QueuedTransaction } from "../types/sync";

type Props = {
  items: QueuedTransaction[];
  currencies: CurrencyMeta[];
  syncing: boolean;
  onSync: () => void;
};

export function PendingQueueScreen({ items, currencies, syncing, onSync }: Props) {
  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View>
          <Text style={styles.eyebrow}>Offline Queue</Text>
          <Text style={styles.title}>Pending</Text>
        </View>
        <Pressable disabled={syncing} onPress={onSync} style={styles.syncButton}>
          <RefreshCw color="#06110d" size={18} strokeWidth={3} />
          <Text style={styles.syncText}>{syncing ? "Syncing" : "Sync"}</Text>
        </Pressable>
      </View>
      <PendingQueueList items={items} currencies={currencies} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: 18,
    padding: 18,
    paddingBottom: 112
  },
  eyebrow: {
    color: "#70d6ff",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase"
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  syncButton: {
    alignItems: "center",
    backgroundColor: "#7ad4a3",
    borderRadius: 8,
    flexDirection: "row",
    gap: 8,
    minHeight: 44,
    paddingHorizontal: 14
  },
  syncText: {
    color: "#06110d",
    fontSize: 14,
    fontWeight: "900"
  },
  title: {
    color: "#f7fff8",
    fontSize: 28,
    fontWeight: "900",
    lineHeight: 32
  }
});

