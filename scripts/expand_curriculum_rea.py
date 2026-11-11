"""Expand SpeakFlow curriculum using REA conversational chunking taxonomy:
- Expands existing 18 scenarios in content/scenarios/*.yaml to 6 phrases each
- Generates 18 new scenarios so every one of the 6 modules covers all 6 CEFR levels (A1..C2) = 36 scenarios total (216 phrases)
- Syncs FALLBACK_SCENARIOS in backend/app/static/index.html
"""

from __future__ import annotations

import json
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = ROOT / "content" / "scenarios"
STATIC_INDEX = ROOT / "backend" / "app" / "static" / "index.html"

# 1. Extra phrases to append to the 18 existing scenarios so each has 6 phrases
EXTRA_PHRASES_FOR_EXISTING: dict[str, list[dict]] = {
    "a1-ordering-coffee": [
        {
            "id": "with-oat-milk",
            "text": "Can I get it with oat milk?",
            "translation": "¿Me lo puede dar con leche de avena?",
            "visual_hint": "🥛🌾",
            "cloze": [2, 5],
            "glossary": [
                {"word": "get", "meaning": "conseguir / pedir", "ipa": "ɡet"},
                {"word": "oat milk", "meaning": "leche de avena", "ipa": "oʊt mɪlk"},
            ],
        },
        {
            "id": "for-here-or-to-go",
            "text": "To go, please, and a blueberry muffin.",
            "translation": "Para llevar, por favor, y un muffin de arándanos.",
            "visual_hint": "🧁🛍️",
            "cloze": [1, 6],
            "glossary": [
                {"word": "to go", "meaning": "para llevar", "ipa": "tə ɡoʊ"},
                {"word": "muffin", "meaning": "panecillo / muffin", "ipa": "ˈmʌfɪn"},
            ],
        },
    ],
    "a2-restaurant-dinner": [
        {
            "id": "sparkling-water",
            "text": "Could you bring us a bottle of sparkling water?",
            "translation": "¿Nos podría traer una botella de agua con gas?",
            "visual_hint": "🍾💧",
            "cloze": [2, 7],
            "glossary": [
                {"word": "bring", "meaning": "traer", "ipa": "brɪŋ"},
                {"word": "sparkling", "meaning": "con gas / espumosa", "ipa": "ˈspɑːrklɪŋ"},
            ],
        },
        {
            "id": "split-the-bill",
            "text": "Can we split the bill by card, please?",
            "translation": "¿Podemos dividir la cuenta con tarjeta, por favor?",
            "visual_hint": "💳➗",
            "cloze": [2, 4],
            "glossary": [
                {"word": "split", "meaning": "dividir", "ipa": "splɪt"},
                {"word": "bill", "meaning": "cuenta / factura", "ipa": "bɪl"},
            ],
        },
        {
            "id": "side-of-vegetables",
            "text": "Does the dish come with a side of vegetables?",
            "translation": "¿El plato viene con una guarnición de verduras?",
            "visual_hint": "🥦🥕",
            "cloze": [3, 6],
            "glossary": [
                {"word": "dish", "meaning": "plato", "ipa": "dɪʃ"},
                {"word": "side", "meaning": "acompañamiento / guarnición", "ipa": "saɪd"},
            ],
        },
    ],
    "b1-dietary-restrictions": [
        {
            "id": "dairy-free-option",
            "text": "Do you have any dairy-free desserts on the menu?",
            "translation": "¿Tienen algún postre sin lácteos en el menú?",
            "visual_hint": "🍨🚫",
            "cloze": [4, 5],
            "glossary": [
                {"word": "dairy-free", "meaning": "sin lácteos", "ipa": "ˈderi friː"},
                {"word": "desserts", "meaning": "postres", "ipa": "dɪˈzɜːrts"},
            ],
        },
        {
            "id": "olive-oil-instead",
            "text": "Could the chef cook it in olive oil instead of butter?",
            "translation": "¿Podría el chef cocinarlo con aceite de oliva en lugar de mantequilla?",
            "visual_hint": "🫒🍳",
            "cloze": [3, 8],
            "glossary": [
                {"word": "instead of", "meaning": "en lugar de", "ipa": "ɪnˈsted əv"},
                {"word": "butter", "meaning": "mantequilla", "ipa": "ˈbʌtər"},
            ],
        },
        {
            "id": "ingredients-list",
            "text": "I'd appreciate it if you could double-check the dressing ingredients.",
            "translation": "Le agradecería si pudiera revisar dos veces los ingredientes del aderezo.",
            "visual_hint": "🥗🔍",
            "cloze": [1, 6, 8],
            "glossary": [
                {"word": "double-check", "meaning": "verificar dos veces", "ipa": "ˌdʌbəl ˈtʃek"},
                {"word": "dressing", "meaning": "aderezo / aliño", "ipa": "ˈdresɪŋ"},
            ],
        },
    ],
    "a1-bus-ticket": [
        {
            "id": "next-bus-time",
            "text": "What time is the next bus?",
            "translation": "¿A qué hora sale el próximo autobús?",
            "visual_hint": "🕒🚌",
            "cloze": [1, 4],
            "glossary": [
                {"word": "time", "meaning": "hora", "ipa": "taɪm"},
                {"word": "next", "meaning": "próximo / siguiente", "ipa": "nekst"},
            ],
        },
        {
            "id": "pay-by-card",
            "text": "Can I pay by credit card here?",
            "translation": "¿Puedo pagar con tarjeta de crédito aquí?",
            "visual_hint": "💳🚌",
            "cloze": [2, 5],
            "glossary": [
                {"word": "pay", "meaning": "pagar", "ipa": "peɪ"},
                {"word": "credit card", "meaning": "tarjeta de crédito", "ipa": "ˈkredɪt kɑːrd"},
            ],
        },
        {
            "id": "return-ticket",
            "text": "A return ticket for today, please.",
            "translation": "Un boleto de ida y vuelta para hoy, por favor.",
            "visual_hint": "🔁🎫",
            "cloze": [1, 2],
            "glossary": [
                {"word": "return ticket", "meaning": "boleto de ida y vuelta", "ipa": "rɪˈtɜːrn ˈtɪkɪt"},
                {"word": "today", "meaning": "hoy", "ipa": "təˈdeɪ"},
            ],
        },
    ],
    "a2-asking-directions": [
        {
            "id": "cross-the-bridge",
            "text": "Should I cross the bridge or turn left at the corner?",
            "translation": "¿Debo cruzar el puente o girar a la izquierda en la esquina?",
            "visual_hint": "🌉⬅️",
            "cloze": [2, 6, 10],
            "glossary": [
                {"word": "cross", "meaning": "cruzar", "ipa": "krɔːs"},
                {"word": "corner", "meaning": "esquina", "ipa": "ˈkɔːrnər"},
            ],
        },
        {
            "id": "show-on-map",
            "text": "Could you show me on my phone map, please?",
            "translation": "¿Podría mostrármelo en el mapa de mi teléfono, por favor?",
            "visual_hint": "📱🗺️",
            "cloze": [2, 7],
            "glossary": [
                {"word": "show", "meaning": "mostrar / enseñar", "ipa": "ʃoʊ"},
                {"word": "map", "meaning": "mapa", "ipa": "mæp"},
            ],
        },
    ],
    "b1-delayed-flight": [
        {
            "id": "meal-voucher",
            "text": "Are we entitled to a meal voucher or hotel accommodation?",
            "translation": "¿Tenemos derecho a un vale de comida o alojamiento en hotel?",
            "visual_hint": "🎟️🏨",
            "cloze": [2, 5, 8],
            "glossary": [
                {"word": "entitled", "meaning": "con derecho a", "ipa": "ɪnˈtaɪtəld"},
                {"word": "voucher", "meaning": "vale / cupón", "ipa": "ˈvaʊtʃər"},
            ],
        },
        {
            "id": "direct-routing",
            "text": "Is there any seat available on a partner airline tonight?",
            "translation": "¿Hay algún asiento disponible en una aerolínea asociada esta noche?",
            "visual_hint": "🛫💺",
            "cloze": [3, 4, 7],
            "glossary": [
                {"word": "available", "meaning": "disponible", "ipa": "əˈveɪləbəl"},
                {"word": "partner airline", "meaning": "aerolínea aliada", "ipa": "ˈpɑːrtnər ˈerlaɪn"},
            ],
        },
        {
            "id": "boarding-gate-change",
            "text": "Will the new boarding pass be sent to my mobile app?",
            "translation": "¿Se enviará la nueva tarjeta de embarque a mi aplicación móvil?",
            "visual_hint": "📲🎫",
            "cloze": [3, 4, 6],
            "glossary": [
                {"word": "boarding pass", "meaning": "pase de abordar", "ipa": "ˈbɔːrdɪŋ pæs"},
                {"word": "sent", "meaning": "enviado", "ipa": "sent"},
            ],
        },
    ],
    "a1-clothing-store": [
        {
            "id": "different-color",
            "text": "Do you have this shirt in black or navy blue?",
            "translation": "¿Tiene esta camisa en negro o azul marino?",
            "visual_hint": "👔🎨",
            "cloze": [4, 8],
            "glossary": [
                {"word": "shirt", "meaning": "camisa", "ipa": "ʃɜːrt"},
                {"word": "navy blue", "meaning": "azul marino", "ipa": "ˈneɪvi bluː"},
            ],
        },
        {
            "id": "on-sale-today",
            "text": "Is this jacket on sale today?",
            "translation": "¿Está esta chaqueta en oferta hoy?",
            "visual_hint": "🏷️🧥",
            "cloze": [2, 4],
            "glossary": [
                {"word": "jacket", "meaning": "chaqueta", "ipa": "ˈdʒækɪt"},
                {"word": "on sale", "meaning": "en oferta / descuento", "ipa": "ɑːn seɪl"},
            ],
        },
        {
            "id": "take-this-one",
            "text": "It fits well. I will take this one, please.",
            "translation": "Me queda bien. Me llevo esta, por favor.",
            "visual_hint": "🛍️✅",
            "cloze": [1, 5],
            "glossary": [
                {"word": "fits", "meaning": "queda bien de talla", "ipa": "fɪts"},
                {"word": "take", "meaning": "llevar", "ipa": "teɪk"},
            ],
        },
    ],
    "b1-hotel-check-in": [
        {
            "id": "quiet-room-high-floor",
            "text": "Do you happen to have a quiet room on a higher floor?",
            "translation": "¿Por casualidad tienen una habitación tranquila en un piso más alto?",
            "visual_hint": "🏢🤫",
            "cloze": [3, 6, 10],
            "glossary": [
                {"word": "happen to", "meaning": "por casualidad", "ipa": "ˈhæpən tə"},
                {"word": "quiet", "meaning": "tranquila / silenciosa", "ipa": "ˈkwaɪət"},
            ],
        },
        {
            "id": "luggage-storage",
            "text": "Could we store our bags at the front desk after checkout?",
            "translation": "¿Podríamos guardar nuestras maletas en recepción después de entregar la habitación?",
            "visual_hint": "🧳🛎️",
            "cloze": [2, 4, 8],
            "glossary": [
                {"word": "store", "meaning": "guardar / almacenar", "ipa": "stɔːr"},
                {"word": "front desk", "meaning": "recepción", "ipa": "frʌnt desk"},
            ],
        },
    ],
    "b2-returning-damaged-item": [
        {
            "id": "under-warranty",
            "text": "Since it's still under warranty, I'd prefer an immediate replacement.",
            "translation": "Dado que aún está en garantía, preferiría un reemplazo inmediato.",
            "visual_hint": "📜🔄",
            "cloze": [4, 8, 9],
            "glossary": [
                {"word": "warranty", "meaning": "garantía", "ipa": "ˈwɔːrənti"},
                {"word": "replacement", "meaning": "reemplazo", "ipa": "rɪˈpleɪsmənt"},
            ],
        },
        {
            "id": "original-packaging",
            "text": "I brought the original packaging along with the digital invoice.",
            "translation": "Traje el empaque original junto con la factura digital.",
            "visual_hint": "📦🧾",
            "cloze": [3, 4, 9],
            "glossary": [
                {"word": "packaging", "meaning": "empaque / embalaje", "ipa": "ˈpækɪdʒɪŋ"},
                {"word": "invoice", "meaning": "factura", "ipa": "ˈɪnvɔɪs"},
            ],
        },
        {
            "id": "speak-to-supervisor",
            "text": "If store credit is the only option, could we check with a supervisor?",
            "translation": "Si el crédito de tienda es la única opción, ¿podríamos consultarlo con un supervisor?",
            "visual_hint": "🧑‍💼💬",
            "cloze": [2, 9, 12],
            "glossary": [
                {"word": "store credit", "meaning": "crédito en la tienda", "ipa": "stɔːr ˈkredɪt"},
                {"word": "supervisor", "meaning": "supervisor / encargado", "ipa": "ˈsuːpərvaɪzər"},
            ],
        },
    ],
    "a2-meeting-new-people": [
        {
            "id": "how-long-living-here",
            "text": "How long have you been living in this city?",
            "translation": "¿Cuánto tiempo llevas viviendo en esta ciudad?",
            "visual_hint": "🏙️⏳",
            "cloze": [1, 4, 8],
            "glossary": [
                {"word": "how long", "meaning": "cuánto tiempo", "ipa": "haʊ lɔːŋ"},
                {"word": "living", "meaning": "viviendo", "ipa": "ˈlɪvɪŋ"},
            ],
        },
        {
            "id": "keep-in-touch",
            "text": "It was great chatting with you; let's exchange numbers!",
            "translation": "Fue genial charlar contigo; ¡intercambiemos números!",
            "visual_hint": "📱🤝",
            "cloze": [2, 3, 7],
            "glossary": [
                {"word": "chatting", "meaning": "charlando / conversando", "ipa": "ˈtʃætɪŋ"},
                {"word": "exchange", "meaning": "intercambiar", "ipa": "ɪksˈtʃeɪndʒ"},
            ],
        },
        {
            "id": "free-time-hobbies",
            "text": "On weekends I usually go hiking or try new coffee shops.",
            "translation": "Los fines de semana suelo ir de excursión o probar nuevas cafeterías.",
            "visual_hint": "🥾☕",
            "cloze": [3, 5, 7],
            "glossary": [
                {"word": "usually", "meaning": "usualmente / normalmente", "ipa": "ˈjuːʒuəli"},
                {"word": "hiking", "meaning": "senderismo / caminata", "ipa": "ˈhaɪkɪŋ"},
            ],
        },
    ],
    "b2-catching-up-plans": [
        {
            "id": "rain-check",
            "text": "If Friday doesn't work for you, we can always do Saturday brunch.",
            "translation": "Si el viernes no te viene bien, siempre podemos hacer un brunch el sábado.",
            "visual_hint": "🥞📅",
            "cloze": [2, 3, 11],
            "glossary": [
                {"word": "work for you", "meaning": "venirte bien / acomodarte", "ipa": "wɜːrk fɔːr juː"},
                {"word": "brunch", "meaning": "desayuno tardío / brunch", "ipa": "brʌntʃ"},
            ],
        },
        {
            "id": "book-in-advance",
            "text": "That place fills up fast, so I'll book a table in advance.",
            "translation": "Ese lugar se llena rápido, así que reservaré una mesa con anticipación.",
            "visual_hint": "📲🍽️",
            "cloze": [2, 7, 11],
            "glossary": [
                {"word": "fills up", "meaning": "se llena", "ipa": "fɪlz ʌp"},
                {"word": "in advance", "meaning": "con anticipación", "ipa": "ɪn ədˈvæns"},
            ],
        },
        {
            "id": "pick-you-up",
            "text": "I can swing by your place around seven to pick you up.",
            "translation": "Puedo pasar por tu casa alrededor de las siete para recogerte.",
            "visual_hint": "🚗🕖",
            "cloze": [2, 3, 9],
            "glossary": [
                {"word": "swing by", "meaning": "pasar rápidamente por", "ipa": "swɪŋ baɪ"},
                {"word": "pick you up", "meaning": "recogerte", "ipa": "pɪk juː ʌp"},
            ],
        },
    ],
    "c2-dinner-debate": [
        {
            "id": "unintended-consequences",
            "text": "We shouldn't overlook the unintended consequences of algorithmic curation.",
            "translation": "No deberíamos pasar por alto las consecuencias imprevistas de la curaduría algorítmica.",
            "visual_hint": "🧠⚖️",
            "cloze": [2, 4, 5],
            "glossary": [
                {"word": "overlook", "meaning": "pasar por alto", "ipa": "ˌoʊvərˈlʊk"},
                {"word": "unintended", "meaning": "imprevistas / no intencionadas", "ipa": "ˌʌnɪnˈtendɪd"},
            ],
        },
        {
            "id": "common-ground",
            "text": "Even if we diverge on regulation, we clearly share common ground on ethics.",
            "translation": "Incluso si discrepamos en la regulación, claramente compartimos puntos en común sobre la ética.",
            "visual_hint": "🤝🌐",
            "cloze": [3, 9, 10],
            "glossary": [
                {"word": "diverge", "meaning": "divergir / discrepar", "ipa": "daɪˈvɜːrdʒ"},
                {"word": "common ground", "meaning": "terreno común / acuerdo base", "ipa": "ˈkɑːmən ɡraʊnd"},
            ],
        },
        {
            "id": "empirical-evidence",
            "text": "Anecdotes are compelling, yet the empirical evidence points toward a more nuanced reality.",
            "translation": "Las anécdotas son convincentes, pero la evidencia empírica apunta hacia una realidad más matizada.",
            "visual_hint": "📊🔬",
            "cloze": [2, 5, 11],
            "glossary": [
                {"word": "compelling", "meaning": "convincente", "ipa": "kəmˈpelɪŋ"},
                {"word": "empirical", "meaning": "empírica", "ipa": "ɪmˈpɪrɪkəl"},
            ],
        },
    ],
    "b2-job-interview": [
        {
            "id": "tight-deadlines",
            "text": "I thrive in collaborative environments where we solve complex problems under tight deadlines.",
            "translation": "Me desenvuelvo muy bien en entornos colaborativos donde resolvemos problemas complejos con plazos ajustados.",
            "visual_hint": "⚡🤝",
            "cloze": [1, 3, 11],
            "glossary": [
                {"word": "thrive", "meaning": "prosperar / destacar", "ipa": "θraɪv"},
                {"word": "tight deadlines", "meaning": "plazos ajustados", "ipa": "taɪt ˈdedlaɪnz"},
            ],
        },
        {
            "id": "measurable-impact",
            "text": "Within two quarters, that initiative boosted customer retention by eighteen percent.",
            "translation": "En dos trimestres, esa iniciativa impulsó la retención de clientes en un dieciocho por ciento.",
            "visual_hint": "📈🎯",
            "cloze": [2, 5, 7],
            "glossary": [
                {"word": "quarters", "meaning": "trimestres", "ipa": "ˈkwɔːrtərz"},
                {"word": "boosted", "meaning": "impulsó / aumentó", "ipa": "ˈbuːstɪd"},
            ],
        },
        {
            "id": "onboarding-expectations",
            "text": "What would success look like in the first ninety days of this role?",
            "translation": "¿Cómo se vería el éxito en los primeros noventa días de este puesto?",
            "visual_hint": "🗓️🏆",
            "cloze": [2, 3, 8],
            "glossary": [
                {"word": "success", "meaning": "éxito", "ipa": "səkˈses"},
                {"word": "role", "meaning": "puesto / rol", "ipa": "roʊl"},
            ],
        },
    ],
    "c1-negotiating-deadline": [
        {
            "id": "parallel-workstreams",
            "text": "We can run QA testing in parallel to compress the critical path.",
            "translation": "Podemos ejecutar las pruebas de calidad en paralelo para comprimir la ruta crítica.",
            "visual_hint": "🔀⚙️",
            "cloze": [5, 7, 10],
            "glossary": [
                {"word": "in parallel", "meaning": "en paralelo", "ipa": "ɪn ˈpærəlel"},
                {"word": "compress", "meaning": "comprimir / acortar", "ipa": "kəmˈpres"},
            ],
        },
        {
            "id": "stakeholder-sign-off",
            "text": "Once we secure stakeholder sign-off today, we'll lock in the sprint scope.",
            "translation": "Una vez que aseguremos la aprobación de los interesados hoy, fijaremos el alcance del sprint.",
            "visual_hint": "✍️🔒",
            "cloze": [2, 4, 7],
            "glossary": [
                {"word": "sign-off", "meaning": "aprobación formal", "ipa": "ˈsaɪn ɔːf"},
                {"word": "lock in", "meaning": "asegurar / fijar", "ipa": "lɑːk ɪn"},
            ],
        },
    ],
    "c2-executive-pitch": [
        {
            "id": "downside-mitigation",
            "text": "We've ring-fenced the downside risk by staging capital deployment across three milestones.",
            "translation": "Hemos acotado el riesgo de pérdida escalonando el despliegue de capital en tres hitos.",
            "visual_hint": "🛡️🏛️",
            "cloze": [1, 3, 7, 11],
            "glossary": [
                {"word": "ring-fenced", "meaning": "blindado / aislado financieramente", "ipa": "ˈrɪŋ fenst"},
                {"word": "milestones", "meaning": "hitos", "ipa": "ˈmaɪlstoʊnz"},
            ],
        },
        {
            "id": "unit-economics",
            "text": "Our unit economics turn cash-flow positive well before the Series B runway expires.",
            "translation": "Nuestra economía unitaria genera flujo de caja positivo mucho antes de que expire el capital de la Serie B.",
            "visual_hint": "💹🏦",
            "cloze": [1, 2, 4, 11],
            "glossary": [
                {"word": "unit economics", "meaning": "economía unitaria", "ipa": "ˈjuːnɪt ˌiːkəˈnɑːmɪks"},
                {"word": "runway", "meaning": "margen de liquidez", "ipa": "ˈrʌnweɪ"},
            ],
        },
        {
            "id": "board-alignment",
            "text": "With the board's green light today, we can execute the rollout by Q3.",
            "translation": "Con la luz verde del directorio hoy, podemos ejecutar el lanzamiento para el tercer trimestre.",
            "visual_hint": "🟢🚀",
            "cloze": [3, 4, 8, 10],
            "glossary": [
                {"word": "green light", "meaning": "aprobación / luz verde", "ipa": "ɡriːn laɪt"},
                {"word": "rollout", "meaning": "despliegue / lanzamiento", "ipa": "ˈroʊlaʊt"},
            ],
        },
    ],
    "a2-pharmacy-symptoms": [
        {
            "id": "any-allergies-meds",
            "text": "I am not allergic to any medication, as far as I know.",
            "translation": "No soy alérgico a ningún medicamento, que yo sepa.",
            "visual_hint": "💊✅",
            "cloze": [3, 6, 8],
            "glossary": [
                {"word": "allergic", "meaning": "alérgico", "ipa": "əˈlɜːrdʒɪk"},
                {"word": "as far as I know", "meaning": "que yo sepa", "ipa": "æz fɑːr æz aɪ noʊ"},
            ],
        },
        {
            "id": "throat-lozenges",
            "text": "Do you also have honey lozenges for a dry cough?",
            "translation": "¿También tiene pastillas de miel para la tos seca?",
            "visual_hint": "🍯🍬",
            "cloze": [4, 5, 9],
            "glossary": [
                {"word": "lozenges", "meaning": "pastillas para chupar", "ipa": "ˈlɑːzɪndʒɪz"},
                {"word": "cough", "meaning": "tos", "ipa": "kɔːf"},
            ],
        },
        {
            "id": "with-food-or-water",
            "text": "Should I take these tablets with food or on an empty stomach?",
            "translation": "¿Debo tomar estas pastillas con comida o con el estómago vacío?",
            "visual_hint": "🍽️🥛",
            "cloze": [4, 6, 10],
            "glossary": [
                {"word": "tablets", "meaning": "comprimidos / pastillas", "ipa": "ˈtæbləts"},
                {"word": "empty stomach", "meaning": "estómago vacío / en ayunas", "ipa": "ˈempti ˈstʌmək"},
            ],
        },
    ],
    "b1-doctors-appointment": [
        {
            "id": "need-an-xray",
            "text": "Do you think I need an X-ray to rule out a fracture?",
            "translation": "¿Cree que necesito una radiografía para descartar una fractura?",
            "visual_hint": "🩻🦴",
            "cloze": [5, 7, 11],
            "glossary": [
                {"word": "X-ray", "meaning": "radiografía", "ipa": "ˈeks reɪ"},
                {"word": "rule out", "meaning": "descartar", "ipa": "ruːl aʊt"},
            ],
        },
        {
            "id": "keep-it-elevated",
            "text": "How many days should I keep my leg elevated and apply ice?",
            "translation": "¿Cuántos días debo mantener la pierna elevada y aplicar hielo?",
            "visual_hint": "🧊🦵",
            "cloze": [5, 8, 10],
            "glossary": [
                {"word": "elevated", "meaning": "elevada", "ipa": "ˈelɪveɪtɪd"},
                {"word": "apply", "meaning": "aplicar", "ipa": "əˈplaɪ"},
            ],
        },
        {
            "id": "medical-certificate",
            "text": "Could you write a medical certificate so I can rest from work?",
            "translation": "¿Podría extenderme un certificado médico para poder descansar del trabajo?",
            "visual_hint": "📋🏥",
            "cloze": [4, 5, 9],
            "glossary": [
                {"word": "medical certificate", "meaning": "certificado / justificante médico", "ipa": "ˈmedɪkəl sərˈtɪfɪkət"},
                {"word": "rest", "meaning": "descansar", "ipa": "rest"},
            ],
        },
    ],
    "c1-insurance-claim": [
        {
            "id": "direct-billing",
            "text": "Can your case management team arrange direct billing with the clinic?",
            "translation": "¿Puede su equipo de gestión de casos coordinar el pago directo con la clínica?",
            "visual_hint": "🏥💳",
            "cloze": [3, 6, 7],
            "glossary": [
                {"word": "arrange", "meaning": "coordinar / gestionar", "ipa": "əˈreɪndʒ"},
                {"word": "direct billing", "meaning": "facturación directa", "ipa": "dəˈrekt ˈbɪlɪŋ"},
            ],
        },
        {
            "id": "reimbursement-timeline",
            "text": "Once I upload the receipts, what is the standard turnaround time for reimbursement?",
            "translation": "Una vez que suba los recibos, ¿cuál es el plazo estándar de respuesta para el reembolso?",
            "visual_hint": "⏱️💸",
            "cloze": [2, 8, 9, 12],
            "glossary": [
                {"word": "turnaround time", "meaning": "tiempo de tramitación", "ipa": "ˈtɜːrnəraʊnd taɪm"},
                {"word": "reimbursement", "meaning": "reembolso", "ipa": "ˌriːɪmˈbɜːrsmənt"},
            ],
        },
        {
            "id": "claim-reference-number",
            "text": "Please email me the claim reference number so I have a written audit trail.",
            "translation": "Por favor envíeme por correo el número de referencia del reclamo para tener un registro escrito.",
            "visual_hint": "📧🔢",
            "cloze": [4, 5, 12],
            "glossary": [
                {"word": "claim", "meaning": "reclamo / siniestro", "ipa": "kleɪm"},
                {"word": "audit trail", "meaning": "registro de auditoría / respaldo", "ipa": "ˈɔːdɪt treɪl"},
            ],
        },
    ],
}

