import { RefreshCw } from "lucide-react-native";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { DashboardAccount } from "../types/dashboard";

type Props = {
  accounts: DashboardAccount[];
};

export function ReconnectBankScreen({ accounts }: Props) {
  const affected = accounts.filter((account) => account.action_required === "reconnect_bank");

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View>
        <Text style={styles.eyebrow}>Bank Access</Text>
        <Text style={styles.title}>Reconnect</Text>
      </View>
      {affected.length === 0 ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>All connected</Text>
        </View>
      ) : (
        affected.map((account) => (
          <View key={account.account_id} style={styles.card}>
            <View style={styles.row}>
              <View>
                <Text style={styles.cardTitle}>{account.account_name}</Text>
                <Text style={styles.meta}>{account.oauth_status}</Text>
              </View>
              <Pressable style={styles.button}>
                <RefreshCw color="#06110d" size={18} strokeWidth={3} />
                <Text style={styles.buttonText}>Reconnect</Text>
              </Pressable>
            </View>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    backgroundColor: "#f5b84b",
    borderRadius: 8,
    flexDirection: "row",
    gap: 8,
    minHeight: 42,
    paddingHorizontal: 12
  },
  buttonText: {
    color: "#06110d",
    fontSize: 13,
    fontWeight: "900"
  },
  card: {
    backgroundColor: "#111b18",
    borderColor: "#2b453a",
    borderRadius: 8,
    borderWidth: 1,
    padding: 16
  },
  cardTitle: {
    color: "#f7fff8",
    fontSize: 17,
    fontWeight: "900"
  },
  content: {
    gap: 16,
    padding: 18,
    paddingBottom: 112
  },
  eyebrow: {
    color: "#f5b84b",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase"
  },
  meta: {
    color: "#a8bbb2",
    fontSize: 13,
    fontWeight: "700",
    marginTop: 4
  },
  row: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  title: {
    color: "#f7fff8",
    fontSize: 28,
    fontWeight: "900",
    lineHeight: 32
  }
});

