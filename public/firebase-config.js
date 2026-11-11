/**
 * Firebase Web SDK v11 Connector for SpeakFlow (Project: agy-sandbox-488016):
 *  - Accepts raw JS snippet (`const firebaseConfig = { ... }`), JSON, or just the `apiKey` (`AIza...`)
 *  - Service 1: Firebase Authentication (Anonymous Auth + optional Google Web Auth)
 *  - Service 2: Cloud Firestore Database with explicit `enableNetwork(db)` (Online access to Firestore)
 *  - Service 3: Firebase Hosting + Google Cloud / Gemini Free Tier integration
 */

export const DEFAULT_PROJECT_CONFIG = {
  apiKey: "",
  authDomain: "agy-sandbox-488016.firebaseapp.com",
  projectId: "agy-sandbox-488016",
  storageBucket: "agy-sandbox-488016.firebasestorage.app",
  messagingSenderId: "1094302132782",
  appId: "1:1094302132782:web:e173010681f04a98a98dbf",
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

  // Case 3: Full JS snippet from Firebase Console ("Step 2: Add Firebase SDK")
  // e.g. const firebaseConfig = { apiKey: "...", authDomain: "...", ... };
  const extracted = { ...DEFAULT_PROJECT_CONFIG };
  const keys = ["apiKey", "authDomain", "projectId", "storageBucket", "messagingSenderId", "appId", "measurementId"];
  let foundAny = false;
  for (const k of keys) {
    const re = new RegExp(`["']?${k}["']?\\s*:\\s*["']([^"']+)["']`);
    const m = text.match(re);
    if (m && m[1]) {
      extracted[k] = m[1].trim();
      foundAny = true;
    }
  }
  return foundAny ? extracted : null;
}

export class SpeakFlowFirebaseBridge {
  constructor() {
    this.app = null;
    this.auth = null;
    this.db = null;
    this.user = null;
    this.connected = false;
    this.onlineEnabled = false;
    this.localUid = localStorage.getItem("sf_anon_uid") || `anon-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem("sf_anon_uid", this.localUid);
  }

  getStoredConfig() {
    try {
      const raw = localStorage.getItem("sf_firebase_config");
      if (raw) {
        const cfg = parseFirebaseConfigInput(raw);
        if (cfg && cfg.apiKey) return cfg;
      }
    } catch (_) {}
    return window.FIREBASE_CONFIG || null;
  }

  async saveFirebaseConfig(rawInput) {
    const parsed = parseFirebaseConfigInput(rawInput);
    if (!parsed || !parsed.apiKey) {
      return {
        connected: false,
        reason: "Pega el bloque 'const firebaseConfig = { ... }' del Paso 2 de Firebase o tu apiKey (AIza...).",
      };
    }
    localStorage.setItem("sf_firebase_config", JSON.stringify(parsed));
    return await this.init(parsed);
  }

  async init(customConfig = null) {
    const cfg = customConfig || this.getStoredConfig();
    if (!cfg || !cfg.apiKey || String(cfg.apiKey).startsWith("REPLACE_")) {
      this.connected = false;
      window.dispatchEvent(
        new CustomEvent("speakflow:firebase-ready", {
          detail: { mode: "local-fallback", uid: this.localUid, projectId: DEFAULT_PROJECT_CONFIG.projectId },
        })
      );
      return { connected: false, uid: this.localUid, reason: "no_api_key" };
    }
    try {
      const [
        { initializeApp, getApps, deleteApp },
        { getAuth, signInAnonymously, GoogleAuthProvider, signInWithPopup },
        { initializeFirestore, getFirestore, enableNetwork, doc, setDoc, getDoc },
      ] = await Promise.all([
        import("https://www.gstatic.com/firebasejs/11.0.2/firebase-app.js"),
        import("https://www.gstatic.com/firebasejs/11.0.2/firebase-auth.js"),
        import("https://www.gstatic.com/firebasejs/11.0.2/firebase-firestore.js"),
      ]);

      if (getApps().length && customConfig) {
        for (const existing of getApps()) {
          await deleteApp(existing);
        }
      }

      this.app = getApps().length ? getApps()[0] : initializeApp(cfg);
      this.auth = getAuth(this.app);
      try {
        this.db = initializeFirestore(this.app, { experimentalAutoDetectLongPolling: true });
      } catch (_) {
        this.db = getFirestore(this.app);
      }
      this._firestoreFns = { doc, setDoc, getDoc, enableNetwork };
      this._authFns = { signInAnonymously, GoogleAuthProvider, signInWithPopup };

      // Enable online access to Firestore explicitly
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
          projectId: cfg.projectId,
          tier: localStorage.getItem("sf_freemium_tier") || "free",
          onlineAccess: true,
          updatedAt: new Date().toISOString(),
        },
        { merge: true }
      );
      window.dispatchEvent(
        new CustomEvent("speakflow:firebase-ready", {
          detail: {
            mode: "firebase-live",
            uid: this.user.uid,
            projectId: cfg.projectId,
            onlineEnabled: true,
          },
        })
      );
      return { connected: true, uid: this.user.uid, projectId: cfg.projectId, onlineEnabled: true };
    } catch (err) {
      this.connected = false;
      const errMsg = String(err && err.message ? err.message : err);
      window.dispatchEvent(
        new CustomEvent("speakflow:firebase-ready", {
          detail: { mode: "local-fallback", uid: this.localUid, error: errMsg },
        })
      );
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
      const { doc, setDoc } = this._firestoreFns;
      const attemptId = `att_${Date.now()}`;
      await setDoc(doc(this.db, "users", this.user.uid, "attempts", attemptId), {
        ...attemptData,
        createdAt: new Date().toISOString(),
      });
    } catch (_) {}
  }

  async syncSrsCard(cardData) {
    if (!this.connected || !this.db || !this.user) return;
    try {
      const { doc, setDoc } = this._firestoreFns;
      const cardId = cardData.card_id || `${cardData.scenario_id}_${cardData.phrase_id}`;
      await setDoc(
        doc(this.db, "users", this.user.uid, "srs_cards", cardId),
        { ...cardData, updatedAt: new Date().toISOString() },
        { merge: true }
      );
    } catch (_) {}
  }

  async syncRoleplay(roleplayData) {
    if (!this.connected || !this.db || !this.user) return;
    try {
      const { doc, setDoc } = this._firestoreFns;
      const sessionId = roleplayData.session_id || `rp_${Date.now()}`;
      await setDoc(
        doc(this.db, "users", this.user.uid, "roleplay_sessions", sessionId),
        { ...roleplayData, updatedAt: new Date().toISOString() },
        { merge: true }
      );
    } catch (_) {}
  }
}

window.SpeakFlowFirebase = new SpeakFlowFirebaseBridge();
window.speakFlowFirebase = window.SpeakFlowFirebase;
window.SpeakFlowFirebase.init();
