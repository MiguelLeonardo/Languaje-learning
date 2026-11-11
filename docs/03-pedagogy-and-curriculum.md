# 03 — Pedagogía y Diseño Curricular (CEFR A1–C2)

## 1. Principios pedagógicos
1. **Comprensible Input + Output inmediato (Shadowing)**: el alumno primero escucha e imita la prosodia completa de la frase antes de enfrentarse a ejercicios de recuperación de memoria.
2. **Andamiaje decreciente (Scaffolding Fade)**:
   - `shadowing` (audio + texto + traducción + icono) → `recall` (+ glosario con IPA) → `guided` (iniciales + traducción) → `completion` (huecos `cloze`, sin traducción) → `roleplay` (objetivo comunicativo + líneas sugeridas).
3. **Repetición espaciada dual (Frases + Errores fonéticos/léxicos)**:
   - Cada intento actualiza la tarjeta `phrase` según la calidad SM-2 (`0..5`).
   - Si hubo palabras omitidas o mal pronunciadas (`focus_words`), se crea/actualiza una tarjeta `feedback` con intervalo corto (10 minutos) que vuelve a presentarse en modo `recall` resaltando las palabras problema.

## 2. Guía por nivel CEFR para `curriculum-designer`
| Nivel | Longitud por frase | Gramática / Registro | Cómo elegir `cloze` |
|---|---|---|---|
| **A1** | 3–7 palabras | Presente simple, fórmulas de cortesía (`Can I have…`, `How much…`) | 1 palabra léxica clave (sustantivo o adjetivo) |
| **A2** | 5–9 palabras | `There is/are`, modales básicos (`Could you…`), direcciones | 1–2 palabras (verbo de movimiento o lugar) |
| **B1** | 7–11 palabras | Pasado/futuro funcional, quejas educadas (`I'm afraid…`, `Would it be possible…`) | 1–2 palabras de función pragmática |
| **B2** | 8–14 palabras | `Present perfect continuous`, condicionales (`I'd be working…`), vocabulario laboral | 2 palabras (auxiliares o colocaciones) |
| **C1** | 10–16 palabras | *Phrasal verbs* e idioms profesionales (`heads-up`, `push back`, `meet halfway`) | 2 palabras del idiom o conector |
| **C2** | 10–18 palabras | Matices argumentativos, inversión/estructuras comparativas (`not so much… as`, `grain of salt`) | 2–3 palabras del giro idiomático |

## 3. Contrato de un archivo `content/scenarios/<nivel>-<slug>.yaml`
Validado por [`backend/app/content/schema.py`](file:///home/antigravity/MiguelLeonardo/Languaje-learning/backend/app/content/schema.py) mediante `make content-validate`:
- `id`: slug en minúsculas (`^[a-z0-9][a-z0-9-]*$`).
- `cefr`: `A1 | A2 | B1 | B2 | C1 | C2`.
- `phrases[]`: mínimo 1 frase, IDs únicos, `cloze` con índices válidos `0..len(words)-1`, `glossary` con `word`, `meaning` (en español) e `ipa` opcional.
- `roleplay`: alterna turnos `ai` (con `text`) y `user` (con `goal` en español y `suggested_lines` en inglés).
