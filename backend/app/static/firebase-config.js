/**
 * Firebase Web SDK (npm `firebase` package) Connector for SpeakFlow
 * Project ID: shadowing-efcab | App: shadowing
 *
 * Uses standard npm bare module specifiers (`firebase/app`, `firebase/analytics`,
 * `firebase/auth`, `firebase/firestore`) resolved via npm/bundlers or `<script type="importmap">`:
 *
 *   import { initializeApp } from "firebase/app";
 *   import { getAnalytics } from "firebase/analytics";
 *   const app = initializeApp(firebaseConfig);
 *   const analytics = getAnalytics(app);
 */

import { initializeApp, getApps, deleteApp } from "firebase/app";
import { getAnalytics, isSupported as isAnalyticsSupported } from "firebase/analytics";
import { getAuth, signInAnonymously, GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { initializeFirestore, getFirestore, enableNetwork, doc, setDoc, getDoc } from "firebase/firestore";

export const DEFAULT_PROJECT_CONFIG = {
  apiKey: "AIzaSyCzMgjgyy3m9PZVCYoUgPYERActP9Wpji8",
  authDomain: "shadowing-efcab.firebaseapp.com",
  projectId: "shadowing-efcab",
  storageBucket: "shadowing-efcab.firebasestorage.app",
  messagingSenderId: "679028690937",
  appId: "1:679028690937:web:97def90cf97255ed2af728",
  measurementId: "G-KK84CSKQCP",
};

export function parseFirebaseConfigInput(rawInput) {
  if (!rawInput) return null;
  if (typeof rawInput === "object") return { ...DEFAULT_PROJECT_CONFIG, ...rawInput };
  const text = String(rawInput).trim();
  if (!text) return null;

  // Case 1: User pasted just the Firebase Web API key (AIzaSy...)
  if (/^AIza[0-9A-Za-z_-]{25,}$/.test(text)) {
    return { ...DEFAULT_PROJECT_CONFIG, apiKey: text };
  }

  // Case 2: Valid JSON object
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === "object") {
      return { ...DEFAULT_PROJECT_CONFIG, ...parsed };
    }
  } catch (_) {}

  // Case 3: Full npm / JS snippet from Firebase Console:
  // import { initializeApp } from "firebase/app";
  // const firebaseConfig = { apiKey: "...", projectId: "shadowing-efcab", ... };
  // const app = initializeApp(firebaseConfig);
  const extracted = { ...DEFAULT_PROJECT_CONFIG };
  const keys = ["apiKey", "authDomain", "projectId", "storageBucket", "messagingSenderId", "appId", "measurementId"];
  let foundAny = false;
  for (const k of keys) {
    const re = new RegExp(`["']?${k}["']?\\s*:\\s*(?:[^"'\\n,}]*?\\|\\|\\s*)?["']([^"']+)["']`);
    const m = text.match(re);
    if (m && m[1]) {
      extracted[k] = m[1].trim();
      foundAny = true;
    }
  }
  return foundAny ? extracted : null;
}

/**
 * Direct npm-style helper matching the Firebase Console snippet:
 *   const app = initializeApp(firebaseConfig);
 *   const analytics = getAnalytics(app);
 */
export async function initializeShadowingFirebaseApp(firebaseConfig) {
  const cfg = parseFirebaseConfigInput(firebaseConfig) || DEFAULT_PROJECT_CONFIG;
  if (getApps().length) {
    for (const existing of getApps()) {
      await deleteApp(existing);
    }
  }
  const app = initializeApp(cfg);
  let analytics = null;
  if (typeof window !== "undefined") {
    try {
      if (await isAnalyticsSupported()) {
        analytics = getAnalytics(app);
      }
    } catch (_) {}
  }
  return { app, analytics, config: cfg };
}

export class SpeakFlowFirebaseBridge {
  constructor() {
    this.app = null;
    this.analytics = null;
    this.auth = null;
    this.db = null;
    this.user = null;
    this.connected = false;
    this.onlineEnabled = false;
    const hasStorage = typeof localStorage !== "undefined";
    this.localUid =
      (hasStorage && localStorage.getItem("sf_anon_uid")) || `anon-${Math.random().toString(36).slice(2, 10)}`;
    if (hasStorage) {
      localStorage.setItem("sf_anon_uid", this.localUid);
    }
  }

  getStoredConfig() {
    try {
      if (typeof localStorage !== "undefined") {
        const raw = localStorage.getItem("sf_firebase_config");
        if (raw) {
          const cfg = parseFirebaseConfigInput(raw);
          if (cfg && cfg.apiKey) return cfg;
        }
      }
    } catch (_) {}
    return (typeof window !== "undefined" && window.FIREBASE_CONFIG) || null;
  }

