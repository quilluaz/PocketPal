import AsyncStorage from "@react-native-async-storage/async-storage";
import { KeyRound, Save } from "lucide-react-native";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

type Props = {
  baseCurrency: string;
};

export function SettingsScreen({ baseCurrency }: Props) {
  const [token, setToken] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem("supabase_token").then((value) => setToken(value ?? ""));
  }, []);

  async function save() {
    if (token) {
      await AsyncStorage.setItem("supabase_token", token);
    } else {
      await AsyncStorage.removeItem("supabase_token");
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 1400);
  }

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View>
        <Text style={styles.eyebrow}>Settings</Text>
        <Text style={styles.title}>PocketPal</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>Base Currency</Text>
        <Text style={styles.value}>{baseCurrency}</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.tokenLabel}>
          <KeyRound color="#70d6ff" size={18} />
          <Text style={styles.label}>Supabase Token</Text>
        </View>
        <TextInput
          autoCapitalize="none"
          onChangeText={setToken}
          placeholder="Bearer token"
          placeholderTextColor="#60736c"
          secureTextEntry
          style={styles.input}
          value={token}
        />
        <Pressable onPress={save} style={styles.button}>
          <Save color="#06110d" size={18} strokeWidth={3} />
          <Text style={styles.buttonText}>{saved ? "Saved" : "Save"}</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    backgroundColor: "#70d6ff",
    borderRadius: 8,
    flexDirection: "row",
    gap: 8,
    justifyContent: "center",
    minHeight: 48
  },
  buttonText: {
    color: "#06110d",
    fontSize: 15,
    fontWeight: "900"
  },
  card: {
    backgroundColor: "#111b18",
    borderColor: "#263d34",
    borderRadius: 8,
    borderWidth: 1,
    gap: 12,
    padding: 16
  },
  content: {
    gap: 16,
    padding: 18,
    paddingBottom: 112
  },
  eyebrow: {
    color: "#70d6ff",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase"
  },
  input: {
    backgroundColor: "#08110e",
    borderColor: "#284337",
    borderRadius: 8,
    borderWidth: 1,
    color: "#f7fff8",
    fontSize: 15,
    minHeight: 52,
    paddingHorizontal: 14
  },
  label: {
    color: "#9ab0a6",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase"
  },
  title: {
    color: "#f7fff8",
    fontSize: 28,
    fontWeight: "900",
    lineHeight: 32
  },
  tokenLabel: {
    alignItems: "center",
    flexDirection: "row",
    gap: 8
  },
  value: {
    color: "#f7fff8",
    fontSize: 22,
    fontWeight: "900"
  }
});

