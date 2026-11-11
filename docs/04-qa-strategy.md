# 04 — Estrategia de QA (Local y Cloud)

## 1. Pirámide de pruebas
1. **Validación estática y de esquemas (`make lint` + `make content-validate`)**:
   - `ruff` (incluyendo reglas de seguridad `S` / flake8-bandit).
   - Validación Pydantic de todos los YAML en `content/scenarios/`.
2. **Pruebas unitarias y de contrato API (`make test`)**:
   - Ubicadas en [`backend/tests/`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/backend/tests/conftest.py).
   - Cubren normalización, alineación de palabras, generación de feedback, algoritmo SM-2, progresión de etapas, flujo completo de roleplay, límites de subida de audio, rate limiting y guardas de producción.
   - **Quality Gate**: cobertura mínima del **85 %** (actualmente **99 %**).
3. **Smoke E2E compartido ([`scripts/smoke.sh`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/scripts/smoke.sh))**:
   - Mismo script para local y para cloud; verifica `/health`, `/ready`, `/v1/levels`, `/v1/lessons/a1-ordering-coffee`, envío de audio a `/v1/exercises/.../attempts`, inicio de `/v1/roleplay/.../sessions` y `/v1/progress`.

## 2. Ejecución en Local (`make qa-local`)
Ejecuta [`scripts/qa-local.sh`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/scripts/qa-local.sh):
1. Corre `ruff`, `app.content.validate` y `pytest`.
2. Levanta `uvicorn` en un puerto efímero contra una base SQLite temporal con `SPEECH_PROVIDER=mock` y `LLM_PROVIDER=mock`.
3. Ejecuta `scripts/smoke.sh` usando `USE_MOCK=1` y el fixture [`tests/fixtures/audio/silence.wav`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/tests/fixtures/audio/silence.wav).

## 3. Ejecución en Cloud / Staging (`make qa-cloud`)
Ejecuta [`scripts/qa-cloud.sh`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/scripts/qa-cloud.sh):
```bash
API_BASE_URL="https://languaje-api-staging-xxxx.run.app" \
API_TOKEN="<jwt-emitido-por-idp-staging>" \
AUDIO_FIXTURE="tests/fixtures/audio/can-i-have.wav" \
make qa-cloud
```
- Con `USE_MOCK=0` (por defecto en cloud), el script **no** envía `debug_transcript`; sube el archivo WAV real para ejercitar la integración con Whisper y Claude en Cloud Run antes de dirigir tráfico productivo.
