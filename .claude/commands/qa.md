Ejecuta QA ($ARGUMENTS = local | cloud) usando el subagente qa-engineer.
- local: `make test && make qa-local`
- cloud: `API_BASE_URL=... API_TOKEN=... scripts/qa-cloud.sh`
Resume fallos con severidad y si bloquean el release.
