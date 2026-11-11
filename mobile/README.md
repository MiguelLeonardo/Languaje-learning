# Cliente Móvil (Fase 5 — Preparado para Lanzamiento Posterior)

El backend ya expone y valida el contrato completo en [`backend/openapi.json`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/backend/openapi.json). Cuando se inicie la Fase 5 con el subagente [`mobile-engineer`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/.claude/agents/mobile-engineer.md):

## Stack previsto
- **Expo SDK 52+ (React Native + TypeScript)** con Expo Router.
- **`expo-audio`** configurado a 16 kHz, mono, AAC/m4a (`audio/m4a`) o WAV (`audio/wav`).
- **Cliente API tipado** generado desde `../backend/openapi.json` (`npx openapi-typescript ../backend/openapi.json -o src/api/schema.d.ts`).
- **Maestro** para flujos E2E móviles en simulador iOS / emulador Android.

## Pantallas que mapean 1:1 con los endpoints del Backend
1. **Selector de nivel y escenario**: `GET /v1/levels`, `GET /v1/scenarios?cefr=A1..C2`.
2. **Sesión de Sombra**: `GET /v1/shadowing/{scenario_id}` → reproducción TTS del `audio_text` + grabación al micrófono → `POST /v1/exercises/{id}/attempts`.
3. **Lección por etapas (`shadowing → recall → guided → completion`)**: `GET /v1/lessons/{scenario_id}`.
4. **Práctica de frases comunes**: `GET /v1/phrases/common`.
5. **Charla con IA guionada**: `POST /v1/roleplay/{scenario_id}/sessions` + `POST /v1/roleplay/sessions/{id}/turns` mostrando `pending_turn.goal` y `pending_turn.suggested_lines`.
6. **Cola de repaso espaciado (SRS) y progreso**: `GET /v1/review/due`, `POST /v1/review/{card_id}/attempts`, `GET /v1/progress`.