# 2. Eighteen brand-new scenarios so EVERY module has ALL 6 CEFR levels (A1, A2, B1, B2, C1, C2)
NEW_SCENARIOS: list[dict] = [
    # --- MODULE 1: food-and-drink (missing B2, C1, C2) ---
    {
        "id": "b2-hosting-business-lunch",
        "title": "Hosting a business lunch",
        "title_es": "Anfitrión en un almuerzo de negocios",
        "cefr": "B2",
        "topic": "food-and-drink",
        "description": "Da la bienvenida a clientes en un restaurante, sugiere entradas para compartir y hazte cargo de la cuenta con cortesía.",
        "phrases": [
            {
                "id": "reserved-table-under",
                "text": "Good afternoon, we have a reservation for four under the name Martinez.",
                "translation": "Buenas tardes, tenemos una reservación para cuatro a nombre de Martínez.",
                "visual_hint": "📋🍽️",
                "cloze": [4, 8],
                "glossary": [
                    {"word": "reservation", "meaning": "reservación", "ipa": "ˌrezərˈveɪʃən"},
                    {"word": "under the name", "meaning": "a nombre de", "ipa": "ˈʌndər ðə neɪm"},
                ],
            },
            {
                "id": "order-appetizers",
                "text": "Shall we order a few appetizers for the table while we look over the menu?",
                "translation": "¿Pedimos algunas entradas para la mesa mientras revisamos el menú?",
                "visual_hint": "🥗🥖",
                "cloze": [2, 5, 11],
                "glossary": [
                    {"word": "appetizers", "meaning": "entradas / aperitivos", "ipa": "ˈæpɪtaɪzərz"},
                    {"word": "look over", "meaning": "revisar / echar un vistazo", "ipa": "lʊk ˈoʊvər"},
                ],
            },
            {
                "id": "seasonal-specials",
                "text": "Could you tell us about today's seasonal specials and fresh catch?",
                "translation": "¿Podría contarnos sobre los platos especiales de temporada de hoy y la pesca del día?",
                "visual_hint": "🐟🌿",
                "cloze": [6, 7, 10],
                "glossary": [
                    {"word": "seasonal", "meaning": "de temporada", "ipa": "ˈsiːzənəl"},
                    {"word": "fresh catch", "meaning": "pesca fresca del día", "ipa": "freʃ kætʃ"},
                ],
            },
            {
                "id": "medium-rare-steak",
                "text": "I'd like the ribeye cooked medium-rare with roasted asparagus on the side.",
                "translation": "Quisiera el ojo de bife término medio-rojo con espárragos asados de guarnición.",
                "visual_hint": "🥩🌱",
                "cloze": [4, 5, 7],
                "glossary": [
                    {"word": "medium-rare", "meaning": "término medio-rojo / al punto menos", "ipa": "ˌmiːdiəm ˈrer"},
                    {"word": "roasted", "meaning": "asados", "ipa": "ˈroʊstɪd"},
                ],
            },
            {
                "id": "espresso-after-meal",
                "text": "Would anyone care for an espresso or dessert before we wrap up?",
                "translation": "¿A alguien le apetece un espresso o postre antes de que terminemos?",
                "visual_hint": "☕🍰",
                "cloze": [2, 5, 10],
                "glossary": [
                    {"word": "care for", "meaning": "apetecer / gustar", "ipa": "ker fɔːr"},
                    {"word": "wrap up", "meaning": "concluir / cerrar", "ipa": "ræp ʌp"},
                ],
            },
            {
                "id": "this-one-is-on-us",
                "text": "Please put everything on one check; this lunch is on us today.",
                "translation": "Por favor ponga todo en una sola cuenta; este almuerzo corre por nuestra cuenta hoy.",
                "visual_hint": "💳🤝",
                "cloze": [5, 9, 10],
                "glossary": [
                    {"word": "one check", "meaning": "una sola cuenta", "ipa": "wʌn tʃek"},
                    {"word": "on us", "meaning": "invitamos nosotros / corre por nuestra cuenta", "ipa": "ɑːn ʌs"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "head waiter",
            "user_role": "business host",
            "setting": "A modern upscale bistro during a client lunch meeting.",
            "turns": [
                {"speaker": "ai", "text": "Good afternoon! Welcome to The Olive Tree. Do you have a reservation with us?"},
                {
                    "speaker": "user",
                    "goal": "Indica que tienes una reservación para cuatro a nombre de Martínez.",
                    "suggested_lines": [
                        "Good afternoon, we have a reservation for four under the name Martinez.",
                        "Yes, a table for four under Martinez, please.",
                    ],
                },
                {"speaker": "ai", "text": "Right this way. Here are your menus. Would you like to start with something for the table?"},
                {
                    "speaker": "user",
                    "goal": "Pregunta por las especialidades de temporada y sugiere pedir entradas.",
                    "suggested_lines": [
                        "Could you tell us about today's seasonal specials and fresh catch?",
                        "Shall we order a few appetizers for the table while we look over the menu?",
                    ],
                },
                {"speaker": "ai", "text": "Today we have wild sea bass and prime ribeye. What can I get for your main course?"},
                {
                    "speaker": "user",
                    "goal": "Ordena el corte de carne término medio-rojo con espárragos.",
                    "suggested_lines": [
                        "I'd like the ribeye cooked medium-rare with roasted asparagus on the side.",
                        "I'll have the ribeye medium-rare with asparagus, please.",
                    ],
                },
                {"speaker": "ai", "text": "Wonderful. Now that you've finished your mains, how should I prepare the bill?"},
                {
                    "speaker": "user",
                    "goal": "Pide todo en una sola cuenta e indica que tú invitas.",
                    "suggested_lines": [
                        "Please put everything on one check; this lunch is on us today.",
                        "One check for the whole table, please.",
                    ],
                },
                {"speaker": "ai", "text": "Certainly! I'll bring the card terminal right over."},
            ],
        },
    },
    {
        "id": "c1-wine-tasting-pairing",
        "title": "Sommelier pairing & tasting notes",
        "title_es": "Maridaje y cata con el sommelier",
        "cefr": "C1",
        "topic": "food-and-drink",
        "description": "Conversa con un sommelier sobre acidez, cuerpo y maridaje ideal para un menú degustación.",
        "phrases": [
            {
                "id": "crisp-acidity",
                "text": "We're looking for a dry white with crisp acidity to complement the ceviche.",
                "translation": "Buscamos un blanco seco con acidez fresca para complementar el ceviche.",
                "visual_hint": "🥂🍋",
                "cloze": [4, 7, 10],
                "glossary": [
                    {"word": "crisp acidity", "meaning": "acidez fresca / viva", "ipa": "krɪsp əˈsɪdəti"},
                    {"word": "complement", "meaning": "complementar / realzar", "ipa": "ˈkɑːmplɪment"},
                ],
            },
            {
                "id": "velvety-tannins",
                "text": "Ideally, the red should have velvety tannins that won't overpower the duck.",
                "translation": "Idealmente, el tinto debería tener taninos aterciopelados que no opaquen el pato.",
                "visual_hint": "🍷🦆",
                "cloze": [5, 6, 9],
                "glossary": [
                    {"word": "velvety tannins", "meaning": "taninos suaves / aterciopelados", "ipa": "ˈvelvɪti ˈtænɪnz"},
                    {"word": "overpower", "meaning": "opacar / dominar en sabor", "ipa": "ˌoʊvərˈpaʊər"},
                ],
            },
            {
                "id": "decant-the-bottle",
                "text": "Would you recommend decanting this vintage for half an hour before serving?",
                "translation": "¿Recomendaría decantar esta cosecha durante media hora antes de servir?",
                "visual_hint": "🏺🍷",
                "cloze": [3, 5, 11],
                "glossary": [
                    {"word": "decanting", "meaning": "decantar / oxigenar el vino", "ipa": "dɪˈkæntɪŋ"},
                    {"word": "vintage", "meaning": "añada / cosecha", "ipa": "ˈvɪntɪdʒ"},
                ],
            },
            {
                "id": "mineral-undertones",
                "text": "On the palate, it has subtle mineral undertones and a lingering finish.",
                "translation": "En boca, tiene sutiles matices minerales y un final persistente.",
                "visual_hint": "✨🍇",
                "cloze": [2, 6, 10],
                "glossary": [
                    {"word": "palate", "meaning": "paladar / en boca", "ipa": "ˈpælət"},
                    {"word": "lingering", "meaning": "persistente / prolongado", "ipa": "ˈlɪŋɡərɪŋ"},
                ],
            },
            {
                "id": "by-the-glass-pairing",
                "text": "Could we opt for the curated by-the-glass pairing across all five courses?",
                "translation": "¿Podríamos optar por el maridaje por copa seleccionado para los cinco tiempos?",
                "visual_hint": "🍷🍽️",
                "cloze": [2, 6, 11],
                "glossary": [
                    {"word": "opt for", "meaning": "optar por / elegir", "ipa": "ɑːpt fɔːr"},
                    {"word": "courses", "meaning": "tiempos del menú", "ipa": "ˈkɔːrsɪz"},
                ],
            },
            {
                "id": "non-alcoholic-botanical",
                "text": "Do you also offer a zero-proof botanical pairing for one of our guests?",
                "translation": "¿Ofrecen también un maridaje botánico sin alcohol para uno de nuestros invitados?",
                "visual_hint": "🌿🥂",
                "cloze": [5, 6, 7],
                "glossary": [
                    {"word": "zero-proof", "meaning": "sin graduación alcohólica", "ipa": "ˈzɪroʊ pruːf"},
                    {"word": "botanical", "meaning": "botánico / herbal", "ipa": "bəˈtænɪkəl"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "sommelier",
            "user_role": "guest",
            "setting": "A tasting-menu restaurant selecting wine and zero-proof pairings.",
            "turns": [
                {"speaker": "ai", "text": "Good evening. I see you've chosen the five-course tasting menu. What styles of wine do you enjoy?"},
                {
                    "speaker": "user",
                    "goal": "Pide un blanco seco con buena acidez para el ceviche.",
                    "suggested_lines": [
                        "We're looking for a dry white with crisp acidity to complement the ceviche.",
                        "Something dry with crisp acidity for the starter.",
                    ],
                },
                {"speaker": "ai", "text": "An Albariño would be stellar. And for the roasted duck breast in the third course?"},
                {
                    "speaker": "user",
                    "goal": "Pide un tinto con taninos suaves que no opaque el pato.",
                    "suggested_lines": [
                        "Ideally, the red should have velvety tannins that won't overpower the duck.",
                        "A red with velvety tannins that won't overpower the dish.",
                    ],
                },
                {"speaker": "ai", "text": "Here is a taste of our aged Pinot Noir. What are your impressions on the palate?"},
                {
                    "speaker": "user",
                    "goal": "Describe sus matices minerales y final persistente.",
                    "suggested_lines": [
                        "On the palate, it has subtle mineral undertones and a lingering finish.",
                        "It has lovely mineral undertones and a lingering finish.",
                    ],
                },
                {"speaker": "ai", "text": "Spot on. Would the whole table like the full wine flight?"},
                {
                    "speaker": "user",
                    "goal": "Pregunta si tienen maridaje botánico sin alcohol para uno de los invitados.",
                    "suggested_lines": [
                        "Do you also offer a zero-proof botanical pairing for one of our guests?",
                        "Could we get the wine pairing plus one zero-proof botanical pairing?",
                    ],
                },
                {"speaker": "ai", "text": "Absolutely, our house-fermented botanical infusions pair beautifully with every course."},
            ],
        },
    },
    {
        "id": "c2-culinary-critique",
        "title": "Gastronomic critique & chef's table",
        "title_es": "Crítica gastronómica en la mesa del chef",
        "cefr": "C2",
        "topic": "food-and-drink",
        "description": "Dialoga con el chef ejecutivo sobre técnicas de fermentación, contraste de texturas y trazabilidad de ingredientes.",
        "phrases": [
            {
                "id": "textural-juxtaposition",
                "text": "The textural juxtaposition between the crispy skin and the silky purée was sublime.",
                "translation": "El contraste de texturas entre la piel crujiente y el puré sedoso fue sublime.",
                "visual_hint": "👨‍🍳✨",
                "cloze": [1, 2, 9, 12],
                "glossary": [
                    {"word": "juxtaposition", "meaning": "contraste / yuxtaposición", "ipa": "ˌdʒʌkstəpəˈzɪʃən"},
                    {"word": "sublime", "meaning": "sublime / extraordinario", "ipa": "səˈblaɪm"},
                ],
            },
            {
                "id": "umami-depth",
                "text": "Fermenting the black garlic clearly imparted an extraordinary depth of umami to the broth.",
                "translation": "Fermentar el ajo negro claramente aportó una extraordinaria profundidad de umami al caldo.",
                "visual_hint": "🧄🍲",
                "cloze": [0, 5, 8, 13],
                "glossary": [
                    {"word": "imparted", "meaning": "aportó / confirió", "ipa": "ɪmˈpɑːrtɪd"},
                    {"word": "broth", "meaning": "caldo / consomé", "ipa": "brɔːθ"},
                ],
            },
            {
                "id": "hyper-local-sourcing",
                "text": "How do you maintain menu consistency while relying strictly on hyper-local foraging?",
                "translation": "¿Cómo mantienen la consistencia del menú dependiendo estrictamente de la recolección hiperlocal?",
                "visual_hint": "🍄🌱",
                "cloze": [4, 7, 11],
                "glossary": [
                    {"word": "relying on", "meaning": "dependiendo de / apoyándose en", "ipa": "rɪˈlaɪɪŋ ɑːn"},
                    {"word": "foraging", "meaning": "recolección silvestre", "ipa": "ˈfɔːrɪdʒɪŋ"},
                ],
            },
            {
                "id": "restraint-in-plating",
                "text": "What struck me most was the restraint in plating—every element earned its place.",
                "translation": "Lo que más me impresionó fue la sobriedad en el emplatado: cada elemento se ganó su lugar.",
                "visual_hint": "🍽️🎨",
                "cloze": [1, 6, 8, 11],
                "glossary": [
                    {"word": "struck me", "meaning": "me llamó la atención / impresionó", "ipa": "strʌk miː"},
                    {"word": "restraint", "meaning": "sobriedad / mesura", "ipa": "rɪˈstreɪnt"},
                ],
            },
            {
                "id": "smoke-infusion",
                "text": "Had the smoke infusion been even slightly heavier, it might have masked the scallop's sweetness.",
                "translation": "Si la infusión de humo hubiera sido apenas más intensa, habría ocultado el dulzor de la vieira.",
                "visual_hint": "💨🐚",
                "cloze": [2, 6, 10, 14],
                "glossary": [
                    {"word": "masked", "meaning": "enmascarado / ocultado", "ipa": "mæskt"},
                    {"word": "scallop", "meaning": "vieira / callo de hacha", "ipa": "ˈskɑːləp"},
                ],
            },
            {
                "id": "culinary-narrative",
                "text": "Each course unfolded like a cohesive narrative bridging ancestral technique and modern precision.",
                "translation": "Cada tiempo se desplegó como una narrativa cohesiva que une técnica ancestral y precisión moderna.",
                "visual_hint": "📖🔥",
                "cloze": [2, 5, 7, 9],
                "glossary": [
                    {"word": "unfolded", "meaning": "se desenvolvió / desplegó", "ipa": "ʌnˈfoʊldɪd"},
                    {"word": "bridging", "meaning": "tendiendo un puente / uniendo", "ipa": "ˈbrɪdʒɪŋ"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "executive chef",
            "user_role": "culinary critic",
            "setting": "Chef's counter at the end of a twelve-course tasting menu.",
            "turns": [
                {"speaker": "ai", "text": "Thank you for dining at the counter tonight. What did you think of the seared scallop and black garlic course?"},
                {
                    "speaker": "user",
                    "goal": "Elogia el contraste de texturas y la profundidad umami del ajo negro fermentado.",
                    "suggested_lines": [
                        "The textural juxtaposition between the crispy skin and the silky purée was sublime.",
                        "Fermenting the black garlic clearly imparted an extraordinary depth of umami to the broth.",
                    ],
                },
                {"speaker": "ai", "text": "We calibrate the cold-smoking to the second so we don't overwhelm the shellfish."},
                {
                    "speaker": "user",
                    "goal": "Comenta que un humo más intenso habría ocultado el dulzor de la vieira.",
                    "suggested_lines": [
                        "Had the smoke infusion been even slightly heavier, it might have masked the scallop's sweetness.",
                        "The balance was exact; any heavier smoke would have masked the sweetness.",
                    ],
                },
                {"speaker": "ai", "text": "All our herbs and mushrooms are foraged within thirty miles of the kitchen each morning."},
                {
                    "speaker": "user",
                    "goal": "Pregunta cómo mantienen la consistencia dependiendo de ingredientes silvestres locales.",
                    "suggested_lines": [
                        "How do you maintain menu consistency while relying strictly on hyper-local foraging?",
                        "How do you balance consistency with hyper-local foraging?",
                    ],
                },
                {"speaker": "ai", "text": "We adapt the micro-garnishes daily while keeping the core flavor architecture intact."},
                {
                    "speaker": "user",
                    "goal": "Destaca la sobriedad del emplatado y la narrativa cohesiva del menú.",
                    "suggested_lines": [
                        "What struck me most was the restraint in plating—every element earned its place.",
                        "Each course unfolded like a cohesive narrative bridging ancestral technique and modern precision.",
                    ],
                },
                {"speaker": "ai", "text": "That means the world to our brigade. It was an honor cooking for you tonight."},
            ],
        },
    },
    # --- MODULE 2: travel-and-transport (missing B2, C1, C2) ---
    {
        "id": "b2-car-rental-dispute",
        "title": "Resolving a car rental issue",
        "title_es": "Resolver un cargo en alquiler de auto",
        "cefr": "B2",
        "topic": "travel-and-transport",
        "description": "Aclara un cobro indebido en la devolución de un auto alquilado mostrando fotos previas y cobertura contratada.",
        "phrases": [
            {
                "id": "pre-existing-scratch",
                "text": "That scratch on the rear bumper was already documented on the pickup inspection sheet.",
                "translation": "Ese rasguño en el parachoques trasero ya estaba documentado en la hoja de inspección al recogerlo.",
                "visual_hint": "🚗📋",
                "cloze": [1, 4, 8, 12],
                "glossary": [
                    {"word": "rear bumper", "meaning": "parachoques trasero", "ipa": "rɪr ˈbʌmpər"},
                    {"word": "documented", "meaning": "documentado / registrado", "ipa": "ˈdɑːkjəmentɪd"},
                ],
            },
            {
                "id": "timestamped-photos",
                "text": "I took timestamped photos in the garage before driving off the lot.",
                "translation": "Tomé fotos con fecha y hora en el garaje antes de salir del estacionamiento.",
                "visual_hint": "📸🕒",
                "cloze": [2, 3, 8, 11],
                "glossary": [
                    {"word": "timestamped", "meaning": "con marca de fecha y hora", "ipa": "ˈtaɪmstæmpt"},
                    {"word": "lot", "meaning": "lote / estacionamiento", "ipa": "lɑːt"},
                ],
            },
            {
                "id": "full-tank-receipt",
                "text": "I refueled two miles away and have the gas station receipt right here.",
                "translation": "Recargué combustible a dos millas de aquí y tengo el recibo de la gasolinera justo aquí.",
                "visual_hint": "⛽🧾",
                "cloze": [1, 8, 10],
                "glossary": [
                    {"word": "refueled", "meaning": "reposté / llené el tanque", "ipa": "ˌriːˈfjuːəld"},
                    {"word": "receipt", "meaning": "recibo / comprobante", "ipa": "rɪˈsiːt"},
                ],
            },
            {
                "id": "comprehensive-waiver",
                "text": "My booking includes the zero-deductible collision damage waiver.",
                "translation": "Mi reserva incluye la exención de daños por colisión con cero deducible.",
                "visual_hint": "🛡️📄",
                "cloze": [2, 4, 6, 7],
                "glossary": [
                    {"word": "zero-deductible", "meaning": "sin franquicia / cero deducible", "ipa": "ˈzɪroʊ dɪˈdʌktəbəl"},
                    {"word": "waiver", "meaning": "exención de responsabilidad", "ipa": "ˈweɪvər"},
                ],
            },
            {
                "id": "remove-extra-fee",
                "text": "Could you please remove the refueling surcharge and send an updated invoice?",
                "translation": "¿Podría por favor eliminar el recargo por combustible y enviarme una factura actualizada?",
                "visual_hint": "💻✅",
                "cloze": [3, 6, 10],
                "glossary": [
                    {"word": "surcharge", "meaning": "recargo adicional", "ipa": "ˈsɜːrtʃɑːrdʒ"},
                    {"word": "updated", "meaning": "actualizada", "ipa": "ˌʌpˈdeɪtɪd"},
                ],
            },
            {
                "id": "release-security-deposit",
                "text": "How soon will the security deposit hold be released on my credit card?",
                "translation": "¿Qué tan pronto se liberará la retención del depósito de garantía en mi tarjeta de crédito?",
                "visual_hint": "🔓💳",
                "cloze": [4, 5, 8],
                "glossary": [
                    {"word": "security deposit", "meaning": "depósito de seguridad", "ipa": "sɪˈkjʊrəti dɪˈpɑːzɪt"},
                    {"word": "released", "meaning": "liberado", "ipa": "rɪˈliːst"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "rental return agent",
            "user_role": "traveler",
            "setting": "Airport car rental return desk before a flight.",
            "turns": [
                {"speaker": "ai", "text": "Welcome back. Looking at the vehicle, there's a scratch on the rear bumper and a refueling fee on your statement."},
                {
                    "speaker": "user",
                    "goal": "Explica que el rasguño ya estaba registrado y tienes fotos con hora.",
                    "suggested_lines": [
                        "That scratch on the rear bumper was already documented on the pickup inspection sheet.",
                        "I took timestamped photos in the garage before driving off the lot.",
                    ],
                },
                {"speaker": "ai", "text": "Oh, let me check the original check-out form. You're right, it's marked here. What about the fuel level?"},
                {
                    "speaker": "user",
                    "goal": "Muestra el recibo de la gasolinera y pide eliminar el recargo.",
                    "suggested_lines": [
                        "I refueled two miles away and have the gas station receipt right here.",
                        "Could you please remove the refueling surcharge and send an updated invoice?",
                    ],
                },
                {"speaker": "ai", "text": "Got it, I've waived the fuel charge and noted your zero-deductible coverage."},
                {
                    "speaker": "user",
                    "goal": "Confirma tu cobertura sin deducible y pregunta cuándo liberan el depósito.",
                    "suggested_lines": [
                        "How soon will the security deposit hold be released on my credit card?",
                        "My booking includes the zero-deductible collision damage waiver.",
                    ],
                },
                {"speaker": "ai", "text": "The hold is released immediately and reflects within two business days. Here is your zero-balance receipt!"},
                {
                    "speaker": "user",
                    "goal": "Agradece y pide que envíen la factura actualizada a tu correo.",
                    "suggested_lines": [
                        "Thank you, please email me the updated invoice as well.",
                        "Could you please remove the refueling surcharge and send an updated invoice?",
                    ],
                },
                {"speaker": "ai", "text": "Just sent it to your inbox. Safe travels home!"},
            ],
        },
    },
    {
        "id": "c1-customs-declaration",
        "title": "Customs inspection & commercial samples",
        "title_es": "Inspección de aduana y muestras comerciales",
        "cefr": "C1",
        "topic": "travel-and-transport",
        "description": "Explica en control aduanero el ingreso temporal de prototipos para una feria tecnológica sin fines de venta.",
        "phrases": [
            {
                "id": "temporary-importation",
                "text": "These hardware prototypes are strictly for exhibition at the trade summit and not for resale.",
                "translation": "Estos prototipos de hardware son estrictamente para exhibición en la cumbre comercial y no para reventa.",
                "visual_hint": "🛂📦",
                "cloze": [2, 6, 14],
                "glossary": [
                    {"word": "prototypes", "meaning": "prototipos", "ipa": "ˈproʊtətaɪps"},
                    {"word": "resale", "meaning": "reventa", "ipa": "ˈriːseɪl"},
                ],
            },
            {
                "id": "ata-carnet-document",
                "text": "Here is our itemized ATA Carnet certifying that all equipment will be re-exported next Friday.",
                "translation": "Aquí está nuestro cuaderno ATA detallado certificando que todo el equipo será reexportado el próximo viernes.",
                "visual_hint": "📑✈️",
                "cloze": [3, 6, 12],
                "glossary": [
                    {"word": "itemized", "meaning": "desglosado / detallado", "ipa": "ˈaɪtəmaɪzd"},
                    {"word": "re-exported", "meaning": "reexportado", "ipa": "ˌriːɪkˈspɔːrtɪd"},
                ],
            },
            {
                "id": "serial-numbers-match",
                "text": "Every serial number on the pelican case corresponds directly to the manifest.",
                "translation": "Cada número de serie en el maletín protector corresponde directamente con el manifiesto de carga.",
                "visual_hint": "🔢🧳",
                "cloze": [1, 7, 11],
                "glossary": [
                    {"word": "corresponds", "meaning": "corresponde / coincide", "ipa": "ˌkɔːrəˈspɑːndz"},
                    {"word": "manifest", "meaning": "manifiesto de carga", "ipa": "ˈmænɪfest"},
                ],
            },
            {
                "id": "nominal-commercial-value",
                "text": "They are non-functional display units carrying only nominal commercial value.",
                "translation": "Son unidades de demostración no funcionales con un valor comercial meramente simbólico.",
                "visual_hint": "🏷️💻",
                "cloze": [2, 4, 7],
                "glossary": [
                    {"word": "display units", "meaning": "unidades de exhibición", "ipa": "dɪˈspleɪ ˈjuːnɪts"},
                    {"word": "nominal", "meaning": "nominal / simbólico", "ipa": "ˈnɑːmɪnəl"},
                ],
            },
            {
                "id": "customs-stamp-departure",
                "text": "Which counter should we report to upon departure to have the export voucher stamped?",
                "translation": "¿A qué mostrador debemos presentarnos al salir para que sellen el comprobante de exportación?",
                "visual_hint": "🖋️🛫",
                "cloze": [4, 7, 13],
                "glossary": [
                    {"word": "upon departure", "meaning": "al momento de partir", "ipa": "əˈpɑːn dɪˈpɑːrtʃər"},
                    {"word": "stamped", "meaning": "sellado", "ipa": "stæmpt"},
                ],
            },
            {
                "id": "open-for-inspection",
                "text": "I'd be happy to unlock the cases so you can verify the contents firsthand.",
                "translation": "Con gusto abro los maletines para que pueda verificar el contenido de primera mano.",
                "visual_hint": "🔓🔍",
                "cloze": [4, 9, 12],
                "glossary": [
                    {"word": "verify", "meaning": "verificar", "ipa": "ˈverɪfaɪ"},
                    {"word": "firsthand", "meaning": "de primera mano / directamente", "ipa": "ˌfɜːrstˈhænd"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "customs officer",
            "user_role": "conference exhibitor",
            "setting": "International airport red channel customs inspection desk.",
            "turns": [
                {"speaker": "ai", "text": "Good morning. I see you're declaring three equipment cases. What is the commercial purpose of these devices?"},
                {
                    "speaker": "user",
                    "goal": "Explica que son prototipos para exhibición en la feria y no están a la venta.",
                    "suggested_lines": [
                        "These hardware prototypes are strictly for exhibition at the trade summit and not for resale.",
                        "They are non-functional display units carrying only nominal commercial value.",
                    ],
                },
                {"speaker": "ai", "text": "Do you have temporary import documentation showing they will leave the country with you?"},
                {
                    "speaker": "user",
                    "goal": "Entrega el cuaderno ATA y menciona que los números de serie coinciden con el manifiesto.",
                    "suggested_lines": [
                        "Here is our itemized ATA Carnet certifying that all equipment will be re-exported next Friday.",
                        "Every serial number on the pelican case corresponds directly to the manifest.",
                    ],
                },
                {"speaker": "ai", "text": "Let me inspect the first case and check the serial tags."},
                {
                    "speaker": "user",
                    "goal": "Ofrece abrir los maletines para que verifique el contenido directamente.",
                    "suggested_lines": [
                        "I'd be happy to unlock the cases so you can verify the contents firsthand.",
                        "Sure, let me unlock the case so you can check the serial numbers.",
                    ],
                },
                {"speaker": "ai", "text": "Everything matches the manifest. I've stamped your entry foil."},
                {
                    "speaker": "user",
                    "goal": "Pregunta a qué mostrador acudir al salir del país para sellar la reexportación.",
                    "suggested_lines": [
                        "Which counter should we report to upon departure to have the export voucher stamped?",
                        "Where do we get the export voucher stamped upon departure?",
                    ],
                },
                {"speaker": "ai", "text": "Report to Customs Desk B in Terminal 2 before checking the cases. Welcome and enjoy the summit!"},
            ],
        },
    },
    {
        "id": "c2-aviation-vip-lounge",
        "title": "Complex multi-leg itinerary rerouting",
        "title_es": "Reubicación de itinerario internacional complejo",
        "cefr": "C2",
        "topic": "travel-and-transport",
        "description": "Gestiona en mostrador ejecutivo una reprogramación interlineal con transferencia de equipaje ante cierre de espacio aéreo.",
        "phrases": [
            {
                "id": "interline-endorsement",
                "text": "Given the airspace closure, could you endorse our tickets over to your alliance carrier via Zurich?",
                "translation": "Dado el cierre del espacio aéreo, ¿podría endosar nuestros boletos a su aerolínea aliada vía Zúrich?",
                "visual_hint": "🌐✈️",
                "cloze": [2, 6, 12],
                "glossary": [
                    {"word": "endorse", "meaning": "endosar / transferir el boleto", "ipa": "ɪnˈdɔːrs"},
                    {"word": "alliance carrier", "meaning": "aerolínea de la misma alianza", "ipa": "əˈlaɪəns ˈkæriər"},
                ],
            },
            {
                "id": "through-checked-luggage",
                "text": "We need assurance that our checked luggage will be interlined through to the final destination.",
                "translation": "Necesitamos la seguridad de que nuestro equipaje documentado será transferido hasta el destino final.",
                "visual_hint": "🧳🏷️",
                "cloze": [2, 9, 14],
                "glossary": [
                    {"word": "assurance", "meaning": "garantía / certeza", "ipa": "əˈʃʊrəns"},
                    {"word": "interlined", "meaning": "transferido entre aerolíneas", "ipa": "ˈɪntərlaɪnd"},
                ],
            },
            {
                "id": "minimum-connecting-time",
                "text": "Does the forty-minute layover in Munich satisfy the legal minimum connecting time for non-Schengen transit?",
                "translation": "¿Cumple la escala de cuarenta minutos en Múnich con el tiempo mínimo legal de conexión para tránsito fuera de Schengen?",
                "visual_hint": "⏱️🛂",
                "cloze": [3, 6, 10],
                "glossary": [
                    {"word": "layover", "meaning": "escala", "ipa": "ˈleɪoʊvər"},
                    {"word": "minimum connecting time", "meaning": "tiempo mínimo de conexión", "ipa": "ˈmɪnɪməm kəˈnektɪŋ taɪm"},
                ],
            },
            {
                "id": "preserve-cabin-class",
                "text": "If business class is waitlist-only on the first leg, we'd request involuntary downgrade compensation.",
                "translation": "Si la clase ejecutiva solo tiene lista de espera en el primer tramo, solicitaríamos compensación por cambio involuntario de cabina.",
                "visual_hint": "💺⚖️",
                "cloze": [4, 8, 12, 13],
                "glossary": [
                    {"word": "leg", "meaning": "tramo de vuelo", "ipa": "leɡ"},
                    {"word": "downgrade", "meaning": "bajada de categoría de cabina", "ipa": "ˈdaʊnɡreɪd"},
                ],
            },
            {
                "id": "reissue-e-ticket",
                "text": "Please ensure the e-ticket numbers are revalidated so we don't hit a snag at the transfer gate.",
                "translation": "Por favor asegúrese de que los números de boleto electrónico sean revalidados para no tener contratiempos en la puerta de conexión.",
                "visual_hint": "🎫✅",
                "cloze": [6, 12, 16],
                "glossary": [
                    {"word": "revalidated", "meaning": "revalidados / reemitidos", "ipa": "ˌriːˈvælɪdeɪtɪd"},
                    {"word": "hit a snag", "meaning": "toparse con un contratiempo", "ipa": "hɪt ə snæɡ"},
                ],
            },
            {
                "id": "keynote-commitment",
                "text": "Time is of the essence, as I'm slated to deliver the opening keynote at nine tomorrow morning.",
                "translation": "El tiempo es crucial, ya que estoy programado para dar la conferencia inaugural mañana a las nueve de la mañana.",
                "visual_hint": "🎙️🕘",
                "cloze": [3, 7, 11],
                "glossary": [
                    {"word": "time is of the essence", "meaning": "el tiempo apremia / es crucial", "ipa": "taɪm ɪz əv ði ˈesəns"},
                    {"word": "slated to", "meaning": "programado para", "ipa": "ˈsleɪtɪd tə"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "concierge desk supervisor",
            "user_role": "international keynote speaker",
            "setting": "Executive airline lounge during an unexpected European airspace disruption.",
            "turns": [
                {"speaker": "ai", "text": "Good evening. Due to the weather system over Frankfurt, your direct flight has been suspended. How can we best reroute you?"},
                {
                    "speaker": "user",
                    "goal": "Explica que das la conferencia inaugural mañana y pide endosar el boleto vía Zúrich.",
                    "suggested_lines": [
                        "Given the airspace closure, could you endorse our tickets over to your alliance carrier via Zurich?",
                        "Time is of the essence, as I'm slated to deliver the opening keynote at nine tomorrow morning.",
                    ],
                },
                {"speaker": "ai", "text": "We have two options: via Munich with a forty-minute connection, or via Zurich leaving in fifty minutes."},
                {
                    "speaker": "user",
                    "goal": "Pregunta si cuarenta minutos en Múnich cumplen el tiempo mínimo legal de conexión.",
                    "suggested_lines": [
                        "Does the forty-minute layover in Munich satisfy the legal minimum connecting time for non-Schengen transit?",
                        "Is forty minutes enough for non-Schengen minimum connecting time?",
                    ],
                },
                {"speaker": "ai", "text": "Zurich is much safer at seventy-five minutes, and I can confirm two seats in Business Class."},
                {
                    "speaker": "user",
                    "goal": "Pide garantía de que el equipaje será transferido y el boleto electrónico revalidado.",
                    "suggested_lines": [
                        "We need assurance that our checked luggage will be interlined through to the final destination.",
                        "Please ensure the e-ticket numbers are revalidated so we don't hit a snag at the transfer gate.",
                    ],
                },
                {"speaker": "ai", "text": "I've reissued the 13-digit e-tickets and sent a priority telex to baggage control to transfer your bags."},
                {
                    "speaker": "user",
                    "goal": "Agradece la gestión y confirma la puerta de salida hacia Zúrich.",
                    "suggested_lines": [
                        "Thank you for revalidating the e-tickets; which gate does the Zurich flight depart from?",
                        "Please ensure the e-ticket numbers are revalidated so we don't hit a snag at the transfer gate.",
                    ],
                },
                {"speaker": "ai", "text": "Gate B24, boarding in twenty minutes. Have a seamless flight and a great keynote!"},
            ],
        },
    },
    # --- MODULE 3: hotel-and-shopping (missing A2, C1, C2) ---
    {
        "id": "a2-hotel-room-request",
        "title": "Requesting hotel room amenities",
        "title_es": "Pedir servicios a la habitación del hotel",
        "cefr": "A2",
        "topic": "hotel-and-shopping",
        "description": "Llama a recepción desde tu habitación para pedir toallas extra, una almohada adicional y preguntar la clave del wifi.",
        "phrases": [
            {
                "id": "extra-towels",
                "text": "Could you send two extra bath towels to room 304, please?",
                "translation": "¿Podría enviar dos toallas de baño extra a la habitación 304, por favor?",
                "visual_hint": "🛁🧺",
                "cloze": [2, 5, 8],
                "glossary": [
                    {"word": "bath towels", "meaning": "toallas de baño", "ipa": "bæθ ˈtaʊəlz"},
                    {"word": "extra", "meaning": "adicionales / extra", "ipa": "ˈekstrə"},
                ],
            },
            {
                "id": "wifi-password",
                "text": "What is the password for the guest Wi-Fi network?",
                "translation": "¿Cuál es la contraseña de la red wifi para huéspedes?",
                "visual_hint": "📶🔑",
                "cloze": [3, 6, 8],
                "glossary": [
                    {"word": "password", "meaning": "contraseña", "ipa": "ˈpæswɜːrd"},
                    {"word": "guest", "meaning": "huésped / invitado", "ipa": "ɡest"},
                ],
            },
            {
                "id": "air-conditioning-warm",
                "text": "The air conditioning in my room is not cooling properly.",
                "translation": "El aire acondicionado de mi habitación no está enfriando bien.",
                "visual_hint": "❄️🌡️",
                "cloze": [1, 2, 8],
                "glossary": [
                    {"word": "air conditioning", "meaning": "aire acondicionado", "ipa": "er kənˈdɪʃənɪŋ"},
                    {"word": "cooling", "meaning": "enfriando", "ipa": "ˈkuːlɪŋ"},
                ],
            },
            {
                "id": "soft-pillow",
                "text": "May I also get an extra pillow and a blanket?",
                "translation": "¿Me podrían traer también una almohada extra y una manta?",
                "visual_hint": "🛏️🪶",
                "cloze": [6, 9],
                "glossary": [
                    {"word": "pillow", "meaning": "almohada", "ipa": "ˈpɪloʊ"},
                    {"word": "blanket", "meaning": "manta / cobija", "ipa": "ˈblæŋkɪt"},
                ],
            },
            {
                "id": "hair-dryer-working",
                "text": "Do you have a clothes iron we can borrow for tonight?",
                "translation": "¿Tienen una plancha de ropa que nos puedan prestar por esta noche?",
                "visual_hint": "👔♨️",
                "cloze": [5, 8],
                "glossary": [
                    {"word": "clothes iron", "meaning": "plancha para ropa", "ipa": "kloʊðz ˈaɪərn"},
                    {"word": "borrow", "meaning": "pedir prestado", "ipa": "ˈbɑːroʊ"},
                ],
            },
            {
                "id": "wake-up-call",
                "text": "Could you set a wake-up call for six thirty tomorrow morning?",
                "translation": "¿Podría programar una llamada despertador para las seis y media mañana por la mañana?",
                "visual_hint": "⏰📞",
                "cloze": [4, 7, 8],
                "glossary": [
                    {"word": "wake-up call", "meaning": "llamada despertador", "ipa": "ˈweɪk ʌp kɔːl"},
                    {"word": "six thirty", "meaning": "seis y media", "ipa": "sɪks ˈθɜːrti"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "front desk agent",
            "user_role": "hotel guest",
            "setting": "Calling the hotel reception desk from Room 304.",
            "turns": [
                {"speaker": "ai", "text": "Front desk, good evening! How can I make your stay more comfortable?"},
                {
                    "speaker": "user",
                    "goal": "Pide dos toallas de baño extra y una almohada para la habitación 304.",
                    "suggested_lines": [
                        "Could you send two extra bath towels to room 304, please?",
                        "May I also get an extra pillow and a blanket?",
                    ],
                },
                {"speaker": "ai", "text": "Right away! Housekeeping will bring them up in five minutes. Anything else?"},
                {
                    "speaker": "user",
                    "goal": "Comenta que el aire acondicionado no está enfriando bien.",
                    "suggested_lines": [
                        "The air conditioning in my room is not cooling properly.",
                        "Also, do you have a clothes iron we can borrow for tonight?",
                    ],
                },
                {"speaker": "ai", "text": "I'll send our maintenance technician to check the thermostat right now."},
                {
                    "speaker": "user",
                    "goal": "Pregunta la contraseña del wifi para huéspedes.",
                    "suggested_lines": [
                        "What is the password for the guest Wi-Fi network?",
                        "Could you tell me the guest Wi-Fi password?",
                    ],
                },
                {"speaker": "ai", "text": "It's 'GrandStay2026' with a capital G and S. Would you like a morning wake-up call?"},
                {
                    "speaker": "user",
                    "goal": "Pide una llamada despertador a las 6:30 de la mañana.",
                    "suggested_lines": [
                        "Could you set a wake-up call for six thirty tomorrow morning?",
                        "Yes, please set a wake-up call for six thirty.",
                    ],
                },
                {"speaker": "ai", "text": "All set for 6:30 AM. Have a restful night!"},
            ],
        },
    },
    {
        "id": "c1-lease-negotiation",
        "title": "Negotiating an apartment lease",
        "title_es": "Negociar un contrato de alquiler",
        "cefr": "C1",
        "topic": "hotel-and-shopping",
        "description": "Negocia cláusulas de un contrato de arrendamiento: duración, mantenimiento incluido y cláusula de salida anticipada.",
        "phrases": [
            {
                "id": "lock-in-rent",
                "text": "If we sign an eighteen-month lease, would the landlord agree to cap the annual rent increase?",
                "translation": "Si firmamos un contrato de dieciocho meses, ¿aceptaría el propietario limitar el aumento anual del alquiler?",
                "visual_hint": "🏠📝",
                "cloze": [5, 8, 11],
                "glossary": [
                    {"word": "lease", "meaning": "contrato de arrendamiento", "ipa": "liːs"},
                    {"word": "cap", "meaning": "poner un tope / limitar", "ipa": "kæp"},
                ],
            },
            {
                "id": "break-clause",
                "text": "Since my company relocates staff periodically, we need a diplomatic break clause with sixty days' notice.",
                "translation": "Como mi empresa reubica personal periódicamente, necesitamos una cláusula de rescisión anticipada con sesenta días de preaviso.",
                "visual_hint": "📄✈️",
                "cloze": [3, 10, 14],
                "glossary": [
                    {"word": "relocates", "meaning": "reubica / traslada", "ipa": "ˌriːˈloʊkeɪts"},
                    {"word": "break clause", "meaning": "cláusula de salida anticipada", "ipa": "breɪk klɔːz"},
                ],
            },
            {
                "id": "utilities-and-hoa",
                "text": "Just to clarify, are building maintenance fees and water utilities bundled into the monthly rent?",
                "translation": "Solo para aclarar, ¿las cuotas de mantenimiento del edificio y el agua están incluidas en la renta mensual?",
                "visual_hint": "💧🏢",
                "cloze": [2, 6, 10],
                "glossary": [
                    {"word": "utilities", "meaning": "servicios básicos (agua, luz, gas)", "ipa": "juːˈtɪlətiz"},
                    {"word": "bundled into", "meaning": "incluidos dentro de", "ipa": "ˈbʌndəld ˈɪntuː"},
                ],
            },
            {
                "id": "wear-and-tear",
                "text": "The security deposit clause should explicitly distinguish between normal wear and tear and structural damage.",
                "translation": "La cláusula del depósito debe distinguir explícitamente entre el desgaste normal por uso y daños estructurales.",
                "visual_hint": "🔍🔑",
                "cloze": [6, 9, 11],
                "glossary": [
                    {"word": "explicitly", "meaning": "explícitamente", "ipa": "ɪkˈsplɪsɪtli"},
                    {"word": "wear and tear", "meaning": "desgaste normal por el uso", "ipa": "wer ænd ter"},
                ],
            },
            {
                "id": "appliance-repairs",
                "text": "We'd like it stated in writing that major appliance repairs remain the owner's responsibility.",
                "translation": "Nos gustaría que conste por escrito que las reparaciones de electrodomésticos principales siguen siendo responsabilidad del propietario.",
                "visual_hint": "🛠️🧊",
                "cloze": [3, 8, 9],
                "glossary": [
                    {"word": "stated in writing", "meaning": "establecido por escrito", "ipa": "ˈsteɪtɪd ɪn ˈraɪtɪŋ"},
                    {"word": "appliance", "meaning": "electrodoméstico", "ipa": "əˈplaɪəns"},
                ],
            },
            {
                "id": "move-in-walkthrough",
                "text": "Let's schedule a joint walkthrough prior to move-in to sign off on the inventory checklist.",
                "translation": "Agendemos un recorrido conjunto antes de la mudanza para firmar la lista de inventario.",
                "visual_hint": "📋🚪",
                "cloze": [4, 7, 14],
                "glossary": [
                    {"word": "walkthrough", "meaning": "inspección / recorrido presencial", "ipa": "ˈwɔːkθruː"},
                    {"word": "sign off on", "meaning": "aprobar con firma", "ipa": "saɪn ɔːf ɑːn"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "leasing agent",
            "user_role": "prospective tenant",
            "setting": "Reviewing a residential lease agreement before signing.",
            "turns": [
                {"speaker": "ai", "text": "Here is the draft lease for the two-bedroom apartment. Did you have any questions about the terms?"},
                {
                    "speaker": "user",
                    "goal": "Pregunta si las cuotas de mantenimiento y agua están incluidas y propone contrato de 18 meses con tope de aumento.",
                    "suggested_lines": [
                        "Just to clarify, are building maintenance fees and water utilities bundled into the monthly rent?",
                        "If we sign an eighteen-month lease, would the landlord agree to cap the annual rent increase?",
                    ],
                },
                {"speaker": "ai", "text": "Water and HOA fees are included, and the owner can cap the renewal increase at three percent."},
                {
                    "speaker": "user",
                    "goal": "Solicita una cláusula de salida anticipada con 60 días de preaviso por posibles traslados laborales.",
                    "suggested_lines": [
                        "Since my company relocates staff periodically, we need a diplomatic break clause with sixty days' notice.",
                        "Could we add a break clause with sixty days' notice in case of work relocation?",
                    ],
                },
                {"speaker": "ai", "text": "We can add that after the sixth month. Anything else regarding maintenance or the deposit?"},
                {
                    "speaker": "user",
                    "goal": "Pide que conste por escrito la responsabilidad de electrodomésticos y el desgaste normal.",
                    "suggested_lines": [
                        "We'd like it stated in writing that major appliance repairs remain the owner's responsibility.",
                        "The security deposit clause should explicitly distinguish between normal wear and tear and structural damage.",
                    ],
                },
                {"speaker": "ai", "text": "Fair enough. I'll amend Clause 9 and Clause 14 right now."},
                {
                    "speaker": "user",
                    "goal": "Propón agendar un recorrido conjunto antes de la mudanza para firmar el inventario.",
                    "suggested_lines": [
                        "Let's schedule a joint walkthrough prior to move-in to sign off on the inventory checklist.",
                        "Can we do a joint walkthrough before move-in to sign the inventory?",
                    ],
                },
                {"speaker": "ai", "text": "Let's meet at the apartment Thursday at 10 AM with the keys!"},
            ],
        },
    },
    {
        "id": "c2-luxury-concierge",
        "title": "Bespoke event planning with a concierge",
        "title_es": "Organización de evento privado con concierge",
        "cefr": "C2",
        "topic": "hotel-and-shopping",
        "description": "Coordina con el jefe de conserjería un evento privado de aniversario en una terraza histórica con logística confidencial.",
        "phrases": [
            {
                "id": "exclusive-buyout",
                "text": "We're inquiring about an exclusive buyout of the rooftop conservatory for an intimate anniversary gala.",
                "translation": "Estamos consultando por la reserva exclusiva del invernadero de la azotea para una gala íntima de aniversario.",
                "visual_hint": "🏛️✨",
                "cloze": [2, 5, 8],
                "glossary": [
                    {"word": "exclusive buyout", "meaning": "reserva privada total del espacio", "ipa": "ɪkˈskluːsɪv ˈbaɪaʊt"},
                    {"word": "conservatory", "meaning": "invernadero / salón acristalado", "ipa": "kənˈsɜːrvətɔːri"},
                ],
            },
            {
                "id": "contingency-for-weather",
                "text": "Should the evening breeze turn brisk, we'll need a seamless contingency plan indoors.",
                "translation": "Si la brisa nocturna se vuelve fría, necesitaremos un plan de contingencia impecable en el interior.",
                "visual_hint": "🌬️🕯️",
                "cloze": [5, 9, 10],
                "glossary": [
                    {"word": "brisk", "meaning": "fresca / fría y vigorosa", "ipa": "brɪsk"},
                    {"word": "contingency plan", "meaning": "plan de contingencia / alternativo", "ipa": "kənˈtɪndʒənsi plæn"},
                ],
            },
            {
                "id": "acoustic-quartet",
                "text": "Could you vet a string quartet capable of transitioning from classical repertoire to contemporary jazz?",
                "translation": "¿Podría seleccionar un cuarteto de cuerdas capaz de pasar de repertorio clásico a jazz contemporáneo?",
                "visual_hint": "🎻🎶",
                "cloze": [2, 4, 7],
                "glossary": [
                    {"word": "vet", "meaning": "evaluar y seleccionar cuidadosamente", "ipa": "vet"},
                    {"word": "repertoire", "meaning": "repertorio", "ipa": "ˈrepərtwɑːr"},
                ],
            },
            {
                "id": "utmost-discretion",
                "text": "Given the profile of several attendees, we trust your staff will exercise the utmost discretion.",
                "translation": "Dado el perfil de varios asistentes, confiamos en que su personal actuará con la máxima discreción.",
                "visual_hint": "🤫🎩",
                "cloze": [5, 11, 13],
                "glossary": [
                    {"word": "attendees", "meaning": "asistentes / invitados", "ipa": "əˌtenˈdiːz"},
                    {"word": "utmost discretion", "meaning": "máxima discreción", "ipa": "ˈʌtmoʊst dɪˈskreʃən"},
                ],
            },
            {
                "id": "bespoke-floral",
                "text": "We want the floral installations to feel understated yet evocative of a Mediterranean courtyard.",
                "translation": "Queremos que los arreglos florales se sientan sobrios pero evocadores de un patio mediterráneo.",
                "visual_hint": "🌿🌸",
                "cloze": [3, 7, 9],
                "glossary": [
                    {"word": "understated", "meaning": "sobrio / elegante sin ostentación", "ipa": "ˌʌndərˈsteɪtɪd"},
                    {"word": "evocative", "meaning": "evocador", "ipa": "ɪˈvɑːkətɪv"},
                ],
            },
            {
                "id": "itemized-retainer",
                "text": "Once you circulate the itemized proposal, we can wire the fifty-percent retainer immediately.",
                "translation": "Una vez que nos envíe la propuesta detallada, podemos transferir el anticipo del cincuenta por ciento de inmediato.",
                "visual_hint": "📑🏦",
                "cloze": [2, 4, 8, 11],
                "glossary": [
                    {"word": "itemized", "meaning": "desglosada partida por partida", "ipa": "ˈaɪtəmaɪzd"},
                    {"word": "retainer", "meaning": "anticipo / depósito de reserva", "ipa": "rɪˈteɪnər"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "chief concierge",
            "user_role": "event host",
            "setting": "Private consultation at a five-star heritage hotel.",
            "turns": [
                {"speaker": "ai", "text": "It is a pleasure to assist with your anniversary celebration. Which venue space did you have in mind?"},
                {
                    "speaker": "user",
                    "goal": "Consulta por la reserva exclusiva de la terraza acristalada y un plan interior por si refresca.",
                    "suggested_lines": [
                        "We're inquiring about an exclusive buyout of the rooftop conservatory for an intimate anniversary gala.",
                        "Should the evening breeze turn brisk, we'll need a seamless contingency plan indoors.",
                    ],
                },
                {"speaker": "ai", "text": "The conservatory and the adjacent library salon can be reserved together. What ambiance and entertainment do you envision?"},
                {
                    "speaker": "user",
                    "goal": "Pide un cuarteto de cuerdas versátil y decoración floral sobria de estilo mediterráneo.",
                    "suggested_lines": [
                        "Could you vet a string quartet capable of transitioning from classical repertoire to contemporary jazz?",
                        "We want the floral installations to feel understated yet evocative of a Mediterranean courtyard.",
                    ],
                },
                {"speaker": "ai", "text": "We work with an ensemble from the Philharmonic and a master botanist who can achieve that exact aesthetic."},
                {
                    "speaker": "user",
                    "goal": "Subraya la importancia de la máxima discreción por el perfil de los invitados.",
                    "suggested_lines": [
                        "Given the profile of several attendees, we trust your staff will exercise the utmost discretion.",
                        "Private elevator access and the utmost discretion will be essential.",
                    ],
                },
                {"speaker": "ai", "text": "Naturally—private elevator access and NDAs are standard protocol for our private buyouts."},
                {
                    "speaker": "user",
                    "goal": "Pide la propuesta desglosada para transferir el anticipo del 50% de inmediato.",
                    "suggested_lines": [
                        "Once you circulate the itemized proposal, we can wire the fifty-percent retainer immediately.",
                        "Send over the itemized proposal and we'll wire the retainer today.",
                    ],
                },
                {"speaker": "ai", "text": "You will have the complete dossier on your desk by four o'clock."},
            ],
        },
    },
    # --- MODULE 4: social-and-smalltalk (missing A1, B1, C1) ---
    {
        "id": "a1-greeting-neighbors",
        "title": "Greeting a new neighbor",
        "title_es": "Saludar a un vecino nuevo",
        "cefr": "A1",
        "topic": "social-and-smalltalk",
        "description": "Saluda a tu vecino en el pasillo, dile tu nombre y número de apartamento y ofrécele ayuda.",
        "phrases": [
            {
                "id": "welcome-to-building",
                "text": "Hi! Welcome to the building. I am Leo.",
                "translation": "¡Hola! Bienvenido al edificio. Soy Leo.",
                "visual_hint": "👋🏢",
                "cloze": [1, 4],
                "glossary": [
                    {"word": "welcome", "meaning": "bienvenido", "ipa": "ˈwelkəm"},
                    {"word": "building", "meaning": "edificio", "ipa": "ˈbɪldɪŋ"},
                ],
            },
            {
                "id": "live-next-door",
                "text": "I live next door in apartment 4B.",
                "translation": "Vivo al lado, en el apartamento 4B.",
                "visual_hint": "🚪🔑",
                "cloze": [1, 2, 3],
                "glossary": [
                    {"word": "live", "meaning": "vivir", "ipa": "lɪv"},
                    {"word": "next door", "meaning": "al lado", "ipa": "nekst dɔːr"},
                ],
            },
            {
                "id": "need-any-help",
                "text": "Do you need any help with those boxes?",
                "translation": "¿Necesitas ayuda con esas cajas?",
                "visual_hint": "📦💪",
                "cloze": [2, 4, 7],
                "glossary": [
                    {"word": "help", "meaning": "ayuda", "ipa": "help"},
                    {"word": "boxes", "meaning": "cajas", "ipa": "ˈbɑːksɪz"},
                ],
            },
            {
                "id": "quiet-neighborhood",
                "text": "This is a very friendly and quiet street.",
                "translation": "Esta es una calle muy amigable y tranquila.",
                "visual_hint": "🌳😊",
                "cloze": [4, 6],
                "glossary": [
                    {"word": "friendly", "meaning": "amigable", "ipa": "ˈfrendli"},
                    {"word": "street", "meaning": "calle", "ipa": "striːt"},
                ],
            },
            {
                "id": "supermarket-on-corner",
                "text": "There is a good supermarket on the corner.",
                "translation": "Hay un buen supermercado en la esquina.",
                "visual_hint": "🛒🏪",
                "cloze": [3, 4],
                "glossary": [
                    {"word": "supermarket", "meaning": "supermercado", "ipa": "ˈsuːpərmɑːrkɪt"},
                    {"word": "on the corner", "meaning": "en la esquina", "ipa": "ɑːn ðə ˈkɔːrnər"},
                ],
            },
            {
                "id": "knock-on-my-door",
                "text": "Let me know if you need anything. See you soon!",
                "translation": "Avísame si necesitas algo. ¡Nos vemos pronto!",
                "visual_hint": "🙌✨",
                "cloze": [2, 6, 9],
                "glossary": [
                    {"word": "let me know", "meaning": "avísame / hazme saber", "ipa": "let miː noʊ"},
                    {"word": "soon", "meaning": "pronto", "ipa": "suːn"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "new neighbor",
            "user_role": "resident",
            "setting": "Apartment hallway while a new neighbor is moving in.",
            "turns": [
                {"speaker": "ai", "text": "Hi there! I just moved in today. My name is Sam."},
                {
                    "speaker": "user",
                    "goal": "Dale la bienvenida al edificio y dile que vives al lado en el 4B.",
                    "suggested_lines": [
                        "Hi! Welcome to the building. I am Leo.",
                        "I live next door in apartment 4B.",
                    ],
                },
                {"speaker": "ai", "text": "Nice to meet you! I still have a few heavy boxes in the elevator."},
                {
                    "speaker": "user",
                    "goal": "Ofrécele ayuda con las cajas.",
                    "suggested_lines": [
                        "Do you need any help with those boxes?",
                        "I can help you with those boxes.",
                    ],
                },
                {"speaker": "ai", "text": "Thank you so much! By the way, is there a grocery store nearby?"},
                {
                    "speaker": "user",
                    "goal": "Dile que la calle es tranquila y que hay un buen supermercado en la esquina.",
                    "suggested_lines": [
                        "There is a good supermarket on the corner.",
                        "This is a very friendly and quiet street.",
                    ],
                },
                {"speaker": "ai", "text": "Awesome, that's really convenient. Thanks again for your help!"},
                {
                    "speaker": "user",
                    "goal": "Despídete diciéndole que te avise si necesita algo.",
                    "suggested_lines": [
                        "Let me know if you need anything. See you soon!",
                        "You're welcome! See you soon!",
                    ],
                },
                {"speaker": "ai", "text": "See you around, neighbor!"},
            ],
        },
    },
    {
        "id": "b1-inviting-to-party",
        "title": "Inviting friends to a weekend barbecue",
        "title_es": "Invitar amigos a un asado de fin de semana",
        "cefr": "B1",
        "topic": "social-and-smalltalk",
        "description": "Invita a un amigo a una reunión en tu terraza, coordina la hora y sugiere qué bebida o postre puede traer.",
        "phrases": [
            {
                "id": "hosting-barbecue",
                "text": "We're hosting a casual barbecue on our patio this Saturday afternoon.",
                "translation": "Vamos a organizar un asado informal en nuestro patio este sábado por la tarde.",
                "visual_hint": "🍔☀️",
                "cloze": [1, 3, 6],
                "glossary": [
                    {"word": "hosting", "meaning": "organizando / siendo anfitriones", "ipa": "ˈhoʊstɪŋ"},
                    {"word": "casual", "meaning": "informal / relajado", "ipa": "ˈkæʒuəl"},
                ],
            },
            {
                "id": "hope-you-can-make-it",
                "text": "We'd love for you to come if you're free around four o'clock.",
                "translation": "Nos encantaría que vinieras si estás libre alrededor de las cuatro.",
                "visual_hint": "🕓🎉",
                "cloze": [1, 5, 8],
                "glossary": [
                    {"word": "love for you", "meaning": "encantaría que tú", "ipa": "lʌv fɔːr juː"},
                    {"word": "free", "meaning": "libre / disponible", "ipa": "friː"},
                ],
            },
            {
                "id": "bring-a-friend",
                "text": "Feel free to bring your partner or a friend along too!",
                "translation": "¡Siéntete con confianza de traer a tu pareja o a un amigo también!",
                "visual_hint": "👫🎈",
                "cloze": [0, 3, 9],
                "glossary": [
                    {"word": "feel free", "meaning": "siéntete libre / con confianza", "ipa": "fiːl friː"},
                    {"word": "bring along", "meaning": "traer contigo", "ipa": "brɪŋ əˈlɔːŋ"},
                ],
            },
            {
                "id": "veggie-burgers-too",
                "text": "We'll grill burgers and veggies, so there's plenty of food for everyone.",
                "translation": "Asaremos hamburguesas y verduras, así que habrá mucha comida para todos.",
                "visual_hint": "🌽🥩",
                "cloze": [1, 7],
                "glossary": [
                    {"word": "grill", "meaning": "asar a la parrilla", "ipa": "ɡrɪl"},
                    {"word": "plenty of", "meaning": "abundante / suficiente", "ipa": "ˈplenti əv"},
                ],
            },
            {
                "id": "just-bring-drinks",
                "text": "You don't need to bring anything, maybe just your favorite drinks.",
                "translation": "No necesitas traer nada, tal vez solo tus bebidas favoritas.",
                "visual_hint": "🥤🧊",
                "cloze": [4, 9, 10],
                "glossary": [
                    {"word": "maybe", "meaning": "tal vez / quizás", "ipa": "ˈmeɪbi"},
                    {"word": "favorite", "meaning": "favoritas", "ipa": "ˈfeɪvərɪt"},
                ],
            },
            {
                "id": "text-you-address",
                "text": "I'll text you the exact pin and buzzer code on Friday.",
                "translation": "Te enviaré por mensaje la ubicación exacta y el código del timbre el viernes.",
                "visual_hint": "📍📱",
                "cloze": [1, 5, 7],
                "glossary": [
                    {"word": "pin", "meaning": "ubicación en el mapa", "ipa": "pɪn"},
                    {"word": "buzzer code", "meaning": "código del interfón / timbre", "ipa": "ˈbʌzər koʊd"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "friend (Chloe)",
            "user_role": "host",
            "setting": "Chatting with a friend after work on Wednesday.",
            "turns": [
                {"speaker": "ai", "text": "Hey! Do you have any plans for this weekend? The weather looks amazing."},
                {
                    "speaker": "user",
                    "goal": "Invítala al asado en tu patio este sábado a las cuatro.",
                    "suggested_lines": [
                        "We're hosting a casual barbecue on our patio this Saturday afternoon.",
                        "We'd love for you to come if you're free around four o'clock.",
                    ],
                },
                {"speaker": "ai", "text": "That sounds so fun! Can I bring my friend Lucas? He's visiting from Boston."},
                {
                    "speaker": "user",
                    "goal": "Dile que por supuesto puede traer a su amigo y que habrá comida para todos.",
                    "suggested_lines": [
                        "Feel free to bring your partner or a friend along too!",
                        "We'll grill burgers and veggies, so there's plenty of food for everyone.",
                    ],
                },
                {"speaker": "ai", "text": "Awesome! What can we bring to help out? A salad or dessert?"},
                {
                    "speaker": "user",
                    "goal": "Dile que no hace falta nada, solo sus bebidas favoritas si gustan.",
                    "suggested_lines": [
                        "You don't need to bring anything, maybe just your favorite drinks.",
                        "Just bring your favorite drinks!",
                    ],
                },
                {"speaker": "ai", "text": "Deal! Send me your address so we don't get lost."},
                {
                    "speaker": "user",
                    "goal": "Promete enviarle la ubicación y el código del timbre el viernes.",
                    "suggested_lines": [
                        "I'll text you the exact pin and buzzer code on Friday.",
                        "I'll text you the address and buzzer code Friday!",
                    ],
                },
                {"speaker": "ai", "text": "Can't wait! See you Saturday at four."},
            ],
        },
    },
    {
        "id": "c1-cultural-nuances",
        "title": "Discussing cross-cultural idioms & humor",
        "title_es": "Conversar sobre matices culturales y humor",
        "cefr": "C1",
        "topic": "social-and-smalltalk",
        "description": "Analiza en una tertulia cómo el sarcasmo, la cortesía indirecta y los modismos cambian entre culturas.",
        "phrases": [
            {
                "id": "lost-in-translation",
                "text": "Dry understatement often gets lost in translation when teams collaborate across continents.",
                "translation": "La ironía sutil a menudo se pierde en la traducción cuando los equipos colaboran entre continentes.",
                "visual_hint": "🌍💬",
                "cloze": [1, 4, 6],
                "glossary": [
                    {"word": "understatement", "meaning": "ironía sutil / atenuación", "ipa": "ˈʌndərsteɪtmənt"},
                    {"word": "lost in translation", "meaning": "perdido en la traducción", "ipa": "lɔːst ɪn trænsˈleɪʃən"},
                ],
            },
            {
                "id": "read-between-lines",
                "text": "In high-context cultures, you quickly learn to read between the lines rather than expect a blunt refusal.",
                "translation": "En culturas de alto contexto, aprendes rápido a leer entre líneas en vez de esperar una negativa directa.",
                "visual_hint": "📖🧐",
                "cloze": [7, 10, 15],
                "glossary": [
                    {"word": "read between the lines", "meaning": "leer entre líneas", "ipa": "riːd bɪˈtwiːn ðə laɪnz"},
                    {"word": "blunt refusal", "meaning": "negativa tajante / directa", "ipa": "blʌnt rɪˈfjuːzəl"},
                ],
            },
            {
                "id": "self-deprecating-humor",
                "text": "Self-deprecating humor is a great icebreaker, provided people realize you're joking.",
                "translation": "El humor autocrítico es excelente para romper el hielo, siempre y cuando la gente note que bromeas.",
                "visual_hint": "😄🧊",
                "cloze": [0, 5, 7],
                "glossary": [
                    {"word": "self-deprecating", "meaning": "autocrítico / que se ríe de sí mismo", "ipa": "ˌself ˈdeprəkeɪtɪŋ"},
                    {"word": "icebreaker", "meaning": "rompehielos", "ipa": "ˈaɪsbreɪkər"},
                ],
            },
            {
                "id": "vivid-idiom",
                "text": "Every language has vivid idioms that sound utterly baffling when translated word for word.",
                "translation": "Cada idioma tiene modismos vívidos que suenan totalmente desconcertantes cuando se traducen palabra por palabra.",
                "visual_hint": "🗣️🧩",
                "cloze": [4, 8, 11],
                "glossary": [
                    {"word": "idioms", "meaning": "modismos / expresiones idiomáticas", "ipa": "ˈɪdiəmz"},
                    {"word": "baffling", "meaning": "desconcertantes / confusos", "ipa": "ˈbæflɪŋ"},
                ],
            },
            {
                "id": "social-cues",
                "text": "Picking up on subtle vocal cues is half the battle toward sounding natural.",
                "translation": "Captar las sutiles señales del tono de voz es la mitad del camino para sonar natural.",
                "visual_hint": "🎧🎯",
                "cloze": [0, 5, 8],
                "glossary": [
                    {"word": "picking up on", "meaning": "captar / percibir", "ipa": "ˈpɪkɪŋ ʌp ɑːn"},
                    {"word": "half the battle", "meaning": "la mitad del triunfo / lo más importante", "ipa": "hæf ðə ˈbætəl"},
                ],
            },
            {
                "id": "bridge-the-gap",
                "text": "Curiosity and a bit of humility go a long way toward bridging cultural gaps.",
                "translation": "La curiosidad y un poco de humildad ayudan muchísimo a acortar las brechas culturales.",
                "visual_hint": "🌉🤝",
                "cloze": [5, 8, 11],
                "glossary": [
                    {"word": "humility", "meaning": "humildad", "ipa": "hjuːˈmɪləti"},
                    {"word": "go a long way", "meaning": "ayudar muchísimo / rendir mucho", "ipa": "ɡoʊ ə lɔːŋ weɪ"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "international colleague",
            "user_role": "speaker",
            "setting": "Coffee break at an international cultural exchange meetup.",
            "turns": [
                {"speaker": "ai", "text": "Have you ever noticed how differently British, American, and Latin colleagues give feedback in meetings?"},
                {
                    "speaker": "user",
                    "goal": "Comenta cómo la ironía sutil o el leer entre líneas cambia según la cultura.",
                    "suggested_lines": [
                        "Dry understatement often gets lost in translation when teams collaborate across continents.",
                        "In high-context cultures, you quickly learn to read between the lines rather than expect a blunt refusal.",
                    ],
                },
                {"speaker": "ai", "text": "Totally! When someone in London says 'With the greatest respect,' you know they strongly disagree. What about humor?"},
                {
                    "speaker": "user",
                    "goal": "Habla del humor autocrítico como rompehielos y de los modismos traducidos literalmente.",
                    "suggested_lines": [
                        "Self-deprecating humor is a great icebreaker, provided people realize you're joking.",
                        "Every language has vivid idioms that sound utterly baffling when translated word for word.",
                    ],
                },
                {"speaker": "ai", "text": "So true! Literal translations of idioms always make for the funniest stories."},
                {
                    "speaker": "user",
                    "goal": "Explica que captar las señales del tono de voz es clave para sonar natural.",
                    "suggested_lines": [
                        "Picking up on subtle vocal cues is half the battle toward sounding natural.",
                        "Listening for vocal cues really helps you understand the real intent.",
                    ],
                },
                {"speaker": "ai", "text": "What's your best advice for someone moving abroad for the first time?"},
                {
                    "speaker": "user",
                    "goal": "Concluye diciendo que la curiosidad y la humildad ayudan muchísimo a unir culturas.",
                    "suggested_lines": [
                        "Curiosity and a bit of humility go a long way toward bridging cultural gaps.",
                        "Curiosity and humility always go a long way.",
                    ],
                },
                {"speaker": "ai", "text": "Couldn't agree more. That's the best mindset to have!"},
            ],
        },
    },
    # --- MODULE 5: work-and-career (missing A1, A2, B1) ---
    {
        "id": "a1-first-day-office",
        "title": "First day at the office",
        "title_es": "Primer día en la oficina",
        "cefr": "A1",
        "topic": "work-and-career",
        "description": "Preséntate en recepción en tu primer día de trabajo, pregunta por tu escritorio y conoce a tu equipo.",
        "phrases": [
            {
                "id": "first-day-here",
                "text": "Good morning! Today is my first day in the marketing team.",
                "translation": "¡Buenos días! Hoy es mi primer día en el equipo de marketing.",
                "visual_hint": "💼😊",
                "cloze": [4, 5, 9],
                "glossary": [
                    {"word": "first day", "meaning": "primer día", "ipa": "fɜːrst deɪ"},
                    {"word": "team", "meaning": "equipo", "ipa": "tiːm"},
                ],
            },
            {
                "id": "where-is-my-desk",
                "text": "Where is my desk, please?",
                "translation": "¿Dónde está mi escritorio, por favor?",
                "visual_hint": "🖥️🪑",
                "cloze": [0, 3],
                "glossary": [
                    {"word": "where", "meaning": "dónde", "ipa": "wer"},
                    {"word": "desk", "meaning": "escritorio", "ipa": "desk"},
                ],
            },
            {
                "id": "visitor-badge",
                "text": "Here is my ID card for the office badge.",
                "translation": "Aquí está mi identificación para la credencial de la oficina.",
                "visual_hint": "🪪🏢",
                "cloze": [3, 8],
                "glossary": [
                    {"word": "ID card", "meaning": "documento de identidad", "ipa": "ˌaɪˈdiː kɑːrd"},
                    {"word": "badge", "meaning": "credencial / gafete", "ipa": "bædʒ"},
                ],
            },
            {
                "id": "kitchen-and-coffee",
                "text": "Is the coffee machine on this floor?",
                "translation": "¿Está la máquina de café en este piso?",
                "visual_hint": "☕🏢",
                "cloze": [2, 6],
                "glossary": [
                    {"word": "coffee machine", "meaning": "máquina de café", "ipa": "ˈkɔːfi məˈʃiːn"},
                    {"word": "floor", "meaning": "piso / planta", "ipa": "flɔːr"},
                ],
            },
            {
                "id": "happy-to-be-here",
                "text": "Nice to meet you! I am very happy to join the team.",
                "translation": "¡Mucho gusto! Estoy muy feliz de unirme al equipo.",
                "visual_hint": "🤝🌟",
                "cloze": [6, 8],
                "glossary": [
                    {"word": "happy", "meaning": "feliz / contento", "ipa": "ˈhæpi"},
                    {"word": "join", "meaning": "unirse a", "ipa": "dʒɔɪn"},
                ],
            },
            {
                "id": "what-time-lunch",
                "text": "What time do we usually have lunch?",
                "translation": "¿A qué hora solemos almorzar?",
                "visual_hint": "🥗🕛",
                "cloze": [1, 6],
                "glossary": [
                    {"word": "usually", "meaning": "usualmente", "ipa": "ˈjuːʒuəli"},
                    {"word": "lunch", "meaning": "almuerzo", "ipa": "lʌntʃ"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "office manager",
            "user_role": "new team member",
            "setting": "Office reception area on Monday morning.",
            "turns": [
                {"speaker": "ai", "text": "Good morning! Welcome to BrightTech. How can I help you today?"},
                {
                    "speaker": "user",
                    "goal": "Di que hoy es tu primer día en el equipo de marketing y muestra tu identificación.",
                    "suggested_lines": [
                        "Good morning! Today is my first day in the marketing team.",
                        "Here is my ID card for the office badge.",
                    ],
                },
                {"speaker": "ai", "text": "Welcome aboard! Here is your security badge and laptop."},
                {
                    "speaker": "user",
                    "goal": "Pregunta dónde está tu escritorio y si la máquina de café está en este piso.",
                    "suggested_lines": [
                        "Where is my desk, please?",
                        "Is the coffee machine on this floor?",
                    ],
                },
                {"speaker": "ai", "text": "Your desk is right by the window, and the kitchen with free coffee is down the hall."},
                {
                    "speaker": "user",
                    "goal": "Di que estás muy feliz de unirte al equipo.",
                    "suggested_lines": [
                        "Nice to meet you! I am very happy to join the team.",
                        "Thank you! I am very happy to join the team.",
                    ],
                },
                {"speaker": "ai", "text": "Everyone is excited to meet you! Do you have any other questions?"},
                {
                    "speaker": "user",
                    "goal": "Pregunta a qué hora suelen almorzar.",
                    "suggested_lines": [
                        "What time do we usually have lunch?",
                        "What time is lunch?",
                    ],
                },
                {"speaker": "ai", "text": "We head out for lunch together around 12:30. Have a great first day!"},
            ],
        },
    },
    {
        "id": "a2-scheduling-meeting",
        "title": "Scheduling a team call",
        "title_es": "Agendar una videollamada de equipo",
        "cefr": "A2",
        "topic": "work-and-career",
        "description": "Coordina una videollamada con un colega en otra zona horaria, confirma la hora y envía la invitación.",
        "phrases": [
            {
                "id": "free-tomorrow-morning",
                "text": "Are you free for a quick video call tomorrow morning?",
                "translation": "¿Estás libre para una videollamada rápida mañana por la mañana?",
                "visual_hint": "💻📅",
                "cloze": [2, 6, 8],
                "glossary": [
                    {"word": "quick", "meaning": "rápida / breve", "ipa": "kwɪk"},
                    {"word": "video call", "meaning": "videollamada", "ipa": "ˈvɪdioʊ kɔːl"},
                ],
            },
            {
                "id": "ten-am-work",
                "text": "Does ten thirty in the morning work for your schedule?",
                "translation": "¿Las diez y media de la mañana te vienen bien en tu agenda?",
                "visual_hint": "🕥🗓️",
                "cloze": [1, 6, 9],
                "glossary": [
                    {"word": "work for", "meaning": "funcionar / acomodar", "ipa": "wɜːrk fɔːr"},
                    {"word": "schedule", "meaning": "agenda / horario", "ipa": "ˈskedʒuːl"},
                ],
            },
            {
                "id": "send-calendar-invite",
                "text": "I will send you a calendar invite with the Zoom link.",
                "translation": "Te enviaré una invitación de calendario con el enlace de Zoom.",
                "visual_hint": "📧🔗",
                "cloze": [2, 6, 10],
                "glossary": [
                    {"word": "calendar invite", "meaning": "invitación de calendario", "ipa": "ˈkælɪndər ˈɪnvaɪt"},
                    {"word": "link", "meaning": "enlace", "ipa": "lɪŋk"},
                ],
            },
            {
                "id": "share-the-slides",
                "text": "Could you share the presentation slides before the meeting?",
                "translation": "¿Podrías compartir las diapositivas de la presentación antes de la reunión?",
                "visual_hint": "📊📤",
                "cloze": [2, 5, 8],
                "glossary": [
                    {"word": "share", "meaning": "compartir", "ipa": "ʃer"},
                    {"word": "slides", "meaning": "diapositivas", "ipa": "slaɪdz"},
                ],
            },
            {
                "id": "push-it-back",
                "text": "If you are busy, we can move it to Thursday afternoon.",
                "translation": "Si estás ocupado, podemos moverla para el jueves por la tarde.",
                "visual_hint": "🔄🕓",
                "cloze": [3, 6, 9],
                "glossary": [
                    {"word": "busy", "meaning": "ocupado", "ipa": "ˈbɪzi"},
                    {"word": "move it", "meaning": "cambiarla de hora / moverla", "ipa": "muːv ɪt"},
                ],
            },
            {
                "id": "talk-to-you-then",
                "text": "Perfect, thirty minutes will be enough. Talk to you tomorrow!",
                "translation": "Perfecto, treinta minutos serán suficientes. ¡Hablamos mañana!",
                "visual_hint": "👍⏱️",
                "cloze": [2, 5, 9],
                "glossary": [
                    {"word": "enough", "meaning": "suficiente", "ipa": "ɪˈnʌf"},
                    {"word": "talk to you", "meaning": "hablamos / conversamos", "ipa": "tɔːk tə juː"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "colleague (David)",
            "user_role": "project coordinator",
            "setting": "Planning a sync call to review client slides.",
            "turns": [
                {"speaker": "ai", "text": "Hi! We should review the client presentation soon. When would you like to meet?"},
                {
                    "speaker": "user",
                    "goal": "Pregunta si está libre para una videollamada mañana a las 10:30 AM.",
                    "suggested_lines": [
                        "Are you free for a quick video call tomorrow morning?",
                        "Does ten thirty in the morning work for your schedule?",
                    ],
                },
                {"speaker": "ai", "text": "Let me check my calendar. Yes, 10:30 AM tomorrow is wide open!"},
                {
                    "speaker": "user",
                    "goal": "Di que enviarás la invitación de calendario con el enlace de Zoom.",
                    "suggested_lines": [
                        "I will send you a calendar invite with the Zoom link.",
                        "Great, I'll send the calendar invite with the link.",
                    ],
                },
                {"speaker": "ai", "text": "Sounds good. Do you need anything from me before we hop on the call?"},
                {
                    "speaker": "user",
                    "goal": "Pídele compartir las diapositivas de la presentación antes de la reunión.",
                    "suggested_lines": [
                        "Could you share the presentation slides before the meeting?",
                        "Please share the slides before the call.",
                    ],
                },
                {"speaker": "ai", "text": "Sure, I'll email them to you this afternoon. Will half an hour be enough?"},
                {
                    "speaker": "user",
                    "goal": "Confirma que treinta minutos bastan y despídete hasta mañana.",
                    "suggested_lines": [
                        "Perfect, thirty minutes will be enough. Talk to you tomorrow!",
                        "Yes, thirty minutes is enough. Talk to you tomorrow!",
                    ],
                },
                {"speaker": "ai", "text": "See you on Zoom tomorrow at 10:30!"},
            ],
        },
    },
    {
        "id": "b1-project-status-update",
        "title": "Giving a daily standup update",
        "title_es": "Dar un avance diario de proyecto",
        "cefr": "B1",
        "topic": "work-and-career",
        "description": "Explica en la reunión diaria qué completaste ayer, en qué trabajas hoy y si tienes algún bloqueo.",
        "phrases": [
            {
                "id": "wrapped-up-feature",
                "text": "Yesterday I finished testing the payment page and fixed two small bugs.",
                "translation": "Ayer terminé de probar la página de pagos y corregí dos pequeños errores.",
                "visual_hint": "✅💻",
                "cloze": [2, 3, 8],
                "glossary": [
                    {"word": "testing", "meaning": "probando / haciendo pruebas", "ipa": "ˈtestɪŋ"},
                    {"word": "bugs", "meaning": "errores de código / fallos", "ipa": "bʌɡz"},
                ],
            },
            {
                "id": "focusing-today-on",
                "text": "Today my main priority is connecting the checkout form to the database.",
                "translation": "Hoy mi prioridad principal es conectar el formulario de pago a la base de datos.",
                "visual_hint": "🎯🗄️",
                "cloze": [2, 3, 6],
                "glossary": [
                    {"word": "priority", "meaning": "prioridad", "ipa": "praɪˈɔːrəti"},
                    {"word": "checkout form", "meaning": "formulario de compra", "ipa": "ˈtʃekaʊt fɔːrm"},
                ],
            },
            {
                "id": "waiting-on-api",
                "text": "I'm currently blocked waiting for the updated API keys from security.",
                "translation": "Actualmente estoy bloqueado esperando las llaves de API actualizadas de seguridad.",
                "visual_hint": "🚧🔑",
                "cloze": [2, 3, 7],
                "glossary": [
                    {"word": "blocked", "meaning": "bloqueado / detenido", "ipa": "blɑːkt"},
                    {"word": "waiting for", "meaning": "esperando por", "ipa": "ˈweɪtɪŋ fɔːr"},
                ],
            },
            {
                "id": "on-track-for-friday",
                "text": "Once I get access, we'll still be on track for Friday's release.",
                "translation": "Una vez que tenga acceso, seguiremos a tiempo para el lanzamiento del viernes.",
                "visual_hint": "🚀📅",
                "cloze": [7, 8, 11],
                "glossary": [
                    {"word": "on track", "meaning": "en camino / a tiempo según el plan", "ipa": "ɑːn træk"},
                    {"word": "release", "meaning": "lanzamiento / entrega", "ipa": "rɪˈliːs"},
                ],
            },
            {
                "id": "pair-after-standup",
                "text": "Could we sync for ten minutes after standup to review the pull request?",
                "translation": "¿Podríamos reunirnos diez minutos después del standup para revisar el pull request?",
                "visual_hint": "🤝🔍",
                "cloze": [2, 7, 9],
                "glossary": [
                    {"word": "sync", "meaning": "sincronizarse / conversar brevemente", "ipa": "sɪŋk"},
                    {"word": "review", "meaning": "revisar", "ipa": "rɪˈvjuː"},
                ],
            },
            {
                "id": "no-other-blockers",
                "text": "Other than that, everything is moving smoothly on my end.",
                "translation": "Fuera de eso, todo avanza sin contratiempos por mi parte.",
                "visual_hint": "🌊👍",
                "cloze": [5, 6, 9],
                "glossary": [
                    {"word": "smoothly", "meaning": "sin problemas / fluidamente", "ipa": "ˈsmuːðli"},
                    {"word": "on my end", "meaning": "por mi lado / de mi parte", "ipa": "ɑːn maɪ end"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "scrum master",
            "user_role": "team member",
            "setting": "Morning 10-minute agile daily standup.",
            "turns": [
                {"speaker": "ai", "text": "Morning everyone! Let's go around the room. How did the payment module go yesterday?"},
                {
                    "speaker": "user",
                    "goal": "Cuenta que ayer terminaste de probar la página de pagos y corregiste dos bugs.",
                    "suggested_lines": [
                        "Yesterday I finished testing the payment page and fixed two small bugs.",
                        "Today my main priority is connecting the checkout form to the database.",
                    ],
                },
                {"speaker": "ai", "text": "Nice progress! What are you focusing on today, and do you have any blockers?"},
                {
                    "speaker": "user",
                    "goal": "Explica tu prioridad de hoy y que estás bloqueado esperando las llaves de API.",
                    "suggested_lines": [
                        "I'm currently blocked waiting for the updated API keys from security.",
                        "Today my main priority is connecting the checkout form to the database.",
                    ],
                },
                {"speaker": "ai", "text": "I'll ping the security lead right now to get those keys unlocked. Will this impact Friday's release?"},
                {
                    "speaker": "user",
                    "goal": "Confirma que en cuanto tengas acceso seguirán a tiempo para el viernes.",
                    "suggested_lines": [
                        "Once I get access, we'll still be on track for Friday's release.",
                        "Other than that, everything is moving smoothly on my end.",
                    ],
                },
                {"speaker": "ai", "text": "Great to hear. Do you need anyone to review your code today?"},
                {
                    "speaker": "user",
                    "goal": "Pide diez minutos después del standup para revisar el pull request.",
                    "suggested_lines": [
                        "Could we sync for ten minutes after standup to review the pull request?",
                        "Yes, let's sync after standup to review the pull request.",
                    ],
                },
                {"speaker": "ai", "text": "Sure thing, let's stay on the line right after this!"},
            ],
        },
    },
    # --- MODULE 6: health-and-emergencies (missing A1, B2, C2) ---
    {
        "id": "a1-calling-help-desk",
        "title": "Asking for first aid at reception",
        "title_es": "Pedir un botiquín en recepción",
        "cefr": "A1",
        "topic": "health-and-emergencies",
        "description": "Pide ayuda sencilla por un corte pequeño en el dedo, solicita una curita y agua.",
        "phrases": [
            {
                "id": "cut-my-finger",
                "text": "Excuse me, I have a small cut on my finger.",
                "translation": "Disculpe, tengo un pequeño corte en el dedo.",
                "visual_hint": "☝️🩹",
                "cloze": [5, 6, 9],
                "glossary": [
                    {"word": "cut", "meaning": "corte / herida pequeña", "ipa": "kʌt"},
                    {"word": "finger", "meaning": "dedo de la mano", "ipa": "ˈfɪŋɡər"},
                ],
            },
            {
                "id": "first-aid-kit",
                "text": "Do you have a first aid kit here?",
                "translation": "¿Tienen un botiquín de primeros auxilios aquí?",
                "visual_hint": "🧰➕",
                "cloze": [4, 5, 6],
                "glossary": [
                    {"word": "first aid kit", "meaning": "botiquín de primeros auxilios", "ipa": "fɜːrst eɪd kɪt"},
                ],
            },
            {
                "id": "need-a-band-aid",
                "text": "Can I have a bandage and some antiseptic wipes, please?",
                "translation": "¿Me puede dar una curita y unas toallitas antisépticas, por favor?",
                "visual_hint": "🩹🧴",
                "cloze": [4, 7],
                "glossary": [
                    {"word": "bandage", "meaning": "curita / vendaje", "ipa": "ˈbændɪdʒ"},
                    {"word": "wipes", "meaning": "toallitas limpiadoras", "ipa": "waɪps"},
                ],
            },
            {
                "id": "glass-of-water",
                "text": "Could I also get a glass of cold water?",
                "translation": "¿Me podría dar también un vaso de agua fría?",
                "visual_hint": "🥛💧",
                "cloze": [5, 7, 8],
                "glossary": [
                    {"word": "glass", "meaning": "vaso", "ipa": "ɡlæs"},
                    {"word": "cold", "meaning": "fría", "ipa": "koʊld"},
                ],
            },
            {
                "id": "feel-much-better",
                "text": "It is not serious. I feel much better now.",
                "translation": "No es grave. Me siento mucho mejor ahora.",
                "visual_hint": "😌👍",
                "cloze": [3, 5, 7],
                "glossary": [
                    {"word": "serious", "meaning": "grave / serio", "ipa": "ˈsɪriəs"},
                    {"word": "better", "meaning": "mejor", "ipa": "ˈbetər"},
                ],
            },
            {
                "id": "nearest-clinic",
                "text": "Where is the nearest pharmacy from here?",
                "translation": "¿Dónde está la farmacia más cercana desde aquí?",
                "visual_hint": "🏥📍",
                "cloze": [3, 4],
                "glossary": [
                    {"word": "nearest", "meaning": "más cercana", "ipa": "ˈnɪrɪst"},
                    {"word": "pharmacy", "meaning": "farmacia", "ipa": "ˈfɑːrməsi"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "receptionist",
            "user_role": "visitor",
            "setting": "Lobby reception desk at a community center.",
            "turns": [
                {"speaker": "ai", "text": "Oh! Are you okay? What happened to your hand?"},
                {
                    "speaker": "user",
                    "goal": "Explica que tienes un pequeño corte en el dedo y pregunta por el botiquín.",
                    "suggested_lines": [
                        "Excuse me, I have a small cut on my finger.",
                        "Do you have a first aid kit here?",
                    ],
                },
                {"speaker": "ai", "text": "Yes, I have our first aid box right under the counter. What do you need?"},
                {
                    "speaker": "user",
                    "goal": "Pide una curita y toallitas antisépticas.",
                    "suggested_lines": [
                        "Can I have a bandage and some antiseptic wipes, please?",
                        "A bandage, please.",
                    ],
                },
                {"speaker": "ai", "text": "Here you go. Please sit down for a moment. Can I get you anything else?"},
                {
                    "speaker": "user",
                    "goal": "Pide un vaso de agua fría y di que ya te sientes mejor.",
                    "suggested_lines": [
                        "Could I also get a glass of cold water?",
                        "It is not serious. I feel much better now.",
                    ],
                },
                {"speaker": "ai", "text": "Here is your water. Glad it's just a paper cut!"},
                {
                    "speaker": "user",
                    "goal": "Pregunta dónde está la farmacia más cercana.",
                    "suggested_lines": [
                        "Where is the nearest pharmacy from here?",
                        "Thank you! Where is the nearest pharmacy?",
                    ],
                },
                {"speaker": "ai", "text": "There's a pharmacy right across the street next to the bakery."},
            ],
        },
    },
    {
        "id": "b2-dental-emergency",
        "title": "Urgent dental appointment abroad",
        "title_es": "Urgencia dental durante un viaje",
        "cefr": "B2",
        "topic": "health-and-emergencies",
        "description": "Explica en una clínica dental que se te fracturó un empaste durante un viaje y necesitas atención de urgencia.",
        "phrases": [
            {
                "id": "cracked-filling",
                "text": "I cracked a filling on my upper molar last night and have sharp sensitivity to cold.",
                "translation": "Se me fracturó un empaste en la muela superior anoche y tengo una sensibilidad aguda al frío.",
                "visual_hint": "🦷⚡",
                "cloze": [1, 3, 6, 13],
                "glossary": [
                    {"word": "filling", "meaning": "empaste / tapadura dental", "ipa": "ˈfɪlɪŋ"},
                    {"word": "molar", "meaning": "muela / molar", "ipa": "ˈmoʊlər"},
                ],
            },
            {
                "id": "fit-me-in-today",
                "text": "Since I'm flying out on Thursday, could the dentist squeeze me in for an emergency slot today?",
                "translation": "Como mi vuelo sale el jueves, ¿podría el dentista hacerme un hueco de urgencia hoy?",
                "visual_hint": "📅✈️",
                "cloze": [9, 14, 15],
                "glossary": [
                    {"word": "squeeze me in", "meaning": "hacerme un espacio en la agenda", "ipa": "skwiːz miː ɪn"},
                    {"word": "slot", "meaning": "turno / espacio disponible", "ipa": "slɑːt"},
                ],
            },
            {
                "id": "temporary-crown",
                "text": "Would a temporary composite restoration hold up until I see my regular dentist back home?",
                "translation": "¿Aguantaría una restauración temporal de resina hasta que vea a mi dentista habitual en casa?",
                "visual_hint": "🛡️🦷",
                "cloze": [2, 4, 5],
                "glossary": [
                    {"word": "temporary", "meaning": "temporal / provisional", "ipa": "ˈtempəreri"},
                    {"word": "hold up", "meaning": "resistir / aguantar", "ipa": "hoʊld ʌp"},
                ],
            },
            {
                "id": "local-anesthetic",
                "text": "I have no adverse reactions to local anesthetic, though I prefer a numbing gel first.",
                "translation": "No tengo reacciones adversas a la anestesia local, aunque prefiero un gel anestésico primero.",
                "visual_hint": "💉🦷",
                "cloze": [3, 6, 12],
                "glossary": [
                    {"word": "adverse reactions", "meaning": "reacciones adversas", "ipa": "ædˈvɜːrs riˈækʃənz"},
                    {"word": "numbing", "meaning": "adormecedor / anestésico tópico", "ipa": "ˈnʌmɪŋ"},
                ],
            },
            {
                "id": "avoid-chewing-side",
                "text": "How long should I wait before chewing solid food on that side?",
                "translation": "¿Cuánto tiempo debo esperar antes de masticar alimentos sólidos de ese lado?",
                "visual_hint": "🍎⏳",
                "cloze": [4, 6, 7],
                "glossary": [
                    {"word": "chewing", "meaning": "masticar", "ipa": "ˈtʃuːɪŋ"},
                    {"word": "solid food", "meaning": "comida sólida", "ipa": "ˈsɑːlɪd fuːd"},
                ],
            },
            {
                "id": "dental-chart-copy",
                "text": "Could you email me the digital X-ray and treatment notes for my travel insurance?",
                "translation": "¿Podría enviarme por correo la radiografía digital y las notas del tratamiento para mi seguro de viaje?",
                "visual_hint": "📧🩻",
                "cloze": [5, 7, 8],
                "glossary": [
                    {"word": "treatment notes", "meaning": "notas clínicas del tratamiento", "ipa": "ˈtriːtmənt noʊts"},
                    {"word": "travel insurance", "meaning": "seguro de viaje", "ipa": "ˈtrævəl ɪnˈʃʊrəns"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "dentist",
            "user_role": "patient",
            "setting": "Dental clinic in London during an urgent walk-in visit.",
            "turns": [
                {"speaker": "ai", "text": "Hello, come on in. Our receptionist mentioned you're traveling and having tooth pain. What happened?"},
                {
                    "speaker": "user",
                    "goal": "Explica que se te rompió un empaste anoche y tienes sensibilidad al frío.",
                    "suggested_lines": [
                        "I cracked a filling on my upper molar last night and have sharp sensitivity to cold.",
                        "Since I'm flying out on Thursday, could the dentist squeeze me in for an emergency slot today?",
                    ],
                },
                {"speaker": "ai", "text": "Let's take a quick bitewing X-ray. Good news: the nerve is healthy, so we can place a bonded composite filling right now."},
                {
                    "speaker": "user",
                    "goal": "Pregunta si la restauración aguantará hasta volver a casa y comenta sobre la anestesia local.",
                    "suggested_lines": [
                        "Would a temporary composite restoration hold up until I see my regular dentist back home?",
                        "I have no adverse reactions to local anesthetic, though I prefer a numbing gel first.",
                    ],
                },
                {"speaker": "ai", "text": "Actually, this UV-cured composite is a full permanent restoration, and I'll apply topical numbing gel first."},
                {
                    "speaker": "user",
                    "goal": "Pregunta cuánto tiempo esperar antes de masticar sólidos de ese lado.",
                    "suggested_lines": [
                        "How long should I wait before chewing solid food on that side?",
                        "When can I chew solid food on that side?",
                    ],
                },
                {"speaker": "ai", "text": "Wait about two hours until the numbness wears off completely so you don't bite your cheek."},
                {
                    "speaker": "user",
                    "goal": "Pide que te envíen por correo la radiografía digital y las notas para tu seguro de viaje.",
                    "suggested_lines": [
                        "Could you email me the digital X-ray and treatment notes for my travel insurance?",
                        "Please email me the X-ray and treatment notes for my insurance.",
                    ],
                },
                {"speaker": "ai", "text": "Our front desk will email the full PDF packet and itemized receipt right now. Safe flight on Thursday!"},
            ],
        },
    },
    {
        "id": "c2-medical-second-opinion",
        "title": "Discussing diagnostic options with a specialist",
        "title_es": "Consultar segunda opinión con un especialista",
        "cefr": "C2",
        "topic": "health-and-emergencies",
        "description": "Analiza con un médico especialista los pros y contras de un tratamiento conservador frente a una intervención quirúrgica.",
        "phrases": [
            {
                "id": "conservative-management",
                "text": "Before consenting to an invasive procedure, I'd like to weigh the efficacy of conservative physical therapy.",
                "translation": "Antes de consentir un procedimiento invasivo, quisiera sopesar la eficacia de la fisioterapia conservadora.",
                "visual_hint": "🩺⚖️",
                "cloze": [1, 4, 9, 11],
                "glossary": [
                    {"word": "invasive procedure", "meaning": "procedimiento invasivo / quirúrgico", "ipa": "ɪnˈveɪsɪv prəˈsiːdʒər"},
                    {"word": "weigh the efficacy", "meaning": "sopesar la eficacia", "ipa": "weɪ ði ˈefɪkəsi"},
                ],
            },
            {
                "id": "mri-findings",
                "text": "Do the high-resolution MRI findings correlate with a partial tear or merely localized inflammation?",
                "translation": "¿Los hallazgos de la resonancia magnética de alta resolución se correlacionan con un desgarro parcial o solo inflamación localizada?",
                "visual_hint": "🧲🔬",
                "cloze": [4, 5, 9, 13],
                "glossary": [
                    {"word": "correlate with", "meaning": "correlacionarse con / corresponder a", "ipa": "ˈkɔːrəleɪt wɪð"},
                    {"word": "partial tear", "meaning": "desgarro parcial", "ipa": "ˈpɑːrʃəl ter"},
                ],
            },
            {
                "id": "recovery-trajectory",
                "text": "What does the postoperative rehabilitation trajectory look like compared to non-surgical management?",
                "translation": "¿Cómo es la evolución de la rehabilitación posoperatoria en comparación con el manejo no quirúrgico?",
                "visual_hint": "📈🏃",
                "cloze": [3, 4, 5, 10],
                "glossary": [
                    {"word": "postoperative", "meaning": "posoperatoria", "ipa": "ˌpoʊstˈɑːpərətɪv"},
                    {"word": "trajectory", "meaning": "trayectoria / curva de recuperación", "ipa": "trəˈdʒektəri"},
                ],
            },
            {
                "id": "long-term-prognosis",
                "text": "If we defer arthroscopy for twelve weeks, do we risk compromising the long-term prognosis?",
                "translation": "Si posponemos la artroscopia por doce semanas, ¿corremos el riesgo de comprometer el pronóstico a largo plazo?",
                "visual_hint": "⏳🩺",
                "cloze": [2, 9, 13],
                "glossary": [
                    {"word": "defer", "meaning": "posponer / diferir", "ipa": "dɪˈfɜːr"},
                    {"word": "prognosis", "meaning": "pronóstico médico", "ipa": "prɑːɡˈnoʊsɪs"},
                ],
            },
            {
                "id": "targeted-biomechanics",
                "text": "I'm keen to pursue a targeted biomechanical protocol and reassess mobility at the six-week mark.",
                "translation": "Estoy muy interesado en seguir un protocolo biomecánico específico y reevaluar la movilidad a las seis semanas.",
                "visual_hint": "🏋️‍♂️🗓️",
                "cloze": [3, 5, 9],
                "glossary": [
                    {"word": "keen to", "meaning": "muy dispuesto / interesado en", "ipa": "kiːn tə"},
                    {"word": "reassess", "meaning": "reevaluar", "ipa": "ˌriːəˈses"},
                ],
            },
            {
                "id": "multidisciplinary-consult",
                "text": "Could your office forward the imaging report to my sports physiotherapist so both teams stay aligned?",
                "translation": "¿Podría su consultorio reenviar el informe de imagenología a mi fisioterapeuta deportivo para que ambos equipos estén alineados?",
                "visual_hint": "📤🤝",
                "cloze": [3, 6, 15],
                "glossary": [
                    {"word": "imaging report", "meaning": "informe radiológico / de imagen", "ipa": "ˈɪmɪdʒɪŋ rɪˈpɔːrt"},
                    {"word": "stay aligned", "meaning": "mantenerse coordinados", "ipa": "steɪ əˈlaɪnd"},
                ],
            },
        ],
        "roleplay": {
            "ai_role": "orthopedic specialist",
            "user_role": "patient",
            "setting": "Specialist consultation reviewing shoulder MRI scans.",
            "turns": [
                {"speaker": "ai", "text": "Good morning. I've reviewed your shoulder MRI from last week. What questions are top of mind for you today?"},
                {
                    "speaker": "user",
                    "goal": "Pregunta si la resonancia muestra un desgarro parcial o inflamación y pide evaluar terapia conservadora.",
                    "suggested_lines": [
                        "Do the high-resolution MRI findings correlate with a partial tear or merely localized inflammation?",
                        "Before consenting to an invasive procedure, I'd like to weigh the efficacy of conservative physical therapy.",
                    ],
                },
                {"speaker": "ai", "text": "It's a low-grade partial tendon tear with bursitis. Surgery is an option, but structured rehab often resolves eighty percent of cases."},
                {
                    "speaker": "user",
                    "goal": "Pregunta por la curva de recuperación posoperatoria y si posponer la cirugía compromete el pronóstico.",
                    "suggested_lines": [
                        "What does the postoperative rehabilitation trajectory look like compared to non-surgical management?",
                        "If we defer arthroscopy for twelve weeks, do we risk compromising the long-term prognosis?",
                    ],
                },
                {"speaker": "ai", "text": "Deferring for twelve weeks carries virtually no structural risk as long as you avoid overhead loading."},
                {
                    "speaker": "user",
                    "goal": "Expresa que prefieres iniciar el protocolo biomecánico y reevaluar a las seis semanas.",
                    "suggested_lines": [
                        "I'm keen to pursue a targeted biomechanical protocol and reassess mobility at the six-week mark.",
                        "Let's start with targeted physical therapy and reassess in six weeks.",
                    ],
                },
                {"speaker": "ai", "text": "That is a very sensible, evidence-based approach. I'll draft the rehab prescription."},
                {
                    "speaker": "user",
                    "goal": "Pide que envíen el informe de imagenología a tu fisioterapeuta deportivo.",
                    "suggested_lines": [
                        "Could your office forward the imaging report to my sports physiotherapist so both teams stay aligned?",
                        "Please forward the MRI report to my physiotherapist.",
                    ],
                },
                {"speaker": "ai", "text": "Consider it done. We'll see you back here in six weeks to measure your range of motion!"},
            ],
        },
    },
]


def main() -> None:
    # 1. Expand existing 18 scenarios
    for slug, extra_phrases in EXTRA_PHRASES_FOR_EXISTING.items():
        path = SCENARIOS_DIR / f"{slug}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        existing_ids = {p["id"] for p in data["phrases"]}
        for ep in extra_phrases:
            if ep["id"] not in existing_ids:
                data["phrases"].append(ep)
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")

    # 2. Write 18 new scenarios
    for sc in NEW_SCENARIOS:
        path = SCENARIOS_DIR / f"{sc['id']}.yaml"
        path.write_text(yaml.safe_dump(sc, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")

    # 3. Validate via ContentRepository
    import sys

    sys.path.insert(0, str(ROOT / "backend"))
    from app.content.repository import get_repository

    repo = get_repository()
    scenarios = repo.list()
    total_phrases = sum(len(s.phrases) for s in scenarios)
    print(f"Validated {len(scenarios)} scenarios and {total_phrases} total phrases across 6 modules and 6 CEFR levels!")

    # 4. Sync FALLBACK_SCENARIOS in backend/app/static/index.html
    fallback_list = []
    for s in scenarios:
        d = s.model_dump(mode="json")
        d["band"] = s.cefr.band
        fallback_list.append(d)

    html = STATIC_INDEX.read_text(encoding="utf-8")
    pattern = re.compile(r"const FALLBACK_SCENARIOS = \[.*?\n    \];", re.DOTALL)
    replacement = "const FALLBACK_SCENARIOS = " + json.dumps(fallback_list, ensure_ascii=False, indent=6) + ";"
    new_html, count = pattern.subn(replacement, html, count=1)
    if count != 1:
        raise RuntimeError(f"Expected 1 FALLBACK_SCENARIOS replacement, got {count}")
    STATIC_INDEX.write_text(new_html, encoding="utf-8")
    print(f"Synced {len(fallback_list)} scenarios into {STATIC_INDEX}")


if __name__ == "__main__":
    main()
