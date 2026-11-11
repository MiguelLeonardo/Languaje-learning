# Preguntas Abiertas de Investigación y Calibración

1. **Evaluación fonémica fina (GOP — Goodness of Pronunciation)**:
   - En la versión inicial combinamos alineación léxica (`SequenceMatcher`) + `avg_logprob` de Whisper.
   - Para una fase posterior se puede añadir un segundo adaptador `SpeechProvider` (p. ej. Azure Pronunciation Assessment o Wav2Vec2 GOP) sin tocar los routers ni los servicios de dominio.
2. **Streaming de audio en tiempo real (WebSockets / WebRTC)**:
   - El contrato REST multipart permite auditar y testear determinísticamente en local y cloud. Cuando se construya la app móvil en Fase 5, se evaluará añadir un endpoint WebSocket opcional para transcripción parcial en vivo.
3. **Curva de olvido personalizada**:
   - Actualmente usamos SM-2 con factor de facilidad `ease >= 1.3` y re-aprendizaje a 10 minutos. Con datos reales en staging se podrá calibrar contra FSRS.