  async saveFirebaseConfig(rawInput) {
    const parsed = parseFirebaseConfigInput(rawInput);
    if (!parsed || !parsed.apiKey) {
      return {
        connected: false,
        reason:
          "Pega el bloque npm 'const firebaseConfig = { ... }; const app = initializeApp(firebaseConfig);' de shadowing-efcab o tu apiKey (AIza...).",
      };
    }
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("sf_firebase_config", JSON.stringify(parsed));
    }
    return await this.init(parsed);
  }

  async init(customConfig = null) {
    const cfg = customConfig || this.getStoredConfig();
    if (!cfg || !cfg.apiKey || String(cfg.apiKey).startsWith("REPLACE_")) {
      this.connected = false;
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("speakflow:firebase-ready", {
            detail: { mode: "local-fallback", uid: this.localUid, projectId: DEFAULT_PROJECT_CONFIG.projectId },
          })
        );
      }
      return { connected: false, uid: this.localUid, reason: "no_api_key" };
    }
    try {
      const { app, analytics } = await initializeShadowingFirebaseApp(cfg);
      this.app = app;
      this.analytics = analytics;
      this.auth = getAuth(this.app);
      try {
        this.db = initializeFirestore(this.app, { experimentalAutoDetectLongPolling: true });
      } catch (_) {
        this.db = getFirestore(this.app);
      }
      this._firestoreFns = { doc, setDoc, getDoc, enableNetwork };
      this._authFns = { signInAnonymously, GoogleAuthProvider, signInWithPopup };

      await enableNetwork(this.db);
      this.onlineEnabled = true;

      const cred = await signInAnonymously(this.auth);
      this.user = cred.user;
      this.connected = true;

      await setDoc(
        doc(this.db, "users", this.user.uid),
        {
          uid: this.user.uid,
          isAnonymous: this.user.isAnonymous,
          projectId: cfg.projectId || "shadowing-efcab",
          appName: "shadowing",
          sdkMode: "npm-modular-v13",
          tier: (typeof localStorage !== "undefined" && localStorage.getItem("sf_freemium_tier")) || "free",
          onlineAccess: true,
          updatedAt: new Date().toISOString(),
        },
        { merge: true }
      );
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("speakflow:firebase-ready", {
            detail: {
              mode: "firebase-live",
              uid: this.user.uid,
              projectId: cfg.projectId || "shadowing-efcab",
              onlineEnabled: true,
              sdkMode: "npm",
            },
          })
        );
      }
      return {
        connected: true,
        uid: this.user.uid,
        projectId: cfg.projectId || "shadowing-efcab",
        onlineEnabled: true,
        sdkMode: "npm",
      };
    } catch (err) {
      this.connected = false;
      const errMsg = String(err && err.message ? err.message : err);
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("speakflow:firebase-ready", {
            detail: {
              mode: "local-fallback",
              uid: this.localUid,
              projectId: cfg.projectId || "shadowing-efcab",
              error: errMsg,
            },
          })
        );
      }
      return { connected: false, uid: this.localUid, reason: errMsg };
    }
  }

  async enableOnlineFirestore() {
    if (this.db && this._firestoreFns && this._firestoreFns.enableNetwork) {
      await this._firestoreFns.enableNetwork(this.db);
      this.onlineEnabled = true;
      return { onlineEnabled: true, connected: this.connected, uid: this.user ? this.user.uid : this.localUid };
    }
    return await this.init();
  }

  async syncAttempt(attemptData) {
    if (!this.connected || !this.db || !this.user) return;
    try {
      const { doc: docFn, setDoc: setDocFn } = this._firestoreFns;
      const attemptId = `att_${Date.now()}`;
      await setDocFn(docFn(this.db, "users", this.user.uid, "attempts", attemptId), {
        ...attemptData,
        createdAt: new Date().toISOString(),
      });
    } catch (_) {}
  }

  async syncSrsCard(cardData) {
    if (!this.connected || !this.db || !this.user) return;
    try {
      const { doc: docFn, setDoc: setDocFn } = this._firestoreFns;
      const cardId = cardData.card_id || `${cardData.scenario_id}_${cardData.phrase_id}`;
      await setDocFn(
        docFn(this.db, "users", this.user.uid, "srs_cards", cardId),
        { ...cardData, updatedAt: new Date().toISOString() },
        { merge: true }
      );
    } catch (_) {}
  }

  async syncRoleplay(roleplayData) {
    if (!this.connected || !this.db || !this.user) return;
    try {
      const { doc: docFn, setDoc: setDocFn } = this._firestoreFns;
      const sessionId = roleplayData.session_id || `rp_${Date.now()}`;
      await setDocFn(
        docFn(this.db, "users", this.user.uid, "roleplay_sessions", sessionId),
        { ...roleplayData, updatedAt: new Date().toISOString() },
        { merge: true }
      );
    } catch (_) {}
  }
}

if (typeof window !== "undefined") {
  window.initializeApp = initializeApp;
  window.getAnalytics = getAnalytics;
  window.SpeakFlowFirebase = new SpeakFlowFirebaseBridge();
  window.speakFlowFirebase = window.SpeakFlowFirebase;
  window.SpeakFlowFirebase.init();
}
