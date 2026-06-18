import { Plus } from "lucide-react-native";
import { useEffect, useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { DashboardAccount } from "../types/dashboard";
import { CurrencyMeta } from "../types/money";
import { NewQueuedTransaction } from "../db/queue";
import { currencyExponent, majorToMinor } from "../utils/money";

type Props = {
  accounts: DashboardAccount[];
  currencies: CurrencyMeta[];
  onSubmit: (transaction: NewQueuedTransaction) => Promise<void>;
};

export function TransactionForm({ accounts, currencies, onSubmit }: Props) {
  const [accountId, setAccountId] = useState(accounts[0]?.account_id ?? "");
  const [currency, setCurrency] = useState(accounts[0]?.currency ?? "PHP");
  const [type, setType] = useState<"expense" | "income">("expense");
  const [amount, setAmount] = useState("");
  const [vendor, setVendor] = useState("");
  const [category, setCategory] = useState("food");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!accountId && accounts[0]) {
      setAccountId(accounts[0].account_id);
      setCurrency(accounts[0].currency);
    }
  }, [accountId, accounts]);

  const currencyOptions = useMemo(
    () => Array.from(new Set([currency, "PHP", "USD", "JPY", "KWD"])),
    [currency]
  );

  const disabled = !accountId || !amount || saving;

  async function submit() {
    if (disabled) {
      return;
    }
    setSaving(true);
    const exponent = currencyExponent(currency, currencies);
    const unsignedMinor = Math.abs(majorToMinor(amount, exponent));
    await onSubmit({
      account_id: accountId,
      currency,
      amount_minor: type === "expense" ? -unsignedMinor : unsignedMinor,
      transaction_type: type,
      category: category || null,
      vendor: vendor || null,
      description: description || null,
      ledger_cutoff_at: new Date().toISOString()
    });
    setAmount("");
    setVendor("");
    setDescription("");
    setSaving(false);
  }

  return (
    <View style={styles.form}>
      <View style={styles.segment}>
        {(["expense", "income"] as const).map((item) => (
          <Pressable
            key={item}
            onPress={() => setType(item)}
            style={[styles.segmentButton, type === item && styles.segmentButtonActive]}
          >
            <Text style={[styles.segmentText, type === item && styles.segmentTextActive]}>{item}</Text>
          </Pressable>
        ))}
      </View>

      <TextInput
        keyboardType="decimal-pad"
        onChangeText={setAmount}
        placeholder="0"
        placeholderTextColor="#60736c"
        style={styles.amountInput}
        value={amount}
      />

      <View style={styles.pills}>
        {currencyOptions.map((item) => (
          <Pressable
            key={item}
            onPress={() => setCurrency(item)}
            style={[styles.pill, currency === item && styles.pillActive]}
          >
            <Text style={[styles.pillText, currency === item && styles.pillTextActive]}>{item}</Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Account</Text>
        <View style={styles.pills}>
          {accounts.map((account) => (
            <Pressable
              key={account.account_id}
              onPress={() => {
                setAccountId(account.account_id);
                setCurrency(account.currency);
              }}
              style={[styles.pill, accountId === account.account_id && styles.pillActive]}
            >
              <Text style={[styles.pillText, accountId === account.account_id && styles.pillTextActive]}>
                {account.account_name}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      <TextInput
        onChangeText={setVendor}
        placeholder="Vendor"
        placeholderTextColor="#60736c"
        style={styles.input}
        value={vendor}
      />
      <TextInput
        onChangeText={setCategory}
        placeholder="Category"
        placeholderTextColor="#60736c"
        style={styles.input}
        value={category}
      />
      <TextInput
        onChangeText={setDescription}
        placeholder="Description"
        placeholderTextColor="#60736c"
        style={styles.input}
        value={description}
      />

      <Pressable disabled={disabled} onPress={submit} style={[styles.submit, disabled && styles.submitDisabled]}>
        <Plus color="#06110d" size={18} strokeWidth={3} />
        <Text style={styles.submitText}>{saving ? "Saving" : "Add"}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  amountInput: {
    color: "#f7fff8",
    fontSize: 44,
    fontWeight: "900",
    minHeight: 72,
    paddingVertical: 4
  },
  fieldGroup: {
    gap: 8
  },
  form: {
    gap: 14
  },
  input: {
    backgroundColor: "#111b18",
    borderColor: "#243b32",
    borderRadius: 8,
    borderWidth: 1,
    color: "#f7fff8",
    fontSize: 16,
    minHeight: 52,
    paddingHorizontal: 14
  },
  label: {
    color: "#8aa39a",
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase"
  },
  pill: {
    borderColor: "#2b453a",
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 9
  },
  pillActive: {
    backgroundColor: "#dbffe8",
    borderColor: "#dbffe8"
  },
  pillText: {
    color: "#b8cec4",
    fontSize: 13,
    fontWeight: "800"
  },
  pillTextActive: {
    color: "#06110d"
  },
  pills: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  segment: {
    backgroundColor: "#101916",
    borderRadius: 8,
    flexDirection: "row",
    padding: 4
  },
  segmentButton: {
    alignItems: "center",
    borderRadius: 6,
    flex: 1,
    paddingVertical: 10
  },
  segmentButtonActive: {
    backgroundColor: "#70d6ff"
  },
  segmentText: {
    color: "#9ab0a6",
    fontSize: 14,
    fontWeight: "900",
    textTransform: "uppercase"
  },
  segmentTextActive: {
    color: "#06110d"
  },
  submit: {
    alignItems: "center",
    backgroundColor: "#7ad4a3",
    borderRadius: 8,
    flexDirection: "row",
    gap: 8,
    justifyContent: "center",
    minHeight: 52
  },
  submitDisabled: {
    opacity: 0.45
  },
  submitText: {
    color: "#06110d",
    fontSize: 16,
    fontWeight: "900"
  }
});

