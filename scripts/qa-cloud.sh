#!/usr/bin/env bash
# Cloud QA (staging): same smoke suite against a deployed URL with a real IdP token and real providers.
#   API_BASE_URL=https://api-staging.example.run.app API_TOKEN=eyJ... scripts/qa-cloud.sh
set -euo pipefail
: "${API_BASE_URL:?set API_BASE_URL}" "${API_TOKEN:?set API_TOKEN (staging IdP JWT)}"
USE_MOCK="${USE_MOCK:-0}" AUDIO_FIXTURE="${AUDIO_FIXTURE:-$(dirname "$0")/../tests/fixtures/audio/can-i-have.wav}" \
  "$(dirname "$0")/smoke.sh"
