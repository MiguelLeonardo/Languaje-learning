/**
 * Firebase Web SDK v11 Connector for SpeakFlow:
 *  - Service 1: Firebase Authentication (Anonymous Auth enabled automatically)
 *  - Service 2: Cloud Firestore Database (users/{uid}, srs_cards, attempts, roleplay_sessions)
 *  - Service 3: Firebase Hosting + Google Cloud / Gemini Free Tier integration
 */

export class SpeakFlowFirebaseBridge {
  constructor() {
    this.app = null;
    this.auth = null;
    this.db = null;
    this.user = null;
    this.connected = false;
    this.localUid = localStorage.getItem("sf_anon_uid") || `anon-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem("sf_anon_uid", this.localUid);
  }

  getStoredConfig() {
    try {
      const raw = localStorage.getItem("sf_firebase_config");
      if (raw) return JSON.parse(raw);
    } catch (_) {}
    return window.FIREBASE_CONFIG || null;
  }

  async saveFirebaseConfig(jsonStr) {
    try {
      const parsed = typeof jsonStr === "string" ? JSON.parse(jsonStr) : jsonStr;
      localStorage.setItem("sf_firebase_config", JSON.stringify(parsed));
      return await this.init(parsed);
    } catch (err) {
      return { connected: false, reason: String(err) };
    }
  }

  async init(customConfig = null) {
    const cfg = customConfig || this.getStoredConfig();
    if (!cfg || !cfg.apiKey || !cfg.projectId || String(cfg.apiKey).startsWith("REPLACE_")) {
      this.connected = false;
      window.dispatchEvent(
        new CustomEvent("speakflow:firebase-ready", {
          detail: { mode: "local-fallback", uid: this.localUid, projectId: "languaje-learning-local" },
        })
      );
      return { connected: false, uid: this.localUid, reason: "no_config" };
    }
    try {
      const [{ initializeApp, getApps }, { getAuth, signInAnonymously }, { getFirestore, doc, setDoc }] =
        await Promise.all([
          import("https://www.gstatic.com/firebasejs/11.0.2/firebase-app.js"),
          import("https://www.gstatic.com/firebasejs/11.0.2/firebase-auth.js"),
          import("https://www.gstatic.com/firebasejs/11.0.2/firebase-firestore.js"),
        ]);

      this.app = getApps().length ? getApps()[0] : initializeApp(cfg);
      this.auth = getAuth(this.app);
      this.db = getFirestore(this.app);
      this._firestoreFns = { doc, setDoc };

      const cred = await signInAnonymously(this.auth);
      this.user = cred.user;
      this.connected = true;

      await setDoc(
        doc(this.db, "users", this.user.uid),
        {
          uid: this.user.uid,
          isAnonymous: this.user.isAnonymous,
          tier: localStorage.getItem("sf_freemium_tier") || "free",
          updatedAt: new Date().toISOString(),
        },
        { merge: true }
      );
      window.dispatchEvent(
        new CustomEvent("speakflow:firebase-ready", {
          detail: { mode: "firebase-live", uid: this.user.uid, projectId: cfg.projectId },
        })
      );
      return { connected: true, uid: this.user.uid, projectId: cfg.projectId };
    } catch (err) {
      this.connected = false;
      window.dispatchEvent(
        new CustomEvent("speakflow:firebase-ready", {
          detail: { mode: "local-fallback", uid: this.localUid, error: String(err) },
        })
      );
      return { connected: false, uid: this.localUid, reason: String(err) };
    }
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
