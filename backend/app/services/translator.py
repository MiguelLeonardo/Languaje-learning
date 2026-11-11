"""Phrase-focused instant translator (Tap-to-Translate Overlay like Speak).

Works across all 5 lesson stages, Common Phrases, and SRS Review:
- Resolves any tapped word or multi-word chunk against the scenario's glossary, curriculum phrase bank,
  and conversational English phrase-builder dictionary.
- Always pairs the word/chunk translation with its full sentence context ("phrase-first learning"),
  phonetic IPA, a grammar/collocation usage tip in Spanish, and related examples from the curriculum.
"""

from pydantic import BaseModel

from app.content.repository import ContentRepository
from app.services.text import normalize_words

# High-frequency conversational lexicon (word -> (meaning_es, ipa, chunk_tip_es))
COMMON_LEXICON: dict[str, tuple[str, str, str]] = {
    "can": (
        "puedo / podría (verbo modal para pedir o preguntar)",
        "kæn",
        "Úsalo en 'Can I have...?' o 'Can you...?' para peticiones cotidianas.",
    ),
    "could": (
        "podría (más cortés que 'can')",
        "kʊd",
        "Estructura clave: 'Could you + verbo base, please?'.",
    ),
    "would": (
        "haría / gustaría (condicional cortés)",
        "wʊd",
        "Úsalo en 'Would it be possible to...?' o 'I'd like...'.",
    ),
    "have": (
        "tener / tomar / haber",
        "hæv",
        "En cafeterías y restaurantes 'Can I have...?' equivale a '¿Me da / me trae...?'.",
    ),
    "please": (
        "por favor",
        "pliːz",
        "Colócalo al final de la frase con entonación descendente suave.",
    ),
    "coffee": (
        "café",
        "ˈkɔːfi",
        "Combínalo con tamaño: 'a small/medium/large coffee'.",
    ),
    "small": (
        "pequeño/a",
        "smɔːl",
        "En 'a small one', 'one' sustituye al sustantivo para no repetir 'coffee'.",
    ),
    "one": (
        "uno/a (pronombre sustituto)",
        "wʌn",
        "'A small one' = 'uno pequeño' (evita repetir el sustantivo).",
    ),
    "how": (
        "cómo / cuánto",
        "haʊ",
        "'How much...?' (precio), 'How do I get to...?' (direcciones), 'How long...?' (tiempo).",
    ),
    "much": (
        "mucho / cuánto (con incontables y precios)",
        "mʌtʃ",
        "'How much is it?' = '¿Cuánto cuesta?'.",
    ),
    "thank": (
        "agradecer (thank you = gracias)",
        "θæŋk",
        "'Thank you very much' o 'Thanks a lot' para cerrar cualquier interacción.",
    ),
    "very": ("muy", "ˈveri", "Intensificador antes de adjetivos o adverbios."),
    "excuse": (
        "disculpar ('Excuse me' = disculpe)",
        "ɪkˈskjuːz",
        "Úsalo siempre para iniciar una pregunta a un desconocido en la calle.",
    ),
    "pharmacy": (
        "farmacia",
        "ˈfɑːrməsi",
        "En EE. UU. también escucharás 'drugstore'; en Reino Unido, 'chemist'.",
    ),
    "near": ("cerca de", "nɪr", "'near here' = 'cerca de aquí' (no lleva 'to')."),
    "here": ("aquí", "hɪr", "Frases clave: 'near here', 'from here', 'right here'."),
    "train": (
        "tren",
        "treɪn",
        "'train station' = estación de tren; 'subway/metro station' = estación de metro.",
    ),
    "station": (
        "estación",
        "ˈsteɪʃən",
        "Se combina como 'train station', 'bus station', 'police station'.",
    ),
    "far": ("lejos", "fɑːr", "'Is it far from here?' = '¿Está lejos de aquí?'."),
    "repeat": (
        "repetir",
        "rɪˈpiːt",
        "'Could you repeat that, please?' es tu frase salvavidas en cualquier nivel.",
    ),
    "reservation": (
        "reserva / reservación",
        "ˌrezərˈveɪʃən",
        "'I have a reservation under the name...' = 'Tengo una reserva a nombre de...'.",
    ),
    "under": (
        "bajo / a nombre de",
        "ˈʌndər",
        "En hoteles y restaurantes: 'under the name + apellido'.",
    ),
    "breakfast": (
        "desayuno",
        "ˈbrekfəst",
        "'Is breakfast included?' = '¿Está incluido el desayuno?'.",
    ),
    "included": (
        "incluido/a",
        "ɪnˈkluːdɪd",
        "'included in the price' = 'incluido en el precio'.",
    ),
    "afraid": (
        "temeroso ('I'm afraid...' = me temo que...)",
        "əˈfreɪd",
        "'I'm afraid + frase' suaviza una queja o mala noticia con mucha educación.",
    ),
    "working": (
        "funcionando / trabajando",
        "ˈwɜːrkɪŋ",
        "'isn't working' = 'no funciona' (para aparatos, wifi, aire acondicionado).",
    ),
    "possible": (
        "posible",
        "ˈpɑːsəbəl",
        "'Would it be possible to + verbo?' es la fórmula B1/B2 más natural para pedir favores.",
    ),
    "check": (
        "revisar / registrarse",
        "tʃek",
        "Phrasal verbs de viaje: 'check in' (registrarse) y 'check out' (salir del hotel).",
    ),
    "later": ("más tarde", "ˈleɪtər", "'a bit later' = 'un poco más tarde'."),
    "support": (
        "soporte / atención / apoyo",
        "səˈpɔːrt",
        "'customer support' = 'atención al cliente'.",
    ),
    "strengths": (
        "fortalezas / puntos fuertes",
        "streŋkθs",
        "'One of my main strengths is + verbo -ing'.",
    ),
    "calm": (
        "calma / tranquilo",
        "kɑːm",
        "'stay calm under pressure' = 'mantener la calma bajo presión'.",
    ),
    "pressure": ("presión", "ˈpreʃər", "Colocación fija: 'under pressure' (bajo presión)."),
    "team": (
        "equipo",
        "tiːm",
        "'the team I'd be working with' = 'el equipo con el que trabajaría'.",
    ),
    "hiring": (
        "contratación / selección",
        "ˈhaɪərɪŋ",
        "'the hiring process' = 'el proceso de selección'.",
    ),
    "deadline": (
        "fecha límite / plazo de entrega",
        "ˈdedlaɪn",
        "Colocaciones C1: 'meet a deadline' (cumplir) y 'push back a deadline' (aplazar).",
    ),
    "schedule": (
        "calendario / horario / cronograma",
        "ˈskedʒuːl",
        "'behind schedule' (atrasado) vs 'on schedule' (a tiempo).",
    ),
    "compromising": (
        "comprometer / sacrificar",
        "ˈkɑːmprəmaɪzɪŋ",
        "'without compromising on quality' = 'sin sacrificar la calidad'.",
    ),
    "halfway": (
        "a mitad de camino",
        "ˌhæfˈweɪ",
        "Idiom clave: 'meet halfway' = 'llegar a un punto medio'.",
    ),
    "advocate": (
        "defensor / abogado",
        "ˈædvəkət",
        "Idiom C2: 'play devil's advocate' = 'hacer de abogado del diablo'.",
    ),
    "isolate": ("aislar", "ˈaɪsəleɪt", "'isolate people' = 'aislar a las personas'."),
    "grain": (
        "grano / pizca",
        "ɡreɪn",
        "Idiom: 'take it with a grain of salt' = 'tomarlo con pinzas / con escepticismo'.",
    ),
    "belonging": (
        "pertenencia",
        "bɪˈlɔːŋɪŋ",
        "'a sense of belonging' = 'un sentido de pertenencia'.",
    ),
    "disagree": (
        "discrepar / no estar de acuerdo",
        "ˌdɪsəˈɡriː",
        "'agree to disagree' = 'aceptar que pensamos distinto sin discutir'.",
    ),
    "bill": (
        "cuenta / factura",
        "bɪl",
        "'Could we have the bill, please?' (UK) / 'the check' (US).",
    ),
    "allergic": (
        "alérgico/a",
        "əˈlɜːrdʒɪk",
        "'I'm allergic to nuts/dairy' = 'Soy alérgico a los frutos secos/lácteos'.",
    ),
    "ticket": (
        "boleto / billete / entrada",
        "ˈtɪkɪt",
        "'a round-trip ticket' (ida y vuelta) vs 'a one-way ticket' (solo ida).",
    ),
    "platform": (
        "andén / plataforma",
        "ˈplætfɔːrm",
        "'Which platform does the train leave from?' = '¿De qué andén sale el tren?'.",
    ),
    "delayed": (
        "retrasado/a",
        "dɪˈleɪd",
        "'My flight has been delayed' = 'Mi vuelo se ha retrasado'.",
    ),
    "gate": ("puerta de embarque", "ɡeɪt", "'boarding gate' = 'puerta de embarque'."),
    "try": ("probar / intentar", "traɪ", "'Can I try this on?' = '¿Me lo puedo probar?' (ropa)."),
    "size": (
        "talla / tamaño",
        "saɪz",
        "'Do you have this in a medium size?' = '¿Tiene esto en talla mediana?'.",
    ),
    "refund": (
        "reembolso / devolución",
        "ˈriːfʌnd",
        "'I'd like a full refund' = 'Me gustaría un reembolso completo'.",
    ),
    "receipt": (
        "recibo / ticket de compra",
        "rɪˈsiːt",
        "La 'p' en 'receipt' es muda: /rɪˈsiːt/.",
    ),
    "headache": (
        "dolor de cabeza",
        "ˈhedeɪk",
        "'I have a terrible headache' = 'Tengo un fuerte dolor de cabeza'.",
    ),
    "appointment": (
        "cita (médica o profesional)",
        "əˈpɔɪntmənt",
        "'make an appointment' = 'pedir una cita'.",
    ),
    "insurance": (
        "seguro",
        "ɪnˈʃʊrəns",
        "'health insurance' = 'seguro médico'; 'file a claim' = 'presentar un reclamo'.",
    ),
    "budget": (
        "presupuesto",
        "ˈbʌdʒɪt",
        "'allocate budget' = 'asignar presupuesto'; 'within budget' = 'dentro del presupuesto'.",
    ),
}


