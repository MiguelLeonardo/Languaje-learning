# ADR-0001 — Arquitectura Backend Speaking-First, Content-as-Code y Paridad Local/Cloud

- **Estado**: Aceptado
- **Fecha**: 2026-11-11

## Contexto
Necesitamos construir y validar primero en backend toda la lógica de una app móvil de aprendizaje de inglés tipo Speak (ejercicios 100 % hablados, niveles CEFR A1–C2, sesiones de sombra, frases comunes, andamiaje decreciente, feedback por palabra, repetición espaciada de lecciones/feedbacks y charla abierta guionada con IA), permitiendo ejecutar QA determinista en local y QA real en cloud antes de lanzar el cliente móvil.

## Decisiones
1. **FastAPI + SQLAlchemy 2 + Pydantic v2**: genera automáticamente el contrato OpenAPI (`backend/openapi.json`) que consumirá el cliente móvil en Fase 5.
2. **Content-as-Code en YAML (`content/scenarios/*.yaml`)**: desacopla el trabajo del agente `curriculum-designer` del código Python y permite validar el currículo como un *quality gate* en CI (`make content-validate`).
3. **Puertos `SpeechProvider` y `LLMProvider` con implementación `mock`**:
   - En local/CI se usan proveedores deterministas (`SPEECH_PROVIDER=mock`, `LLM_PROVIDER=mock`) que permiten probar el 99 % del código sin costes ni flakiness de red.
   - En `staging`/`production` se inyectan `openai_whisper` y `anthropic` (Claude) y se bloquea por código cualquier intento de usar `mock` o `debug_transcript`.
4. **REA (`rea-agents@6.8.0`) aislado en `tools/rea` y `.mcp.json`**: disponible solo para el subagente `re-analyst` bajo la política clean-room (`docs/06-clean-room-policy.md`).

## Consecuencias
- El mismo script [`scripts/smoke.sh`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/scripts/smoke.sh) sirve para `make qa-local` y `make qa-cloud`.
- Añadir un nuevo nivel o escenario no requiere migraciones de base de datos.
