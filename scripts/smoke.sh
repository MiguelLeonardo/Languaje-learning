#!/usr/bin/env bash
# Shared end-to-end smoke test. Usage: API_BASE_URL=... [API_TOKEN=...] [USE_MOCK=1] scripts/smoke.sh
set -euo pipefail
BASE="${API_BASE_URL:?API_BASE_URL required}"
AUDIO="${AUDIO_FIXTURE:-$(dirname "$0")/../tests/fixtures/audio/silence.wav}"
pass() { echo "  ✔ $1"; }
fail() { echo "  ✘ $1"; exit 1; }
j() { python3 -c "import sys,json;d=json.load(sys.stdin);print(eval(sys.argv[1]))" "$1"; }

echo "== Smoke against $BASE"
curl -fsS "$BASE/health" | grep -q ok && pass health || fail health
curl -fsS "$BASE/ready" | grep -q ready && pass ready || fail ready

TOKEN="${API_TOKEN:-}"
if [[ -z "$TOKEN" ]]; then
  TOKEN=$(curl -fsS -X POST "$BASE/v1/auth/dev-token" -H 'content-type: application/json' \
    -d '{"user_id":"qa-smoke"}' | j 'd["access_token"]')
fi
H=(-H "Authorization: Bearer $TOKEN")

N=$(curl -fsS "${H[@]}" "$BASE/v1/levels" | j 'len(d)'); [[ "$N" == 6 ]] && pass "6 CEFR levels" || fail levels
STAGES=$(curl -fsS "${H[@]}" "$BASE/v1/lessons/a1-ordering-coffee" | j '",".join(s["type"] for s in d["stages"])')
[[ "$STAGES" == "shadowing,recall,guided,completion" ]] && pass "lesson stages" || fail "stages=$STAGES"

EX="a1-ordering-coffee.can-i-have.shadowing"
if [[ "${USE_MOCK:-1}" == 1 ]]; then
  EXTRA=(-F "debug_transcript=Can I have a coffee, please?")
else
  EXTRA=()
fi
R=$(curl -fsS "${H[@]}" -F "audio=@$AUDIO;type=audio/wav" "${EXTRA[@]}" "$BASE/v1/exercises/$EX/attempts")
echo "$R" | j 'd["feedback"]["message_es"]' >/dev/null && pass "speech attempt + feedback" || fail attempt
[[ "${USE_MOCK:-1}" == 1 ]] && { [[ $(echo "$R" | j 'd["evaluation"]["passed"]') == True ]] && pass "mock pass" || fail "mock pass"; }

SID=$(curl -fsS -X POST "${H[@]}" "$BASE/v1/roleplay/a1-ordering-coffee/sessions" | j 'd["session_id"]')
[[ -n "$SID" ]] && pass "roleplay session" || fail roleplay
curl -fsS "${H[@]}" "$BASE/v1/progress" | grep -q attempts && pass progress || fail progress
echo "== Smoke OK"
