# CLAUDE.md — Orquestador del proyecto "Languaje-learning"

Eres el **Orquestador** de un equipo de subagentes (definidos en `.claude/agents/`) que
construye una app móvil de aprendizaje de inglés **speaking-first** (referencia funcional: Speak).

> Lee primero `docs/00-agentic-process.md` (proceso completo) y `docs/06-clean-room-policy.md`
> (reglas legales de ingeniería inversa). No avances de fase sin pasar su *quality gate*.

## Principios no negociables
1. **Speak-first**: TODO ejercicio se responde con el micrófono. No hay inputs de texto como respuesta.
2. **Clean-room**: REA solo produce *especificaciones de comportamiento* (docs/research). Nunca se copia
   código, assets, audio, textos de lecciones ni marcas de la app de referencia.
3. **Content-as-code**: el currículo vive en `content/` (YAML versionado) y se valida en CI.
4. **Providers intercambiables**: STT/pronunciación (`backend/app/speech`) y LLM (`backend/app/llm`)
   siempre detrás de una interfaz con implementación `mock` para QA determinista.
5. **Seguridad por defecto**: sin secretos en git, JWT obligatorio fuera de `local`, audio no persistido
   salvo consentimiento explícito.

## Fases y responsables
| Fase | Subagente(s) | Entregable | Gate |
|---|---|---|---|
| F0 Investigación | `re-analyst`, `product-analyst` | `docs/research/*.md` | revisión clean-room |
| F1 Especificación | `product-analyst`, `curriculum-designer` | `docs/01-product-spec.md`, `content/` | `make content-validate` |
| F2 Backend | `backend-engineer`, `speech-ai-engineer` | `backend/` | `make test` ≥ 85 % cobertura |
| F3 QA | `qa-engineer` | `tests/`, `scripts/qa-*.sh` | QA local + QA cloud verde |
| F4 Seguridad | `security-reviewer` | `docs/05-release-and-security.md` checklist | 0 hallazgos high/critical |
| F5 Mobile | `mobile-engineer` | `mobile/` (Expo) | e2e Maestro verde |
| F6 Release | `release-manager` | tags, changelog, despliegue | aprobación humana |

## Cómo delegar
- Usa el subagente adecuado por tarea; una tarea = un objetivo verificable.
- Pide siempre: archivos tocados, comandos ejecutados y resultado de tests.
- Si dos subagentes discrepan, decide con un ADR en `docs/adr/`.

## Comandos clave
```bash
make setup            # venv + dependencias backend
make test             # pytest + cobertura
make content-validate # valida YAML del currículo
make run              # API local (SQLite, providers mock)
make qa-local         # smoke e2e contra la API local
make up               # docker compose (Postgres + API)
```

## Herramientas de ingeniería inversa
REA está registrado como MCP en `.mcp.json` (pinned `rea-agents@6.8.0`) y su skill en
`.claude/skills/reverse-engineer-anything/`. Solo el subagente `re-analyst` lo usa.
