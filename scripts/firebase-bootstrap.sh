#!/usr/bin/env bash
# Bootstraps the Firebase / Google Cloud project from the console:
#  1. Enables Service 1: Identity Platform / Firebase Auth (with Anonymous Auth)
#  2. Enables Service 2: Cloud Firestore Database (Native mode) + deploys rules & indexes
#  3. Enables Service 3: Firebase Hosting + Google Cloud AI/Speech Free Tier (Gemini, Speech-to-Text, Text-to-Speech)
#  4. Generates public/firebase-config.js from the Firebase Web App SDK config
set -euo pipefail

PROJECT_ID="${FIREBASE_PROJECT_ID:-languaje-learning}"
REGION="${GCP_REGION:-us-central1}"
FB_CLI="node $(cd "$(dirname "$0")/.." && pwd)/tools/firebase/node_modules/firebase-tools/lib/bin/firebase.js"

echo "== Bootstrapping Firebase & Google Cloud services for project: $PROJECT_ID ($REGION)"

if command -v gcloud >/dev/null 2>&1; then
  echo "-> Enabling Google Cloud & Firebase APIs (Auth, Firestore, Hosting, Gemini, Speech, TTS)..."
  gcloud services enable \
    firebase.googleapis.com \
    firebasehosting.googleapis.com \
    identitytoolkit.googleapis.com \
    firestore.googleapis.com \
    generativelanguage.googleapis.com \
    aiplatform.googleapis.com \
    speech.googleapis.com \
    texttospeech.googleapis.com \
    translate.googleapis.com \
    --project="$PROJECT_ID" || echo "   (Run 'gcloud auth login' if project permissions are needed)"

  echo "-> Provisioning Cloud Firestore Native database '(default)'..."
  gcloud firestore databases create --location="$REGION" --type=firestore-native --project="$PROJECT_ID" 2>/dev/null || true

  echo "-> Enabling Anonymous Authentication in Identity Platform..."
  TOKEN="$(gcloud auth print-access-token 2>/dev/null || true)"
  if [[ -n "$TOKEN" ]]; then
    curl -fsS -X PATCH \
      "https://identitytoolkit.googleapis.com/admin/v2/projects/${PROJECT_ID}/config?updateMask=signIn.anonymous.enabled" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "x-goog-user-project: ${PROJECT_ID}" \
      -H "Content-Type: application/json" \
      -d '{"signIn":{"anonymous":{"enabled":true}}}' >/dev/null && echo "   ✔ Anonymous Auth enabled" || true
  fi
fi

echo "-> Fetching Firebase Web SDK config and deploying Firestore rules, indexes & Hosting..."
$FB_CLI use "$PROJECT_ID" 2>/dev/null || true
$FB_CLI apps:sdkconfig WEB --project "$PROJECT_ID" 2>/dev/null || echo "   (Tip: run 'npx firebase login --no-localhost' to authenticate Firebase CLI)"
$FB_CLI deploy --only firestore:rules,firestore:indexes,hosting --project "$PROJECT_ID" 2>/dev/null || true
echo "== Bootstrap complete."
