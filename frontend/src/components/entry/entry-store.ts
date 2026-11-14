"use client";

import { useSyncExternalStore } from "react";

const STORE = "nama-analyze-entry-v1";
const CHANGE = "nama:entry-change";
let memorySnapshot = "{}";
let canPersist = true;

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(CHANGE, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(CHANGE, callback);
  };
}

function getSnapshot() {
  if (!canPersist) return memorySnapshot;
  try {
    return window.localStorage.getItem(STORE) ?? memorySnapshot;
  } catch {
    return memorySnapshot;
  }
}

function parseSnapshot(snapshot: string): Record<string, unknown> {
  try {
    const value: unknown = JSON.parse(snapshot);
    return typeof value === "object" && value !== null && !Array.isArray(value)
      ? value as Record<string, unknown>
      : {};
  } catch {
    return {};
  }
}

export function useEntryState(): Record<string, unknown> {
  return parseSnapshot(useSyncExternalStore(subscribe, getSnapshot, () => "{}"));
}

function getPersistenceSnapshot() {
  if (!canPersist) return false;
  try {
    window.localStorage.getItem(STORE);
    return true;
  } catch {
    return false;
  }
}

export function useEntryPersistence(): boolean {
  return useSyncExternalStore(subscribe, getPersistenceSnapshot, () => true);
}

export function updateEntryState(patch: Record<string, unknown>) {
  memorySnapshot = JSON.stringify({ ...parseSnapshot(getSnapshot()), ...patch });
  try {
    window.localStorage.setItem(STORE, memorySnapshot);
    canPersist = true;
  } catch {
    // Keep the draft usable when storage is denied or full.
    canPersist = false;
  }
  window.dispatchEvent(new Event(CHANGE));
}
