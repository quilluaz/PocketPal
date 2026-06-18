import { Clock3, Home, PlusCircle, RefreshCw, Settings, WifiOff } from "lucide-react-native";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Pressable, SafeAreaView, StyleSheet, Text, View } from "react-native";
import { StatusBar } from "expo-status-bar";

import { fetchDashboard } from "./src/api/dashboard";
import { fetchRates } from "./src/api/fx";
import { syncLocalQueue } from "./src/api/sync";
import { enqueueTransaction, listQueuedTransactions, NewQueuedTransaction } from "./src/db/queue";
import { migrateLocalDatabase } from "./src/db/migrations";
import { AddTransactionScreen } from "./src/screens/AddTransactionScreen";
import { DashboardScreen } from "./src/screens/DashboardScreen";
import { PendingQueueScreen } from "./src/screens/PendingQueueScreen";
import { ReconnectBankScreen } from "./src/screens/ReconnectBankScreen";
import { SettingsScreen } from "./src/screens/SettingsScreen";
import { Dashboard } from "./src/types/dashboard";
import { RatesResponse } from "./src/types/money";
import { QueuedTransaction } from "./src/types/sync";
import { fallbackCurrencies } from "./src/utils/money";

type Screen = "dashboard" | "add" | "queue" | "reconnect" | "settings";

export default function App() {
  const [screen, setScreen] = useState<Screen>("dashboard");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [rates, setRates] = useState<RatesResponse | null>(null);
  const [queue, setQueue] = useState<QueuedTransaction[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currencies = rates?.currencies ?? fallbackCurrencies;
  const accounts = dashboard?.accounts ?? [];
  const hasReconnect = accounts.some((account) => account.action_required === "reconnect_bank");

  const refresh = useCallback(async () => {
    const localQueue = await listQueuedTransactions();
    setQueue(localQueue);
    try {
      const [nextRates, nextDashboard] = await Promise.all([fetchRates(), fetchDashboard()]);
      setRates(nextRates);
      setDashboard(nextDashboard);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Backend unavailable");
    }
  }, []);

  useEffect(() => {
    migrateLocalDatabase()
      .then(refresh)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Startup failed"));
  }, [refresh]);

  async function handleSync() {
    setSyncing(true);
    try {
      await syncLocalQueue();
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Sync failed");
      setQueue(await listQueuedTransactions());
    } finally {
      setSyncing(false);
    }
  }

  async function handleSave(transaction: NewQueuedTransaction) {
    await enqueueTransaction(transaction);
    setQueue(await listQueuedTransactions());
    setScreen("queue");
  }

  const content = useMemo(() => {
    if (screen === "add") {
      return <AddTransactionScreen accounts={accounts} currencies={currencies} onSave={handleSave} />;
    }
    if (screen === "queue") {
      return (
        <PendingQueueScreen
          currencies={currencies}
          items={queue}
          onSync={handleSync}
          syncing={syncing}
        />
      );
    }
    if (screen === "reconnect") {
      return <ReconnectBankScreen accounts={accounts} />;
    }
    if (screen === "settings") {
      return <SettingsScreen baseCurrency={dashboard?.base_currency ?? "PHP"} />;
    }
    return (
      <DashboardScreen
        currencies={currencies}
        dashboard={dashboard}
        onReconnect={() => setScreen("reconnect")}
        onSync={handleSync}
        queueCount={queue.length}
        syncing={syncing}
      />
    );
  }, [accounts, currencies, dashboard, queue, screen, syncing]);

  return (
    <SafeAreaView style={styles.shell}>
      <StatusBar style="light" />
      {error ? (
        <View style={styles.errorBar}>
          <WifiOff color="#ff9b8f" size={16} />
          <Text numberOfLines={1} style={styles.errorText}>
            {error}
          </Text>
          <Pressable onPress={refresh} style={styles.errorAction}>
            <RefreshCw color="#ffddd8" size={15} />
          </Pressable>
        </View>
      ) : null}
      <View style={styles.body}>{content}</View>
      <View style={styles.nav}>
        <TabButton
          active={screen === "dashboard"}
          icon="home"
          label="Home"
          onPress={() => setScreen("dashboard")}
        />
        <TabButton active={screen === "add"} icon="add" label="Add" onPress={() => setScreen("add")} />
        <TabButton
          active={screen === "queue"}
          icon="queue"
          label={`${queue.length}`}
          onPress={() => setScreen("queue")}
        />
        <TabButton
          active={screen === "reconnect"}
          attention={hasReconnect}
          icon="reconnect"
          label="Bank"
          onPress={() => setScreen("reconnect")}
        />
        <TabButton
          active={screen === "settings"}
          icon="settings"
          label="Prefs"
          onPress={() => setScreen("settings")}
        />
      </View>
    </SafeAreaView>
  );
}

type TabProps = {
  active: boolean;
  attention?: boolean;
  icon: "home" | "add" | "queue" | "reconnect" | "settings";
  label: string;
  onPress: () => void;
};

function TabButton({ active, attention, icon, label, onPress }: TabProps) {
  const color = active ? "#06110d" : attention ? "#f5b84b" : "#b9cec4";
  const iconMap = {
    add: PlusCircle,
    home: Home,
    queue: Clock3,
    reconnect: RefreshCw,
    settings: Settings
  };
  const Icon = iconMap[icon];
  return (
    <Pressable onPress={onPress} style={[styles.tab, active && styles.tabActive]}>
      <Icon color={color} size={19} strokeWidth={2.7} />
      <Text style={[styles.tabText, active && styles.tabTextActive, attention && !active && styles.tabTextAttention]}>
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  body: {
    flex: 1
  },
  errorAction: {
    alignItems: "center",
    height: 28,
    justifyContent: "center",
    width: 28
  },
  errorBar: {
    alignItems: "center",
    backgroundColor: "#3a1612",
    borderBottomColor: "#783028",
    borderBottomWidth: 1,
    flexDirection: "row",
    gap: 8,
    minHeight: 42,
    paddingHorizontal: 14
  },
  errorText: {
    color: "#ffddd8",
    flex: 1,
    fontSize: 13,
    fontWeight: "800"
  },
  nav: {
    alignItems: "center",
    backgroundColor: "#07100d",
    borderColor: "#20352c",
    borderRadius: 8,
    borderWidth: 1,
    bottom: 14,
    flexDirection: "row",
    gap: 6,
    left: 12,
    padding: 6,
    position: "absolute",
    right: 12
  },
  shell: {
    backgroundColor: "#07100d",
    flex: 1
  },
  tab: {
    alignItems: "center",
    borderRadius: 6,
    flex: 1,
    gap: 3,
    minHeight: 54,
    justifyContent: "center"
  },
  tabActive: {
    backgroundColor: "#dbffe8"
  },
  tabText: {
    color: "#b9cec4",
    fontSize: 11,
    fontWeight: "900"
  },
  tabTextActive: {
    color: "#06110d"
  },
  tabTextAttention: {
    color: "#f5b84b"
  }
});
