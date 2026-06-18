import * as SQLite from "expo-sqlite";

let dbPromise: Promise<SQLite.SQLiteDatabase> | null = null;

export function getDatabase(): Promise<SQLite.SQLiteDatabase> {
  if (!dbPromise) {
    dbPromise = SQLite.openDatabaseAsync("pocketpal.db");
  }
  return dbPromise;
}

export async function run(sql: string, params: SQLite.SQLiteBindParams = []): Promise<void> {
  const db = await getDatabase();
  await db.runAsync(sql, params);
}

export async function all<T>(sql: string, params: SQLite.SQLiteBindParams = []): Promise<T[]> {
  const db = await getDatabase();
  return db.getAllAsync<T>(sql, params);
}

