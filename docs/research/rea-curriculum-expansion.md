# REA Curriculum & Architecture Expansion Report (`reverse-engineer-anything`)

## 1. Evidence Artifact Inventory (`rea analyze-javascript-application`)

Executed via the local REA CLI (`./tools/rea/node_modules/.bin/rea analyze-javascript-application public --json`):

- **Semantic Relationship Graph ID**: `jsrg_1c9135f99846267b83fb59bd401e83878d7cdc48edcad3df37bd1c6ab07b6615`
- **Route Inventory ID**: `jsri:91faf981fb572238b83f1ce145e7168d7eda0d6a8b075ad9bb03a50aa9fc5ad9`
- **Source Container SHA-256**: `a3cdcacdc999938a9fa953d445f6bf8410f46fe3f61420c8a4134e4ed9787e78`
- **Analyzed ESM Module**: `public/firebase-config.js`
  - Uses standard `npm` bare module specifiers (`firebase/app`, `firebase/analytics`, `firebase/auth`, `firebase/firestore`) backed by `package.json` (`"firebase": "^13.3.0"`) and browser `<script type="importmap">`.
  - Initializes Firebase project `shadowing-efcab` (app `shadowing`) via `initializeApp(firebaseConfig)`, enables online Firestore access (`enableNetwork(db)`), and authenticates via `signInAnonymously(auth)`.

## 2. REA Conversational Chunking Matrix (6 Modules × 6 CEFR Levels = 36 Scenarios, 216 Phrases)

Using conversational chunk reverse-engineering principles (high-frequency lexical bundles, pragmatic discourse markers, phonetic linking, and progressive syntactic complexity from A1 to C2), every thematic module is populated across all 6 CEFR levels with **6 target phrases** and **4 interactive user roleplay turns** per scenario:

| Thematic Module (`topic`) | A1 (Beginner) | A2 (Elementary) | B1 (Intermediate) | B2 (Upper-Intermediate) | C1 (Advanced) | C2 (Mastery) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`food-and-drink`** | `a1-ordering-coffee` (6 phrases) | `a2-restaurant-dinner` (6 phrases) | `b1-dietary-restrictions` (6 phrases) | `b2-hosting-business-lunch` (6 phrases) | `c1-wine-tasting-pairing` (6 phrases) | `c2-culinary-critique` (6 phrases) |
| **`travel-and-transport`** | `a1-bus-ticket` (6 phrases) | `a2-asking-directions` (6 phrases) | `b1-delayed-flight` (6 phrases) | `b2-car-rental-dispute` (6 phrases) | `c1-customs-declaration` (6 phrases) | `c2-aviation-vip-lounge` (6 phrases) |
| **`hotel-and-shopping`** | `a1-clothing-store` (6 phrases) | `a2-hotel-room-request` (6 phrases) | `b1-hotel-check-in` (6 phrases) | `b2-returning-damaged-item` (6 phrases) | `c1-lease-negotiation` (6 phrases) | `c2-luxury-concierge` (6 phrases) |
| **`social-and-smalltalk`** | `a1-greeting-neighbors` (6 phrases) | `a2-meeting-new-people` (6 phrases) | `b1-inviting-to-party` (6 phrases) | `b2-catching-up-plans` (6 phrases) | `c1-cultural-nuances` (6 phrases) | `c2-dinner-debate` (6 phrases) |
| **`work-and-career`** | `a1-first-day-office` (6 phrases) | `a2-scheduling-meeting` (6 phrases) | `b1-project-status-update` (6 phrases) | `b2-job-interview` (6 phrases) | `c1-negotiating-deadline` (6 phrases) | `c2-executive-pitch` (6 phrases) |
| **`health-and-emergencies`** | `a1-calling-help-desk` (6 phrases) | `a2-pharmacy-symptoms` (6 phrases) | `b1-doctors-appointment` (6 phrases) | `b2-dental-emergency` (6 phrases) | `c1-insurance-claim` (6 phrases) | `c2-medical-second-opinion` (6 phrases) |

## 3. Pedagogical Progression per Exercise Stage

1. **Stage 1 — Escucha y Repite (`1. Escucha`)**: Full sentence prosody + IPA glossary chunks + Instant Tap-to-Translate (`POST /v1/translate`).
2. **Stage 2 — Completa el Hueco (`2. Completa`)**: Cloze indices targeting high-value functional collocations (`cloze: [...]`).
3. **Stage 3 — Responde con Pista Visual (`3. Pista`)**: Visual emoji/context cue triggering active production from memory.
4. **Stage 4 — Roleplay de Escenario (`4. Roleplay`)**: 4-turn structured dialogue (`ai` ↔ `user`) with explicit pragmatic goals.
5. **Stage 5 — Conversación IA Libre con Libreto (`5. Conversa`)**: Guided script prompts combining all 6 scenario phrases in open-ended AI turn-taking.
