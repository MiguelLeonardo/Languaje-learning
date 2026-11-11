# 06 — Política Clean-Room e Integración de REA

## 1. Propósito
Usamos **REA (`morluto/rea`, `rea-agents@6.8.0`)** para comprender el comportamiento observable de aplicaciones de referencia (como Speak) y construir nuestra propia implementación desde cero (**clean-room design**).

## 2. Separación de responsabilidades (Chinese Wall)
1. **Sala de análisis (`re-analyst`)**:
   - Tiene acceso al servidor MCP `rea` (registrado en [`.mcp.json`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/.mcp.json) y en [`.claude/skills/reverse-engineer-anything/SKILL.md`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/.claude/skills/reverse-engineer-anything/SKILL.md)).
   - Analiza únicamente artefactos obtenidos de forma legítima en `research-artifacts/` (directorio ignorado por `.gitignore`).
   - Escribe **únicamente especificaciones funcionales abstractas** en `docs/research/*.md` (qué pantallas existen, cómo progresa la dificultad, qué métricas recibe el alumno).
2. **Sala de implementación (`curriculum-designer`, `backend-engineer`, `speech-ai-engineer`, `mobile-engineer`)**:
   - **No** invoca REA ni lee artefactos crudos.
   - Construye código y contenido 100 % original a partir de `docs/01-product-spec.md` y `docs/03-pedagogy-and-curriculum.md`.

## 3. Qué está prohibido subir al repositorio
- Archivos `.apk`, `.ipa`, `.har`, `.saz`, bases SQLite extraídas o dumps de memoria (bloqueados en [`.gitignore`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/.gitignore)).
- Código fuente descompilado, nombres internos propietarios, claves API, URLs privadas de terceros.
- Textos de lecciones, diálogos, grabaciones de audio o activos gráficos de aplicaciones de terceros.
