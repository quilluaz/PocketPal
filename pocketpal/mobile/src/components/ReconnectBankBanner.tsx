import { AlertTriangle, RefreshCw } from "lucide-react-native";
import { Pressable, StyleSheet, Text, View } from "react-native";

type Props = {
  onPress?: () => void;
};

export function ReconnectBankBanner({ onPress }: Props) {
  return (
    <Pressable onPress={onPress} style={styles.banner}>
      <View style={styles.iconWrap}>
        <AlertTriangle color="#1b1002" size={18} strokeWidth={2.5} />
      </View>
      <View style={styles.copy}>
        <Text style={styles.title}>Action Required: Reconnect Bank</Text>
        <Text style={styles.subtitle}>Manual entries remain available</Text>
      </View>
      <RefreshCw color="#1b1002" size={18} strokeWidth={2.5} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  banner: {
    alignItems: "center",
    backgroundColor: "#f5b84b",
    borderRadius: 8,
    flexDirection: "row",
    gap: 12,
    padding: 12
  },
  copy: {
    flex: 1
  },
  iconWrap: {
    alignItems: "center",
    backgroundColor: "rgba(27,16,2,0.12)",
    borderRadius: 18,
    height: 32,
    justifyContent: "center",
    width: 32
  },
  subtitle: {
    color: "#382305",
    fontSize: 12,
    fontWeight: "700",
    marginTop: 2
  },
  title: {
    color: "#1b1002",
    fontSize: 14,
    fontWeight: "900"
  }
});

