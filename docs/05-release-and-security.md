# 05 — Seguridad, Privacidad y Lanzamiento

## 1. Controles de seguridad implementados en el Backend
- **Guardas de entorno en arranque** ([`config.py`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/backend/app/core/config.py)):
  - Prohibido iniciar en `staging`/`production` con el `JWT_SECRET` por defecto o con longitud `< 32` bytes.
  - Prohibido iniciar en `staging`/`production` con `SPEECH_PROVIDER=mock`.
  - Endpoint `/v1/auth/dev-token` deshabilitado (HTTP 404) fuera de `local`/`test`.
  - Swagger `/docs` deshabilitado en `production`.
- **Protección de endpoints de voz** ([`deps.py`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/backend/app/api/deps.py) y [`security.py`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/backend/app/core/security.py)):
  - Lista blanca de MIME types de audio (`audio/wav`, `audio/m4a`, `audio/mpeg`, `audio/webm`, `audio/ogg`, `audio/aac`).
  - Límite estricto de tamaño de subida (`max_audio_bytes = 5 MiB`, lectura acotada `read(max + 1)` → HTTP 413).
  - Rechazo de `debug_transcript` cuando el proveedor de voz no es `mock` (HTTP 400).
  - Rate limit por usuario autenticado (`60 req / 60 s` → HTTP 429).
- **Privacidad de voz por defecto**:
  - `persist_audio = False`: el audio en bytes se procesa en memoria para transcripción y se descarta; solo se guarda la transcripción textual truncada a 1000 caracteres y las métricas.
- **Cabeceras HTTP de seguridad** ([`main.py`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/backend/app/main.py)):
  - `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`.

## 2. Gates automatizados en CI ([`.github/workflows/ci.yml`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/.github/workflows/ci.yml))
- **SAST**: `ruff` (reglas `S`) + `bandit -r app`.
- **SCA (dependencias)**: `pip-audit`.
- **Secret scanning**: `gitleaks`.
- **Container scanning**: `trivy` bloqueando vulnerabilidades `HIGH` y `CRITICAL`.

## 3. Checklist de Release (`release-manager` + `security-reviewer`)
- [ ] `make lint test content-validate qa-local security` en verde.
- [ ] Revisión clean-room completada (ningún asset o texto propietario en `content/` o `docs/`).
- [ ] Despliegue en Cloud Run `staging` con `--no-traffic` + `make qa-cloud` verde.
- [ ] Promoción a `production` mediante aprobación manual en GitHub Environment protegido.
- [ ] Comando de rollback verificado: `gcloud run services update-traffic languaje-api-production --to-revisions=<prev>=100`.