class RelatedPhrase(BaseModel):
    scenario_id: str
    cefr: str
    text: str
    translation_es: str


class TranslationCard(BaseModel):
    selected_text: str
    query: str
    normalized: str
    word_translation_es: str
    translation_es: str
    ipa: str | None = None
    phrase_text: str | None = None
    phrase_translation_es: str | None = None
    usage_tip_es: str
    chunk_tip_es: str
    chunk_breakdown: list[str] = []
    scenario_id: str | None = None
    phrase_id: str | None = None
    related_examples: list[RelatedPhrase] = []


def _build_chunks(phrase_text: str | None, selected: str) -> list[str]:
    if not phrase_text:
        return [selected]
    words = phrase_text.split()
    if len(words) <= 4:
        return [phrase_text]
    mid = len(words) // 2
    return [" ".join(words[:mid]), " ".join(words[mid:])]


def translate_selection(
    repo: ContentRepository,
    query: str,
    context_phrase: str | None = None,
    scenario_id: str | None = None,
    phrase_id: str | None = None,
) -> TranslationCard:
    cleaned = query.strip().strip(".,!?;:\"'“”")
    norm_tokens = normalize_words(cleaned)
    norm_key = " ".join(norm_tokens) if norm_tokens else cleaned.lower()

    matched_phrase = None
    matched_scen_id = scenario_id
    matched_glossary = None
    related: list[RelatedPhrase] = []

    scenarios = ([repo.get(scenario_id)] if scenario_id and repo.get(scenario_id) else []) + repo.list()
    seen_phrases: set[str] = set()

    for sc in scenarios:
        if not sc:
            continue
        for ph in sc.phrases:
            if phrase_id and ph.id == phrase_id:
                matched_phrase = ph
                matched_scen_id = sc.id
            if context_phrase and ph.text.lower() == context_phrase.strip().lower():
                matched_phrase = ph
                matched_scen_id = sc.id
            if ph.text.strip(".,!?;:").lower() == cleaned.lower():
                matched_phrase = ph
                matched_scen_id = sc.id
            for g in ph.glossary:
                if g.word.lower() == cleaned.lower() or g.word.lower() == norm_key:
                    matched_glossary = g
                    if not matched_phrase:
                        matched_phrase = ph
                        matched_scen_id = sc.id
            if norm_key and norm_key in " ".join(normalize_words(ph.text)) and ph.text not in seen_phrases:
                seen_phrases.add(ph.text)
                if len(related) < 3:
                    related.append(
                        RelatedPhrase(
                            scenario_id=sc.id,
                            cefr=sc.cefr.value,
                            text=ph.text,
                            translation_es=ph.translation,
                        )
                    )

    eff_phrase = matched_phrase.text if matched_phrase else (context_phrase or cleaned)
    eff_phrase_es = matched_phrase.translation if matched_phrase else None
    eff_phrase_id = matched_phrase.id if matched_phrase else phrase_id
    chunks = _build_chunks(eff_phrase, cleaned)

    if matched_phrase and matched_phrase.text.strip(".,!?;:").lower() == cleaned.lower():
        tip = "Aprende esta expresión como un bloque completo (chunk) sin traducir palabra por palabra."
        return TranslationCard(
            selected_text=cleaned,
            query=cleaned,
            normalized=norm_key,
            word_translation_es=matched_phrase.translation,
            translation_es=matched_phrase.translation,
            ipa=matched_phrase.glossary[0].ipa if matched_phrase.glossary else None,
            phrase_text=matched_phrase.text,
            phrase_translation_es=matched_phrase.translation,
            usage_tip_es=tip,
            chunk_tip_es=tip,
            chunk_breakdown=chunks,
            scenario_id=matched_scen_id,
            phrase_id=eff_phrase_id,
            related_examples=related,
        )

    if matched_glossary:
        tip = (
            f"En la frase «{matched_phrase.text}», «{matched_glossary.word}» funciona como pieza clave del bloque."
            if matched_phrase
            else "Practica esta palabra siempre dentro de la oración completa."
        )
        return TranslationCard(
            selected_text=cleaned,
            query=cleaned,
            normalized=norm_key,
            word_translation_es=matched_glossary.meaning,
            translation_es=matched_glossary.meaning,
            ipa=matched_glossary.ipa,
            phrase_text=eff_phrase,
            phrase_translation_es=eff_phrase_es or matched_glossary.meaning,
            usage_tip_es=tip,
            chunk_tip_es=tip,
            chunk_breakdown=chunks,
            scenario_id=matched_scen_id,
            phrase_id=eff_phrase_id,
            related_examples=related,
        )

    first_tok = norm_tokens[0] if norm_tokens else cleaned.lower()
    if norm_key in COMMON_LEXICON or first_tok in COMMON_LEXICON:
        meaning, ipa, tip = COMMON_LEXICON.get(norm_key) or COMMON_LEXICON[first_tok]
        return TranslationCard(
            selected_text=cleaned,
            query=cleaned,
            normalized=norm_key,
            word_translation_es=meaning,
            translation_es=meaning,
            ipa=ipa,
            phrase_text=eff_phrase,
            phrase_translation_es=eff_phrase_es or meaning,
            usage_tip_es=tip,
            chunk_tip_es=tip,
            chunk_breakdown=chunks,
            scenario_id=matched_scen_id,
            phrase_id=eff_phrase_id,
            related_examples=related,
        )

    fallback_meaning = (
        f"Parte de la expresión: «{matched_phrase.translation}»"
        if matched_phrase
        else f"Expresión en contexto («{cleaned}»)"
    )
    tip = "Repite la frase completa en voz alta para fijar el patrón gramatical en memoria muscular."
    return TranslationCard(
        selected_text=cleaned,
        query=cleaned,
        normalized=norm_key,
        word_translation_es=fallback_meaning,
        translation_es=fallback_meaning,
        ipa=None,
        phrase_text=eff_phrase,
        phrase_translation_es=eff_phrase_es or fallback_meaning,
        usage_tip_es=tip,
        chunk_tip_es=tip,
        chunk_breakdown=chunks,
        scenario_id=matched_scen_id,
        phrase_id=eff_phrase_id,
        related_examples=related,
    )
