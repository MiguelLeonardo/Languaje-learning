# V1. Repetición espaciada (`v1.0.0`)

Estado estable congelado de **SpeakFlow V1** (`MiguelLeonardo/Languaje-learning`).

## Capacidades incluidas en `v1.0.0`
- **Currículo CEFR (`A1`–`C2`)**: 8 módulos temáticos × 8 escenarios por nivel (**384 escenarios**, **5 frases** por escenario), incluyendo módulo temático de gramática (`grammar-and-connectors`) y tecnología/rutinas (`daily-tech-and-media`).
- **Flujo de aprendizaje en 5 pasos**:
  1. `1. Sombra` (escucha automática + resaltado de modismos)
  2. `2. Practica` (frase completa con ~33% letras guía únicamente en modismos + audio guía)
  3. `3. Completa` (espacios `____` + audio guía)
  4. `4. Aplica` (variación de contexto con integración de hasta 2 modismos aprendidos)
  5. `5. Conversa` (roleplay con cierre por despedida, 30 s de inactividad, uso de modismos o botón manual, y reporte por concepto hacia Mi Repaso)
- **Entrenador Palabra por Palabra**: alineación LCS, grabación aislada por palabra (`🎧 Mi voz`) y reproducción inmediata.
- **Traductor contextual y Mi Repaso (SRS)**: traducción individual palabra por palabra, tips situacionales y guardado automático de palabras consultadas/clickeadas en `Mi Repaso`.
- **Calidad**: 30/30 pruebas `pytest` con 97.23% de cobertura, 0 errores Ruff y validación estricta de 384 escenarios YAML.
