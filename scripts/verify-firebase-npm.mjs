import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import {
  DEFAULT_PROJECT_CONFIG,
  parseFirebaseConfigInput,
  initializeShadowingFirebaseApp,
} from "../public/firebase-config.js";

const sampleSnippet = `
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: process.env.FIREBASE_API_KEY || "AIzaSyShadowingDemoKeyForVerification12345",
  authDomain: "shadowing-efcab.firebaseapp.com",
  projectId: "shadowing-efcab",
  storageBucket: "shadowing-efcab.firebasestorage.app",
  messagingSenderId: "100000000000",
  appId: "1:100000000000:web:abcdef1234567890",
  measurementId: "G-SHADOWING1"
};

const app = initializeApp(firebaseConfig);
`;

const parsed = parseFirebaseConfigInput(sampleSnippet);
const { app } = await initializeShadowingFirebaseApp(parsed);
const auth = getAuth(app);
const db = getFirestore(app);

console.log(
  JSON.stringify(
    {
      status: "ok",
      sdk: "npm:firebase",
      projectId: app.options.projectId,
      authDomain: app.options.authDomain,
      storageBucket: app.options.storageBucket,
      authConfigured: Boolean(auth),
      firestoreConfigured: Boolean(db),
      defaultProject: DEFAULT_PROJECT_CONFIG.projectId,
    },
    null,
    2
  )
);
process.exit(0);
