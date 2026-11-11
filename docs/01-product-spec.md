# 01 — Especificación de Producto (Speaking-First English Learning)

> Referencia contextual de UX/pedagogía: **Speak**. Implementación 100 % clean-room.

## 1. Visión y regla de oro
Aplicación móvil para aprender inglés hablando desde el primer segundo.
- **Regla de oro (Speak-first)**: **todos** los ejercicios se responden mediante el micrófono (`multipart/form-data` con archivo de audio). No existen ejercicios de opción múltiple con tap ni respuestas por teclado.

## 2. Escalas y temáticas (CEFR A1–C2)
El catálogo se organiza en tres bandas y seis niveles CEFR con escenarios del mundo real del día a día:

| Banda | Nivel CEFR | Complejidad lingüística | Ejemplo incluido en `content/scenarios/` |
|---|---|---|---|
| **Básico** (`basic`) | **A1** | Frases de 4–7 palabras, presente simple, peticiones cortas | [`a1-ordering-coffee.yaml`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/content/scenarios/a1-ordering-coffee.yaml) — Pedir un café |
| **Básico** (`basic`) | **A2** | Preguntas cotidianas, ubicaciones, pedir repetición | [`a2-asking-directions.yaml`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/content/scenarios/a2-asking-directions.yaml) — Pedir indicaciones |
| **Intermedio** (`intermediate`) | **B1** | Resolver imprevistos en viajes, peticiones corteses (`Would it be possible…`) | [`b1-hotel-check-in.yaml`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/content/scenarios/b1-hotel-check-in.yaml) — Check-in en hotel |
| **Intermedio** (`intermediate`) | **B2** | Ámbito laboral, *present perfect continuous*, condicionales | [`b2-job-interview.yaml`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/content/scenarios/b2-job-interview.yaml) — Entrevista de trabajo |
| **Avanzado** (`advanced`) | **C1** | Negociación diplomática, *phrasal verbs* e idioms profesionales | [`c1-negotiating-deadline.yaml`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/content/scenarios/c1-negotiating-deadline.yaml) — Negociar un plazo |
| **Avanzado** (`advanced`) | **C2** | Matices argumentativos, registro culto/coloquial, debate | [`c2-dinner-debate.yaml`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/content/scenarios/c2-dinner-debate.yaml) — Debatir en una cena |

## 3. Progresión de ejercicios (andamiaje decreciente)
Cada lección (`GET /v1/lessons/{scenario_id}`) guía al alumno por **4 etapas habladas** más la **charla abierta con IA guionada**:

1. **Sesión de Sombra (`shadowing`, soporte `full`, umbral 0.70)** — *Ejercicio principal de input*:
   - El usuario escucha el audio modelo (`audio_text`), ve la frase en inglés, su traducción y el apoyo visual (`visual_hint`), y repite en voz alta imitando ritmo y entonación.
   - También accesible como sesión dedicada en `GET /v1/shadowing/{scenario_id}`.
2. **Recordación con apoyo visual y glosario (`recall`, soporte `full`, umbral 0.75)**:
   - Muestra frase, traducción, `visual_hint` y `glossary` (significado en español + IPA de palabras clave).
   - También alimenta el banco de **frases comunes** (`GET /v1/phrases/common`).
3. **Refuerzo guiado (`guided`, soporte `partial`, umbral 0.80)**:
   - Oculta el glosario y el audio modelo; muestra traducción, `visual_hint` y pista de iniciales (`C__ I h___ a c_____, p_____?`).
4. **Completar frases (`completion`, soporte `low`, umbral 0.85)**:
   - Sin traducción ni pista visual; muestra la frase con huecos (`cloze`, p. ej. `Can I have a ____ please?`) y el usuario debe pronunciar la frase completa.
5. **Charla abierta con IA con guion (`roleplay`, umbral 0.60)**:
   - `POST /v1/roleplay/{scenario_id}/sessions` inicia la conversación en contexto (`ai_role`, `user_role`, `setting`).
   - En cada turno del usuario se entrega un `goal` en español y `suggested_lines` en inglés que puede leer o parafrasear hablando al micrófono (`POST /v1/roleplay/sessions/{id}/turns`).

## 4. Sistema de retroalimentación (`Feedback`)
Cada intento (`POST /v1/exercises/{id}/attempts`) devuelve:
- Alineación palabra por palabra (`correct`, `mispronounced`, `missing`, `extra`).
- Puntaje compuesto (`accuracy`, `fluency`, `confidence` del motor STT y `score` final).
- Nivel (`excellent` ≥ 0.95, `good` ≥ umbral, `retry` < umbral), mensaje en español y `tips` accionables con IPA/significado extraídos del glosario.
- `focus_words`: lista de palabras con error que pasan automáticamente a la memoria espaciada.

## 5. Memoria de aprendizaje espaciado (SRS — variante SM-2)
El sistema mantiene dos tipos de tarjetas por usuario en `srs_cards`:
- **`phrase`**: repaso de cada frase practicada (en `guided` si `repetitions < 3`, en `completion` si `repetitions >= 3`).
- **`feedback`**: tarjetas específicas para las palabras falladas (`focus_words`), re-enseñadas con soporte `full` (`recall`) y prioridad alta en la cola (`GET /v1/review/due`, `POST /v1/review/{card_id}/attempts`).

## 6. Historias de usuario y criterios Given/When/Then (MoSCoW)
- **US-01 (Must)** — *Sesión de sombra*: **Given** un escenario CEFR, **When** el alumno solicita `/v1/shadowing/{id}` y envía su voz a `/v1/exercises/{ex_id}/attempts`, **Then** recibe transcripción, `score` y `feedback` por palabra.
- **US-02 (Must)** — *Frases comunes*: **Given** un nivel CEFR opcional, **When** consulta `/v1/phrases/common`, **Then** recibe ejercicios hablados de las frases marcadas como `common: true`.
- **US-03 (Must)** — *Progresión de soporte*: **Given** `/v1/lessons/{id}`, **When** inspecciona `stages`, **Then** obtiene `shadowing → recall → guided → completion` con soporte `full → full → partial → low` y umbrales crecientes `0.70 → 0.75 → 0.80 → 0.85`.
- **US-04 (Must)** — *SRS de lecciones y feedbacks*: **Given** un intento con palabras omitidas o mal pronunciadas, **When** se registra el intento, **Then** se programa una tarjeta `phrase` y una tarjeta `feedback` con `focus_words` y re-intento a los 10 minutos si `quality < 3`.
- **US-05 (Must)** — *Roleplay guionado con IA*: **Given** una sesión activa, **When** el usuario pronuncia una frase cercana a `suggested_lines`, **Then** la IA avanza al siguiente turno del guion y al finalizar calcula `average_score`.
