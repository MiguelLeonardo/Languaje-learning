# Languaje-learning — Proceso Agéntico y Backend Speaking-First (Estilo Speak)

Sistema agéntico completo (orquestado con **Claude Code** + **REA** para investigación clean-room) y backend productivo en **FastAPI** para una app móvil de aprendizaje de inglés donde **todos los ejercicios se responden hablando al micrófono**.

## Características principales implementadas
- **100 % Speak-first**: cada ejercicio (`shadowing`, `recall`, `guided`, `completion`, `roleplay` y repasos `srs`) recibe audio por micrófono (`multipart/form-data`) y devuelve `response_mode: "speech"`.
- **Escenarios reales del día a día en toda la escala CEFR (`A1`, `A2`, `B1`, `B2`, `C1`, `C2`)** agrupados en bandas `basic`, `intermediate` y `advanced` en [`content/scenarios/`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/content/scenarios/a1-ordering-coffee.yaml).
- **Sesiones de sombra (`GET /v1/shadowing/{scenario_id}`)**: ejercicio principal de input comprensible e imitación prosódica.
- **Aprendizaje de frases comunes (`GET /v1/phrases/common`)**: banco filtrable por nivel CEFR.
- **Progresión de ejercicios con soporte visual decreciente (`GET /v1/lessons/{scenario_id}`)**:
  1. `shadowing` (soporte `full`, umbral `0.70`) — escuchar y repetir con texto, traducción e icono.
  2. `recall` (soporte `full`, umbral `0.75`) — apoyo visual + traducción + glosario con explicación e IPA.
  3. `guided` (soporte `partial`, umbral `0.80`) — menor soporte visual: iniciales (`C__ I h___...`) + traducción.
  4. `completion` (soporte `low`, umbral `0.85`) — completar frases con huecos (`cloze`) sin traducción.
  5. `roleplay` (`POST /v1/roleplay/{scenario_id}/sessions`) — charla abierta con IA (Claude) siguiendo un guion establecido (`goal` + `suggested_lines`) para que el alumno complete la conversación.
- **Sistema de retroalimentación (`Feedback`)**: alineación palabra por palabra (`correct`, `mispronounced`, `missing`, `extra`), puntaje compuesto (`accuracy`, `fluency`, `confidence`) y consejos con IPA en español.
- **Memoria de aprendizaje espaciado (SRS SM-2)**: agenda automáticamente tanto las **frases de las lecciones** (`kind="phrase"`) como las **palabras con errores del feedback** (`kind="feedback"`, `focus_words`) en `/v1/review/due`.
- **REA (`morluto/rea`, `rea-agents@6.8.0`) instalado y conectado**:
  - Binario y paquete fijados en [`tools/rea/package.json`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/tools/rea/package.json).
  - Servidor MCP registrado en [`.mcp.json`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/.mcp.json) y skill oficial en [`.claude/skills/reverse-engineer-anything/SKILL.md`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/.claude/skills/reverse-engineer-anything/SKILL.md).

## Estructura del repositorio
```text
├── CLAUDE.md                        # Playbook del Orquestador Agéntico
├── .mcp.json                        # Registro MCP de REA (rea-agents@6.8.0)
├── .claude/
│   ├── agents/                      # 9 subagentes especializados por fase
│   ├── commands/                    # Slash commands (/phase, /qa, /new-scenario)
│   ├── settings.json                # Permisos y guardarraíles de Claude Code
│   └── skills/reverse-engineer-anything/
├── docs/
│   ├── 00-agentic-process.md        # Flujo F0..F6 y Quality Gates
│   ├── 01-product-spec.md           # Especificación funcional e historias
│   ├── 02-architecture.md           # Arquitectura backend, IA, mobile y cloud
│   ├── 03-pedagogy-and-curriculum.md# Diseño curricular CEFR y andamiaje
│   ├── 04-qa-strategy.md            # Estrategia de QA local y cloud
│   ├── 05-release-and-security.md   # Controles de seguridad y checklist de release
│   ├── 06-clean-room-policy.md      # Política legal clean-room para REA
│   ├── adr/0001-speaking-first-architecture.md
│   └── research/                    # Entregables clean-room de F0
├── content/scenarios/               # Currículo YAML (A1, A2, B1, B2, C1, C2)
├── backend/                         # API FastAPI + motor pedagógico + tests (99% cov)
├── scripts/                         # smoke.sh, qa-local.sh, qa-cloud.sh
├── infra/                           # docker-compose.yml + Terraform (Cloud Run + Cloud SQL)
├── mobile/                          # Guía de integración Expo/React Native (Fase 5)
└── tools/rea/                       # Instalación local de rea-agents@6.8.0
```

## Inicio rápido y comandos de QA
```bash
make setup            # Crea el venv Python e instala dependencias + REA
make content-validate # Valida los escenarios YAML (A1..C2)
make lint             # Ruff (estilo + reglas de seguridad S)
make test             # Pytest con gate de cobertura >= 85% (actual: 99%)
make qa-local         # Levanta la API local y ejecuta el smoke E2E completo
make security         # Ejecuta Bandit + pip-audit
make openapi          # Exporta backend/openapi.json para el cliente móvil
make rea-doctor       # Verifica el estado de REA para Claude Code
```

Para ejecutar el mismo smoke test contra el entorno Cloud (staging en Cloud Run):
```bash
API_BASE_URL="https://languaje-api-staging-xxxx.run.app" \
API_TOKEN="<jwt-staging>" \
make qa-cloud
```