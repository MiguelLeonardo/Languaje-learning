"""Generate 4 additional scenarios per (module, CEFR level) cell so that:
- Every one of the 6 modules × 6 CEFR levels (A1..C2) has 5 distinct scenarios (36 × 5 = 180 scenarios total)
- Every scenario has 6 conversational phrases with Spanish translations, IPA glossaries, visual hints, and cloze indices (1,081 phrases total)
- Every scenario has a 4-turn guided roleplay script
- Syncs FALLBACK_SCENARIOS in backend/app/static/index.html
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = ROOT / "content" / "scenarios"
STATIC_INDEX = ROOT / "backend" / "app" / "static" / "index.html"

# Blueprint of 4 additional scenarios per (topic, CEFR) cell = 144 new scenarios (plus 36 existing = 180 total)
# Format: (topic, cefr, slug_suffix, title_en, title_es, description_es, ai_role, user_role, setting, items)
# Each item in items: (phrase_id, en_text, es_translation, visual_hint, glossary_word, glossary_meaning, glossary_ipa, user_goal, ai_prompt)

CELL_BLUEPRINTS: list[tuple] = [
    # ==================== 1. FOOD-AND-DRINK ====================
    # A1 (4 new -> total 5 with a1-ordering-coffee)
    (
        "food-and-drink", "A1", "bakery-breakfast", "Buying bread at a bakery", "Comprar pan en la panadería",
        "Pide croissants recién horneados, jugo de naranja y pregunta el precio en una panadería.",
        "baker", "customer", "A neighborhood bakery at 8 AM.",
        [
            ("two-croissants", "Can I have two warm croissants, please?", "¿Me da dos croissants calientes, por favor?", "🥐🔥", "warm", "caliente / tibio", "wɔːrm", "Pide dos croissants calientes.", "Good morning! Everything is fresh out of the oven. What would you like?"),
            ("orange-juice", "And one fresh orange juice, please.", "Y un jugo de naranja natural, por favor.", "🍊🧃", "fresh", "fresco / natural", "freʃ", "Agrega un jugo de naranja natural.", "Two warm croissants. Would you like something to drink?"),
            ("slice-of-cake", "Is that chocolate cake sweet?", "¿Ese pastel de chocolate es dulce?", "🍰🍫", "sweet", "dulce", "swiːt", "Pregunta por el pastel y pide una bolsa.", "Yes, one orange juice! Anything else from the display case?"),
            ("paper-bag", "Put them in a paper bag, please.", "Póngalos en una bolsa de papel, por favor.", "🛍️🥖", "paper bag", "bolsa de papel", "ˈpeɪpər bæɡ", "Pide pagar con efectivo.", "It's delicious! That will be six dollars in total."),
            ("pay-with-cash", "Here is ten dollars in cash.", "Aquí tiene diez dólares en efectivo.", "💵🙌", "cash", "efectivo", "kæʃ", "", ""),
            ("keep-the-receipt", "Thank you! Have a lovely morning.", "¡Gracias! Que tenga una linda mañana.", "☀️😊", "lovely", "linda / agradable", "ˈlʌvli", "", ""),
        ],
    ),
    (
        "food-and-drink", "A1", "ice-cream-shop", "Ordering ice cream", "Pedir un helado",
        "Elige sabores de helado, decide entre vaso o cono y pide chispas de chocolate.",
        "server", "customer", "A sunny ice cream parlor near the beach.",
        [
            ("vanilla-and-strawberry", "I would like vanilla and strawberry, please.", "Quisiera vainilla y fresa, por favor.", "🍦🍓", "strawberry", "fresa / frutilla", "ˈstrɔːberi", "Elige los sabores vainilla y fresa.", "Hi there! Which flavors would you like today?"),
            ("in-a-cup", "In a small cup with a spoon, please.", "En un vaso pequeño con cuchara, por favor.", "🍨🥄", "spoon", "cuchara", "spuːn", "Pídelo en un vaso pequeño con cuchara.", "Great choice! Would you like that in a cup or a waffle cone?"),
            ("chocolate-sprinkles", "Can you add chocolate sprinkles on top?", "¿Puede agregar chispas de chocolate arriba?", "🍫✨", "sprinkles", "chispas dulces", "ˈsprɪŋkəlz", "Pide chispas de chocolate arriba.", "One small cup. Any toppings on your ice cream?"),
            ("napkin-please", "Can I have an extra napkin, please?", "¿Me da una servilleta extra, por favor?", "🧻👌", "napkin", "servilleta", "ˈnæpkɪn", "Pide una servilleta extra y agradece.", "Here is your ice cream! That's four dollars."),
            ("taste-the-mango", "May I taste the mango flavor first?", "¿Puedo probar el sabor de mango primero?", "🥭🥄", "taste", "probar", "teɪst", "", ""),
            ("very-cold-and-good", "This ice cream is very good, thank you!", "¡Este helado está muy rico, gracias!", "😋🍦", "good", "bueno / rico", "ɡʊd", "", ""),
        ],
    ),
    (
        "food-and-drink", "A1", "fast-food-combo", "Ordering a burger combo", "Pedir un combo de hamburguesa",
        "Ordena una hamburguesa con queso, papas fritas sin sal y una limonada.",
        "cashier", "customer", "A casual burger counter at lunchtime.",
        [
            ("cheeseburger-combo", "Can I get the cheeseburger combo, please?", "¿Me da el combo de hamburguesa con queso, por favor?", "🍔🍟", "combo", "menú completo / combo", "ˈkɑːmboʊ", "Pide el combo de hamburguesa con queso.", "Welcome! What can I get started for you?"),
            ("french-fries", "Medium french fries with ketchup, please.", "Papas fritas medianas con kétchup, por favor.", "🍟🍅", "french fries", "papas fritas", "frentʃ fraɪz", "Elige papas medianas con kétchup.", "Sure! What size fries and sauce would you like?"),
            ("iced-lemonade", "I want an iced lemonade to drink.", "Quiero una limonada con hielo para tomar.", "🍋🧊", "iced", "con hielo / helada", "aɪst", "Pide una limonada con hielo para tomar.", "And what drink comes with your meal?"),
            ("eat-here-tray", "We will eat here at a table.", "Vamos a comer aquí en una mesa.", "🍽️🪑", "eat here", "comer aquí", "iːt hɪr", "Indica que comerán aquí en una mesa.", "Got it! Is that for here or to go?"),
            ("no-onions-please", "No onions on the burger, please.", "Sin cebolla en la hamburguesa, por favor.", "🧅🚫", "onions", "cebollas", "ˈʌnjənz", "", ""),
            ("order-number", "Thank you, what is my order number?", "Gracias, ¿cuál es mi número de pedido?", "🔢🧾", "order number", "número de pedido", "ˈɔːrdər ˈnʌmbər", "", ""),
        ],
    ),
    (
        "food-and-drink", "A1", "fruit-market-stand", "Buying fresh fruit at the market", "Comprar fruta en el mercado",
        "Compra manzanas rojas, plátanos maduros y fresas en un puesto del mercado.",
        "vendor", "shopper", "An open-air morning fruit market.",
        [
            ("four-red-apples", "I would like four red apples, please.", "Quisiera cuatro manzanas rojas, por favor.", "🍎🧺", "apples", "manzanas", "ˈæpəlz", "Pide cuatro manzanas rojas.", "Good morning! Fresh fruit today. What would you like?"),
            ("ripe-bananas", "Are these yellow bananas ripe for today?", "¿Estos plátanos amarillos están maduros para hoy?", "🍌✨", "ripe", "maduro", "raɪp", "Pregunta si los plátanos están maduros.", "Four red apples! Anything else from the stand?"),
            ("box-of-berries", "I will also take one box of strawberries.", "También me llevo una caja de fresas.", "🍓📦", "box", "caja", "bɑːks", "Agrega una caja de fresas.", "Yes, they are sweet and ready to eat!"),
            ("how-much-all", "How much is everything together?", "¿Cuánto es todo junto?", "💶🧮", "together", "junto / en total", "təˈɡeðər", "Pregunta cuánto es todo junto.", "One box of strawberries. I have my own bag right here."),
            ("sweet-oranges", "These oranges smell very fresh.", "Estas naranjas huelen muy frescas.", "🍊🌿", "smell", "oler", "smel", "", ""),
            ("have-my-own-bag", "I have my own cloth bag, thanks.", "Traigo mi propia bolsa de tela, gracias.", "👜♻️", "own", "propia", "oʊn", "", ""),
        ],
    ),
    # A2 (4 new -> total 5 with a2-restaurant-dinner)
    (
        "food-and-drink", "A2", "pizzeria-delivery", "Ordering pizza to your hotel", "Pedir pizza a domicilio al hotel",
        "Llama a una pizzería local para pedir una pizza mediana, indica tu habitación y forma de pago.",
        "pizza order taker", "hotel guest", "Calling a local pizzeria from your hotel room.",
        [
            ("order-for-delivery", "Hi, I'd like to place an order for delivery, please.", "Hola, quisiera hacer un pedido a domicilio, por favor.", "🍕🛵", "delivery", "entrega a domicilio", "dɪˈlɪvəri", "Di que quieres hacer un pedido a domicilio.", "Luigi's Pizza, how can I help you tonight?"),
            ("medium-margherita", "Could I get a medium Margherita pizza with mushrooms?", "¿Me podría dar una pizza Margherita mediana con champiñones?", "🍕🍄", "mushrooms", "champiñones / hongos", "ˈmʌʃruːmz", "Pide una pizza Margherita mediana con champiñones.", "Sure! What kind of pizza would you like?"),
            ("thin-crust-crispy", "We prefer thin crust and extra garlic sauce.", "Preferimos masa delgada y salsa de ajo extra.", "🧄🥖", "thin crust", "masa delgada", "θɪn krʌst", "Indica que prefieres masa delgada y salsa de ajo.", "Medium Margherita with mushrooms. Thick or thin crust?"),
            ("deliver-hotel-lobby", "Please deliver it to the Park Hotel lobby, room 210.", "Por favor entréguela en la recepción del Hotel Park, habitación 210.", "🏨📍", "lobby", "vestíbulo / recepción", "ˈlɑːbi", "Da la dirección del Hotel Park y pregunta el tiempo de entrega.", "Got it! What is the delivery address?"),
            ("how-long-delivery", "How long will the delivery take tonight?", "¿Cuánto tardará la entrega esta noche?", "⏱️🛵", "take", "tardar / tomar tiempo", "teɪk", "", ""),
            ("pay-driver-by-card", "Can I pay the driver with a credit card?", "¿Puedo pagarle al repartidor con tarjeta de crédito?", "💳🤝", "driver", "repartidor / conductor", "ˈdraɪvər", "", ""),
        ],
    ),
    (
        "food-and-drink", "A2", "breakfast-buffet", "At the breakfast buffet", "En el buffet de desayuno",
        "Pregunta qué incluye el buffet, pide huevos revueltos recién hechos y leche sin lactosa.",
        "breakfast host", "guest", "A bright hotel dining room at 8:30 AM.",
        [
            ("buffet-included", "Good morning, is the breakfast buffet included with my room?", "Buenos días, ¿el buffet de desayuno está incluido con mi habitación?", "🥞🏨", "included", "incluido", "ɪnˈkluːdɪd", "Pregunta si el buffet está incluido con tu habitación.", "Good morning! Welcome to the breakfast room. What is your room number?"),
            ("scrambled-eggs-station", "Where can I order freshly cooked scrambled eggs?", "¿Dónde puedo pedir huevos revueltos recién hechos?", "🍳👨‍🍳", "scrambled eggs", "huevos revueltos", "ˈskræmbəld eɡz", "Pregunta dónde pedir huevos revueltos recién hechos.", "Room 405—yes, your breakfast is fully included!"),
            ("lactose-free-milk", "Do you have almond milk or lactose-free milk for cereal?", "¿Tienen leche de almendras o sin lactosa para el cereal?", "🥛🥣", "lactose-free", "sin lactosa", "ˈlæktoʊs friː", "Pregunta si tienen leche de almendras o sin lactosa.", "The chef at the omelet station makes them to order."),
            ("sit-by-window", "Can we sit at that sunny table by the window?", "¿Podemos sentarnos en esa mesa soleada junto a la ventana?", "🪟☀️", "sunny", "soleada", "ˈsʌni", "Pregunta si pueden sentarse junto a la ventana.", "Yes, the almond milk pitcher is right next to the fruit bowl."),
            ("refill-coffee-pot", "Could we get a pot of hot coffee for the table?", "¿Nos podría traer una jarra de café caliente para la mesa?", "☕🫖", "pot", "jarra / cafetera", "pɑːt", "", ""),
            ("until-what-time", "Until what time is the buffet open today?", "¿Hasta qué hora está abierto el buffet hoy?", "🕙🍽️", "until", "hasta", "ənˈtɪl", "", ""),
        ],
    ),
    (
        "food-and-drink", "A2", "food-truck-lunch", "Ordering at a street food truck", "Pedir en un camión de comida",
        "Pide tacos de pescado a la parrilla, pregunta qué tan picante es la salsa y pide servilletas.",
        "food truck chef", "customer", "A lively downtown food truck park.",
        [
            ("grilled-fish-tacos", "Hi! I'll try an order of three grilled fish tacos.", "¡Hola! Probaré una orden de tres tacos de pescado a la parrilla.", "🌮🐟", "order", "orden / ración", "ˈɔːrdər", "Pide una orden de tres tacos de pescado a la parrilla.", "Hey! Welcome to Taco Wheel. What are you hungry for?"),
            ("how-spicy-salsa", "How spicy is the green salsa? I prefer mild.", "¿Qué tan picante es la salsa verde? La prefiero suave.", "🌶️🥣", "mild", "poco picante / suave", "maɪld", "Pregunta qué tan picante es la salsa verde y di que prefieres suave.", "Three fish tacos coming up! Do you want red or green salsa?"),
            ("extra-lime-cilantro", "Could you put extra lime and cilantro on the side?", "¿Podría poner limón y cilantro extra aparte?", "🍋🌿", "on the side", "aparte / a un lado", "ɑːn ðə saɪd", "Pide limón y cilantro extra aparte.", "The green salsa is very mild, made with roasted tomatillos."),
            ("call-my-name", "Will you call my name when the food is ready?", "¿Llamará mi nombre cuando la comida esté lista?", "📣🌮", "ready", "lista", "ˈredi", "Pregunta si llamarán tu nombre cuando esté listo.", "Sure thing, extra lime and cilantro on the side!"),
            ("cold-horchata", "Add a large cold horchata to my order, please.", "Agregue una horchata fría grande a mi pedido, por favor.", "🥤🧊", "add", "agregar / añadir", "æd", "", ""),
            ("picnic-benches", "Are those picnic benches over there free to use?", "¿Esas bancas de picnic de allá son de uso libre?", "🪑🌳", "benches", "bancas", "ˈbentʃɪz", "", ""),
        ],
    ),
    (
        "food-and-drink", "A2", "pub-fish-and-chips", "Ordering lunch at a British pub", "Almorzar en un pub británico",
        "Ordena en la barra indicando el número de tu mesa, pide pescado con papas y vinagre de malta.",
        "bartender", "visitor", "A cozy traditional pub in London.",
        [
            ("order-at-the-bar", "Hi, we are sitting at table twelve. Do we order here at the bar?", "Hola, estamos en la mesa doce. ¿Pedimos aquí en la barra?", "🍺🪑", "at the bar", "en la barra", "æt ðə bɑːr", "Indica que están en la mesa doce y pregunta si se pide en la barra.", "Hello! Welcome to The Crown. How can I help you?"),
            ("traditional-fish-chips", "We'd like two portions of fish and chips with mushy peas.", "Quisiéramos dos porciones de pescado con papas y puré de guisantes.", "🐟🍟", "portions", "porciones / raciones", "ˈpɔːrʃənz", "Pide dos porciones de fish and chips.", "Yes, you order right here and we bring the food to table twelve!"),
            ("malt-vinegar-sauce", "Could you bring some malt vinegar and tartar sauce?", "¿Podría traernos vinagre de malta y salsa tártara?", "🍾🥣", "tartar sauce", "salsa tártara", "ˈtɑːrtər sɔːs", "Pide vinagre de malta y salsa tártara.", "Two fish and chips! Anything to drink with your meal?"),
            ("ginger-beer-ice", "Two glasses of ginger beer with ice and lemon, please.", "Dos vasos de cerveza de jengibre con hielo y limón, por favor.", "🥂🍋", "ginger beer", "refresco de jengibre", "ˈdʒɪndʒər bɪr", "Pide dos vasos de ginger beer con hielo y limón.", "Of course, I'll bring the condiments right over."),
            ("sunday-roast-special", "Do you also serve the traditional Sunday roast here?", "¿También sirven el asado tradicional de los domingos aquí?", "🥩🥕", "roast", "asado al horno", "roʊst", "", ""),
            ("close-the-tab", "We're ready to pay right now by contactless card.", "Estamos listos para pagar ahora mismo con tarjeta sin contacto.", "💳📲", "contactless", "sin contacto", "ˈkɑːntæktləs", "", ""),
        ],
    ),
    # B1 (4 new -> total 5 with b1-dietary-restrictions)
    (
        "food-and-drink", "B1", "wrong-dish-served", "Politely fixing a wrong order", "Corregir amablemente un pedido equivocado",
        "Explica con cortesía al mesero que te trajeron pasta con carne cuando habías pedido el risotto vegetariano.",
        "waiter", "diner", "A busy Italian restaurant during dinner.",
        [
            ("sorry-to-bother", "Excuse me, sorry to bother you, but I think there's a mix-up.", "Disculpe, lamento molestarle, pero creo que hay una confusión.", "🙋‍♂️🍝", "mix-up", "confusión / error", "ˈmɪks ʌp", "Explica amablemente que crees que hay una confusión con tu plato.", "Here is your pasta Bolognese! Enjoy your meal."),
            ("ordered-mushroom-risotto", "I actually ordered the wild mushroom risotto without meat.", "En realidad pedí el risotto de hongos silvestres sin carne.", "🍄🍚", "actually", "en realidad", "ˈæktʃuəli", "Aclara que habías pedido el risotto de hongos sin carne.", "Oh, I'm so sorry! What did you order?"),
            ("no-rush-at-all", "No worries at all, mistakes happen when it's this busy.", "No se preocupe en absoluto, los errores pasan cuando hay tanta gente.", "😊🙌", "mistakes happen", "los errores pasan", "mɪˈsteɪks ˈhæpən", "Tranquiliza al mesero y pregunta cuánto tardará el risotto.", "Let me take this back to the kitchen immediately!"),
            ("how-long-new-dish", "Will the risotto take long, or is there one ready?", "¿Tardará mucho el risotto, o tienen alguno listo?", "⏱️🍲", "take long", "tardar mucho", "teɪk lɔːŋ", "Acepta la ensalada de cortesía mientras esperas.", "The chef can have a fresh risotto out in six minutes, and I'll bring a free side salad."),
            ("keep-side-salad", "Thank you for offering the complimentary salad while I wait.", "Gracias por ofrecer la ensalada de cortesía mientras espero.", "🥗🙏", "complimentary", "de cortesía / gratuito", "ˌkɑːmplɪˈmentəri", "", ""),
            ("tastes-wonderful", "The risotto came out hot and tastes wonderful, thank you!", "¡El risotto salió caliente y sabe maravilloso, gracias!", "👨‍🍳🌟", "came out", "salió / quedó", "keɪm aʊt", "", ""),
        ],
    ),
    (
        "food-and-drink", "B1", "booking-birthday-table", "Reserving a birthday dinner table", "Reservar mesa para una cena de cumpleaños",
        "Llama a un restaurante para reservar mesa para ocho personas en la terraza y coordinar un pastel.",
        "restaurant host", "caller", "Calling a restaurant to plan a friend's birthday dinner.",
        [
            ("table-for-eight-patio", "Hi, I'd like to book a table for eight on the heated patio this Friday.", "Hola, quisiera reservar una mesa para ocho en la terraza climatizada este viernes.", "🎂🌿", "heated patio", "terraza climatizada", "ˈhiːtɪd ˈpætioʊ", "Pide reservar una mesa para ocho en la terraza este viernes.", "Bella Vista Restaurant, how can I help you?"),
            ("around-eight-pm", "Do you have availability around eight o'clock in the evening?", "¿Tienen disponibilidad alrededor de las ocho de la noche?", "🕗📅", "availability", "disponibilidad", "əˌveɪləˈbɪləti", "Pregunta si tienen disponibilidad a las 8:00 PM.", "Let me check our Friday book. What time were you thinking?"),
            ("bring-birthday-cake", "We're celebrating a birthday; is it okay if we bring our own cake?", "Celebramos un cumpleaños; ¿está bien si llevamos nuestro propio pastel?", "🎂🕯️", "celebrating", "celebrando", "ˈselɪbreɪtɪŋ", "Pregunta si pueden llevar su propio pastel de cumpleaños.", "We have a large round table on the patio at 8:15 PM!"),
            ("store-in-fridge", "Could your staff keep the cake in the fridge until dessert?", "¿Podría su personal guardar el pastel en el refrigerador hasta el postre?", "🧊🍰", "fridge", "refrigerador / nevera", "frɪdʒ", "Pide que guarden el pastel en el refrigerador hasta el postre.", "Yes, you're welcome to bring a cake! We don't charge a cutting fee."),
            ("one-vegetarian-guest", "Two of our guests are vegetarian, just so the kitchen knows.", "Dos de nuestros invitados son vegetarianos, para que la cocina lo sepa.", "🥗🌱", "just so", "solo para que", "dʒʌst soʊ", "", ""),
            ("confirm-by-text", "Great, please put the reservation under Sofia and send a text confirmation.", "Genial, ponga la reserva a nombre de Sofía y envíe confirmación por mensaje.", "📱✅", "confirmation", "confirmación", "ˌkɑːnfərˈmeɪʃən", "", ""),
        ],
    ),
    (
        "food-and-drink", "B1", "cooking-class-inquiry", "Joining a local cooking class", "Unirse a una clase de cocina local",
        "Pregunta al chef instructor cómo preparar pasta fresca, pide un delantal y anota las proporciones.",
        "chef instructor", "student", "A hands-on culinary studio in Florence.",
        [
            ("knead-the-dough", "How many minutes should we knead the pasta dough until it's smooth?", "¿Cuántos minutos debemos amasar la masa de pasta hasta que quede suave?", "👐🍝", "knead", "amasar", "niːd", "Pregunta cuántos minutos amasar la pasta hasta que quede suave.", "Welcome to our pasta workshop! Everyone has flour and eggs at their station."),
            ("pinch-of-salt", "Should I add a pinch of salt and olive oil right now?", "¿Debo agregar una pizca de sal y aceite de oliva ahora mismo?", "🧂🫒", "pinch", "pizca", "pɪntʃ", "Pregunta si agregas una pizca de sal y aceite ahora.", "Knead it firmly with the heel of your hand for about ten minutes."),
            ("let-it-rest", "Why is it important to let the dough rest under a towel?", "¿Por qué es importante dejar reposar la masa bajo un paño?", "⏳🧺", "rest", "reposar", "rest", "Pregunta por qué es importante dejar reposar la masa.", "Just a pinch of salt! Now wrap the dough ball in a clean towel."),
            ("email-the-recipe", "Will you email us the recipe card so we can practice at home?", "¿Nos enviará por correo la ficha de la receta para practicar en casa?", "📧📖", "recipe card", "ficha de receta", "ˈresəpi kɑːrd", "Pregunta si enviarán la receta por correo para practicar en casa.", "Resting relaxes the gluten so you can roll it super thin!"),
            ("apron-and-rolling-pin", "Could I borrow an apron and a wooden rolling pin?", "¿Me podría prestar un delantal y un rodillo de madera?", "👨‍🍳🪵", "apron", "delantal", "ˈeɪprən", "", ""),
            ("simmer-the-sauce", "Let the tomato basil sauce simmer on low heat for twenty minutes.", "Deja que la salsa de tomate y albahaca hierva a fuego lento veinte minutos.", "🍅🔥", "simmer", "hervir a fuego lento", "ˈsɪmər", "", ""),
        ],
    ),
    (
        "food-and-drink", "B1", "farmers-market-cheese", "Tasting artisanal cheeses", "Probar quesos artesanales en el mercado",
        "Pide probar un queso de cabra curado, pregunta cómo conservarlo en un viaje y compra una cuña.",
        "cheesemonger", "customer", "A bustling Saturday farmers' market stall.",
        [
            ("sample-aged-cheddar", "Could I try a small sample of the aged goat cheese?", "¿Podría probar una pequeña muestra del queso de cabra curado?", "🧀🔪", "aged", "curado / añejado", "eɪdʒd", "Pide probar una muestra del queso de cabra curado.", "Good morning! All our cheeses come from our family farm. Want to try one?"),
            ("nutty-and-creamy", "It has a wonderful nutty flavor and a really creamy texture.", "Tiene un maravilloso sabor a nuez y una textura muy cremosa.", "🥜✨", "nutty", "con notas de nuez", "ˈnʌti", "Comenta su sabor a nuez y textura cremosa.", "Here is a slice of our six-month aged goat cheese. What do you think?"),
            ("pair-with-figs", "What kind of jam or crackers goes best with this cheese?", "¿Qué tipo de mermelada o galletas combina mejor con este queso?", "🍯🥖", "goes best", "combina mejor", "ɡoʊz best", "Pregunta qué mermelada o galletas combinan mejor.", "Glad you like it! We age it in natural stone caves."),
            ("vacuum-seal-travel", "Could you vacuum-seal a half-pound wedge so I can pack it?", "¿Podría sellar al vacío una cuña de media libra para llevarla de viaje?", "📦✈️", "vacuum-seal", "sellar al vacío", "ˈvækjuːm siːl", "Pide sellar al vacío una cuña de media libra para tu viaje.", "Fig jam and walnut sourdough crackers pair with it beautifully."),
            ("unpasteurized-milk", "Is this made with raw milk or pasteurized sheep's milk?", "¿Está hecho con leche cruda o leche de oveja pasteurizada?", "🐑🥛", "pasteurized", "pasteurizada", "ˈpæstʃəraɪzd", "", ""),
            ("keep-at-room-temp", "Take it out of the fridge thirty minutes before serving.", "Sácalo del refrigerador treinta minutos antes de servir.", "🌡️🍽️", "serving", "servir", "ˈsɜːrvɪŋ", "", ""),
        ],
    ),
    # B2 (4 new -> total 5 with b2-hosting-business-lunch)
    (
        "food-and-drink", "B2", "catering-menu-planning", "Planning corporate event catering", "Planificar el catering de un evento",
        "Coordina con una empresa de banquetes estaciones de comida, opciones veganas y horarios de servicio.",
        "catering manager", "event organizer", "Planning the menu for a 60-person product launch.",
        [
            ("bite-sized-canapes", "We want passed bite-sized canapés so guests can mingle easily.", "Queremos canapés de un bocado servidos en bandeja para que los invitados conversen cómodamente.", "🍢🥂", "mingle", "socializar / mezclarse", "ˈmɪŋɡəl", "Explica que prefieren canapés de un bocado para facilitar el networking.", "Thanks for meeting today! For your 60 guests, do you prefer a sit-down buffet or cocktail style?"),
            ("clearly-labeled-allergens", "At least thirty percent of the platter options should be vegan and clearly labeled.", "Al menos el treinta por ciento de las bandejas deben ser veganas y estar claramente etiquetadas.", "🌱🏷️", "platter", "bandeja / fuente", "ˈplætər", "Pide que el 30% de las opciones sean veganas y estén etiquetadas.", "Passed canapés work great for product launches. Any dietary requirements?"),
            ("coffee-and-pastry-break", "Can you set up an espresso bar during the afternoon networking break?", "¿Pueden instalar una barra de espresso durante el receso de networking de la tarde?", "☕⚡", "set up", "instalar / montar", "set ʌp", "Pregunta si pueden montar una barra de espresso en el receso.", "We use color-coded cards showing gluten-free, vegan, and nut-free items."),
            ("final-headcount-deadline", "When is the final cutoff date to confirm our exact guest headcount?", "¿Cuál es la fecha límite para confirmar el número exacto de asistentes?", "📅👥", "headcount", "número de asistentes", "ˈhedkaʊnt", "Pregunta la fecha límite para confirmar el número final de invitados.", "Yes, our mobile barista cart is very popular. Let's talk logistics."),
            ("staffing-and-clean-up", "Does the quote include servers, glassware rental, and post-event cleanup?", "¿La cotización incluye meseros, alquiler de cristalería y limpieza final?", "🧾🥂", "glassware", "cristalería", "ˈɡlæswer", "", ""),
            ("tasting-session-friday", "Let's schedule a menu tasting this Friday before we sign the deposit.", "Agendemos una degustación de menú este viernes antes de firmar el anticipo.", "🍽️✍️", "tasting", "degustación", "ˈteɪstɪŋ", "", ""),
        ],
    ),
    (
        "food-and-drink", "B2", "specialty-coffee-roastery", "Discussing single-origin coffee", "Conversar sobre café de especialidad",
        "Conversa con un tostador sobre notas florales, molienda para filtro V60 y tueste ligero.",
        "head roaster", "coffee enthusiast", "A specialty micro-roastery tasting bar.",
        [
            ("washed-ethiopian-beans", "I'm drawn to light-roast Ethiopian beans with floral and bergamot notes.", "Me atraen los granos etíopes de tueste claro con notas florales y de bergamota.", "☕🌸", "light-roast", "tueste ligero / claro", "laɪt roʊst", "Di que te gustan los granos etíopes de tueste ligero con notas florales.", "Welcome to the roastery! What flavor profile do you usually brew at home?"),
            ("grind-for-pour-over", "Could you leave the bag whole-bean? I grind fresh for a V60 pour-over.", "¿Podría dejar la bolsa en grano entero? Muelo al momento para filtro V60.", "⚙️🫖", "whole-bean", "en grano entero", "hoʊl biːn", "Pide la bolsa en grano entero porque mueles en casa para V60.", "We just roasted a washed Yirgacheffe yesterday—it's super bright and floral."),
            ("water-temperature-ratio", "What water temperature and coffee-to-water ratio bring out the best sweetness?", "¿Qué temperatura de agua y proporción resaltan mejor el dulzor?", "🌡️⚖️", "bring out", "resaltar / sacar a relucir", "brɪŋ aʊt", "Pregunta qué temperatura y proporción resaltan mejor el dulzor.", "Smart move—whole bean keeps the aromatics intact much longer."),
            ("roast-date-degassing", "Since it was roasted yesterday, should I let it degas for a few days?", "Como se tostó ayer, ¿debería dejarlo desgasificar unos días?", "📦⏳", "degas", "desgasificar (reposar tras el tueste)", "diːˈɡæs", "Pregunta cuántos días dejarlo reposar tras el tueste.", "Aim for a 1-to-16 ratio at 93 degrees Celsius with a 40-second bloom."),
            ("natural-process-fruity", "How does the natural-process Colombian compare in body and acidity?", "¿Cómo se compara el colombiano de proceso natural en cuerpo y acidez?", "🍒☕", "body", "cuerpo / densidad en boca", "ˈbɑːdi", "", ""),
            ("monthly-bean-subscription", "I'd love to sign up for your monthly roaster's choice subscription.", "Me encantaría suscribirme a su selección mensual del tostador.", "📬☕", "sign up", "inscribirse / suscribirse", "saɪn ʌp", "", ""),
        ],
    ),
    (
        "food-and-drink", "B2", "supper-club-hosting", "Hosting a themed dinner party", "Ser anfitrión de una cena temática",
        "Presenta los platos a tus invitados en una cena mediterránea, ofrece maridaje y comparte la historia de la receta.",
        "guest (Elena)", "dinner host", "A warm candlelit dinner table at your apartment.",
        [
            ("make-yourselves-at-home", "Come on in, everyone! Hang up your coats and make yourselves at home.", "¡Pasen todos! Cuelguen sus abrigos y siéntanse como en su casa.", "🏠🥂", "make yourselves at home", "siéntanse como en casa", "meɪk jɔːrˈselvz æt hoʊm", "Recibe a tus invitados y diles que se sientan como en casa.", "Thank you for having us! Your apartment smells incredible—what's cooking?"),
            ("slow-braised-lamb", "Tonight's main dish is slow-braised lamb shoulder with pomegranate and mint.", "El plato principal de esta noche es paleta de cordero braseada lentamente con granada y menta.", "🍖🌿", "slow-braised", "braseado a fuego lento", "sloʊ breɪzd", "Explica que preparaste cordero braseado con granada y menta.", "We brought a bottle of Rioja! Tell us about tonight's menu."),
            ("family-recipe-twist", "It's my grandmother's recipe, though I added smoked paprika for extra warmth.", "Es la receta de mi abuela, aunque agregué pimentón ahumado para darle calidez.", "👵🌶️", "smoked paprika", "pimentón ahumado", "smoʊkt pəˈpriːkə", "Cuenta que es la receta de tu abuela con un toque de pimentón ahumado.", "The meat is so tender! Where did you learn to make this?"),
            ("help-yourselves-seconds", "Please help yourselves to seconds—there is plenty of saffron rice left.", "Por favor sírvanse una segunda porción; queda bastante arroz con azafrán.", "🍚🥄", "seconds", "segunda porción / repetir plato", "ˈsekəndz", "Anima a todos a servirse una segunda porción.", "That smoky note is delicious. May I have a little more rice?"),
            ("citrus-almond-tart", "For dessert, I baked a flourless orange and almond tart.", "De postre, horneé una tarta de naranja y almendras sin harina.", "🍊🥧", "flourless", "sin harina", "ˈflaʊərləs", "", ""),
            ("toast-to-good-friends", "Let's raise a glass to good friends and unforgettable evenings!", "¡Levantemos la copa por los buenos amigos y las noches inolvidables!", "🥂✨", "raise a glass", "brindar / alzar la copa", "reɪz ə ɡlæs", "", ""),
        ],
    ),
    (
        "food-and-drink", "B2", "restaurant-waitlist-negotiation", "Securing seats at a packed restaurant", "Conseguir mesa en un restaurante lleno",
        "Consulta el tiempo de espera en un restaurante sin reserva y pide cenar en la barra del chef.",
        "maître d'", "diner", "Friday night at a popular neighborhood restaurant.",
        [
            ("walk-in-for-two", "Good evening! We don't have a reservation, but any chance of squeezing in two?", "¡Buenas noches! No tenemos reserva, pero ¿habría posibilidad de acomodar a dos?", "🍽️🤞", "squeezing in", "hacer un hueco / acomodar", "ˈskwiːzɪŋ ɪn", "Pregunta si hay posibilidad de acomodar a dos personas sin reserva.", "Good evening! Welcome to Ember. Do you have a reservation tonight?"),
            ("full-menu-at-bar", "Do you serve the full dinner menu at the kitchen counter or bar seats?", "¿Sirven el menú completo de cena en la barra de la cocina o del bar?", "🍸📖", "counter", "barra / mostrador", "ˈkaʊntər", "Pregunta si sirven el menú completo en la barra de la cocina.", "Our dining tables are booked until 9:30, though two bar seats just opened up."),
            ("put-name-on-waitlist", "We'd love to take the bar seats—or put our name down if a booth opens.", "Nos encantaría tomar los asientos de la barra, o anotarnos por si se libera un reservado.", "📝🪑", "booth", "mesa tipo gabinete / reservado", "buːθ", "Acepta los asientos de la barra.", "Yes, the full menu is available at the chef's counter, and you get a view of the wood grill!"),
            ("grab-aperitif-first", "We'll grab an aperitif at the counter right now; thank you for fitting us in!", "Tomaremos un aperitivo en la barra ahora mismo; ¡gracias por hacernos espacio!", "🥂🔥", "fitting us in", "hacernos lugar", "ˈfɪtɪŋ ʌs ɪn", "Agradece que les hayan hecho lugar y pide la carta de bebidas.", "Fantastic! Follow me right here—here are your dinner and cocktail menus."),
            ("notify-by-sms", "If a patio table frees up early, could you ping my phone?", "Si se desocupa antes una mesa en la terraza, ¿podría avisarme al celular?", "📲🔔", "frees up", "se desocupa / libera", "friːz ʌp", "", ""),
            ("kitchen-last-call", "What time does the kitchen take last orders on Friday nights?", "¿A qué hora toma la cocina los últimos pedidos los viernes por la noche?", "🕙👨‍🍳", "last orders", "últimos pedidos", "læst ˈɔːrdərz", "", ""),
        ],
    ),
    # C1 (4 new -> total 5 with c1-wine-tasting-pairing)
    (
        "food-and-drink", "C1", "private-dining-contract", "Booking a private dining room", "Contratar un salón privado en restaurante",
        "Negocia el consumo mínimo, la tarifa de descorche y el menú impreso para una cena ejecutiva de veinte personas.",
        "private events director", "corporate host", "Reviewing terms for an executive dinner in a private dining room.",
        [
            ("minimum-food-spend", "Does the three-thousand-dollar minimum spend include service charges, or strictly food and beverage?", "¿El consumo mínimo de tres mil dólares incluye el cargo por servicio o estrictamente alimentos y bebidas?", "📑🍷", "minimum spend", "consumo mínimo", "ˈmɪnɪməm spend", "Pregunta si el consumo mínimo incluye el servicio o solo alimentos y bebidas.", "Our Glass Room seats twenty comfortably with a $3,000 minimum spend."),
            ("waive-corkage-fee", "If we order champagne through your cellar, would you waive corkage on two collector bottles?", "Si pedimos el champán de su cava, ¿eximirían el descorche de dos botellas de colección?", "🍾🤝", "corkage", "derecho de descorche", "ˈkɔːrkɪdʒ", "Propón que eximan el descorche de dos botellas si compran el champán allí.", "It applies strictly to food and beverage before the 18% gratuity."),
            ("three-choice-prix-fixe", "A three-course prix fixe with tableside entrée selection will keep service pacing brisk.", "Un menú de precio fijo de tres tiempos con elección de plato fuerte en mesa mantendrá un ritmo ágil.", "🍽️⏱️", "prix fixe", "menú de precio fijo", "priː fɪks", "Elige un menú fijo de tres tiempos con selección en mesa para agilizar el servicio.", "We can certainly waive corkage on two bottles. How would you like to structure the menu?"),
            ("custom-printed-menus", "Could you print bespoke menus featuring our company crest without listing individual prices?", "¿Podrían imprimir menús personalizados con nuestro logotipo sin mostrar precios individuales?", "🖨️🏛️", "bespoke", "hecho a medida / personalizado", "bɪˈspoʊk", "Solicita menús impresos con su logotipo y sin precios individuales.", "Agreed—our kitchen handles tableside choices for up to twenty-four guests effortlessly."),
            ("av-projector-screen", "We'll need a discreet screen for a ten-minute toast, then ambient lighting afterward.", "Necesitaremos una pantalla discreta para un brindis de diez minutos y luego iluminación ambiental.", "📽️🕯️", "discreet", "discreta", "dɪˈskriːt", "", ""),
            ("countersign-agreement", "Send over the revised BEO and I'll countersign it before close of business.", "Envíe la orden de evento revisada y la firmaré antes del cierre del día.", "✍️📄", "countersign", "refrendar / firmar contrato", "ˈkaʊntərsaɪn", "", ""),
        ],
    ),
    (
        "food-and-drink", "C1", "sustainable-seafood-sourcing", "Inquiring about sustainable seafood", "Consultar sobre pesca sostenible y trazabilidad",
        "Conversa con el chef de un restaurante costero sobre pesca de anzuelo, vedas y trazabilidad marina.",
        "seafood chef", "conscious diner", "An oceanfront seafood restaurant known for ethical sourcing.",
        [
            ("line-caught-wild", "Is the halibut line-caught in local waters or sourced from offshore trawlers?", "¿El fletán es pescado con anzuelo en aguas locales o proviene de arrastreros de altura?", "🎣🐟", "line-caught", "pescado con caña / anzuelo", "laɪn kɔːt", "Pregunta si el fletán es de pesca artesanal con anzuelo.", "Good evening! Tonight our featured catch is Pacific halibut and diver scallops."),
            ("bycatch-mitigation", "We try to support fisheries that actively minimize bycatch and seabed disruption.", "Intentamos apoyar pesquerías que minimizan activamente la captura incidental y el daño al fondo marino.", "🌊🐢", "bycatch", "captura incidental", "ˈbaɪkætʃ", "Explica que prefieren apoyar pesquerías que reducen la captura incidental.", "All our halibut is hook-and-line caught by day-boats out of Half Moon Bay."),
            ("hand-harvested-scallops", "Knowing the scallops are hand-harvested by divers makes the dish even more compelling.", "Saber que las vieiras son recolectadas a mano por buzos hace que el plato sea aún más atractivo.", "🤿🐚", "hand-harvested", "recolectadas a mano", "hænd ˈhɑːrvɪstɪd", "Celebra que las vieiras sean recolectadas a mano y pide ese plato.", "That's our core philosophy too—we never buy dredged shellfish."),
            ("traceability-qr-code", "I love that your menu lists the vessel name and landing port for full traceability.", "Me encanta que su menú indique el nombre de la embarcación y el puerto de desembarque para total trazabilidad.", "⚓📋", "traceability", "trazabilidad", "ˌtreɪsəˈbɪləti", "Elogia la trazabilidad del menú indicando la embarcación y el puerto.", "I'll fire an order of the diver scallops and halibut for your table right away!"),
            ("in-season-oysters", "Which of the cold-water oysters has the cleanest briny finish tonight?", "¿Cuál de las ostras de agua fría tiene el final salino más limpio esta noche?", "🦪🌊", "briny", "salino / sabor a mar", "ˈbraɪni", "", ""),
            ("underutilized-species", "Highlighting underutilized fish species takes real pressure off overfished stocks.", "Destacar especies poco conocidas alivia la presión sobre las poblaciones sobreexplotadas.", "🐟♻️", "underutilized", "poco aprovechadas", "ˌʌndərˈjuːtəlaɪzd", "", ""),
        ],
    ),
    (
        "food-and-drink", "C1", "artisanal-bakery-fermentation", "Discussing sourdough fermentation", "Conversar sobre masa madre y fermentación",
        "Habla con un maestro panadero sobre hidratación de harinas integrales, fermentación en frío y corteza.",
        "master baker", "bread baker", "An artisanal sourdough bakery counter after the morning bake.",
        [
            ("high-hydration-crumb", "How do you achieve such an open, custardy crumb at eighty-percent hydration?", "¿Cómo logran una miga tan alveolada y cremosa con un ochenta por ciento de hidratación?", "🍞🫧", "crumb", "miga del pan", "krʌm", "Pregunta cómo logran esa miga tan abierta con 80% de hidratación.", "Here is a warm country loaf just out of the deck oven. Look at that blistered crust!"),
            ("cold-retard-overnight", "Does a twenty-four-hour cold retard in the walk-in sharpen the lactic tang?", "¿Una fermentación en frío de veinticuatro horas acentúa la acidez láctica?", "❄️⏱️", "cold retard", "fermentación lenta en frío", "koʊld rɪˈtɑːrd", "Pregunta si la fermentación en frío de 24 horas acentúa el perfil láctico.", "We do four gentle coil folds and use stone-milled heritage wheat."),
            ("stone-milled-rye-starter", "Do you feed your levain with whole rye to boost enzymatic activity?", "¿Alimentan su masa madre con centeno integral para impulsar la actividad enzimática?", "🌾🫙", "levain", "masa madre activa / fermento", "ləˈvæn", "Pregunta si alimentan la masa madre con centeno integral.", "Exactly—cold proofing at four degrees develops complex sweetness without harsh sourness."),
            ("steam-injection-crust", "That caramelized, shattering crust clearly comes from heavy steam during the firstifteen minutes.", "Esa corteza caramelizada y crujiente claramente proviene del vapor intenso en los primeros minutos.", "🔥🥖", "shattering", "ultracrujiente / quebradiza", "ˈʃætərɪŋ", "Comenta el efecto del vapor en la corteza caramelizada y compra una hogaza.", "Yes, thirty percent dark rye keeps the starter vigorous year-round."),
            ("autolyse-before-salt", "Giving the flour a one-hour autolyse before adding salt makes extensibility effortless.", "Darle a la harina una autólisis de una hora antes de la sal facilita mucho la extensibilidad.", "🥣💧", "autolyse", "autólisis (reposo de agua y harina)", "ˈɔːtoʊlaɪz", "", ""),
            ("take-home-country-loaf", "I'll take a country boule and a jar of your dehydrated starter culture.", "Me llevaré una hogaza rústica y un frasco de su cultivo de masa madre.", "🛍️🍞", "boule", "hogaza redonda", "buːl", "", ""),
        ],
    ),
    (
        "food-and-drink", "C1", "mixology-bespoke-cocktail", "Ordering a bespoke craft cocktail", "Pedir un cóctel de autor a medida",
        "Pide a un mixólogo un cóctel equilibrado con mezcal ahumado, cítricos frescos y amargo aromático.",
        "head mixologist", "patron", "A speakeasy cocktail bar with no printed menu.",
        [
            ("smoky-yet-herbaceous", "I'm in the mood for something smoky yet herbaceous—perhaps built around artisanal mezcal.", "Me apetece algo ahumado pero herbal, tal vez elaborado a base de mezcal artesanal.", "🍸🌿", "in the mood for", "con ganas de / me apetece", "ɪn ðə muːd fɔːr", "Pide algo ahumado y herbal a base de mezcal artesanal.", "Welcome! We craft bespoke drinks to your palate. What spirit and flavors do you gravitate toward?"),
            ("not-cloyingly-sweet", "Could you keep it spirit-forward and dry rather than cloyingly sweet?", "¿Podría mantenerlo seco y con presencia de destilado en vez de empalagosamente dulce?", "🥃🍋", "cloyingly", "empalagosamente", "ˈklɔɪɪŋli", "Pide que sea seco y equilibrado, no empalagoso.", "I love working with mezcal. How do you feel about sweetness versus bitterness?"),
            ("chartreuse-and-bitters", "A rinse of green Chartreuse and grapefruit bitters sounds like a brilliant counterbalance.", "Un toque de Chartreuse verde y bíter de pomelo suena como un contrapeso brillante.", "🍊✨", "counterbalance", "contrapeso / equilibrio", "ˈkaʊntərbæləns", "Aprueba la combinación con Chartreuse verde y bíter de pomelo.", "I'm thinking Tobalá mezcal, dry vermouth, a touch of green Chartreuse, and grapefruit bitters."),
            ("served-up-large-rock", "Let's serve it over a single hand-carved ice sphere with expressed orange peel.", "Sirvámoslo sobre una esfera de hielo tallada con piel de naranja exprimida.", "🧊🍊", "expressed peel", "piel cítrica exprimida por sus aceites", "ɪkˈsprest piːl", "Elige que lo sirva en roca grande de hielo con piel de naranja.", "Would you prefer that served up in a coupe or over a large crystal rock?"),
            ("clarified-citrus-cordial", "Using clarified lime cordial gives it a silky mouthfeel without clouding the glass.", "Usar cordial de lima clarificado le da una textura sedosa sin enturbiar la copa.", "🥂🔬", "mouthfeel", "sensación en boca / textura", "ˈmaʊθfiːl", "", ""),
            ("compliments-on-balance", "The interplay of peat smoke and botanicals is spot-on; my compliments!", "El juego entre el humo y los botánicos es exacto; ¡mis felicitaciones!", "👏🍸", "spot-on", "exacto / en el clavo", "spɑːt ɑːn", "", ""),
        ],
    ),
    # C2 (4 new -> total 5 with c2-culinary-critique)
    (
        "food-and-drink", "C2", "michelin-kitchen-stage", "Debriefing a Michelin kitchen service", "Analizar el servicio en cocina Michelin",
        "Evalúa junto al chef ejecutivo la sincronización del pase, el punto de cocción del pichón y la reducción de mermas.",
        "chef de cuisine", "visiting culinary director", "Post-service debrief at the pass of a three-Michelin-star kitchen.",
        [
            ("cadence-at-the-pass", "The cadence at the pass during the eight-o'clock rush was remarkably composed.", "La cadencia en el pase durante la hora punta de las ocho fue notablemente serena.", "👨‍🍳⏱️", "cadence", "cadencia / ritmo", "ˈkeɪdəns", "Destaca la serenidad y el ritmo en el pase durante la hora punta.", "That was a 95-cover Saturday service. How did the workflow look from the pass?"),
            ("Maillard-caramelization", "Searing the squab on the plancha yielded an immaculate Maillard crust without gray banding.", "Sellar el pichón en la plancha logró una costra de Maillard inmaculada sin sobrecocción interior.", "🔥🍖", "yielded", "produjo / dio como resultado", "ˈjiːldɪd", "Elogia el sellado del pichón y su punto exacto de cocción.", "We redesigned the meat station layout last week. How did the squab plates come across?"),
            ("upcycling-vegetable-trimmings", "Lacto-fermenting the root trimmings into a glaze is a masterclass in zero-waste gastronomy.", "Lactofermentar los recortes de tubérculos para hacer un glaseado es una cátedra de cocina sin desperdicio.", "🥕♻️", "trimmings", "recortes / mermas de cocina", "ˈtrɪmɪŋz", "Resalta el aprovechamiento de mermas mediante lactofermentación.", "Our saucier has been turning all our root vegetable trimmings into the reduction glaze."),
            ("tighten-interval-courses", "If we shave ninety seconds off the palate cleanser, the transition to savory finals will feel effortless.", "Si acortamos noventa segundos el limpiador de paladar, la transición a los platos finales se sentirá fluida.", "🍧⚡", "shave off", "recortar / reducir sutilmente", "ʃeɪv ɔːf", "Sugiere acortar noventa segundos la pausa antes del plato fuerte final.", "Was there any bottleneck in the tasting progression that we should refine for tomorrow?"),
            ("emulsion-stability", "Mounting the jus withcultured whey butter kept the emulsion glossy right to the table.", "Montar el jugo con mantequilla de suero mantuvo la emulsión brillante hasta la mesa.", "🥄✨", "glossy", "brillante / satinada", "ˈɡlɔːsi", "", ""),
            ("brigade-morale", "Precision without shouting is what sets a world-class brigade apart.", "La precisión sin gritos es lo que distingue a una brigada de clase mundial.", "🤝🌟", "sets apart", "distingue / diferencia", "sets əˈpɑːrt", "", ""),
        ],
    ),
    (
        "food-and-drink", "C2", "olive-oil-terroir-panel", "Evaluating extra-virgin olive oil terroir", "Evaluar terroir en cata de aceite de oliva",
        "Participa como jurado en un panel sensorial analizando polifenoles, picor retronasal y cosecha temprana.",
        "panel chair", "sensory judge", "An international extra-virgin olive oil sensory evaluation panel.",
        [
            ("herbaceous-nose", "On the nose, this early-harvest Picual bursts with cut grass and green tomato leaf.", "En nariz, este Picual de cosecha temprana estalla con notas de hierba recién cortada y hoja de tomate.", "🫒🌿", "early-harvest", "cosecha temprana", "ˈɜːrli ˈhɑːrvɪst", "Describe los aromas de hierba cortada y hoja de tomate en nariz.", "Judge 3, please share your olfactory and retronasal notes on Sample B."),
            ("polyphenol-pungency", "The peppery pungency at the back of the throat attests to an exceptionally high polyphenol count.", "El picor pimienta al fondo de la garganta atestigua una concentración excepcionalmente alta de polifenoles.", "🌶️🔬", "pungency", "picor característico del aceite joven", "ˈpʌndʒənsi", "Señala que el picor en garganta demuestra un alto nivel de polifenoles.", "And how did the bitterness and pungency register on the palate?"),
            ("cold-extraction-integrity", "Milling within three hours of picking clearly prevented any trace of oxidative fustiness.", "Moler a las tres horas de la recolección evitó claramente cualquier rastro de defecto oxidativo.", "⚙️⏱️", "milling", "molienda / almazara", "ˈmɪlɪŋ", "Comenta que la molienda inmediata evitó cualquier defecto de oxidación.", "There's zero defect on the finish—remarkably clean extraction."),
            ("score-harmonious-complexity", "I'm scoring it nine point four for its harmonious balance between astringency and almond sweetness.", "Le otorgo nueve punto cuatro por su equilibrio armonioso entre astringencia y dulzor almendrado.", "🏆📋", "astringency", "astringencia", "əˈstrɪndʒənsi", "Otorga tu puntuación destacando su equilibrio entre astringencia y almendra.", "What is your final numerical score for the gold-medal shortlist?"),
            ("dry-farmed-groves", "Dry-farmed mountain groves concentrate volatile aromatics far more intensely than irrigated plains.", "Los olivares de montaña de secano concentran los compuestos aromáticos mucho más que las llanuras regadas.", "⛰️🌳", "dry-farmed", "cultivado en secano", "draɪ fɑːrmd", "", ""),
            ("unanimous-gold-commendation", "We have unanimous consensus to award this estate our highest distinction.", "Tenemos consenso unánime para otorgar a esta finca nuestra máxima distinción.", "🥇🤝", "unanimous", "unánime", "juːˈnænɪməs", "", ""),
        ],
    ),
    (
        "food-and-drink", "C2", "food-documentary-interview", "Interviewing a heritage seed keeper", "Entrevistar a un guardián de semillas nativas",
        "Conduce una entrevista documental sobre biodiversidad agrícola, maíces criollos y resiliencia climática.",
        "agronomist & seed keeper", "documentary host", "Filming in an Andean heritage grain sanctuary.",
        [
            ("genetic-biodiversity", "Preserving heirloom landraces is our strongest insurance policy against monoculture blight.", "Preservar las variedades criollas nativas es nuestra mejor póliza de seguro frente a las plagas del monocultivo.", "🌽🧬", "heirloom landraces", "variedades criollas / ancestrales", "ˈerluːm ˈlændreɪsɪz", "Reflexiona sobre cómo las variedades nativas protegen frente al monocultivo.", "Welcome to our seed bank. Here we safeguard over four hundred varieties of ancestral corn and quinoa."),
            ("culinary-memory", "When a seed variety vanishes, we lose not only genetics but centuries of culinary memory.", "Cuando desaparece una semilla, perdemos no solo genética sino siglos de memoria culinaria.", "🏺🌾", "vanishes", "desaparece / se extingue", "ˈvænɪʃɪz", "Destaca que al perder una semilla también se pierde memoria culinaria.", "Farmers in these valleys have selected each color for specific ceremonial dishes."),
            ("drought-tolerant-strains", "How are these high-altitude strains adapting to erratic rainfall patterns?", "¿Cómo se están adaptando estas variedades de gran altitud a los patrones erráticos de lluvia?", "⛰️🌧️", "erratic", "erráticos / impredecibles", "ɪˈrætɪk", "Pregunta cómo se adaptan estas semillas a las lluvias irregulares.", "Exactly—each kernel carries the story of the community that tended it."),
            ("chef-farmer-alliances", "Direct alliances between fine-dining chefs and smallholder farmers make conservation economically viable.", "Las alianzas directas entre chefs y pequeños agricultores hacen que la conservación sea económicamente viable.", "👨‍🍳🌾", "smallholder", "pequeño agricultor / minifundista", "ˈsmɔːlhoʊldər", "Concluye explicando cómo las alianzas con chefs hacen viable la conservación.", "Their deep root systems survive frost and drought far better than commercial hybrids."),
            ("nixtamalization-nutrition", "Traditional nixtamalization unlocks bioavailable niacin and gives the masa its unmistakable aroma.", "La nixtamalización tradicional libera niacina biodisponible y da a la masa su aroma inconfundible.", "🫓🔥", "unlocks", "libera / desbloquea", "ʌnˈlɑːks", "", ""),
            ("intergenerational-stewardship", "Passing this stewardship to young growers ensures the sanctuary thrives for generations.", "Transmitir esta custodia a jóvenes agricultores asegura que el santuario prospere por generaciones.", "🌱👐", "stewardship", "custodia / cuidado responsable", "ˈstuːərdʃɪp", "", ""),
        ],
    ),
    (
        "food-and-drink", "C2", "molecular-gastronomy-symposium", "Debating modernist vs. traditional cuisine", "Debatir gastronomía molecular frente a tradición",
        "Debate en un simposio gastronómico el uso de hidrocoloides y cocción al vacío frente al fuego de leña.",
        "traditionalist chef", "culinary panelist", "Main stage at an international gastronomy congress.",
        [
            ("technique-serves-flavor", "Modernist technique should illuminate the ingredient's essence, never become a parlor trick.", "La técnica modernista debe iluminar la esencia del ingrediente, nunca convertirse en un truco de salón.", "🔬🍽️", "parlor trick", "truco superficial / artificio", "ˈpɑːrlər trɪk", "Sostén que la técnica debe realzar el ingrediente y no ser puro espectáculo.", "Some critics argue that rotary evaporators and spherification strip cooking of its soul. Where do you stand?"),
            ("false-dichotomy", "Framing hearth cooking and precision sous-vide as mutually exclusive is a false dichotomy.", "Plantear el fuego de leña y la precisión del sous-vide como excluyentes es una falsa dicotomía.", "🔥⚖️", "false dichotomy", "falsa dicotomía", "fɔːls daɪˈkɑːtəmi", "Argumenta que oponer el fuego de leña al sous-vide es una falsa dicotomía.", "Fair point, yet nothing replicates the primal unpredictability of live wood fire."),
            ("distill-volatile-aromas", "Vacuum distillation captures fleeting blossom aromas that boiling would utterly destroy.", "La destilación al vacío captura aromas florales efímeros que el hervor destruiría por completo.", "🌸⚗️", "fleeting", "efímeros / fugaces", "ˈfliːtɪŋ", "Explica cómo la destilación al vacío preserva aromas florales efímeros.", "Where do laboratory tools genuinely surpass classic French reductions?"),
            ("tradition-was-once-innovation", "Every revered classic—from puff pastry to mayonnaise—was once a radical technical innovation.", "Todo clásico venerado —desde el hojaldre hasta la mayonesa— fue alguna vez una innovación técnica radical.", "🥐📜", "revered", "venerado / consagrado", "rɪˈvɪrd", "Cierra recordando que todo clásico fue alguna vez una innovación radical.", "I have to admit, cold-distilled elderflower essence is extraordinary."),
            ("sensory-resonance", "Ultimately, the diner judges a dish by its emotional and sensory resonance, not its equipment.", "En última instancia, el comensal juzga un plato por su resonancia sensorial y emocional, no por su equipo.", "❤️🥄", "resonance", "resonancia / impacto profundo", "ˈrezənəns", "", ""),
            ("mutual-enrichment", "When ancestral craft informs scientific curiosity, gastronomy moves forward.", "Cuando el oficio ancestral nutre la curiosidad científica, la gastronomía avanza.", "🤝✨", "informs", "nutre / guía con fundamento", "ɪnˈfɔːrmz", "", ""),
        ],
    ),
]

CELL_BLUEPRINTS.extend([
    # ==================== 2. TRAVEL-AND-TRANSPORT ====================
    # A1 (4 new)
    (
        "travel-and-transport", "A1", "taxi-to-airport", "Taking a taxi to the airport", "Tomar un taxi al aeropuerto",
        "Sube a un taxi, indica que vas a la terminal internacional y pregunta cuánto cuesta el viaje.",
        "taxi driver", "passenger", "Outside the city hotel with two suitcases.",
        [
            ("to-airport-terminal", "Hello! To the international airport, Terminal 2, please.", "¡Hola! Al aeropuerto internacional, Terminal 2, por favor.", "🚕✈️", "terminal", "terminal aérea", "ˈtɜːrmɪnəl", "Pide ir al aeropuerto internacional, Terminal 2.", "Good morning! Where can I take you today?"),
            ("put-bags-in-trunk", "Can we put these two suitcases in the trunk?", "¿Podemos poner estas dos maletas en el maletero?", "🧳🚗", "trunk", "maletero / cajuela", "trʌŋk", "Pregunta si pueden poner las dos maletas en el maletero.", "Terminal 2, sure! Do you have luggage with you?"),
            ("how-long-drive", "How many minutes is the drive to the airport?", "¿De cuántos minutos es el trayecto al aeropuerto?", "⏱️🛣️", "drive", "trayecto en auto", "draɪv", "Pregunta cuántos minutos toma llegar al aeropuerto.", "All loaded! Hop in and buckle your seatbelt."),
            ("pay-by-card-taxi", "Here we are! Can I pay with my card?", "¡Aquí estamos! ¿Puedo pagar con mi tarjeta?", "💳🚕", "here we are", "aquí estamos / llegamos", "hɪr wiː ɑːr", "Pregunta si puedes pagar con tarjeta al llegar.", "It takes about twenty-five minutes this morning. Here is Terminal 2!"),
            ("need-a-receipt-taxi", "Could I have a printed receipt, please?", "¿Me podría dar un recibo impreso, por favor?", "🧾🙌", "printed", "impreso", "ˈprɪntɪd", "", ""),
            ("thank-you-safe-drive", "Thank you for the safe ride! Have a good day.", "¡Gracias por el viaje seguro! Que tenga un buen día.", "😊👋", "ride", "viaje / traslado", "raɪd", "", ""),
        ],
    ),
    (
        "travel-and-transport", "A1", "subway-metro-card", "Buying a metro card", "Comprar una tarjeta de metro",
        "Compra una tarjeta de metro para todo el día y pregunta hacia dónde va la línea azul.",
        "station clerk", "traveler", "Underground metro station ticket window.",
        [
            ("one-day-metro-pass", "Can I buy a one-day metro pass, please?", "¿Puedo comprar un pase de metro por un día, por favor?", "🚇🎫", "pass", "pase / abono", "pæs", "Pide comprar un pase de metro por un día.", "Hello! Welcome to the city metro. How can I help you?"),
            ("blue-line-downtown", "Does the blue line go to the city center?", "¿La línea azul va al centro de la ciudad?", "🔵🏙️", "city center", "centro de la ciudad", "ˈsɪti ˈsentər", "Pregunta si la línea azul va al centro.", "Here is your one-day pass for eight dollars."),
            ("how-many-stops", "How many stops is it to Central Museum?", "¿Cuántas estaciones son hasta el Museo Central?", "🏛️🔢", "stops", "paradas / estaciones", "stɑːps", "Pregunta cuántas paradas son hasta el Museo Central.", "Yes, take the blue line northbound on platform 1."),
            ("tap-card-at-gate", "Do I tap the card on the yellow gate?", "¿Debo pasar la tarjeta por el lector amarillo?", "📲🚧", "tap", "acercar / tocar con la tarjeta", "tæp", "Pregunta si pasas la tarjeta por el lector amarillo.", "It is only four stops from here—about ten minutes."),
            ("free-metro-map", "May I take one of these pocket metro maps?", "¿Puedo llevarme uno de estos mapas de bolsillo del metro?", "🗺️🚇", "pocket", "de bolsillo", "ˈpɑːkɪt", "", ""),
            ("trains-every-five-min", "Great! The train is coming now, thank you.", "¡Genial! El tren ya viene, gracias.", "🚆👍", "coming", "viniendo / llegando", "ˈkʌmɪŋ", "", ""),
        ],
    ),
    (
        "travel-and-transport", "A1", "train-platform-check", "Checking the train platform", "Preguntar el andén del tren",
        "Pregunta a un empleado de la estación de qué andén sale el tren a Oxford y en qué vagón subir.",
        "station guard", "passenger", "Main departure board at Paddington Station.",
        [
            ("which-platform-oxford", "Excuse me, which platform is the train to Oxford?", "Disculpe, ¿en qué andén está el tren a Oxford?", "🚆🪧", "platform", "andén / plataforma", "ˈplætfɔːrm", "Pregunta de qué andén sale el tren a Oxford.", "Good morning! Looking for your train?"),
            ("leaves-at-nine", "Is this the fast train that leaves at nine o'clock?", "¿Es este el tren rápido que sale a las nueve en punto?", "🕘⚡", "leaves", "sale / parte", "liːvz", "Pregunta si es el tren rápido de las nueve.", "The Oxford train is boarding on Platform 4 right now."),
            ("where-is-coach-b", "My seat is in Coach B. Is it at the front?", "Mi asiento está en el vagón B. ¿Está adelante?", "🎫🚃", "coach", "vagón de pasajeros", "koʊtʃ", "Pregunta si el vagón B está en la parte delantera.", "Yes, the 9:00 AM express! It only stops once."),
            ("show-ticket-on-phone", "Here is my ticket QR code on my phone.", "Aquí está el código QR de mi boleto en mi teléfono.", "📱🎫", "code", "código", "koʊd", "Muestra el boleto en tu teléfono y agradece.", "Coach B is right in the middle of the train, by the green sign."),
            ("quiet-car-rules", "Is there a cafe car on this train?", "¿Hay un vagón cafetería en este tren?", "☕🚆", "cafe car", "vagón cafetería", "kæˈfeɪ kɑːr", "", ""),
            ("have-a-good-trip", "Thank you very much for your help!", "¡Muchas gracias por su ayuda!", "🙏😊", "help", "ayuda", "help", "", ""),
        ],
    ),
    (
        "travel-and-transport", "A1", "ferry-boat-ticket", "Buying harbor ferry tickets", "Comprar boletos de ferry",
        "Compra dos boletos para el barco del puerto, pregunta si puedes sentarte afuera y a qué hora regresa.",
        "ticket agent", "tourist", "Harbor pier ticket booth on a sunny day.",
        [
            ("two-ferry-tickets", "Two adult tickets for the island ferry, please.", "Dos boletos de adulto para el ferry a la isla, por favor.", "⛴️🎟️", "island", "isla", "ˈaɪlənd", "Pide dos boletos de adulto para el ferry a la isla.", "Welcome to the harbor pier! Where are you sailing today?"),
            ("sit-on-top-deck", "Can we sit outside on the top deck?", "¿Podemos sentarnos afuera en la cubierta superior?", "☀️🌊", "top deck", "cubierta superior", "tɑːp dek", "Pregunta si pueden sentarse afuera en la cubierta superior.", "Two adult tickets! The boat boards at Gate B in ten minutes."),
            ("last-boat-back", "What time is the last boat back to the city?", "¿A qué hora sale el último barco de regreso a la ciudad?", "🌇⛴️", "last", "último", "læst", "Pregunta a qué hora sale el último barco de regreso.", "Yes, the upper deck has open seats and great views of the bridge."),
            ("how-long-crossing", "Is the boat ride thirty minutes long?", "¿El paseo en barco dura treinta minutos?", "⏱️⚓", "boat ride", "viaje en barco", "boʊt raɪd", "Pregunta si el viaje dura treinta minutos.", "The last ferry back from the island leaves at 7:00 PM."),
            ("life-jackets-under-seat", "Where do we wait for boarding?", "¿Dónde esperamos para abordar?", "🚶‍♂️🪧", "wait", "esperar", "weɪt", "", ""),
            ("enjoy-the-breeze", "Thank you! It is a great day for the water.", "¡Gracias! Es un gran día para navegar.", "🌊😊", "water", "agua / mar", "ˈwɔːtər", "", ""),
        ],
    ),
    # A2 (4 new)
    (
        "travel-and-transport", "A2", "airport-baggage-claim", "Finding luggage at baggage claim", "Buscar equipaje en la banda",
        "Pregunta en el área de llegadas en qué carrusel salen las maletas de tu vuelo y dónde están los carritos.",
        "airport staff", "arriving passenger", "International arrivals baggage claim hall.",
        [
            ("which-carousel-madrid", "Excuse me, which baggage carousel is for the flight from Madrid?", "Disculpe, ¿qué banda de equipaje es para el vuelo de Madrid?", "🧳✈️", "carousel", "banda / carrusel de maletas", "ˌkærəˈsel", "Pregunta qué banda de equipaje corresponde al vuelo de Madrid.", "Welcome! Do you need help finding your flight's bags?"),
            ("luggage-carts-free", "Where can I get a luggage cart for our heavy bags?", "¿Dónde puedo conseguir un carrito para nuestras maletas pesadas?", "🛒🧳", "luggage cart", "carrito de equipaje", "ˈlʌɡɪdʒ kɑːrt", "Pregunta dónde conseguir un carrito para maletas.", "Flight IB-302 from Madrid is unloading on Carousel 6."),
            ("oversized-ski-bag", "We also checked a large stroller; does it come out here?", "También documentamos una carriola grande; ¿sale por aquí?", "👶🛷", "checked", "documentamos / facturamos", "tʃekt", "Pregunta por dónde sale el equipaje grande como la carriola.", "The luggage carts are right by the glass doors, and they are free!"),
            ("exit-toward-trains", "After we pick up our bags, which way is the airport train?", "Después de recoger las maletas, ¿hacia dónde está el tren del aeropuerto?", "🚆➡️", "pick up", "recoger", "pɪk ʌp", "Pregunta hacia dónde está el tren del aeropuerto al salir.", "Oversized items come out at Door B, right next to Carousel 6."),
            ("nothing-to-declare", "We only have personal clothes, so we take the green exit.", "Solo traemos ropa personal, así que salimos por el carril verde.", "🟢🛂", "personal", "personal", "ˈpɜːrsənəl", "", ""),
            ("thanks-for-directions", "Thank you, I can see our blue suitcase coming out now!", "¡Gracias, ya veo salir nuestra maleta azul!", "🧳🙌", "suitcase", "maleta", "ˈsuːtkeɪs", "", ""),
        ],
    ),
    (
        "travel-and-transport", "A2", "bike-rental-park", "Renting city bikes for the afternoon", "Alquilar bicicletas para el parque",
        "Alquila dos bicicletas con casco y candado, pregunta por la ciclovía junto al río y la hora de devolución.",
        "bike shop clerk", "visitor", "A bike rental stand at the entrance to Central Park.",
        [
            ("rent-two-bikes", "Hi! We'd like to rent two city bikes for three hours.", "¡Hola! Quisiéramos alquilar dos bicicletas urbanas por tres horas.", "🚲🌳", "rent", "alquilar", "rent", "Pide alquilar dos bicicletas por tres horas.", "Good afternoon! Beautiful day for a ride. How can I help you?"),
            ("helmets-and-locks", "Do the rentals come with helmets and a strong bike lock?", "¿El alquiler incluye cascos y un candado resistente?", "🪖🔒", "helmets", "cascos", "ˈhelmɪts", "Pregunta si incluyen cascos y candado.", "Two city bikes for three hours! Let me adjust the seat height for you."),
            ("river-bike-path", "Is there a safe bike path that goes along the river?", "¿Hay una ciclovía segura que vaya junto al río?", "🌊🚴", "bike path", "ciclovía / carril bici", "baɪk pæθ", "Pregunta si hay una ciclovía segura junto al río.", "Yes, helmets, locks, and a front basket are all included at no extra cost."),
            ("return-by-six-pm", "If we return them before six o'clock, do we get our ID back here?", "Si las devolvemos antes de las seis, ¿recogemos nuestra identificación aquí?", "🕕🪪", "return", "devolver", "rɪˈtɜːrn", "Confirma que las devolverán antes de las seis en este mismo puesto.", "Yes! Follow the green lane west and it goes straight along the waterfront."),
            ("check-tire-brakes", "Both brakes feel good and the tires have plenty of air.", "Ambos frenos se sienten bien y las llantas tienen buen aire.", "🛞👌", "brakes", "frenos", "breɪks", "", ""),
            ("park-at-designated-racks", "We will lock them at the metal bike racks when we stop for coffee.", "Las aseguraremos en los aparcabicis metálicos cuando paremos por café.", "☕🚲", "racks", "soportes / aparcabicis", "ræks", "", ""),
        ],
    ),
    (
        "travel-and-transport", "A2", "uber-pickup-spot", "Confirming a rideshare pickup spot", "Confirmar punto de recogida con el conductor",
        "Llama a tu conductor de aplicación para explicarle exactamente en qué esquina estás esperando.",
        "rideshare driver", "passenger", "Standing outside a busy theater after a show.",
        [
            ("waiting-by-pharmacy", "Hi! I'm your passenger. I'm standing in front of the green pharmacy.", "¡Hola! Soy tu pasajero. Estoy parado frente a la farmacia verde.", "📱🚕", "in front of", "frente a / delante de", "ɪn frʌnt əv", "Explica que estás frente a la farmacia verde.", "Hello! I'm two blocks away on Main Street, but the theater entrance is blocked."),
            ("cross-to-north-corner", "Should I cross the street to the north corner by the cafe?", "¿Debo cruzar la calle hacia la esquina norte junto a la cafetería?", "🚶‍♂️☕", "cross", "cruzar", "krɔːs", "Pregunta si debes cruzar hacia la esquina norte junto a la cafetería.", "I see the pharmacy, but police aren't letting cars stop on that side."),
            ("wearing-yellow-coat", "I'm wearing a bright yellow jacket and holding a blue umbrella.", "Llevo puesta una chaqueta amarilla brillante y un paraguas azul.", "🧥☂️", "wearing", "llevando puesto / vistiendo", "ˈwerɪŋ", "Describe que llevas chaqueta amarilla y paraguas azul.", "Yes! Cross to the cafe corner—I can pull over right there."),
            ("see-your-silver-car", "I see your silver Toyota with the hazard lights on now!", "¡Ya veo tu Toyota plateado con las luces intermitentes encendidas!", "🚗✨", "hazard lights", "luces preventivas / intermitentes", "ˈhæzərd laɪts", "Di que ya ves su auto plateado con las intermitentes.", "I'm pulling up to the curb in a silver Camry right now!"),
            ("check-license-plate", "Just checking your license plate—is this ride for Alex?", "Solo verificando la placa: ¿este viaje es para Alex?", "🔢✅", "license plate", "placa / matrícula", "ˈlaɪsəns pleɪt", "", ""),
            ("take-the-highway", "Thanks for finding us! Is the highway faster tonight?", "¡Gracias por encontrarnos! ¿La autopista es más rápida esta noche?", "🛣️🌙", "highway", "autopista", "ˈhaɪweɪ", "", ""),
        ],
    ),
    (
        "travel-and-transport", "A2", "train-seat-reservation", "Finding your reserved train seat", "Encontrar tu asiento reservado en el tren",
        "Verifica el número de tu asiento junto a la ventana y pide permiso para guardar tu mochila arriba.",
        "fellow passenger", "traveler", "Boarding a high-speed intercity train.",
        [
            ("seat-twelve-window", "Excuse me, I think my ticket is for seat 12A by the window.", "Disculpe, creo que mi boleto es para el asiento 12A junto a la ventana.", "🚆🪟", "by the window", "junto a la ventana", "baɪ ðə ˈwɪndoʊ", "Indica amablemente que tu boleto es el asiento 12A junto a la ventana.", "Oh, hello! Are you sitting in this row?"),
            ("check-coach-number", "Let me check—yes, this is Coach 4 and I have 12A.", "Déjeme revisar: sí, este es el vagón 4 y tengo el 12A.", "🎫🔍", "let me check", "déjeme revisar", "let miː tʃek", "Confirma que es el vagón 4 y tienes el asiento 12A.", "Oops, my ticket is actually for 12B on the aisle! Let me stand up for you."),
            ("overhead-luggage-rack", "Do you mind if I put my backpack on the overhead rack?", "¿Le importa si pongo mi mochila en el portaequipajes superior?", "🎒⬆️", "do you mind", "¿le importa / molesta?", "duː juː maɪnd", "Pregunta si puedes colocar tu mochila en el compartimento superior.", "Here you go, the window seat is all yours!"),
            ("power-outlet-under-seat", "Is there a power outlet under the seat to charge my phone?", "¿Hay un enchufe debajo del asiento para cargar mi teléfono?", "🔌📱", "power outlet", "toma de corriente / enchufe", "ˈpaʊər ˈaʊtlet", "Pregunta si hay un enchufe bajo el asiento para cargar tu teléfono.", "Not at all, go right ahead! There is plenty of room up there."),
            ("free-train-wifi", "Does this train have free Wi-Fi during the trip?", "¿Este tren tiene wifi gratuito durante el viaje?", "📶🚄", "during", "durante", "ˈdʊrɪŋ", "", ""),
            ("wake-me-at-station", "I'm getting off at York; have a pleasant journey!", "Me bajo en York; ¡que tenga un buen viaje!", "👋😊", "getting off", "bajarse (de tren/autobús)", "ˈɡetɪŋ ɔːf", "", ""),
        ],
    ),
    # B1 (4 new)
    (
        "travel-and-transport", "B1", "lost-suitcase-report", "Reporting a delayed suitcase", "Reportar una maleta demorada",
        "Reporta en el mostrador de equipaje que tu maleta no salió en la banda y deja la dirección de tu hotel.",
        "baggage service agent", "passenger", "Airline baggage service office in the arrivals hall.",
        [
            ("bag-didnt-arrive", "Hi, my flight from Chicago just landed, but my checked bag didn't come out.", "Hola, mi vuelo de Chicago acaba de aterrizar, pero mi maleta documentada no salió.", "🧳❓", "landed", "aterrizó", "ˈlændɪd", "Explica que tu vuelo de Chicago aterrizó pero tu maleta no salió.", "Hello! Welcome to Baggage Services. How can I assist you today?"),
            ("baggage-claim-tag", "Here is the baggage claim sticker attached to my boarding pass.", "Aquí está la etiqueta de reclamo de equipaje pegada en mi pase de abordar.", "🏷️🎫", "sticker", "etiqueta adhesiva / talón", "ˈstɪkər", "Entrega la etiqueta de equipaje pegada en tu pase de abordar.", "I'm sorry about that. May I see your baggage tag number so I can trace it?"),
            ("hard-shell-navy-bag", "It's a medium navy-blue hard-shell suitcase with a red ribbon on the handle.", "Es una maleta rígida mediana azul marino con una cinta roja en el asa.", "🧳🎀", "hard-shell", "de carcasa rígida", "hɑːrd ʃel", "Describe tu maleta azul marino rígida con cinta roja.", "Good news: the scanner shows it's coming on the next flight in three hours. Can you describe the bag?"),
            ("deliver-to-hotel-desk", "Could the courier deliver it directly to the Grand Hotel front desk tonight?", "¿Podría el mensajero entregarla directamente en la recepción del Grand Hotel esta noche?", "🚐🏨", "courier", "servicio de mensajería", "ˈkʊriər", "Pide que la entreguen directamente en la recepción de tu hotel esta noche.", "Thank you. You don't need to wait at the airport—we can deliver it to you."),
            ("overnight-toiletry-kit", "Do you provide an overnight toiletry kit while we wait for the bag?", "¿Proporcionan un kit de aseo nocturno mientras esperamos la maleta?", "🪥🧴", "toiletry kit", "neceser / kit de aseo", "ˈtɔɪlətri kɪt", "", ""),
            ("tracking-reference-code", "I'll save this tracking number so I can check the delivery status online.", "Guardaré este número de rastreo para revisar el estado de entrega en línea.", "📲🔢", "tracking", "seguimiento / rastreo", "ˈtrækɪŋ", "", ""),
        ],
    ),
    (
        "travel-and-transport", "B1", "missed-train-connection", "Revalidating a missed train connection", "Validar boleto tras perder conexión de tren",
        "Explica al inspector que tu primer tren llegó con retraso y necesitas subir al siguiente tren sin recargo.",
        "train conductor", "traveler", "On the platform at a transfer railway station.",
        [
            ("first-train-was-delayed", "Excuse me, our incoming regional train was delayed by twenty minutes, so we missed our connection.", "Disculpe, nuestro tren regional llegó con veinte minutos de retraso, así que perdimos la conexión.", "🚆⏱️", "incoming", "entrante / de llegada", "ˈɪnkʌmɪŋ", "Explica que su primer tren se retrasó veinte minutos y perdieron la conexión.", "Tickets, please! Keep in mind this 11:15 express requires a seat reservation."),
            ("stamp-ticket-for-next", "Can you endorse our tickets so we can board this 11:15 train without a penalty?", "¿Puede sellar nuestros boletos para abordar este tren de las 11:15 sin penalización?", "🎫🖋️", "without a penalty", "sin multa / sin recargo", "wɪˈðaʊt ə ˈpenəlti", "Pregunta si puede validar sus boletos para subir a este tren sin multa.", "Let me check the delay log—yes, the regional service from Bath arrived eighteen minutes late."),
            ("sit-in-unreserved-coach", "Since our original seat reservations are gone, which coach has unreserved seating?", "Como perdimos nuestros asientos originales, ¿qué vagón tiene asientos sin reserva?", "💺🚃", "unreserved", "sin reserva / libre", "ˌʌnrɪˈzɜːrvd", "Pregunta qué vagón tiene asientos libres sin reserva.", "I've stamped your tickets as valid for this service—no extra charge."),
            ("change-again-at-reading", "Do we stay on this train all the way, or do we need to transfer again?", "¿Nos quedamos en este tren todo el trayecto o debemos hacer transbordo otra vez?", "🔄🗺️", "all the way", "todo el camino / directo", "ɔːl ðə weɪ", "Pregunta si este tren va directo o requiere otro transbordo.", "Coaches E and F at the rear of the train are completely unreserved."),
            ("delay-repay-compensation", "Can we claim a partial refund online under the Delay Repay guarantee?", "¿Podemos solicitar un reembolso parcial en línea por la garantía de retraso?", "💻💷", "partial refund", "reembolso parcial", "ˈpɑːrʃəl ˈriːfʌnd", "", ""),
            ("hop-on-before-whistle", "Thank you so much! We'll board Coach E right now.", "¡Muchísimas gracias! Subiremos al vagón E ahora mismo.", "🙌🚆", "board", "abordar / subir", "bɔːrd", "", ""),
        ],
    ),
    (
        "travel-and-transport", "B1", "international-sim-card", "Buying an eSIM data plan at arrivals", "Comprar un plan de datos eSIM al aterrizar",
        "Compra una eSIM de datos para dos semanas, pide ayuda para escanear el código QR y activar el roaming.",
        "telecom kiosk agent", "traveler", "Mobile SIM kiosk in the airport arrivals terminal.",
        [
            ("two-week-esim-plan", "Hi, I'm staying for two weeks and need an eSIM with plenty of mobile data.", "Hola, me quedo dos semanas y necesito una eSIM con suficientes datos móviles.", "📱🌐", "plenty of", "suficientes / abundantes", "ˈplenti əv", "Explica que estarás dos semanas y necesitas una eSIM con bastantes datos.", "Welcome! Looking for a local SIM card or an instant eSIM for your trip?"),
            ("hotspot-tethering-allowed", "Does the twenty-gigabyte plan allow hotspot tethering to my laptop?", "¿El plan de veinte gigabytes permite compartir internet con mi laptop?", "💻📶", "tethering", "compartir internet (hotspot)", "ˈteðərɪŋ", "Pregunta si el plan de 20 GB permite compartir internet a tu laptop.", "Our 20-gigabyte tourist eSIM is twenty-five dollars and lasts thirty days."),
            ("scan-qr-to-install", "Could you help me scan the activation QR code in my phone settings?", "¿Podría ayudarme a escanear el código QR de activación en los ajustes de mi teléfono?", "📷⚙️", "settings", "ajustes / configuración", "ˈsetɪŋz", "Pide ayuda para escanear el código QR de activación en tus ajustes.", "Yes, personal hotspot is completely unrestricted on that plan!"),
            ("keep-whatsapp-number", "Will my regular WhatsApp number keep working while I use this data line?", "¿Mi número habitual de WhatsApp seguirá funcionando mientras use esta línea de datos?", "💬✅", "keep working", "seguir funcionando", "kiːp ˈwɜːrkɪŋ", "Pregunta si tu número de WhatsApp seguirá funcionando normalmente.", "All installed! You already have full 5G signal bars at the top."),
            ("coverage-in-mountains", "How is the network coverage if we drive up to the national park?", "¿Qué tal es la cobertura de red si conducimos hacia el parque nacional?", "⛰️📡", "coverage", "cobertura de señal", "ˈkʌvərɪdʒ", "", ""),
            ("turn-off-home-roaming", "I'll switch data roaming off on my home SIM to avoid extra charges.", "Desactivaré el roaming de datos en mi SIM principal para evitar cobros extra.", "🚫💸", "avoid", "evitar", "əˈvɔɪd", "", ""),
        ],
    ),
    (
        "travel-and-transport", "B1", "highway-toll-pass", "Using electronic highway tolls", "Consultar cómo funciona el telepeaje",
        "Pregunta en la agencia de autos cómo funciona el telepeaje electrónico y dónde estacionar en el centro.",
        "rental counter agent", "driver", "Picking up car keys at a regional rental counter.",
        [
            ("electronic-toll-lanes", "Do the highways around here use cash booths or electronic toll transponders?", "¿Las autopistas de esta zona usan casetas de efectivo o telepeaje electrónico?", "🛣️📡", "transponders", "dispositivos de telepeaje", "trænˈspɑːndərz", "Pregunta si las autopistas usan casetas de efectivo o telepeaje electrónico.", "Here are the keys to your crossover SUV. Are you driving up the coast today?"),
            ("activate-windshield-box", "Do I need to slide the little box on the windshield open to activate it?", "¿Necesito deslizar la cajita del parabrisas para activarla?", "🚗🪟", "windshield", "parabrisas", "ˈwɪndʃiːld", "Pregunta cómo activar la cajita del parabrisas.", "All bridges and expressways are cashless now, using the E-ZPass on your windshield."),
            ("billed-to-card-later", "Are the toll fees billed automatically to the card on file after we return?", "¿Los peajes se cobran automáticamente a la tarjeta registrada después de devolver el auto?", "💳🧾", "card on file", "tarjeta registrada", "kɑːrd ɑːn faɪl", "Pregunta si los peajes se cargan automáticamente a la tarjeta registrada.", "Yes, just slide the grey switch to the left and drive through the express lanes."),
            ("unleaded-regular-fuel", "Just to be sure, does this car take regular unleaded gasoline?", "Solo para estar seguro, ¿este auto usa gasolina regular sin plomo?", "⛽🚗", "unleaded", "sin plomo (gasolina)", "ˌʌnˈledɪd", "Confirma que el auto usa gasolina regular sin plomo.", "Exactly—you'll receive an itemized toll summary by email forty-eight hours after return."),
            ("congestion-zone-downtown", "Is there a downtown congestion charge we should register for online?", "¿Hay algún cargo por congestión en el centro en el que debamos registrarnos?", "🏙️⚠️", "congestion", "congestión vehicular", "kənˈdʒestʃən", "", ""),
            ("emergency-roadside-number", "Good to know the 24-hour roadside assistance number is on the key tag.", "Es bueno saber que el número de asistencia vial 24 horas está en el llavero.", "🔑📞", "roadside assistance", "asistencia en carretera", "ˈroʊdsaɪd əˈsɪstəns", "", ""),
        ],
    ),
    # B2 (4 new)
    (
        "travel-and-transport", "B2", "overbooked-flight-volunteer", "Volunteering on an overbooked flight", "Negociar compensación en vuelo sobrevendido",
        "Ofrece tu asiento en un vuelo sobrevendido a cambio de ascenso a clase ejecutiva, hotel y bono.",
        "gate agent", "flexible traveler", "Departure gate announcement calling for volunteers.",
        [
            ("flexible-if-compensated", "Hi, I heard you're oversold—my schedule is flexible if the compensation package makes sense.", "Hola, escuché que el vuelo está sobrevendido; mi horario es flexible si el paquete de compensación vale la pena.", "🛫💼", "oversold", "sobrevendido", "ˌoʊvərˈsoʊld", "Indica que tu horario es flexible si la compensación es atractiva.", "Attention passengers: we are looking for two volunteers to take the morning flight."),
            ("confirmed-seat-tomorrow", "Can you guarantee a confirmed seat on the 8:00 AM flight tomorrow rather than standby?", "¿Puede garantizar un asiento confirmado en el vuelo de las 8:00 AM mañana en lugar de lista de espera?", "✅💺", "standby", "en lista de espera / sujeto a espacio", "ˈstændbaɪ", "Pide asiento confirmado en el vuelo de las 8:00 AM y no en lista de espera.", "Thank you for coming up! We're offering a $600 travel credit for volunteers."),
            ("upgrade-and-hotel-voucher", "If you can include a business-class upgrade plus the airport hotel and meal vouchers, count me in.", "Si puede incluir un ascenso a clase ejecutiva más el hotel del aeropuerto y vales de comida, cuente conmigo.", "🏨🥂", "count me in", "cuente conmigo / acepto", "kaʊnt miː ɪn", "Propón aceptar si incluyen ascenso a clase ejecutiva, hotel y comidas.", "Yes, I have one seat left in Business Class on the 8:00 AM departure!"),
            ("pull-checked-bag-or-keep", "Will my checked bag stay safely in the hold overnight, or should I retrieve it now?", "¿Mi maleta documentada quedará resguardada durante la noche o debo recogerla ahora?", "🧳🔒", "retrieve", "recuperar / recoger", "rɪˈtriːv", "Pregunta qué pasará con tu maleta documentada esta noche.", "Deal! I've locked in seat 3A for tomorrow, plus your hotel voucher and $600 credit."),
            ("no-expiration-voucher", "Is the travel credit transferable or valid for twelve months without blackout dates?", "¿El crédito de viaje es válido por doce meses sin fechas restringidas?", "🎟️📅", "blackout dates", "fechas restringidas", "ˈblækaʊt deɪts", "", ""),
            ("shuttle-to-airport-hotel", "Where does the complimentary shuttle to the airport hotel pick up?", "¿Dónde se toma el transporte gratuito hacia el hotel del aeropuerto?", "🚐🏨", "shuttle", "autobús de enlace / transporte", "ˈʃʌtəl", "", ""),
        ],
    ),
    (
        "travel-and-transport", "B2", "sleeper-train-compartment", "Resolving a sleeper train booking", "Resolver cabina duplicada en tren nocturno",
        "Aclara con el jefe de tren nocturno que dos pasajeros tienen impreso el mismo camarote y solicita reubicación.",
        "sleeping car attendant", "overnight passenger", "Corridor of a European night train departing Vienna.",
        [
            ("duplicate-cabin-assignment", "Excuse me, it looks like there's a system glitch—both of us have tickets for Cabin 7.", "Disculpe, parece que hay un fallo del sistema: ambos tenemos boletos para el camarote 7.", "🚆🛏️", "system glitch", "fallo técnico del sistema", "ˈsɪstəm ɡlɪtʃ", "Explica que ambos pasajeros tienen boletos asignados al camarote 7.", "Good evening and welcome aboard the Nightjet! How can I help you two?"),
            ("booked-private-sleeper", "I booked this private two-berth compartment three months ago; here is my PDF confirmation.", "Reservé este compartimento privado de dos literas hace tres meses; aquí está mi confirmación en PDF.", "📱📄", "berth", "litera de tren o barco", "bɜːrθ", "Muestra tu confirmación en PDF reservada hace tres meses.", "Let me scan both QR codes—ah, theycoupled a replacement carriage today."),
            ("vacant-deluxe-cabin", "Is there a vacant compartment in the next carriage so neither of us has to downgrade?", "¿Hay algún compartimento libre en el siguiente vagón para que ninguno baje de categoría?", "🚪✨", "vacant", "libre / desocupado", "ˈveɪkənt", "Pregunta si hay un camarote libre en el vagón contiguo.", "I see what happened. Let me check my manifest for Carriage 412."),
            ("breakfast-tray-order", "Thank you for sorting that out! Where should I hang our morning breakfast order card?", "¡Gracias por resolverlo! ¿Dónde debo colgar nuestra tarjeta de pedido de desayuno?", "🥐☕", "sorting that out", "resolver / solucionar eso", "ˈsɔːrtɪŋ ðæt aʊt", "Agradece la solución y pregunta por la tarjeta de desayuno.", "Good news: Cabin 3 in the Deluxe carriage is completely empty—I'll move you there at no charge!"),
            ("lock-compartment-inside", "Does the security latch lock from the inside while we sleep?", "¿El pestillo de seguridad cierra por dentro mientras dormimos?", "🔒🌙", "latch", "pestillo / cerrojo", "lætʃ", "", ""),
            ("border-passport-check", "Do border police check passports overnight, or do you hold our tickets?", "¿La policía fronteriza revisa pasaportes de noche o usted guarda los boletos?", "🛂🌙", "overnight", "durante la noche", "ˌoʊvərˈnaɪt", "", ""),
        ],
    ),
    (
        "travel-and-transport", "B2", "schengen-visa-extension", "Explaining a weather delay at border control", "Explicar cancelación de vuelo en migración",
        "Explica a un oficial de migración con constancia de la aerolínea por qué tu vuelo salió un día después.",
        "border control officer", "departing traveler", "Airport passport control booth.",
        [
            ("airline-disruption-letter", "Good morning. My outbound flight yesterday was canceled due to the blizzard; here is the airline's certificate.", "Buenos días. Mi vuelo de salida de ayer fue cancelado por la tormenta de nieve; aquí está la constancia de la aerolínea.", "🛂❄️", "outbound", "de salida", "ˈaʊtbaʊnd", "Muestra la constancia de la aerolínea por la cancelación debida a la tormenta.", "Good morning. Passport and boarding pass, please. I notice your 90-day stay expired yesterday."),
            ("rebooked-first-available", "The carrier rebooked me onto the very first available departure this morning.", "La aerolínea me reprogramó en la primera salida disponible de esta mañana.", "✈️🌅", "carrier", "aerolínea / transportista", "ˈkæriər", "Explica que te reubicaron en el primer vuelo disponible de esta mañana.", "Let me verify the flight cancellation notice from Lufthansa."),
            ("force-majeure-waiver", "Could you annotate my exit record as force majeure so it doesn't flag future entries?", "¿Podría anotar mi registro de salida como fuerza mayor para que no afecte futuros ingresos?", "📝🛡️", "force majeure", "fuerza mayor", "fɔːrs mɑːˈʒɜːr", "Pide que anoten la salida como causa de fuerza mayor en el sistema.", "Yes, all flights out of Terminal 1 were grounded for eighteen hours yesterday."),
            ("keep-stamped-copy", "Should I keep a stamped copy of this disruption form for my next trip?", "¿Debo conservar una copia sellada de este formulario para mi próximo viaje?", "📑✅", "annotate", "anotar / dejar constancia", "ˈænəteɪt", "Pregunta si conviene guardar copia sellada para tu próximo viaje.", "I've entered the weather waiver code into the system—your record remains completely clean."),
            ("checked-in-on-time", "As you can see from my original boarding pass, I had already cleared check-in on time.", "Como puede ver en mi pase original, ya había hecho el check-in a tiempo.", "🎫⏱️", "on time", "a tiempo", "ɑːn taɪm", "", ""),
            ("appreciate-your-understanding", "I really appreciate your thoroughness and understanding. Have a good day!", "Agradezco mucho su atención y comprensión. ¡Que tenga un buen día!", "🙏🛂", "understanding", "comprensión", "ˌʌndərˈstændɪŋ", "", ""),
        ],
    ),
    (
        "travel-and-transport", "B2", "harbor-charter-itinerary", "Adjusting a coastal boat charter", "Ajustar ruta en barco por vientos fuertes",
        "Coordina con el capitán de un velero alquilado cambiar el recorrido hacia una bahía protegida del viento.",
        "charter skipper", "group organizer", "Marina dock before setting sail along the coast.",
        [
            ("sheltered-cove-route", "Given the gusty afternoon forecast, would it be wiser to hug the sheltered southern coves?", "Dado el pronóstico de ráfagas por la tarde, ¿sería más prudente bordear las calas protegidas del sur?", "⛵🌬️", "sheltered", "protegidas / resguardadas", "ˈʃeltərd", "Pregunta si conviene ir por las calas protegidas del sur ante el viento.", "Morning! The breeze is picking up to twenty knots from the northwest this afternoon."),
            ("avoid-choppy-swell", "A couple of friends get seasick easily, so we'd love to avoid choppy open-water swell.", "Un par de amigos se marean fácilmente, así que preferimos evitar el oleaje picado de mar abierto.", "🌊🤢", "choppy", "picado / agitado (el mar)", "ˈtʃɑːpi", "Explica que algunos amigos se marean y prefieren aguas tranquilas.", "Hugging the southern peninsula keeps us in flat water all day."),
            ("drop-anchor-for-swim", "Can we drop anchor in the turquoise bay around noon for snorkeling and lunch?", "¿Podemos echar el ancla en la bahía turquesa al mediodía para hacer snorkel y almorzar?", "⚓🤿", "drop anchor", "echar el ancla / fondear", "drɑːp ˈæŋkər", "Pregunta si pueden fondear al mediodía para hacer snorkel y almorzar.", "That's a great plan—Blue Lagoon on the south side is crystal clear and calm."),
            ("head-back-before-dusk", "Let's aim to dock back at the marina thirty minutes before sunset.", "Apuntemos a atracar de regreso en la marina treinta minutos antes del atardecer.", "🌅⚓", "dock", "atracar en el muelle", "dɑːk", "Propón regresar al muelle treinta minutos antes del atardecer.", "Absolutely! I have snorkeling masks, fins, and paddleboards stowed on deck."),
            ("life-vest-briefing", "Please give everyone a quick safety briefing before we cast off the lines.", "Por favor dé a todos una breve charla de seguridad antes de soltar amarras.", "🦺📢", "cast off", "soltar amarras / zarpar", "kæst ɔːf", "", ""),
            ("split-fuel-and-tip", "We'll settle the fuel tab and crew gratuity as soon as we tie up.", "Liquidaremos el combustible y la propina de la tripulación en cuanto amarremos.", "💳🤝", "gratuity", "propina", "ɡrəˈtuːəti", "", ""),
        ],
    ),
    # C1 (4 new)
    (
        "travel-and-transport", "C1", "eu261-flight-compensation", "Claiming statutory flight compensation", "Reclamar indemnización legal por vuelo cancelado",
        "Solicita la compensación reglamentaria tras una cancelación por fallo técnico de la aeronave.",
        "customer relations supervisor", "passenger", "Airline service desk after a long-haul technical cancellation.",
        [
            ("technical-fault-not-extraordinary", "Under European court precedent, a routine technical fault does not qualify as an extraordinary circumstance.", "Según la jurisprudencia europea, un fallo técnico rutinario no califica como circunstancia extraordinaria.", "⚖️✈️", "precedent", "precedente / jurisprudencia", "ˈpresɪdənt", "Recuerda que un fallo técnico rutinario no es circunstancia extraordinaria.", "We apologize for the four-hour delay, which was caused by a faulty valve replaced in Madrid."),
            ("statutory-six-hundred-euros", "Since we arrived four hours late on a long-haul route, we're eligible for the statutory six-hundred-euro payout.", "Como llegamos cuatro horas tarde en una ruta de larga distancia, calificamos para la compensación legal de seiscientos euros.", "💶📋", "statutory", "establecido por ley / reglamentario", "ˈstætʃətɔːri", "Solicita la compensación reglamentaria por llegar cuatro horas tarde.", "I understand your frustration. Were you looking for travel vouchers or a bank transfer?"),
            ("prefer-bank-wire-over-voucher", "We'd prefer the cash settlement via IBAN wire transfer rather than restricted airline vouchers.", "Preferimos la liquidación en efectivo por transferencia bancaria en lugar de bonos restringidos.", "🏦💳", "settlement", "liquidación / pago", "ˈsetəlmənt", "Indica que prefieren transferencia bancaria en lugar de bonos de viaje.", "Under EU Regulation 261, you do have the right to choose cash payment over vouchers."),
            ("duty-of-care-receipts", "I've also attached itemized receipts for our dinner and taxi under the airline's duty-of-care obligation.", "También adjunté los recibos detallados de cena y taxi bajo la obligación de asistencia de la aerolínea.", "🧾🍽️", "duty of care", "deber de asistencia al pasajero", "ˈduːti əv ker", "Entrega los recibos de comida y transporte cubiertos por el deber de asistencia.", "Please enter your IBAN details on this claim portal and upload any meal receipts."),
            ("written-acknowledgment-number", "Could you issue a claim dossier number so we can track processing within fourteen days?", "¿Podría emitir un número de expediente para dar seguimiento en catorce días?", "🔢📧", "dossier", "expediente", "ˈdɑːsieɪ", "", ""),
            ("appreciate-prompt-resolution", "Thank you for handling the claim transparently and logging our documentation.", "Gracias por gestionar el reclamo con transparencia y registrar nuestra documentación.", "🤝✅", "transparently", "con transparencia", "trænsˈpærəntli", "", ""),
        ],
    ),
    (
        "travel-and-transport", "C1", "maritime-port-clearance", "Coordinating marina port clearance", "Coordinar despacho portuario y atraque",
        "Gestiona por radio VHF y en capitanía de puerto el atraque, conexión eléctrica y despacho de entrada.",
        "harbormaster", "vessel captain", "Port authority office at a Mediterranean marina.",
        [
            ("request-berth-assignment", "Good afternoon, Harbormaster. We're a forty-five-foot sloop requesting a stern-to berth for three nights.", "Buenas tardes, Capitán de Puerto. Somos un velero de cuarenta y cinco pies solicitando atraque de popa por tres noches.", "⛵⚓", "stern-to berth", "atraque de popa en muelle", "stɜːrn tuː bɜːrθ", "Solicita un atraque de popa por tres noches para un velero de 45 pies.", "Harbormaster's office, welcome to Palma Marina! What is your vessel's length and draft?"),
            ("shore-power-and-water", "Does Slip C-14 have thirty-amp shore power and potable water hookups?", "¿El amarre C-14 cuenta con conexión eléctrica de treinta amperios y toma de agua potable?", "🔌💧", "shore power", "toma eléctrica de tierra", "ʃɔːr ˈpaʊər", "Pregunta si el amarre C-14 tiene toma eléctrica y agua potable.", "With a two-meter draft, I can assign you to Slip C-14 on the outer pontoon."),
            ("crew-list-and-registry", "Here are our ship's registry papers, hull insurance certificate, and stamped crew manifest.", "Aquí están los documentos de registro del barco, póliza de casco y lista de tripulación sellada.", "📑🛂", "manifest", "rol de tripulación / manifiesto", "ˈmænɪfest", "Entrega el registro de la embarcación, seguro y lista de tripulación.", "Yes, C-14 has full pedestal utilities. May I inspect your vessel documents?"),
            ("fuel-bunkering-dock", "Tomorrow morning we'd like to top off diesel at the fuel dock before the charter guests embark.", "Mañana temprano quisiéramos recargar diésel en el muelle de combustible antes de que embarquen los invitados.", "⛽🌅", "top off", "llenar por completo el tanque", "tɑːp ɔːf", "Coordina recargar diésel mañana temprano antes de que suban los invitados.", "All documents are in order. Here is your marina gate keycard."),
            ("blackwater-pump-out", "We'll also schedule a holding-tank pump-out on Channel 9 prior to departure.", "También programaremos el vaciado del tanque de aguas residuales por el canal 9 antes de zarpar.", "📻♻️", "prior to", "antes de / previo a", "ˈpraɪər tuː", "", ""),
            ("weather-bulletin-posted", "Thank you—we'll check the morning barometric bulletin at your office.", "Gracias; revisaremos el boletín barométrico matutino en su oficina.", "🌡️🧭", "bulletin", "boletín / reporte", "ˈbʊlətɪn", "", ""),
        ],
    ),
    (
        "travel-and-transport", "C1", "rail-strike-rerouting", "Navigating a national rail strike", "Reorganizar ruta durante huelga ferroviaria",
        "Coordina en ventanilla internacional una ruta alternativa combinando tren de servicio mínimo y autobús transfronterizo.",
        "international rail agent", "business traveler", "Central station international travel center during a 24-hour strike.",
        [
            ("guaranteed-minimum-service", "Which cross-border trains are operating under the mandatory minimum-service schedule today?", "¿Qué trenes transfronterizos están operando hoy bajo el horario obligatorio de servicios mínimos?", "🚄📋", "mandatory", "obligatorio", "ˈmændətɔːri", "Pregunta qué trenes internacionales operan bajo el horario de servicios mínimos.", "Good morning. As you know, only one in three high-speed trains is running today due to the strike."),
            ("reroute-via-geneva", "If the Lyon corridor is shut, could we route through Geneva and connect to the Swiss network?", "Si el corredor de Lyon está cerrado, ¿podríamos ir vía Ginebra y conectar con la red suiza?", "🗺️🇨🇭", "corridor", "corredor ferroviario", "ˈkɔːrɪdɔːr", "Propón desviar la ruta vía Ginebra para conectar con la red suiza.", "The 10:40 to Milan via Lyon is canceled, but the Swiss border line remains open."),
            ("cross-honor-rail-ticket", "Will the Swiss operator cross-honor our existing first-class Eurail reservation without a supplement?", "¿El operador suizo aceptará nuestra reserva actual de primera clase sin cobrar suplemento?", "🎫🤝", "cross-honor", "reconocer boletos entre operadores", "krɔːs ˈɑːnər", "Pregunta si el operador suizo aceptará el boleto actual sin suplemento.", "Routing via Geneva gets you into Milan only ninety minutes later than planned!"),
            ("issue-control-coupon", "Please print the strike-rerouting endorsement slip so the onboard inspector sees the authorization.", "Por favor imprima el volante de reubicación por huelga para que el inspector a bordo vea la autorización.", "🖨️✅", "endorsement slip", "comprobante de endoso / autorización", "ɪnˈdɔːrsmənt slɪp", "Pide imprimir el comprobante de autorización para mostrarlo al inspector.", "Yes, we have a reciprocal disruption agreement with SBB today—no supplement required."),
            ("coach-transfer-fallback", "If the afternoon connection slips, is there an express coach running from the border station?", "Si falla la conexión de la tarde, ¿hay algún autobús expreso desde la estación fronteriza?", "🚌🔄", "slips", "se retrasa / falla", "slɪps", "", ""),
            ("grateful-for-quick-thinking", "That Geneva workaround saves our entire conference trip—thank you!", "Esa alternativa por Ginebra salva todo nuestro viaje al congreso; ¡gracias!", "🙌🚆", "workaround", "solución alternativa", "ˈwɜːrkəraʊnd", "", ""),
        ],
    ),
    (
        "travel-and-transport", "C1", "global-entry-interview", "Trusted traveler border interview", "Entrevista de viajero frecuente en frontera",
        "Responde con precisión las preguntas de un oficial sobre historial de viajes, motivo laboral y cumplimiento aduanero.",
        "customs & border officer", "applicant", "Trusted Traveler enrollment center at an international airport.",
        [
            ("frequent-transatlantic-travel", "I fly transatlantic roughly once a month to oversee our European engineering hubs.", "Vuelo a través del Atlántico aproximadamente una vez al mes para supervisar nuestros centros de ingeniería europeos.", "✈️🌐", "oversee", "supervisar / dirigir", "ˌoʊvərˈsiː", "Explica que vuelas cada mes a Europa para supervisar equipos de ingeniería.", "Please have a seat. Why are you applying for the Trusted Traveler program?"),
            ("five-year-address-history", "I brought my residency utility bills and employment verification covering the past five years.", "Traje mis comprobantes de domicilio y constancia laboral que cubren los últimos cinco años.", "📑🏠", "covering", "que abarcan / cubren", "ˈkʌvərɪŋ", "Presenta tus comprobantes de domicilio y constancia laboral de cinco años.", "Thank you. Let's verify your residential and employment history."),
            ("strict-customs-compliance", "I've never had a customs violation or agricultural seizure in any jurisdiction.", "Nunca he tenido una infracción aduanera ni retención agrícola en ninguna jurisdicción.", "🛂✅", "seizure", "decomiso / retención aduanera", "ˈsiːʒər", "Confirma que nunca has tenido infracciones aduaneras en ninguna jurisdicción.", "Have you ever been cited for failing to declare commercial goods or agricultural items?"),
            ("biometric-kiosk-rules", "I understand that even with biometric kiosk clearance, I must declare any food or currency over the threshold.", "Entiendo que incluso usando el quiosco biométrico debo declarar cualquier alimento o divisa que supere el límite.", "👁️📋", "threshold", "umbral / límite legal", "ˈθreʃhoʊld", "Demuestra que conoces la obligación de declarar alimentos o divisas sobre el límite.", "Good. Place your right four fingers flat on the glass scanner for biometrics."),
            ("known-traveler-number", "How soon does my Known Traveler Number activate for upcoming airline bookings?", "¿Qué tan pronto se activa mi número de viajero confiable para próximas reservas?", "🔢📲", "upcoming", "próximas / futuras", "ˈʌpkʌmɪŋ", "", ""),
            ("renew-every-five-years", "Thank you, Officer—I'll add the KTN to my frequent-flyer profile today.", "Gracias, oficial; agregaré el número a mi perfil de viajero frecuente hoy mismo.", "🤝✈️", "profile", "perfil de usuario", "ˈproʊfaɪl", "", ""),
        ],
    ),
    # C2 (4 new)
    (
        "travel-and-transport", "C2", "charter-fuel-diversion", "Coordinating an aviation weather diversion", "Coordinar desvío meteorológico de vuelo",
        "Toma decisiones rápidas con despacho de vuelo ante vientos cruzados severos, calculando combustible de reserva y aeropuerto alterno.",
        "flight dispatcher", "charter director", "Operations control center monitoring a transatlantic charter flight.",
        [
            ("crosswind-exceeds-limits", "Crosswinds at Keflavik just exceeded thirty-five knots, so we should execute our alternate diversion to Glasgow.", "Los vientos cruzados en Keflavik acaban de superar los treinta y cinco nudos, por lo que debemos ejecutar el desvío alterno a Glasgow.", "✈️🌩️", "exceeded", "superaron / excedieron", "ɪkˈsiːdɪd", "Propón activar el desvío al aeropuerto alterno de Glasgow por vientos cruzados.", "Operations update: Keflavik runway 28 is reporting severe wind shear and braking action poor."),
            ("holding-fuel-margin", "Committing to the alternate now preserves a comfortable forty-five-minute holding fuel margin.", "Confirmar el alterno ahora preserva un margen cómodo de cuarenta y cinco minutos de combustible de reserva.", "⛽🧭", "margin", "margen de seguridad", "ˈmɑːrdʒɪn", "Destaca que desviar ahora mantiene intacto el margen de 45 minutos de reserva.", "The captain concurs—staying in the holding stack much longer will eat into contingency fuel."),
            ("slot-and-ground-handling", "Have our ground handlers in Glasgow secured a turnaround slot and customs standby?", "¿Nuestro equipo de tierra en Glasgow ya aseguró turno de plataforma y aduana en espera?", "🛬📋", "turnaround slot", "franja operativa de escala", "ˈtɜːrnəraʊnd slɑːt", "Pregunta si el personal de tierra en Glasgow aseguró plataforma y aduana.", "I'm filing the amended flight plan with Eurocontrol right now."),
            ("crew-duty-time-cap", "Let's verify that a ninety-minute refuel stop won't push the flight deck past their statutory duty-time cap.", "Verifiquemos que una escala de noventa minutos no lleve a la tripulación más allá del límite legal de horas de servicio.", "⏱️👨‍✈️", "duty-time cap", "límite legal de jornada de vuelo", "ˈduːti taɪm kæp", "Pide verificar que la escala no exceda el límite legal de jornada de los pilotos.", "Glasgow FBO confirmed apron parking and rapid refueling on arrival."),
            ("passenger-briefing-cabin", "Ask the purser to brief the cabin calmly once the new arrival estimate is locked.", "Pida al sobrecargo informar a la cabina con serenidad en cuanto se confirme la nueva hora estimada.", "🎙️💺", "purser", "jefe de cabina / sobrecargo", "ˈpɜːrsər", "", ""),
            ("seamless-operational-call", "Decisive call—safety margins and crew legality always take precedence.", "Decisión acertada: los márgenes de seguridad y la normativa de tripulación siempre tienen prioridad.", "🛡️✅", "take precedence", "tener prioridad absoluta", "teɪk ˈpresɪdəns", "", ""),
        ],
    ),
    (
        "travel-and-transport", "C2", "diplomatic-pouch-transit", "Clearing a diplomatic courier pouch", "Verificar tránsito de valija diplomática",
        "Invoca el artículo 27 de la Convención de Viena en control aeroportuario para proteger una valija diplomática sellada.",
        "aviation security supervisor", "diplomatic courier", "International transit security checkpoint.",
        [
            ("vienna-convention-article", "Pursuant to Article 27 of the Vienna Convention, this sealed diplomatic pouch is exempt from X-ray obertura.", "Conforme al artículo 27 de la Convención de Viena, esta valija diplomática sellada está exenta de apertura.", "🛂📜", "pursuant to", "de conformidad con / según", "pərˈsuːənt tuː", "Explica que bajo el Artículo 27 la valija sellada no puede ser abierta.", "Good afternoon. All transit parcels must be opened for manual inspection at this checkpoint."),
            ("courier-waybill-seal", "Here is my diplomatic courier credential along with the ministry waybill matching the lead wax seal.", "Aquí está mi credencial de correo diplomático junto con la guía del ministerio que coincide con el sello de plomo.", "🪪🔒", "waybill", "guía de despacho oficial", "ˈweɪbɪl", "Presenta tu credencial diplomática y la guía oficial que coincide con el sello.", "May I verify your diplomatic passport and the official courier letter?"),
            ("external-swab-permissible", "While the pouch cannot be opened, you are welcome to inspect the exterior seal integrity.", "Aunque la valija no puede abrirse, puede verificar visualmente la integridad de los sellos exteriores.", "🔍🛡️", "exterior", "exterior / externo", "ɪkˈstɪriər", "Permite que verifiquen visualmente los sellos externos sin abrir la valija.", "The seal serial numbers and Ministry of Foreign Affairs stamp match your courier dossier."),
            ("escort-to-boarding-gate", "Could a protocol officer countersign the transit log and escort us to Gate A12?", "¿Podría un oficial de protocolo refrendar la bitácora de tránsito y escoltarnos a la puerta A12?", "✍️🛫", "protocol officer", "oficial de protocolo diplomático", "ˈproʊtəkɔːl ˈɔːfɪsər", "Solicita que el oficial de protocolo firme la bitácora y los acompañe a la puerta A12.", "Understood. We will log the diplomatic transit without opening the seal."),
            ("unaccompanied-custody-forbidden", "Protocol requires the pouch to remain in my personal custody in the cabin at all times.", "El protocolo exige que la valija permanezca bajo mi custodia personal en cabina en todo momento.", "💼💺", "custody", "custodia directa", "ˈkʌstədi", "", ""),
            ("courteous-adherence-protocol", "I appreciate your team's strict adherence to international treaty protocol.", "Agradezco el estricto apego de su equipo al protocolo de los tratados internacionales.", "🤝🌐", "adherence", "apego / cumplimiento estricto", "ədˈhɪrəns", "", ""),
        ],
    ),
    (
        "travel-and-transport", "C2", "antarctic-expedition-briefing", "Ice-navigation expedition briefing", "Revisar contingencias de navegación polar",
        "Evalúa con el capitán de un buque polar las cartas de hielo marino, protocolos de desembarco en Zodiac y bioseguridad.",
        "ice-pilot captain", "expedition leader", "Bridge of a polar expedition vessel crossing the Drake Passage.",
        [
            ("pack-ice-drift", "Satellite synthetic-aperture radar shows dense pack ice drifting across the Lemaire Channel entrance.", "El radar satelital muestra hielo marino denso desplazándose hacia la entrada del canal Lemaire.", "🧊🛰️", "pack ice", "banquisa / hielo marino flotante", "pæk aɪs", "Señala que el radar satelital muestra hielo denso en la entrada del canal.", "Welcome to the bridge. Let's review tomorrow's landing sites along the peninsula."),
            ("pivot-to-leeward-bay", "If brash ice chokes the narrows, we should pivot our morning Zodiac landing to the leeward bay.", "Si el hielo fragmentado bloquea el estrecho, debemos redirigir el desembarco matutino en Zodiac a la bahía de sotavento.", "🚤🧭", "leeward", "a sotavento / protegido del viento", "ˈliːwərd", "Propón cambiar el desembarco en Zodiac a la bahía de sotavento si hay bloqueo.", "Agreed—pushing through heavy floes would eat up our entire morning window."),
            ("biosecurity-boot-scrub", "Every passenger must complete the biosecurity vacuuming and virucidal boot scrub before stepping ashore.", "Cada pasajero debe completar el aspirado de bioseguridad y desinfección de botas antes de bajar a tierra.", "🥾🧪", "ashore", "en tierra firme / a la costa", "əˈʃɔːr", "Recuerda el protocolo obligatorio de desinfección de botas antes de bajar a tierra.", "The leeward bay has a sheltered pebble beach and a gentoo penguin colony."),
            ("katabatic-wind-watch", "We'll keep a coxswain on continuous barometric watch in case katabatic gusts sweep off the glacier.", "Mantendremos un timonel en vigilancia barométrica continua por si bajan ráfagas catabáticas del glaciar.", "🌬️🏔️", "gusts", "ráfagas de viento", "ɡʌsts", "Establece vigilancia continua ante posibles vientos catabáticos del glaciar.", "Strict IAATO biosecurity is non-negotiable. What about wind monitoring during shore operations?"),
            ("maintain-five-meter-buffer", "Remind all photographers to maintain a strict five-meter wildlife buffer along the penguin highways.", "Recuerde a los fotógrafos mantener cinco metros de distancia respecto a los senderos de pingüinos.", "🐧📸", "buffer", "zona de respeto / distancia mínima", "ˈbʌfər", "", ""),
            ("update-evening-recap", "Let's present the revised chart to the guests during tonight's briefing in the lounge.", "Presentemos la carta náutica actualizada a los pasajeros en la charla de esta noche.", "🗺️🎙️", "chart", "carta náutica", "tʃɑːrt", "", ""),
        ],
    ),
    (
        "travel-and-transport", "C2", "autonomous-mobility-panel", "Debating urban autonomous transit policy", "Debatir políticas de movilidad autónoma",
        "Participa en un panel de urbanismo sobre flotas autónomas compartidas, transporte público e infraestructura peatonal.",
        "urban transport commissioner", "mobility researcher", "Keynote panel at a global smart-cities summit.",
        [
            ("induced-congestion-paradox", "Replacing private cars one-for-one with empty roaming robotaxis risks worsening induced congestion.", "Reemplazar autos privados uno por uno con robotaxis circulando vacíos corre el riesgo de agravar la congestión inducida.", "🤖🚗", "worsening", "empeorar / agravar", "ˈwɜːrsənɪŋ", "Advierte que sustituir autos por robotaxis vacíos puede aumentar la congestión.", "Proponents claim autonomous vehicles will eliminate urban traffic overnight. What does your data show?"),
            ("first-mile-feeder-integration", "Autonomous shuttles deliver the highest civic return when integrated as first-mile feeders into high-capacity rail.", "Las lanzaderas autónomas rinden el mayor beneficio cívico cuando se integran como alimentadores de primera milla hacia el tren.", "🚊🔄", "first-mile feeders", "rutas alimentadoras de primera milla", "fɜːrst maɪl ˈfiːdərz", "Explica que su mayor valor está en conectar el primer tramo con el tren masivo.", "So how should municipalities integrate autonomous fleets without cannibalizing mass transit?"),
            ("curbside-pricing-telemetry", "Dynamic curbside pricing and anonymized telemetry sharing should be preconditions for operating permits.", "La tarificación dinámica de bordillos y el intercambio de telemetría anónima deberían ser requisitos para los permisos.", "📊🏙️", "preconditions", "requisitos previos / condiciones", "ˌpriːkənˈdɪʃənz", "Propón tarifas dinámicas de acera y telemetría anónima para otorgar permisos.", "That's a compelling framework. What regulatory levers should cities retain over curb space?"),
            ("reclaim-streetscape-pedestrians", "Our ultimate metric of success is reclaiming asphalt for Micromobility, trees, and pedestrian plazas.", "Nuestra métrica definitiva de éxito es recuperar el asfalto para micromovilidad, árboles y plazas peatonales.", "🌳🚶‍♀️", "reclaiming", "recuperar (espacio público)", "rɪˈkleɪmɪŋ", "Concluye que el verdadero éxito es recuperar espacio público para los peatones.", "If we price drop-off zones dynamically, how should cities reinvest that revenue?"),
            ("equitable-suburban-access", "Subsidizing off-peak autonomous microtransit can bridge transit deserts in underserved suburbs.", "Subsidiar el microtransporte autónomo fuera de hora punta puede cubrir zonas sin transporte en la periferia.", "🏘️🚌", "underserved", "desatendidos / con pocos servicios", "ˌʌndərˈsɜːrvd", "", ""),
            ("algorithmic-safety-audits", "Independent algorithmic safety audits must precede any expansion of driverless operating domains.", "Las auditorías independientes de seguridad algorítmica deben preceder cualquier expansión operativa.", "🛡️🔍", "precede", "preceder / ir antes de", "prɪˈsiːd", "", ""),
        ],
    ),
])

CELL_BLUEPRINTS.extend([
    # ==================== 3. HOTEL-AND-SHOPPING ====================
    # A1 (4 new)
    (
        "hotel-and-shopping", "A1", "souvenir-postcard-shop", "Buying postcards and magnets", "Comprar postales e imanes",
        "Compra tres postales, un imán para el refrigerador y estampillas en una tienda de recuerdos.",
        "shopkeeper", "tourist", "A colorful souvenir shop near the old town square.",
        [
            ("three-postcards", "I would like these three city postcards, please.", "Quisiera estas tres postales de la ciudad, por favor.", "🖼️🏙️", "postcards", "tarjetas postales", "ˈpoʊstkɑːrdz", "Pide estas tres postales de la ciudad.", "Hello! Welcome to Old Town Gifts. Did you find everything okay?"),
            ("fridge-magnet", "How much is this little bridge magnet?", "¿Cuánto cuesta este pequeño imán del puente?", "🧲🌉", "magnet", "imán", "ˈmæɡnɪt", "Pregunta cuánto cuesta el imán del puente.", "Three postcards! Anything else from the rack?"),
            ("stamps-for-postcards", "Do you sell international stamps here too?", "¿Venden estampillas internacionales aquí también?", "✉️🌍", "stamps", "estampillas / sellos postales", "stæmps", "Pregunta si venden estampillas internacionales.", "The bridge magnet is three dollars. It's hand-painted!"),
            ("small-gift-bag", "Can you put them in a small gift bag?", "¿Puede ponerlos en una bolsita de regalo?", "🎁🛍️", "gift bag", "bolsa de regalo", "ɡɪft bæɡ", "Pide que los pongan en una bolsita de regalo.", "Yes, I have international stamps right behind the counter."),
            ("red-keychain", "I will also take this red keychain for my sister.", "También me llevo este llavero rojo para mi hermana.", "🔑❤️", "keychain", "llavero", "ˈkiːtʃeɪn", "", ""),
            ("mailbox-outside", "Great, I see the yellow mailbox outside the shop!", "¡Genial, veo el buzón amarillo afuera de la tienda!", "📮😊", "mailbox", "buzón de correo", "ˈmeɪlbɑːks", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "A1", "shoe-store-size", "Trying on running shoes", "Probarse zapatos deportivos",
        "Pide unos tenis para correr en talla nueve, pruébatelos y comenta que son muy cómodos.",
        "shoe sales associate", "shopper", "A sports shoe store on Main Street.",
        [
            ("size-nine-shoes", "Do you have these blue running shoes in size nine?", "¿Tienen estos tenis azules para correr en talla nueve?", "👟🔵", "size", "talla / número", "saɪz", "Pregunta si tienen los tenis azules en talla nueve.", "Hi there! Let me know if you'd like to try on any shoes."),
            ("try-both-on", "Can I sit here and try both shoes on?", "¿Puedo sentarme aquí y probarme ambos zapatos?", "🪑👟", "both", "ambos / los dos", "boʊθ", "Pide sentarte y probarte ambos zapatos.", "Here is a size nine in blue! Would you like to try them?"),
            ("very-comfortable", "They feel very light and comfortable on my feet.", "Se sienten muy ligeros y cómodos en mis pies.", "🦶✨", "comfortable", "cómodos", "ˈkʌmfərtəbəl", "Comenta que se sienten muy ligeros y cómodos.", "Take a walk around the mirror. How do they feel?"),
            ("pair-of-white-socks", "I will take the shoes and one pack of white socks.", "Me llevo los zapatos y un paquete de calcetines blancos.", "🧦🛍️", "socks", "calcetines / medias", "sɑːks", "Di que te llevas los zapatos y un paquete de calcetines blancos.", "They look great on you! Ready to check out?"),
            ("half-size-bigger", "Nine is my exact size; I don't need a bigger one.", "Nueve es mi talla exacta; no necesito uno más grande.", "📏✅", "bigger", "más grande", "ˈbɪɡər", "", ""),
            ("keep-the-shoebox", "Yes, please put them inside the shoebox.", "Sí, por favor póngalos dentro de la caja de zapatos.", "📦👟", "shoebox", "caja de zapatos", "ˈʃuːbɑːks", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "A1", "hotel-breakfast-hours", "Asking about hotel breakfast & pool", "Preguntar horario de desayuno y piscina",
        "Pregunta en recepción a qué hora empieza el desayuno, en qué piso está la piscina y pide la llave.",
        "receptionist", "hotel guest", "Hotel lobby desk in the afternoon.",
        [
            ("what-time-breakfast", "Excuse me, what time does breakfast start tomorrow?", "Disculpe, ¿a qué hora empieza el desayuno mañana?", "🥐🕖", "start", "empezar / comenzar", "stɑːrt", "Pregunta a qué hora empieza el desayuno mañana.", "Good afternoon! How are you enjoying your stay with us?"),
            ("where-is-dining-room", "Is the breakfast room on the ground floor?", "¿El comedor del desayuno está en la planta baja?", "🍽️🏨", "ground floor", "planta baja / primer piso", "ɡraʊnd flɔːr", "Pregunta si el comedor está en la planta baja.", "Breakfast starts at seven o'clock and runs until ten."),
            ("swimming-pool-open", "Is the indoor swimming pool open this evening?", "¿La piscina techada está abierta esta tarde?", "🏊‍♂️💧", "swimming pool", "piscina / alberca", "ˈswɪmɪŋ puːl", "Pregunta si la piscina techada está abierta esta tarde.", "Yes, right past the elevators on the ground floor."),
            ("towels-by-the-pool", "Do you have clean towels by the pool?", "¿Tienen toallas limpias junto a la piscina?", "🧺🏊", "clean", "limpias", "kliːn", "Pregunta si hay toallas limpias junto a la piscina.", "The pool is open until 9:00 PM on the second floor."),
            ("second-room-key", "Can I have a second key card for my room, please?", "¿Me da una segunda tarjeta llave para mi habitación, por favor?", "🪪🚪", "key card", "tarjeta llave", "kiː kɑːrd", "", ""),
            ("thank-you-reception", "Thank you very much! See you tomorrow morning.", "¡Muchas gracias! Nos vemos mañana por la mañana.", "😊👋", "tomorrow", "mañana", "təˈmɔːroʊ", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "A1", "bookstore-dictionary", "Buying a travel guide at a bookstore", "Comprar una guía en la librería",
        "Busca una guía de viaje en inglés con mapa de la ciudad y un cuaderno pequeño en una librería.",
        "bookseller", "reader", "A quiet neighborhood bookshop.",
        [
            ("travel-books-section", "Excuse me, where are the city travel guides?", "Disculpe, ¿dónde están las guías de viaje de la ciudad?", "📚🗺️", "travel guides", "guías de viaje", "ˈtrævəl ɡaɪdz", "Pregunta dónde están las guías de viaje de la ciudad.", "Hello! Welcome to City Books. Can I help you find a title?"),
            ("book-with-street-map", "Does this small guide have a pull-out street map?", "¿Esta guía pequeña trae un mapa desplegable de calles?", "🗺️📖", "street map", "mapa de calles", "striːt mæp", "Pregunta si esa guía pequeña incluye un mapa de calles.", "The travel section is right over here by the green armchair."),
            ("pocket-notebook", "I also want this blue notebook and a black pen.", "También quiero este cuaderno azul y un bolígrafo negro.", "📓🖊️", "notebook", "cuaderno / libreta", "ˈnoʊtbʊk", "Agrega el cuaderno azul y un bolígrafo negro.", "Yes, there is a full color fold-out map in the back cover!"),
            ("free-bookmark", "May I have one of these paper bookmarks, please?", "¿Me regala uno de estos separadores de libros, por favor?", "🔖📘", "bookmark", "separador de libros / marcapáginas", "ˈbʊkmɑːrk", "Pide uno de los separadores de libros en la caja.", "Let's ring these up at the register for you."),
            ("english-short-stories", "This book of easy short stories looks great too.", "Este libro de cuentos cortos fáciles también se ve genial.", "📖✨", "short stories", "cuentos cortos / relatos", "ʃɔːrt ˈstɔːriz", "", ""),
            ("pay-at-counter", "Here is my card. Thank you for your help!", "Aquí está mi tarjeta. ¡Gracias por su ayuda!", "💳😊", "counter", "mostrador", "ˈkaʊntər", "", ""),
        ],
    ),
    # A2 (4 new)
    (
        "hotel-and-shopping", "A2", "supermarket-self-checkout", "Using the supermarket self-checkout", "Pedir ayuda en la caja de autopago",
        "Pide ayuda al encargado del supermercado cuando la máquina de autopago no escanea el pan.",
        "store attendant", "shopper", "Self-checkout lanes at a grocery store.",
        [
            ("barcode-wont-scan", "Excuse me, this bakery bag doesn't have a barcode to scan.", "Disculpe, esta bolsa de panadería no tiene código de barras para escanear.", "🥐🛒", "barcode", "código de barras", "ˈbɑːrkoʊd", "Explica que la bolsa de panadería no tiene código de barras.", "Hi! Need a hand with the self-checkout screen?"),
            ("enter-item-code", "How do I look up fresh bread Rolls on the touch screen?", "¿Cómo busco los panecillos frescos en la pantalla táctil?", "🖥️👆", "look up", "buscar en una lista", "lʊk ʌp", "Pregunta cómo buscar los panecillos en la pantalla táctil.", "No problem! For fresh bakery items, we select them by picture."),
            ("weighed-the-apples", "I also weighed these apples—do I press the fruit button first?", "También pesé estas manzanas; ¿presiono primero el botón de frutas?", "🍎⚖️", "weighed", "pesé / puse en la báscula", "weɪd", "Pregunta cómo registrar las manzanas en la báscula.", "Just tap 'Bakery' on the left and enter quantity four."),
            ("remove-double-scan", "Oops, it scanned the milk twice! Could you remove one carton?", "¡Uy, escaneó la leche dos veces! ¿Podría borrar un cartón?", "🥛❌", "twice", "dos veces", "twaɪs", "Pide ayuda porque la leche se escaneó dos veces.", "Yes, place the apples flat on the scale and tap 'Honeycrisp Apples'."),
            ("use-my-own-bag", "I tapped 'using my own bag' and placed it on the bagging area.", "Toqué 'uso mi propia bolsa' y la coloqué en el área de empaque.", "👜✅", "bagging area", "zona de embolsado", "ˈbæɡɪŋ ˈeriə", "", ""),
            ("tap-phone-to-pay", "All fixed! I'll pay with Apple Pay on the card reader.", "¡Todo listo! Pagaré con el celular en el lector de tarjetas.", "📲💳", "card reader", "lector de tarjetas", "kɑːrd ˈriːdər", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "A2", "laundry-dry-cleaning", "Dropping off clothes for dry cleaning", "Dejar ropa en la tintorería",
        "Entrega un traje y una camisa blanca en la tintorería, indica una mancha de café y pide entrega exprés.",
        "dry cleaner", "customer", "A neighborhood dry cleaning and laundry shop.",
        [
            ("dry-clean-this-suit", "Hi, I need to get this wool suit dry-cleaned and pressed.", "Hola, necesito lavar en seco y planchar este traje de lana.", "🤵🧥", "pressed", "planchado", "prest", "Pide lavar en seco y planchar este traje de lana.", "Good morning! Dropping off some items for cleaning today?"),
            ("coffee-stain-on-cuff", "There is a small coffee stain on the right sleeve cuff.", "Hay una pequeña mancha de café en el puño de la manga derecha.", "☕👔", "stain", "mancha", "steɪn", "Señala que hay una pequeña mancha de café en el puño derecho.", "Let me inspect the jacket and trousers. Any spots I should treat?"),
            ("ready-by-tomorrow-five", "Is it possible to have it ready by five o'clock tomorrow afternoon?", "¿Es posible tenerlo listo mañana a las cinco de la tarde?", "🕔📅", "ready by", "listo antes de / para", "ˈredi baɪ", "Pregunta si puede estar listo mañana a las cinco de la tarde.", "I'll pre-treat that cuff stain so it comes right out."),
            ("hangers-instead-folded", "Please put the white shirts on hangers instead of folding them.", "Por favor ponga las camisas blancas en ganchos en lugar de doblarlas.", "👔🪝", "hangers", "ganchos / perchas de ropa", "ˈhæŋərz", "Pide que pongan las camisas en ganchos en lugar de doblarlas.", "Yes, our next-day express service will have it ready by 4:30 PM tomorrow."),
            ("light-starch-collar", "Just light starch on the shirt collars, please.", "Solo un poco de almidón en los cuellos de las camisas, por favor.", "✨👔", "collar", "cuello de camisa", "ˈkɑːlər", "", ""),
            ("keep-pickup-ticket", "I'll bring this pink pickup ticket with me tomorrow.", "Traeré este boleto rosa de recogida conmigo mañana.", "🎟️👍", "pickup", "recogida", "ˈpɪkʌp", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "A2", "electronics-power-adapter", "Buying a universal travel adapter", "Comprar un adaptador de enchufe universal",
        "Compra un adaptador universal con puertos USB-C en una tienda de electrónica y verifica el voltaje.",
        "electronics clerk", "traveler", "An electronics store near the train station.",
        [
            ("universal-plug-adapter", "Hi, I'm looking for a universal travel plug adapter for Europe and the UK.", "Hola, busco un adaptador de enchufe universal para Europa y el Reino Unido.", "🔌🌍", "plug adapter", "adaptador de enchufe", "plʌɡ əˈdæptər", "Di que buscas un adaptador universal para Europa y Reino Unido.", "Welcome! What kind of accessory are you looking for today?"),
            ("fast-usb-c-ports", "Does this model have two fast-charging USB-C ports built in?", "¿Este modelo tiene dos puertos USB-C de carga rápida integrados?", "⚡📱", "built in", "incorporados / integrados", "bɪlt ɪn", "Pregunta si ese modelo tiene dos puertos USB-C de carga rápida.", "We have this compact all-in-one world adapter right here."),
            ("safe-for-laptop", "Is it safe to plug my laptop charger and phone into it at the same time?", "¿Es seguro conectar el cargador de mi laptop y mi teléfono al mismo tiempo?", "💻🔌", "at the same time", "al mismo tiempo", "æt ðə seɪm taɪm", "Pregunta si es seguro conectar la laptop y el teléfono a la vez.", "Yes, it delivers 65 watts across two USB-C ports plus the main AC socket."),
            ("braided-charging-cable", "I'll also grab a two-meter braided charging cable, please.", "También me llevaré un cable de carga trenzado de dos metros, por favor.", "➰🔋", "cable", "cable", "ˈkeɪbəl", "Agrega un cable de carga de dos metros a tu compra.", "Completely safe for dual-voltage laptops and tablets!"),
            ("spare-fuse-inside", "It's nice that it includes a spare safety fuse inside the case.", "Qué bueno que incluye un fusible de repuesto dentro del estuche.", "🛡️⚙️", "spare", "de repuesto", "sper", "", ""),
            ("test-before-leaving", "Everything fits snugly in the travel pouch—I'll take it!", "Todo cabe perfecto en el estuche de viaje; ¡me lo llevo!", "🎒✅", "pouch", "estuche / bolsita", "paʊtʃ", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "A2", "changing-hotel-rooms", "Asking to move to a quieter hotel room", "Pedir cambio a una habitación más tranquila",
        "Explica en recepción que tu habitación está justo al lado del ascensor y pide cambiar a otra más silenciosa.",
        "front desk clerk", "guest", "Hotel reception desk the morning after your first night.",
        [
            ("next-to-elevator", "Good morning. I'm in room 201, right next to the elevator and ice machine.", "Buenos días. Estoy en la habitación 201, justo al lado del ascensor y la máquina de hielo.", "🏨🛗", "ice machine", "máquina de hielo", "aɪs məˈʃiːn", "Explica que estás en la habitación 201 junto al ascensor y la máquina de hielo.", "Good morning! How did you sleep last night?"),
            ("move-to-quieter-room", "Would it be possible to move to a quieter room down the hall?", "¿Sería posible cambiarme a una habitación más silenciosa al final del pasillo?", "🤫🚪", "quieter", "más silenciosa / tranquila", "ˈkwaɪətər", "Pregunta si es posible cambiar a una habitación más silenciosa.", "Oh, I'm sorry if the hallway noise disturbed your rest! Let me check our system."),
            ("courtyard-view-fine", "A room facing the inner courtyard on the fourth floor sounds wonderful.", "Una habitación con vista al patio interior en el cuarto piso suena maravilloso.", "🌳🪟", "courtyard", "patio interior", "ˈkɔːrtjɑːrd", "Acepta encantado la habitación con vista al patio interior.", "We have room 418 available right now—it's at the end of the hall facing the quiet courtyard."),
            ("pack-up-in-ten-minutes", "I can pack my suitcase in ten minutes and swap the key cards here.", "Puedo empacar mi maleta en diez minutos y cambiar las tarjetas llave aquí.", "🧳🔑", "swap", "intercambiar / cambiar", "swɑːp", "Indica que empacarás en diez minutos y bajarás a cambiar las llaves.", "There is no extra charge for the move, and housekeeping has already cleaned 418."),
            ("bellhop-help-bags", "We only have two carry-on bags, so we can carry them up ourselves.", "Solo tenemos dos maletas de mano, así que podemos subirlas nosotros mismos.", "🎒🙌", "carry-on", "equipaje de mano", "ˈkæri ɑːn", "", ""),
            ("sleep-much-better", "Thank you for being so helpful—we'll sleep much better tonight!", "¡Gracias por ser tan amable; dormiremos mucho mejor esta noche!", "😴🌟", "helpful", "servicial / amable", "ˈhelpfəl", "", ""),
        ],
    ),
    # B1 (4 new)
    (
        "hotel-and-shopping", "B1", "tailor-suit-alterations", "Getting trousers hemmed at a tailor", "Ajustar el largo de un pantalón en la sastrería",
        "Pide a un sastre subir el dobladillo de un pantalón de vestir para una boda el sábado.",
        "master tailor", "customer", "A traditional tailoring shop with fitting mirrors.",
        [
            ("shorten-trouser-hem", "Hi! I bought these dress trousers for a wedding, but the legs are too long.", "¡Hola! Compré este pantalón de vestir para una boda, pero las piernas me quedan largas.", "👖📏", "trousers", "pantalón de vestir", "ˈtraʊzərz", "Explica que compraste el pantalón para una boda pero te queda largo.", "Welcome in! Step up onto the platform with your dress shoes on."),
            ("slight-break-on-shoe", "Could you hem them so there's just a slight break over my leather shoes?", "¿Podría subir el dobladillo para que caiga apenas sobre mis zapatos de cuero?", "👞📌", "hem", "hacer el dobladillo", "hem", "Pide que el dobladillo caiga suavemente sobre tus zapatos.", "Let me pin the fabric right here—do you prefer a modern no-break or a classic slight break?"),
            ("take-in-the-waist", "The waist is also half an inch loose; can you take it in slightly?", "La cintura también me queda media pulgada suelta; ¿puede ajustarla un poco?", "🪡✨", "take it in", "entallar / meter costura", "teɪk ɪt ɪn", "Pregunta si también puede ajustar media pulgada la cintura.", "Pinned at a slight break! How does the waistband feel when you button it?"),
            ("pick-up-friday-noon", "Since the wedding is on Saturday, will they be ready for pickup Friday at noon?", "Como la boda es el sábado, ¿estarán listos para recoger el viernes al mediodía?", "📅🕛", "wedding", "boda", "ˈwedɪŋ", "Pregunta si estarán listos para recoger el viernes al mediodía.", "Taking the back seam in half an inch is very easy—we'll keep the extra fabric inside."),
            ("blind-stitch-finish", "A blind-stitch finish without cuffs will look cleanest with this jacket.", "Un acabado de puntada invisible sin valenciana se verá más limpio con este saco.", "🧵👌", "blind-stitch", "puntada invisible", "blaɪnd stɪtʃ", "", ""),
            ("try-on-at-pickup", "Great, I'll try them on quickly when I pick them up on Friday.", "Genial, me los probaré rápido cuando pase a recogerlos el viernes.", "🪞✅", "try them on", "probármelos", "traɪ ðem ɑːn", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "B1", "optical-shop-glasses", "Repairing eyeglasses at an optical shop", "Reparar lentes en una óptica",
        "Pide a un óptico reemplazar el tornillo de la patilla de tus lentes y ajustar el puente nasal.",
        "optician", "customer", "A downtown optical boutique.",
        [
            ("hinge-screw-fell-out", "Hello! The tiny screw on the left arm of my glasses just fell out.", "¡Hola! El pequeño tornillo de la patilla izquierda de mis lentes se acaba de caer.", "👓🔩", "screw", "tornillo", "skruː", "Explica que se cayó el tornillo de la patilla izquierda de tus lentes.", "Oh dear, holding your glasses in two pieces! Let me take a look at the frame."),
            ("replace-and-tighten", "Do you have a replacement screw that fits this titanium hinge?", "¿Tienen un tornillo de repuesto que le quede a esta bisagra de titanio?", "🛠️👓", "hinge", "bisagra de la montura", "hɪndʒ", "Pregunta si tienen un tornillo de repuesto para esa bisagra.", "The threads on the hinge are completely fine—it just needs a new 1.4-millimeter screw."),
            ("sliding-down-my-nose", "They've also been sliding down my nose lately; could you adjust the nose pads?", "Últimamente también se me resbalan por la nariz; ¿podría ajustar las plaquetas?", "👃🔧", "nose pads", "plaquetas nasales", "noʊz pædz", "Pide que ajusten las plaquetas porque se te resbalan.", "I've put a new lock-screw in both sides so the right one doesn't loosen either."),
            ("ultrasonic-lens-clean", "Thank you! How much do I owe you for the repair and cleaning?", "¡Gracias! ¿Cuánto le debo por la reparación y la limpieza?", "✨💳", "owe", "deber (pago)", "oʊ", "Pregunta cuánto debes por la reparación y el ajuste.", "I warmed the temple tips and adjusted the pads, plus ran them through our ultrasonic cleaner."),
            ("microfiber-cloth-spray", "I'll buy a bottle of anti-fog lens spray and a microfiber cloth.", "Compraré un frasco de spray antiempañante y un paño de microfibra.", "🧴🧼", "anti-fog", "antiempañante", "ˈænti fɑːɡ", "", ""),
            ("fit-snugly-now", "They sit level and fit snugly behind my ears now—thank you!", "Ahora quedan nivelados y ajustan perfecto detrás de las orejas; ¡gracias!", "😊👌", "snugly", "cómodamente ajustados", "ˈsnʌɡli", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "B1", "airbnb-host-check-in", "Coordinating vacation rental check-in", "Coordinar llegada a departamento vacacional",
        "Llama al anfitrión de tu alojamiento para confirmar el código de la cerradura digital y el estacionamiento.",
        "property host", "guest", "Outside a townhouse vacation rental upon arrival.",
        [
            ("arrived-at-front-gate", "Hi! We just pulled up in front of the townhouse; how do we unlock the keypad?", "¡Hola! Acabamos de llegar frente a la casa; ¿cómo abrimos el teclado numérico?", "🏡🔢", "keypad", "teclado numérico de acceso", "ˈkiːpæd", "Avisa que ya llegaron y pregunta cómo usar el teclado numérico.", "Welcome to Seattle! Glad you made it safely. Are you at the front door?"),
            ("press-pound-after-code", "Do I press the hash key before or after entering the four-digit pin?", "¿Presiono la tecla de gato antes o después de ingresar el código de cuatro dígitos?", "#️⃣🔓", "four-digit", "de cuatro dígitos", "fɔːr ˈdɪdʒɪt", "Pregunta si se presiona el signo de número antes o después del código.", "Wake the screen with your palm, type 4829, and press the checkmark at the bottom right."),
            ("driveway-parking-spot", "Should we park in the driveway on the left or on the street with a permit?", "¿Estacionamos en la entrada izquierda o en la calle con permiso?", "🚗🅿️", "driveway", "entrada para auto / cochera", "ˈdraɪvweɪ", "Pregunta dónde deben estacionar el auto.", "Awesome, I just heard the smart lock click open!"),
            ("thermostat-and-recycling", "Where is the heating thermostat, and which bin outside is for recycling?", "¿Dónde está el termostato de calefacción y qué contenedor es para reciclaje?", "🌡️♻️", "bin", "contenedor / bote", "bɪn", "Pregunta dónde está el termostato y cuál es el bote de reciclaje.", "Park right in the left driveway spot—it's reserved exclusively for your unit."),
            ("checkout-instructions-binder", "We see the welcome binder on the kitchen island with the Wi-Fi QR code.", "Ya vimos la carpeta de bienvenida en la barra de la cocina con el código QR del wifi.", "📖📶", "binder", "carpeta informativa", "ˈbaɪndər", "", ""),
            ("message-if-anything-needed", "The apartment is spotless—thank you for the local coffee beans!", "El departamento está impecable; ¡gracias por el café local!", "☕🌟", "spotless", "impecable / reluciente", "ˈspɑːtləs", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "B1", "tax-free-shopping-form", "Requesting a VAT tax-free refund form", "Solicitar formulario libre de impuestos (Tax Free)",
        "Solicita el formulario de devolución de IVA al comprar un abrigo en una tienda departamental.",
        "customer service clerk", "international shopper", "Tax-free desk on the top floor of a department store.",
        [
            ("qualify-for-vat-refund", "Hi, I'm visiting from outside the EU; does this coat purchase qualify for a VAT refund?", "Hola, visito desde fuera de la Unión Europea; ¿esta compra de abrigo califica para devolución de IVA?", "🧥🛂", "qualify", "calificar / cumplir requisitos", "ˈkwɑːlɪfaɪ", "Pregunta si la compra de tu abrigo califica para devolución de IVA.", "Good afternoon! Welcome to the International Visitor Desk. May I see your store receipts?"),
            ("original-passport-ready", "Here is my original passport along with the receipt from the third floor.", "Aquí está mi pasaporte original junto con el recibo del tercer piso.", "🪪🧾", "receipt", "recibo de compra", "rɪˈsiːt", "Muestra tu pasaporte original y el recibo de compra.", "Yes, any same-day purchase over a hundred euros qualifies! Do you have your passport?"),
            ("refund-back-to-card", "Could you set the refund to go straight back to my Visa card?", "¿Podría configurar el reembolso para que regrese directo a mi tarjeta Visa?", "💳🔄", "straight back", "directamente de vuelta", "streɪt bæk", "Pide que el reembolso se acredite directamente a tu tarjeta Visa.", "I've entered your passport details. Do you want a cash refund at the airport or back to your card?"),
            ("scan-at-airport-kiosk", "Do I scan this barcode at the customs kiosk before checking my suitcase?", "¿Escaneo este código de barras en el quiosco de aduana antes de documentar mi maleta?", "🛫🔍", "kiosk", "quiosco digital", "ˈkiːɑːsk", "Pregunta si debes validar el formulario en aduana antes de documentar la maleta.", "Card refunds have zero handling fee! Here is your printed Tax-Free form in the envelope."),
            ("keep-tags-attached", "I'll keep the coat unworn with the tags attached in my luggage until customs.", "Mantendré el abrigo sin usar y con etiquetas en mi maleta hasta pasar por aduana.", "🏷️🧳", "unworn", "sin usar / nuevo", "ˌʌnˈwɔːrn", "", ""),
            ("five-business-days-credit", "Thanks for explaining the steps so clearly!", "¡Gracias por explicar los pasos con tanta claridad!", "🙏✅", "steps", "pasos", "steps", "", ""),
        ],
    ),
    # B2 (4 new)
    (
        "hotel-and-shopping", "B2", "disputing-minibar-charge", "Disputing erroneous hotel checkout charges", "Aclarar cargos erróneos al hacer checkout",
        "Revisa el estado de cuenta al salir del hotel y pide eliminar cargos de minibar y gimnasio que no consumiste.",
        "front desk supervisor", "departing guest", "Hotel reception desk during morning checkout.",
        [
            ("reviewing-folio-statement", "Good morning. I'm checking out of Room 612, and I noticed two erroneous charges on my folio.", "Buenos días. Estoy entregando la habitación 612 y noté dos cargos erróneos en mi estado de cuenta.", "🧾🏨", "erroneous", "erróneos / equivocados", "ɪˈroʊniəs", "Indica que entregas la habitación 612 y notaste dos cargos erróneos en la factura.", "Good morning! I emailed your preliminary folio for Room 612. Did everything look okay?"),
            ("didnt-touch-minibar", "We never opened the minibar sensor tray—we only placed our own water bottles on top.", "Nunca abrimos la bandeja con sensor del minibar; solo pusimos nuestras botellas de agua encima.", "🍾🚫", "sensor tray", "bandeja con sensor automático", "ˈsensər treɪ", "Explica que nunca consumieron del minibar, solo apoyaron botellas de agua.", "Which line items on the statement look incorrect to you?"),
            ("resort-fee-waived-tier", "Also, the daily spa access fee should be waived under our loyalty tier booking.", "Además, el cargo diario de spa debería estar exento según nuestra reserva de categoría fidelidad.", "🏅✨", "waived", "exento / condonado", "weɪvd", "Recuerda que el cargo diario de spa está exento por tu nivel de fidelidad.", "Ah, those optical weight sensors trigger if anything rests on the tray! I'll void the $42 minibar charge."),
            ("reprint-zero-balance", "Could you rerun the final charge and print an updated invoice for my expense report?", "¿Podría procesar el cargo corregido e imprimir la factura actualizada para mi reporte de gastos?", "🖨️💼", "expense report", "reporte de gastos", "ɪkˈspens rɪˈpɔːrt", "Pide imprimir la factura corregida para tu reporte de gastos laborales.", "You're completely right—Platinum bookings include complimentary spa access. I've removed both items."),
            ("hold-bags-until-two", "May we leave our two bags with the bell desk until our 2:00 PM airport transfer?", "¿Podemos dejar dos maletas en custodia hasta nuestro traslado de las 2:00 PM?", "🧳🕑", "bell desk", "mostrador de botones / consigna", "bel desk", "", ""),
            ("wonderful-stay-overall", "Aside from that billing hiccup, we had a wonderful stay—thank you!", "Fuera de ese detalle en la cuenta, tuvimos una estancia maravillosa; ¡gracias!", "🌟🤝", "hiccup", "pequeño contratiempo", "ˈhɪkʌp", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "B2", "custom-jewelry-engraving", "Ordering a custom engraved watch", "Encargar un grabado personalizado en relojería",
        "Elige una tipografía cursiva para grabar la tapa trasera de un reloj de regalo y verifica la fecha de entrega.",
        "watchmaker & jeweler", "buyer", "A boutique watch and jewelry shop.",
        [
            ("engrave-case-back", "I'd like to purchase this automatic dress watch and have a dedication engraved on the case back.", "Quisiera comprar este reloj automático de vestir y grabar una dedicatoria en la tapa trasera.", "⌚✒️", "dedication", "dedicatoria", "ˌdedɪˈkeɪʃən", "Di que quieres comprar el reloj automático y grabar una dedicatoria atrás.", "Welcome! This stainless-steel automatic has a solid polished case back—ideal for engraving."),
            ("italic-serif-typeface", "Between block capitals and italic script, which typeface reads more legibly at this scale?", "Entre mayúsculas de molde y letra cursiva, ¿qué tipografía se lee mejor a esta escala?", "🔤🔍", "legibly", "de forma legible", "ˈledʒəbli", "Pregunta qué tipografía se lee mejor a ese tamaño.", "We do diamond-tip engraving in-house. What inscription and font style did you have in mind?"),
            ("double-check-spelling", "Let's double-check the spelling and Roman numerals on the proof sheet before you start.", "Revisemos dos veces la ortografía y los números romanos en la hoja de prueba antes de empezar.", "📝✅", "proof sheet", "hoja de prueba de diseño", "pruːf ʃiːt", "Pide revisar dos veces la ortografía y los números romanos en la prueba.", "Our classic italic serif looks super crisp and timeless for initials and a date."),
            ("remove-two-bracelet-links", "Could you also remove two links from the bracelet and include the spare pins in the box?", "¿Podría también quitar dos eslabones del brazalete y guardar los pasadores en la caja?", "🔗📦", "links", "eslabones de correa metálica", "lɪŋks", "Pide ajustar dos eslabones de la correa y guardar los sobrantes en la caja.", "Here is the digital mockup on screen—please verify every character."),
            ("international-warranty-card", "Will the five-year international movement warranty still apply after case-back engraving?", "¿La garantía internacional de cinco años sigue vigente tras grabar la tapa?", "📜🛡️", "movement", "maquinaria / movimiento del reloj", "ˈmuːvmənt", "", ""),
            ("gift-wrap-with-ribbon", "It's for my father's retirement on Friday—gift wrapping would be fantastic.", "Es para la jubilación de mi padre el viernes; envolverlo para regalo sería fantástico.", "🎁🎉", "retirement", "jubilación", "rɪˈtaɪərmənt", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "B2", "furniture-delivery-window", "Coordinating a freight elevator delivery", "Coordinar entrega de muebles y elevador de carga",
        "Reprograma una entrega de sofá para que coincida con la reserva del elevador de carga de tu edificio.",
        "logistics coordinator", "apartment resident", "Calling the furniture store's delivery dispatch desk.",
        [
            ("freight-elevator-window", "Hi, my building only allows furniture deliveries between 9:00 AM and noon when the freight elevator is padded.", "Hola, mi edificio solo permite mudanzas y muebles entre las 9:00 AM y el mediodía con el elevador de carga protegido.", "🛋️🛗", "freight elevator", "elevador de carga / montacargas", "freɪt ˈelɪveɪtər", "Explica que tu edificio solo permite entregas de 9:00 AM a 12:00 PM por el elevador de carga.", "Delivery Dispatch, hello! I see your sectional sofa is scheduled for Thursday afternoon."),
            ("switch-to-morning-route", "Could you move our stop to the first morning window on Friday so the crew isn't turned away?", "¿Podría pasar nuestra entrega al primer turno matutino del viernes para que no rechacen al camión?", "🚚🕘", "turned away", "rechazados en puerta", "tɜːrnd əˈweɪ", "Pide cambiar la entrega al primer turno matutino del viernes.", "Good catch! Afternoon trucks wouldn't be allowed past your concierge desk."),
            ("white-glove-assembly", "Our order includes white-glove assembly and haul-away of all the cardboard packaging.", "Nuestro pedido incluye armado completo y retiro de todo el cartón de embalaje.", "🧤📦", "white-glove", "servicio completo con instalación", "waɪt ɡlʌv", "Confirma que el pedido incluye armado y retiro del cartón.", "I can lock you into Slot 1 on Friday between 9:00 and 10:30 AM."),
            ("certificate-of-insurance", "Could you email your carrier's certificate of insurance to our property manager today?", "¿Podría enviar hoy por correo la póliza de seguro del transportista al administrador del edificio?", "📧🏢", "certificate of insurance", "póliza de responsabilidad civil", "sərˈtɪfɪkət əv ɪnˈʃʊrəns", "Pide enviar la póliza de seguro del transportista a la administración del edificio.", "Yes, our two-person team will bolt the sectional together and take every scrap of packing material."),
            ("measure-doorway-clearance", "The hallway doorway is thirty-four inches wide, so the sofa legs unscrew easily.", "La puerta del pasillo mide treinta y cuatro pulgadas, así que las patas se desenroscan fácil.", "📐🚪", "clearance", "espacio libre de paso", "ˈklɪrəns", "", ""),
            ("call-thirty-min-out", "Please ask the driver to call me thirty minutes before arrival.", "Por favor pida al conductor llamarme treinta minutos antes de llegar.", "📞🚛", "arrival", "llegada", "əˈraɪvəl", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "B2", "vintage-camera-appraisal", "Inspecting a vintage film camera", "Inspeccionar una cámara clásica antes de comprar",
        "Revisa velocidades de obturación, limpieza del lente y fotómetro de una cámara analógica en una tienda especializada.",
        "camera shop specialist", "photographer", "A specialist vintage camera store.",
        [
            ("check-slow-shutter-speeds", "Do the slow shutter speeds—especially one-eighth and one-quarter second—fire without sticking?", "¿Las velocidades lentas de obturación —especialmente un octavo y un cuarto— disparan sin trabarse?", "📷⚙️", "shutter speeds", "velocidades de obturación", "ˈʃʌtər spiːdz", "Pregunta si las velocidades lentas de obturación disparan sin trabarse.", "Here is the 1978 mechanical SLR you called about. Go ahead and cock the lever!"),
            ("hold-lens-to-light", "When I hold the 50mm lens up to the light, the glass looks free of haze or fungus.", "Cuando pongo el lente de 50 mm a contraluz, el cristal se ve libre de neblina u hongos.", "🔍💡", "haze", "neblina interna en el cristal", "heɪz", "Verifica el lente a contraluz para comprobar que no tenga hongos ni neblina.", "Our technician just cla'd the shutter mechanism last month—every speed is dead-on."),
            ("light-seals-and-meter", "Have the foam light seals around the film door been replaced recently?", "¿Se han reemplazado recientemente los sellos de espuma contra luz en la tapa del rollo?", "🎞️🛠️", "light seals", "sellos de espuma contra filtración de luz", "laɪt siːlz", "Pregunta si cambiaron los sellos de espuma de la tapa del rollo.", "The optics are pristine, and the aperture blades snap back with zero oil."),
            ("bundle-with-leather-strap", "If I take the camera body and two prime lenses, could you throw in the leather strap and a UV filter?", "Si me llevo el cuerpo y dos lentes fijos, ¿podría incluir la correa de cuero y un filtro UV?", "🤝🎒", "throw in", "incluir sin costo adicional", "θroʊ ɪn", "Propón que incluyan la correa de cuero y un filtro UV al comprar el equipo.", "Yes, new foam seals and a fresh silver-oxide battery for the light meter were installed Tuesday."),
            ("ninety-day-shop-warranty", "Knowing it comes with a ninety-day mechanical shop warranty gives me total peace of mind.", "Saber que incluye garantía mecánica de noventa días me da total tranquilidad.", "🛡️✅", "peace of mind", "tranquilidad", "piːs əv maɪnd", "", ""),
            ("grab-three-rolls-film", "Let's add three rolls of 400-speed color film so I can shoot a test roll today!", "Agreguemos tres rollos de película a color ISO 400 para hacer una prueba hoy mismo.", "🎞️☀️", "test roll", "rollo de prueba", "test roʊl", "", ""),
        ],
    ),
    # C1 (4 new)
    (
        "hotel-and-shopping", "C1", "boutique-wholesale-order", "Negotiating a wholesale showroom order", "Negociar pedido mayorista en showroom",
        "Negocia cantidades mínimas por color, exclusividad territorial y pago a 60 días con un proveedor de moda.",
        "showroom sales director", "boutique buyer", "Private showroom appointment during fashion week.",
        [
            ("lower-moq-per-colorway", "Since we're testing this knitwear line in our flagship store, could we lower the MOQ to twelve units per colorway?", "Como estamos probando esta línea de tejido en nuestra tienda principal, ¿podríamos bajar el mínimo a doce unidades por color?", "🧶📋", "colorway", "combinación de color", "ˈkʌlərweɪ", "Propón reducir el pedido mínimo a doce unidades por color para probar la línea.", "Welcome to the showroom! Normally our wholesale minimum is twenty-four pieces per colorway."),
            ("neighborhood-exclusivity", "We'd commit to the full autumn capsule if you grant us six-block boutique exclusivity.", "Nos comprometeríamos con toda la cápsula de otoño si nos otorgan exclusividad en un radio de seis cuadras.", "🏪🤝", "capsule", "colección cápsula", "ˈkæpsjuːl", "Pide exclusividad zonal de seis cuadras a cambio de comprar toda la colección.", "If you order across four styles in the autumn capsule, we can approve twelve units per color."),
            ("net-sixty-payment-terms", "Can we structure payment as thirty percent upon order confirmation and net-sixty after delivery?", "¿Podemos estructurar el pago con treinta por ciento al confirmar y el resto a sesenta días tras la entrega?", "🏦📅", "net-sixty", "pago a 60 días", "net ˈsɪksti", "Propón pagar 30% al confirmar y el saldo a 60 días de la entrega.", "None of our existing stockists are in your district, so we can write territorial exclusivity into the order."),
            ("late-shipment-discount", "Let's include a clause specifying a ten-percent discount if shipments slip past September first.", "Incluyamos una cláusula de diez por ciento de descuento si el envío se retrasa después del primero de septiembre.", "📦⏱️", "slip past", "retrasarse más allá de", "slɪp pæst", "Solicita una cláusula de descuento si el despacho se retrasa después de septiembre.", "With two trade references, our finance team can approve 30% deposit and net-60 on the balance."),
            ("duty-paid-incoterms", "Shipping under DDP Incoterms keeps our landed unit cost predictable.", "Enviar bajo modalidad DDP mantiene predecible nuestro costo unitario puesto en tienda.", "🚢🧮", "landed cost", "costo total puesto en destino", "ˈlændɪd kɔːst", "", ""),
            ("sign-line-sheet-today", "Send the amended line sheet and we'll countersign the purchase order this afternoon.", "Envíe la hoja de pedido actualizada y firmaremos la orden de compra esta tarde.", "✍️📄", "purchase order", "orden de compra", "ˈpɜːrtʃəs ˈɔːrdər", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "C1", "home-inspection-walkthrough", "Reviewing a property inspection report", "Revisar informe técnico de inspección de vivienda",
        "Recorre una casa con el inspector técnico evaluando el estado del techo, el tablero eléctrico y el drenaje.",
        "licensed home inspector", "homebuyer", "Walkthrough inspection of a 1930s brick house before closing.",
        [
            ("flashing-around-chimney", "Did the thermal camera pick up any active moisture intrusion around the chimney flashing?", "¿La cámara térmica detectó alguna filtración activa de humedad alrededor de la junta de la chimenea?", "🏠🔍", "flashing", "tapajuntas metálico del techo", "ˈflæʃɪŋ", "Pregunta si la cámara térmica detectó humedad en la junta de la chimenea.", "I've just come down from the attic and roof. Overall, the structural framing is rock-solid."),
            ("upgrade-breaker-panel", "Since the electrical panel is only a hundred amps, we'll need to upgrade to two hundred amps for an EV charger.", "Como el tablero eléctrico es de solo cien amperios, necesitaremos ampliarlo a doscientos para cargador de auto eléctrico.", "⚡🧰", "breaker panel", "tablero de interruptores eléctricos", "ˈbreɪkər ˈpænəl", "Señala que deberán ampliar el tablero eléctrico a 200 amperios.", "The chimney flashing was resealed recently—bone dry on the infrared scan."),
            ("seller-repair-credit", "Rather than having the seller do a rushed patch job, we'll request a five-thousand-dollar closing credit.", "En vez de que el vendedor haga una reparación apresurada, pediremos un crédito de cinco mil dólares al cierre.", "📑💵", "closing credit", "descuento a favor del comprador al escriturar", "ˈkloʊzɪŋ ˈkredɪt", "Explica que pedirán un crédito al cierre en lugar de reparaciones apresuradas.", "The panel upgrade and adding GFCI outlets in the garage will run about four thousand dollars."),
            ("sewer-scope-clear", "Did the fiber-optic sewer scope confirm the main line to the street is free of tree-root intrusion?", "¿La cámara de fibra óptica en el drenaje confirmó que la tubería principal está libre de raíces?", "📹🚰", "sewer scope", "inspección con cámara del drenaje", "ˈsuːər skoʊp", "Pregunta si la inspección con cámara del drenaje descartó raíces de árboles.", "Requesting a closing credit is always smarter so you can hire your own licensed electrician."),
            ("hvac-heat-exchanger", "Knowing the furnace heat exchanger still has ten years of serviceable life is a huge relief.", "Saber que el intercambiador de calor de la calefacción tiene diez años de vida útil es un gran alivio.", "🌡️✅", "serviceable life", "vida útil operativa", "ˈsɜːrvɪsəbəl laɪf", "", ""),
            ("pdf-report-by-tomorrow", "Once you upload the annotated PDF report tonight, we'll submit our inspection addendum.", "En cuanto suba el informe en PDF esta noche, presentaremos nuestro anexo de inspección.", "💻📋", "addendum", "anexo contractual", "əˈdendəm", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "C1", "art-gallery-provenance", "Acquiring a painting at an art gallery", "Consultar procedencia y conservación en galería",
        "Conversa con el director de una galería sobre procedencia de una obra, cristal antirreflejo y transporte asegurado.",
        "gallery director", "art collector", "Private viewing room at a contemporary art gallery.",
        [
            ("exhibition-provenance", "Could you share the full provenance and exhibition history for this oil-on-linen piece?", "¿Podría compartir la procedencia completa y el historial de exposiciones de este óleo sobre lino?", "🖼️📜", "provenance", "procedencia / historial de propiedad", "ˈprɑːvənəns", "Pide revisar la procedencia completa y el historial de exposiciones de la obra.", "This 2019 canvas is one of the artist's most sought-after coastal studies."),
            ("museum-grade-uv-glazing", "If we hang it in a sunlit foyer, would you recommend framing it behind museum-grade UV acrylic?", "Si lo colgamos en un vestíbulo iluminado, ¿recomendaría enmarcarlo con acrílico UV de grado museístico?", "☀️🛡️", "museum-grade", "de calidad de museo", "mjuːˈziːəm ɡreɪd", "Pregunta cómo proteger la obra de la luz solar en el vestíbulo.", "It comes directly from the estate collection and was exhibited at the Venice Biennale."),
            ("condition-report-craquelure", "The impasto brushwork is vibrant, and I see zero surface craquelure under raking light.", "La pincelada de empaste es vibrante y no veo ninguna grieta superficial bajo luz rasante.", "🎨🔦", "impasto", "empaste (capa gruesa de pintura)", "ɪmˈpæstoʊ", "Comenta el excelente estado del empaste bajo luz rasante.", "For an oil painting, we'll apply a breathable conservation varnish and recommend indirect LED spots."),
            ("fine-art-crate-shipping", "Can your registrars arrange climate-controlled fine-art shipping and wall installation?", "¿Puede su equipo gestionar el transporte climatizado de obras de arte y la instalación en pared?", "📦🚚", "registrars", "encargados de registro y conservación", "ˈredʒɪstrɑːrz", "Pregunta si la galería coordina el transporte climatizado y el montaje.", "Our conservator signed the clean condition report this morning."),
            ("certificate-of-authenticity", "Please include the signed certificate of authenticity and archival invoice for our insurer.", "Por favor incluya el certificado de autenticidad firmado y la factura para nuestra aseguradora.", "✍️📑", "authenticity", "autenticidad", "ˌɔːθenˈtɪsəti", "", ""),
            ("place-red-dot-reserve", "Let's place a formal hold on the work while our bank processes the wire.", "Pongamos una reserva formal sobre la obra mientras nuestro banco procesa la transferencia.", "🔴🤝", "formal hold", "reserva formal de compra", "ˈfɔːrməl hoʊld", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "C1", "hotel-conference-block", "Negotiating a corporate hotel room block", "Negociar bloque corporativo de habitaciones",
        "Negocia con el director de ventas de un hotel la cláusula de reducción (attrition), salas de trabajo y ascensos VIP.",
        "hotel sales director", "summit producer", "Negotiating a 50-room hotel contract for an annual leadership summit.",
        [
            ("twenty-percent-attrition", "Could we increase the allowable room-block attrition from ten percent to twenty percent until thirty days out?", "¿Podríamos ampliar el margen permitido de reducción del bloque del diez al veinte por ciento hasta treinta días antes?", "🏨📊", "attrition", "reducción permitida de habitaciones sin penalización", "əˈtrɪʃən", "Pide ampliar al 20% el margen de ajuste de habitaciones sin penalización.", "We're delighted to host your fifty executives in October. Did you review the room-block draft?"),
            ("waive-breakout-room-rental", "If our banquet food-and-beverage spend exceeds twenty thousand dollars, will you waive the breakout room rental?", "Si nuestro consumo de banquetes supera los veinte mil dólares, ¿eximirán el alquiler de las salas de trabajo?", "🍽️🏛️", "breakout room", "sala para sesiones paralelas", "ˈbreɪkaʊt ruːm", "Propón eximir el costo de las salas de trabajo si el banquete supera los $20,000.", "We can grant 20% cumulative attrition up to thirty days prior to arrival."),
            ("complimentary-suite-upgrades", "We'd also ask for three complimentary suite upgrades for our keynote speakers and board chair.", "También solicitaríamos tres ascensos gratuitos a suite para nuestros conferencistas principales y presidenta del directorio.", "🛎️🌟", "complimentary", "sin costo / de cortesía", "ˌkɑːmplɪˈmentəri", "Solicita tres ascensos a suite sin costo para los conferencistas principales.", "Yes, hitting the $20,000 catering tier waves all meeting-space rental fees."),
            ("dedicated-gigabit-vlan", "Can your IT team provision a dedicated symmetrical gigabit VLAN for our livestream keynote?", "¿Puede su equipo de TI habilitar una red gigabit dedicada para la transmisión en vivo de la conferencia?", "🌐📡", "provision", "habilitar / aprovisionar", "prəˈvɪʒən", "Pregunta si pueden habilitar una red de internet dedicada para la transmisión.", "I'll add three Junior Suite upgrades at the group rate plus VIP airport transfers."),
            ("master-account-billing", "Route room-and-tax to the corporate master account, while guests settle their own incidentals.", "Cargue habitación e impuestos a la cuenta maestra corporativa, y que cada huésped pague sus gastos extras.", "💳📋", "incidentals", "gastos incidentales / extras de habitación", "ˌɪnsɪˈdentəlz", "", ""),
            ("execute-addendum-today", "With those four revisions in the addendum, we're ready to sign today.", "Con esas cuatro revisiones en el anexo, estamos listos para firmar hoy mismo.", "✍️✅", "revisions", "modificaciones / ajustes", "rɪˈvɪʒənz", "", ""),
        ],
    ),
    # C2 (4 new)
    (
        "hotel-and-shopping", "C2", "auction-house-bidding", "Registering for a fine-art auction", "Registrar puja telefónica en casa de subastas",
        "Coordina en una casa de subastas la garantía bancaria, el informe de conservación ultravioleta y la puja telefónica.",
        "senior auction specialist", "private collector", "Evening sale preview room at an international auction house.",
        [
            ("register-telephone-paddle", "I'd like to register an absentee ceiling and a dedicated telephone line for Lot 42 in tomorrow's evening sale.", "Quisiera registrar un tope en ausencia y una línea telefónica dedicada para el Lote 42 en la subasta de mañana.", "🔨📞", "absentee ceiling", "puja máxima de respaldo en ausencia", "ˌæbsənˈtiː ˈsiːlɪŋ", "Solicita registrar una línea telefónica y un tope de respaldo para el Lote 42.", "Welcome to the preview! Lot 42 has drawn strong institutional interest this week."),
            ("uv-fluorescence-report", "Did the conservation lab's ultraviolet examination reveal any inpainting along the lower margin?", "¿El examen con luz ultravioleta del laboratorio reveló algún retoque pictórico en el margen inferior?", "🔬🖼️", "inpainting", "retoque / reintegración pictórica", "ˈɪnpeɪntɪŋ", "Pregunta si el análisis ultravioleta reveló algún retoque en el margen inferior.", "Our head restorer examined the panel out of its frame yesterday afternoon."),
            ("buyers-premium-calculation", "Factoring in the tiered buyer's premium and artist's resale royalty, what is the all-in hammer equivalent?", "Considerando la comisión escalonada de la casa y el derecho de seguimiento del artista, ¿cuál es el costo total sobre el martillo?", "🧮🏛️", "buyer's premium", "comisión del comprador en subasta", "ˈbaɪərz ˈpriːmiəm", "Pide confirmar el cálculo total incluyendo la comisión de subasta y regalías.", "Under UV fluorescence, the varnish is untouched and completely free of restoration."),
            ("escrow-wire-verification", "Our private banker has already transmitted the bank reference letter to clear our bidding limit.", "Nuestro banquero privado ya transmitió la carta de referencia bancaria para autorizar nuestro límite de puja.", "🏦✅", "bidding limit", "límite autorizado de puja", "ˈbɪdɪŋ ˈlɪmɪt", "Confirma que su banco ya envió la referencia para liberar el límite de puja.", "At a hammer price of two hundred thousand, the all-in total with premium is two hundred fifty-two thousand."),
            ("bonded-freeport-transfer", "Should we prevail on the lot, we'll transfer it directly to bonded storage in Geneva.", "En caso de adjudicarnos el lote, lo trasladaremos directamente al depósito franco en Ginebra.", "🔐✈️", "prevail", "resultar adjudicatario / ganar la puja", "prɪˈveɪl", "", ""),
            ("call-three-lots-prior", "Please have your desk specialist ring my mobile three lots prior to Lot 42.", "Por favor pida a su especialista llamarme tres lotes antes del Lote 42.", "📲🔔", "three lots prior", "tres lotes antes", "θriː lɑːts ˈpraɪər", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "C2", "heritage-restoration-architect", "Restoring a listed heritage property", "Discutir normativas de patrimonio arquitectónico",
        "Debate con el arquitecto conservador la restauración de fachadas de piedra caliza y aislamiento oculto en un edificio histórico.",
        "conservation architect", "property steward", "On-site architectural review inside a Grade-II listed townhouse.",
        [
            ("preserve-ashlar-facade", "The heritage commission requires us to repoint the limestone ashlar facade using breathable lime mortar.", "La comisión de patrimonio nos exige rejuntar la fachada de sillería caliza usando mortero de cal transpirable.", "🏛️🧱", "breathable", "transpirable / permeable al vapor", "ˈbriːðəbəl", "Recuerda la exigencia de usar mortero de cal transpirable en la fachada histórica.", "We've received the conservation officer's preliminary notes on the townhouse exterior."),
            ("slim-profile-double-glazing", "Can we mill bespoke timber sashes that house slim-profile vacuum glazing without altering the sightlines?", "¿Podemos fabricar bastidores de madera a medida con doble acristalamiento al vacío sin alterar los perfiles visuales?", "🪟📐", "sightlines", "perfiles visuales / líneas arquitectónicas", "ˈsaɪtlaɪnz", "Pregunta si pueden instalar vidrio al vacío ultrafino manteniendo la carpintería original.", "Yes—Portland cement would trap moisture and spall the nineteenth-century stone."),
            ("conceal-heat-pump-ducting", "Running the heat-pump conduits beneath the suspended floor voids preserves the ornate plaster cornices.", "Pasar los conductos de climatización bajo el entrepiso preserva intactas las cornisas históricas de yeso.", "🛠️🏛️", "cornices", "cornisas ornamentales", "ˈkɔːrnɪsɪz", "Propón ocultar los conductos bajo el piso para proteger las cornisas de yeso.", "Vacuum-insulated glass is only six millimeters thick, so the historic glazing bars remain identical."),
            ("structural-underpinning-signoff", "Once the structural engineer signs off on the basement underpinning, we can lodge the listed-building consent.", "En cuanto el ingeniero estructural firme la cimentación del sótano, presentaremos la solicitud de licencia patrimonial.", "📋✍️", "underpinning", "recalce de cimentación", "ˈʌndərpɪnɪŋ", "Indica que presentarán el expediente en cuanto se firme el cálculo estructural.", "Routing through the floor voids is brilliant—zero impact on the lath-and-plaster ceilings."),
            ("salvage-original-parquet", "Every original oak parquet herringbone batten will be numbered, lifted, and relaid over acoustic matting.", "Cada tablilla original del parqué de roble en espiga será numerada, levantada y recolocada sobre base acústica.", "🪵🔢", "salvage", "recuperar / restaurar piezas originales", "ˈsælvɪdʒ", "", ""),
            ("sympathetic-modernization", "It's a textbook example of sympathetic modernization honoring historical fabric.", "Es un ejemplo modelo de modernización respetuosa con el tejido histórico.", "🌟🏛️", "sympathetic", "respetuosa / armónica con el entorno", "ˌsɪmpəˈθetɪk", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "C2", "bespoke-savile-row-fitting", "Baste fitting at a bespoke tailor", "Ajuste de hilván en sastrería a medida",
        "Evalúa con un maestro cortador la caída del lienzo de lana fría, la altura de sisa y el giro de solapa.",
        "master cutter", "client", "Fitting room at a traditional Savile Row tailoring house.",
        [
            ("floating-horsehair-canvas", "The floating horsehair canvas gives the chest a remarkably natural three-dimensional roll.", "El entretelado flotante de crin le da al pecho una caída tridimensional notablemente natural.", "🧥🪡", "floating canvas", "entretela flotante cosida a mano", "ˈfloʊtɪŋ ˈkænvəs", "Elogia la caída tridimensional que aporta la entretela flotante cosida a mano.", "Welcome to your first baste fitting! Let's see how the chalk-stripe worsted drapes on your shoulders."),
            ("high-armhole-mobility", "Cutting a high armhole with extra fullness across the shoulder blades allows effortless reach without collar gap.", "Cortar una sisa alta con holgura en los omóplatos permite mover los brazos sin que el cuello se separe.", "📐👔", "collar gap", "separación indeseada del cuello del saco", "ˈkɑːlər ɡæp", "Destaca cómo la sisa alta permite movilidad sin despegar el cuello de la camisa.", "Raise your arms forward as if holding a steering wheel—notice how the collar hugs your neck?"),
            ("pitch-of-right-sleeve", "Because my right shoulder drops a quarter inch, let's rotate the right sleeve pitch slightly forward.", "Como mi hombro derecho cae un cuarto de pulgada, rotemos ligeramente hacia adelante el aplomo de la manga derecha.", "🪞📌", "sleeve pitch", "ángulo de aplomo de la manga", "sliːv pɪtʃ", "Pide ajustar el ángulo de la manga derecha para compensar la caída natural del hombro.", "Good eye—there is a faint diagonal crease at the back of the right scye."),
            ("working-surgeon-cuffs", "For the forward fitting next month, we'll finish the four working horn buttons on the cuffs.", "Para la siguiente prueba el próximo mes, terminaremos los cuatro ojales practicables con botones de asta en los puños.", "🔘✨", "working cuffs", "ojales de puño practicables (funcionales)", "ˈwɜːrkɪŋ kʌfs", "Confirma el acabado con cuatro botones de asta funcionales en los puños.", "I've re-chalked the right sleeve head and let out the waist suppression by three millimeters."),
            ("high-twist-fresco-wool", "This high-twist fresco weave breathes exceptionally well in humid summer climates.", "Este tejido fresco de alta torsión transpira excepcionalmente bien en climas húmedos de verano.", "🌬️🧵", "high-twist", "hilo de alta torsión resistente a arrugas", "haɪ twɪst", "", ""),
            ("impeccable-craftsmanship", "We'll reconvene in four weeks for the forward baste—thank you, Master Cutter.", "Nos reuniremos en cuatro semanas para la segunda prueba; muchas gracias, maestro.", "🤝🎩", "reconvene", "volver a reunirse", "ˌriːkənˈviːn", "", ""),
        ],
    ),
    (
        "hotel-and-shopping", "C2", "commercial-flagship-lease", "Structuring a flagship retail lease", "Estructurar contrato de local comercial insignia",
        "Negocia una estructura híbrida de renta base más porcentaje sobre ventas y periodo de carencia por obra.",
        "commercial REIT director", "retail expansion VP", "Boardroom negotiation for a prime corner retail flagship.",
        [
            ("base-plus-turnover-rent", "We propose a hybrid structure combining a conservative base rent with a six-percent turnover overage above the breakpoint.", "Proponemos una estructura híbrida que combine una renta base moderada con un seis por ciento sobre ventas por encima del umbral.", "🏢📈", "turnover rent", "renta variable sobre facturación", "ˈtɜːrnoʊvər rent", "Propón una renta híbrida con base fija más porcentaje sobre ventas.", "For this corner flagship on Bond Street, our asking rent is a flat nine hundred thousand per annum."),
            ("nine-month-fit-out-rent-free", "Given the extensive structural fit-out required, we need a nine-month rent-free abatement period.", "Dada la extensa adecuación arquitectónica requerida, necesitamos un periodo de gracia de nueve meses sin pago de renta.", "🏗️⏳", "abatement", "exención temporal / periodo de carencia", "əˈbeɪtmənt", "Solicita nueve meses de carencia de renta para ejecutar la obra de adecuación.", "A turnover component aligns our incentives, provided the natural breakpoint is set at twelve million."),
            ("exclude-ecommerce-returns", "The gross-sales definition must explicitly exclude online orders returned in-store and employee purchases.", "La definición de ventas brutas debe excluir explícitamente las devoluciones de compras web en tienda y ventas a empleados.", "💻🧾", "explicitly exclude", "excluir de forma expresa", "ɪkˈsplɪsɪtli ɪkˈskluːd", "Pide que el cálculo de ventas excluya devoluciones de comercio electrónico en tienda.", "We can grant six months rent-free plus a landlord capital contribution toward HVAC and facade glazing."),
            ("right-of-first-refusal-adjacent", "We also want a right of first refusal on the adjacent mezzanine should the current tenant vacate.", "También queremos derecho de preferencia sobre el entrepiso contiguo en caso de que el inquilino actual desocupe.", "🔑📐", "right of first refusal", "derecho de tanteo / primera opción", "raɪt əv fɜːrst rɪˈfjuːzəl", "Solicita derecho de preferencia sobre el local contiguo si llega a desocuparse.", "Excluding web returns from audited store turnover is completely reasonable."),
            ("cap-service-charge-escalation", "Annual common-area service-charge escalations must be capped at the consumer price index.", "Los incrementos anuales de mantenimiento de áreas comunes deben toparse a la inflación.", "📊🛡️", "capped at", "topado / limitado a", "kæpt æt", "", ""),
            ("instruct-solicitors-heads-of-terms", "Let's sign these Heads of Terms so our respective counsels can engross the lease.", "Firmemos esta carta de intención para que nuestros abogados redacten el contrato definitivo.", "✍️⚖️", "Heads of Terms", "acuerdo marco de términos principales", "hedz əv tɜːrmz", "", ""),
        ],
    ),
    # ==================== 4. SOCIAL-AND-SMALLTALK ====================
    # A1 (4 new)
    (
        "social-and-smalltalk", "A1", "introducing-a-friend", "Introducing two friends", "Presentar a dos amigos",
        "Presenta a tu amiga Ana a tu compañero de trabajo Tom en una cafetería y conversen sobre de dónde son.",
        "colleague (Tom)", "friend", "Running into a coworker at a neighborhood cafe.",
        [
            ("meet-my-friend-ana", "Hi Tom! I want you to meet my good friend, Ana.", "¡Hola Tom! Quiero que conozcas a mi buena amiga, Ana.", "👋😊", "meet", "conocer a alguien", "miːt", "Preséntale a tu amiga Ana a tu compañero Tom.", "Hey! Good to see you here at the cafe!"),
            ("she-is-from-lima", "Ana is visiting from Lima for the week.", "Ana está de visita desde Lima por esta semana.", "✈️🌎", "visiting", "visitando / de visita", "ˈvɪzɪtɪŋ", "Cuéntale que Ana está de visita desde Lima por esta semana.", "Hi Ana, nice to meet you! Where are you from?"),
            ("work-in-same-office", "Tom and I work together in the design office.", "Tom y yo trabajamos juntos en la oficina de diseño.", "💼🎨", "together", "juntos", "təˈɡeðər", "Explica que Tom y tú trabajan juntos en la oficina de diseño.", "Lima is a wonderful city! Is this your first time here?"),
            ("sit-at-our-table", "Would you like to sit and have coffee with us?", "¿Te gustaría sentarte y tomar un café con nosotros?", "☕🪑", "with us", "con nosotros", "wɪð ʌs", "Invita a Tom a sentarse a tomar café con ustedes.", "Yes, we work on the same team!"),
            ("love-the-sunny-weather", "You brought the warm sunny weather with you!", "¡Trajiste el clima cálido y soleado contigo!", "☀️😄", "weather", "clima / tiempo", "ˈweðər", "", ""),
            ("see-you-on-monday", "Great chatting with you, Tom! See you on Monday.", "¡Qué gusto charlar contigo, Tom! Nos vemos el lunes.", "🙌📅", "Monday", "lunes", "ˈmʌndeɪ", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "A1", "talking-about-pets", "Chatting about dogs at the park", "Hablar de mascotas en el parque",
        "Conversa con otro dueño de perro en el parque sobre el nombre, la edad y qué le gusta jugar a tu mascota.",
        "dog owner", "park visitor", "A sunny dog park in the afternoon.",
        [
            ("cute-golden-dog", "Your dog is so cute and friendly! What is his name?", "¡Tu perro es muy lindo y amigable! ¿Cómo se llama?", "🐕💛", "cute", "lindo / tierno", "kjuːt", "Elogia a su perro y pregunta cómo se llama.", "Hi! Our dogs are having fun running together!"),
            ("my-dog-is-max", "My dog's name is Toby, and he is two years old.", "Mi perro se llama Toby y tiene dos años.", "🐾🎂", "years old", "años de edad", "jɪrz oʊld", "Dile que tu perro se llama Toby y tiene dos años.", "Thank you! His name is Bruno. What about yours?"),
            ("loves-the-tennis-ball", "He loves chasing the yellow tennis ball all day.", "Le encanta perseguir la pelota de tenis amarilla todo el día.", "🎾🐕", "chasing", "perseguir / correr tras", "ˈtʃeɪsɪŋ", "Cuenta que a tu perro le encanta perseguir la pelota de tenis.", "Toby has so much energy! Does he like playing fetch?"),
            ("come-here-every-morning", "We walk in this park every morning at eight.", "Caminamos en este parque todas las mañanas a las ocho.", "🌳🕗", "every morning", "todas las mañanas", "ˈevri ˈmɔːrnɪŋ", "Dile que caminan en este parque todas las mañanas a las ocho.", "Bruno loves tennis balls too! Do you live near the park?"),
            ("give-him-a-treat", "May I give Bruno a small dog biscuit?", "¿Puedo darle a Bruno una pequeña galleta para perro?", "🦴😊", "biscuit", "galleta / premio", "ˈbɪskɪt", "", ""),
            ("time-for-water", "Look, they are thirsty now—let's go to the water bowl!", "Mira, ya tienen sed; ¡vamos al bebedero de agua!", "💧🐕", "thirsty", "sedientos / con sed", "ˈθɜːrsti", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "A1", "weekend-weather-chat", "Small talk in the elevator", "Charlar sobre el clima en el ascensor",
        "Rompe el hielo en el ascensor hablando del buen clima del fin de semana y qué piso presionas.",
        "neighbor", "resident", "Apartment building elevator on Friday afternoon.",
        [
            ("going-up-floor-five", "Good afternoon! Which floor are you going to?", "¡Buenas tardes! ¿A qué piso vas?", "🛗🔢", "floor", "piso / planta", "flɔːr", "Saluda y pregunta a qué piso va.", "Good afternoon! Thanks for holding the elevator door!"),
            ("press-button-six", "I will press floor six for you right here.", "Presionaré el piso seis por ti justo aquí.", "👆6️⃣", "press", "presionar / pulsar", "pres", "Di que presionarás el botón del piso seis por él.", "Floor six, please! My hands are full with groceries."),
            ("beautiful-sunny-friday", "The weather is so warm and sunny today!", "¡El clima está muy cálido y soleado hoy!", "☀️🌤️", "sunny", "soleado", "ˈsʌni", "Comenta lo cálido y soleado que está el día.", "Thank you! Isn't it a lovely Friday outside?"),
            ("walk-by-the-beach", "Yes! I am going to the beach with my family tomorrow.", "¡Sí! Mañana voy a la playa con mi familia.", "🏖️👨‍👩‍👧", "beach", "playa", "biːtʃ", "Cuéntale que mañana irás a la playa con tu familia.", "It's supposed to stay warm all weekend! Any fun plans?"),
            ("no-rain-until-monday", "I am glad there is no rain this weekend.", "Me alegra que no haya lluvia este fin de semana.", "🌈😊", "rain", "lluvia", "reɪn", "", ""),
            ("have-a-great-weekend", "Here is your floor. Have a great weekend!", "Aquí está tu piso. ¡Que tengas un excelente fin de semana!", "👋🌟", "weekend", "fin de semana", "ˈwiːkend", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "A1", "birthday-wishes", "Wishing a friend happy birthday", "Felicitar a un amigo en su cumpleaños",
        "Felicita a una compañera de clase por su cumpleaños, entrégale una tarjeta y unos chocolates.",
        "classmate (Emma)", "friend", "Before English class starts in the morning.",
        [
            ("happy-birthday-emma", "Happy birthday, Emma! I hope you have a wonderful day.", "¡Feliz cumpleaños, Emma! Espero que tengas un día maravilloso.", "🎂🎈", "wonderful", "maravilloso", "ˈwʌndərfəl", "Desea un feliz cumpleaños a Emma.", "Good morning! Look, I brought cupcakes for the class today!"),
            ("card-from-all-of-us", "This birthday card is from all of us in the class.", "Esta tarjeta de cumpleaños es de parte de todos en la clase.", "💌✍️", "all of us", "todos nosotros", "ɔːl əv ʌs", "Entrégale la tarjeta firmada por toda la clase.", "Aw, thank you so much! What is that envelope in your hand?"),
            ("box-of-dark-chocolates", "And we got you a small box of dark chocolates!", "¡Y te compramos una pequeña caja de chocolates oscuros!", "🍫🎁", "dark chocolates", "chocolates amargos / oscuros", "dɑːrk ˈtʃɑːkləts", "Dale la caja de chocolates oscuros.", "Everyone signed the card—that is so sweet of you all!"),
            ("dinner-with-family", "Are you having a special dinner tonight with your family?", "¿Vas a tener una cena especial esta noche con tu familia?", "🍽️🥂", "special", "especial", "ˈspeʃəl", "Pregunta si tendrá una cena especial esta noche.", "Dark chocolate is my favorite! Thank you!"),
            ("try-a-vanilla-cupcake", "Thank you for the vanilla cupcake—it looks delicious!", "¡Gracias por el cupcake de vainilla; se ve delicioso!", "🧁😋", "delicious", "delicioso", "dɪˈlɪʃəs", "", ""),
            ("sing-happy-birthday", "Let's sing Happy Birthday together before the lesson!", "¡Cantemos el Feliz Cumpleaños juntos antes de la lección!", "🎶🎉", "sing", "cantar", "sɪŋ", "", ""),
        ],
    ),
    # A2 (4 new)
    (
        "social-and-smalltalk", "A2", "movie-night-choice", "Choosing a movie at the cinema", "Elegir una película en el cine",
        "Decide con un amigo entre una comedia o una película de ciencia ficción y compren palomitas.",
        "friend (Liam)", "moviegoer", "Cinema lobby looking at the showtime screens.",
        [
            ("sci-fi-or-comedy", "Do you feel like watching the new sci-fi adventure or the comedy?", "¿Te apetece ver la nueva aventura de ciencia ficción o la comedia?", "🎬🍿", "feel like", "tener ganas de / apetecer", "fiːl laɪk", "Pregunta si prefiere ver ciencia ficción o la comedia.", "We made it to the cinema with fifteen minutes to spare! What should we watch?"),
            ("starts-at-seven-thirty", "The sci-fi movie starts at seven thirty in the IMAX theater.", "La película de ciencia ficción empieza a las siete y media en la sala IMAX.", "🕢📽️", "starts", "empieza", "stɑːrts", "Propón la película de ciencia ficción de las 7:30 en sala IMAX.", "I read great reviews about the space adventure! What time does it start?"),
            ("seats-in-middle-row", "Let's pick two seats in the middle row so we have a great view.", "Elijamos dos asientos en la fila del medio para tener una buena vista.", "💺👀", "middle row", "fila central", "ˈmɪdəl roʊ", "Sugiere elegir dos asientos en la fila central.", "7:30 is perfect! Which seats on the screen should we choose?"),
            ("share-large-popcorn", "Want to share a large bucket of buttered popcorn and two sodas?", "¿Quieres compartir una cubeta grande de palomitas con mantequilla y dos refrescos?", "🍿🥤", "share", "compartir", "ʃer", "Propón compartir unas palomitas grandes con mantequilla.", "Row G seats 10 and 11 are right in the center!"),
            ("put-phones-on-silent", "Don't forget to put our phones on silent before the trailers start.", "No olvidemos poner los teléfonos en silencio antes de que empiecen los avances.", "📵🎞️", "silent", "modo silencio", "ˈsaɪlənt", "", ""),
            ("grab-tickets-at-kiosk", "I'll get the popcorn while you print the tickets at the kiosk!", "¡Yo compro las palomitas mientras tú imprimes los boletos en el quiosco!", "🎟️🙌", "while", "mientras", "waɪl", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "A2", "gym-workout-buddy", "Chatting at a fitness class", "Conversar en una clase del gimnasio",
        "Saluda a un compañero en la clase de ciclismo bajo techo, comparte pesas y comenten el entrenamiento.",
        "gym member", "fitness class participant", "Studio room before an evening spin and strength class.",
        [
            ("first-time-in-class", "Hi! Is this spot next to you taken? It's my first time in this class.", "¡Hola! ¿Está ocupado este lugar junto a ti? Es mi primera vez en esta clase.", "🏋️‍♀️👋", "taken", "ocupado (un lugar)", "ˈteɪkən", "Pregunta si el lugar está libre y comenta que es tu primera vez en la clase.", "Hey there! Welcome to the 6:00 PM strength and cardio session!"),
            ("which-dumbbells-to-use", "Which weight dumbbells do you recommend for the shoulder exercises?", "¿Qué peso de mancuernas recomiendas para los ejercicios de hombros?", "💪🏋️", "dumbbells", "mancuernas / pesas", "ˈdʌmbelz", "Pregunta qué peso de mancuernas recomienda para hombros.", "Not taken at all, grab that mat! The instructor, Maya, is super encouraging."),
            ("great-upbeat-playlist", "I love the upbeat music playlist she uses for the warm-up!", "¡Me encanta la lista de música animada que usa para el calentamiento!", "🎵🔥", "upbeat", "animada / con energía", "ˈʌpbiːt", "Comenta que te gusta mucho la música del calentamiento.", "Start with the ten-pound dumbbells—we do a lot of repetitions!"),
            ("grab-smoothie-after", "That was a great workout! Do you come to the Tuesday and Thursday sessions?", "¡Fue un gran entrenamiento! ¿Vienes a las sesiones de martes y jueves?", "🥤💦", "workout", "entrenamiento / rutina", "ˈwɜːrkaʊt", "Dile que fue un gran entrenamiento y pregunta si viene martes y jueves.", "Whew, we survived the final plank challenge! How do you feel?"),
            ("wipe-down-the-mat", "Here are the disinfectant wipes to clean our mats and weights.", "Aquí están las toallitas desinfectantes para limpiar nuestros tapetes y pesas.", "🧻✨", "mat", "tapete de ejercicio / colchoneta", "mæt", "", ""),
            ("see-you-on-thursday", "Awesome, I'll book my spot for Thursday—see you then!", "Genial, reservaré mi lugar para el jueves; ¡nos vemos entonces!", "📅🙌", "book my spot", "reservar mi lugar", "bʊk maɪ spɑːt", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "A2", "book-club-recommendation", "Recommending a book to a friend", "Recomendar un libro a un amigo",
        "Recomienda una novela de misterio que no pudiste soltar el fin de semana y ofrece prestársela.",
        "friend (Nora)", "reader", "Having tea on a rainy Sunday afternoon.",
        [
            ("finished-great-novel", "I just finished an amazing mystery novel last night—I couldn't put it down!", "Anoche terminé una novela de misterio increíble; ¡no podía soltarla!", "📖🌙", "couldn't put it down", "no pude dejar de leerlo", "ˈkʊdənt pʊt ɪt daʊn", "Cuenta que anoche terminaste una novela de misterio que no podías soltar.", "I'm looking for a new book to read on my train commute. Read anything good lately?"),
            ("set-on-scottish-island", "It's set on a tiny island in Scotland during a winter storm.", "Está ambientada en una pequeña isla de Escocia durante una tormenta de invierno.", "🏝️🌨️", "set on", "ambientada en", "set ɑːn", "Explica que está ambientada en una isla de Escocia durante una tormenta.", "Ooh, I love a good mystery! What is the story about, without spoilers?"),
            ("plot-twist-at-the-end", "The characters feel very real, and I never guessed the twist at the end.", "Los personajes se sienten muy reales y nunca adiviné el giro del final.", "🕵️‍♀️✨", "twist", "giro inesperado en la trama", "twɪst", "Comenta que los personajes son muy reales y el final sorprende.", "A stormy Scottish island sounds like the perfect atmosphere!"),
            ("lend-you-my-copy", "I have the paperback in my bag—you can borrow my copy right now!", "Traigo la edición de bolsillo en mi bolso; ¡te puedo prestar mi ejemplar ahora mismo!", "👜📚", "borrow", "tomar prestado", "ˈbɑːroʊ", "Ofrécele prestarle tu ejemplar que llevas en el bolso.", "You've convinced me! I'll look for it at the bookstore tomorrow."),
            ("short-chapters-fast-read", "The chapters are short, so it's super easy to read on the train.", "Los capítulos son cortos, así que es muy fácil de leer en el tren.", "🚆📖", "chapters", "capítulos", "ˈtʃæptərz", "", ""),
            ("tell-me-who-you-suspect", "Text me when you reach Chapter 10 and tell me who you suspect!", "¡Escríbeme cuando llegues al capítulo 10 y dime de quién sospechas!", "📱🕵️", "suspect", "sospechar", "səˈspekt", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "A2", "picnic-in-the-park", "Organizing a Sunday park picnic", "Organizar un picnic en el parque",
        "Coordina con tus amigos quién lleva la manta, los sándwiches y el altavoz Bluetooth para el domingo.",
        "friend (Sam)", "organizer", "Planning a Sunday afternoon picnic by the lake.",
        [
            ("meet-by-lake-fountain", "Let's meet by the big fountain near the lake at one o'clock on Sunday.", "Encontrémonos junto a la fuente grande cerca del lago el domingo a la una.", "⛲🌳", "fountain", "fuente de agua", "ˈfaʊntən", "Propón encontrarse junto a la fuente del lago el domingo a la una.", "The forecast for Sunday is 24 degrees and sunny! Where should we set up our picnic?"),
            ("bring-waterproof-blanket", "I'll bring a large waterproof picnic blanket and paper plates.", "Yo llevaré una manta impermeable grande para picnic y platos de cartón.", "🧺🍽️", "waterproof", "impermeable", "ˈwɔːtərpruːf", "Ofrece llevar una manta impermeable grande y platos.", "1:00 PM by the lake fountain is easy for everyone to find. What should I bring?"),
            ("fresh-caprese-sandwiches", "Could you bring a cooler with cold lemonade and some fruit?", "¿Podrías traer una hielera con limonada fría y algo de fruta?", "🧊🍓", "cooler", "hielera / nevera portátil", "ˈkuːlər", "Pídele llevar una hielera con limonada fría y fruta.", "I can make fresh baguette sandwiches! What about drinks and snacks?"),
            ("bluetooth-speaker-frisbee", "I also packed a Frisbee and a small speaker for background music.", "También guardé un frisbi y una bocina pequeña para poner música de fondo.", "🥏🎶", "background music", "música de fondo", "ˈbækɡraʊnd ˈmjuːzɪk", "Di que llevarás un frisbi y una bocina pequeña para música.", "Consider it done—watermelon, grapes, and homemade lemonade!"),
            ("sit-under-oak-trees", "There is plenty of shade under the big oak trees by the water.", "Hay mucha sombra bajo los grandes robles junto al agua.", "🌳☀️", "shade", "sombra", "ʃeɪd", "", ""),
            ("bring-sunscreen-and-hat", "Remind everyone in the group chat to bring sunglasses and sunscreen!", "¡Recuérdales a todos en el chat grupal traer lentes de sol y bloqueador!", "🕶️🧴", "remind", "recordar a alguien", "rɪˈmaɪnd", "", ""),
        ],
    ),
    # B1 (4 new)
    (
        "social-and-smalltalk", "B1", "apologizing-for-lateness", "Apologizing for running late", "Disculparse por llegar tarde debido al tráfico",
        "Llama a tu amigo para avisar que el metro se detuvo, calcula tu hora de llegada y pídele que vaya pidiendo.",
        "friend waiting at restaurant", "caller", "Calling from the subway station when running 15 minutes late.",
        [
            ("so-sorry-running-late", "Hey! I'm so sorry, I'm running about fifteen minutes behind schedule.", "¡Hola! Lo siento muchísimo, voy con unos quince minutos de retraso.", "⌚🙏", "running behind", "ir con retraso / llegar tarde", "ˈrʌnɪŋ bɪˈhaɪnd", "Disculpate y avisa que vas con unos quince minutos de retraso.", "Hey! I just got to the restaurant and got us a table. How close are you?"),
            ("train-held-in-tunnel", "Our subway train was held in the tunnel because of a signal problem.", "Nuestro tren del metro se detuvo en el túnel por un fallo de señalización.", "🚇🚦", "signal problem", "fallo de señalización", "ˈsɪɡnəl ˈprɑːbləm", "Explica que el tren se detuvo en el túnel por un problema de señales.", "No worries! Everything okay with the transit?"),
            ("please-order-starter", "Please go ahead and order a drink and a starter—don't wait for me!", "Por favor ve pidiendo una bebida y una entrada; ¡no me esperes!", "🥂🥗", "go ahead", "adelante / procede sin esperar", "ɡoʊ əˈhed", "Pídele que vaya ordenando una bebida y una entrada sin esperarte.", "Ugh, the green line always does that at rush hour!"),
            ("walking-fast-two-blocks", "I just exited the station and I'm walking fast—I'll be there in four minutes!", "Acabo de salir de la estación y voy caminando rápido; ¡llego en cuatro minutos!", "🏃‍♂️🏙️", "exited", "salí de", "ˈeksɪtɪd", "Avisa que ya saliste de la estación y llegas en cuatro minutos.", "I ordered some olives and sparkling water for the table. Take your time!"),
            ("first-round-on-me", "Thanks for being so patient—the first round of drinks is definitely on me!", "Gracias por ser tan paciente; ¡la primera ronda de bebidas corre por mi cuenta!", "🍹🤝", "round", "ronda de bebidas", "raʊnd", "", ""),
            ("wave-from-the-door", "I'm walking through the front door right now—I see you waving!", "Estoy entrando por la puerta principal ahora mismo; ¡ya te veo saludando!", "👋😊", "waving", "saludando con la mano", "ˈweɪvɪŋ", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "B1", "housewarming-gift", "Attending a friend's housewarming party", "Ir a una fiesta de inauguración de casa",
        "Felicita a tus amigos por su nuevo departamento, entrégales una planta para la sala y elogia la luz natural.",
        "new homeowner", "guest", "Arriving at a friend's bright new apartment for a housewarming.",
        [
            ("congrats-on-new-place", "Congratulations on the new apartment! We're so excited to see it.", "¡Felicidades por el nuevo departamento! Qué ilusión conocerlo.", "🏡🎉", "excited", "emocionados / ilusionados", "ɪkˈsaɪtɪd", "Felicita a tus amigos por su nuevo departamento.", "Come on in! Welcome to our new place—we finally unpacked the last box yesterday!"),
            ("low-maintenance-plant", "We brought you this potted olive tree for the balcony—it's super easy to care for.", "Les trajimos este pequeño olivo en maceta para el balcón; es muy fácil de cuidar.", "🪴🌿", "care for", "cuidar", "ker fɔːr", "Entrégales la planta en maceta y di que es muy fácil de cuidar.", "Aw, you didn't have to bring a gift! What a beautiful plant!"),
            ("tons-of-natural-light", "These floor-to-ceiling windows let in so much natural light!", "¡Estas ventanas de piso a techo dejan entrar muchísima luz natural!", "🪟☀️", "let in", "dejar entrar", "let ɪn", "Elogia la cantidad de luz natural que entra por los ventanales.", "It'll look amazing on the sunny corner of our balcony. Let me give you the grand tour!"),
            ("open-kitchen-layout", "I love how the open kitchen flows right into the living room.", "Me encanta cómo la cocina abierta se conecta directo con la sala.", "🍳🛋️", "flows into", "se integra / fluye hacia", "floʊz ˈɪntuː", "Comenta lo bien que se integra la cocina abierta con la sala.", "The natural light was the main reason we fell in love with this unit."),
            ("cozy-reading-nook", "That bookshelf alcove by the window makes the perfect reading nook.", "Ese rincón con librero junto a la ventana es perfecto para leer.", "📚🪑", "nook", "rincón acogedor", "nʊk", "", ""),
            ("toast-to-new-memories", "Here's to many happy years and great dinners in your new home!", "¡Por muchos años felices y grandes cenas en su nuevo hogar!", "🥂🏠", "here's to", "brindemos por", "hɪrz tuː", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "B1", "joining-running-club", "Joining a Saturday running club", "Integrarse a un club de corredores local",
        "Preséntate en un grupo de corredores de fin de semana, pregunta el ritmo por kilómetro y la ruta.",
        "run club pacer", "new runner", "Saturday morning warmup stretch by the river promenade.",
        [
            ("first-time-joining-group", "Morning! I saw your club on Instagram and decided to join for the first time today.", "¡Buenos días! Vi su club en Instagram y decidí unirme por primera vez hoy.", "👟🌅", "decided", "decidí", "dɪˈsaɪdɪd", "Saluda y cuenta que viste el club en Instagram y vienes por primera vez.", "Good morning and welcome! We're just starting our dynamic warm-up stretches."),
            ("pace-groups-five-k", "Do you split into different pace groups for the eight-kilometer loop?", "¿Se dividen en distintos grupos de ritmo para el circuito de ocho kilómetros?", "⏱️🏃‍♀️", "pace", "ritmo de carrera", "peɪs", "Pregunta si se dividen en distintos grupos de ritmo para el recorrido.", "So glad you came out! What distance and pace do you usually enjoy running?"),
            ("conversational-pace-group", "I'll stick with the five-thirty per kilometer group so I can chat along the way.", "Me uniré al grupo de cinco treinta por kilómetro para poder conversar en el camino.", "💬🏃", "stick with", "mantenerse con / ir en", "stɪk wɪð", "Elige el grupo de ritmo conversacional de 5:30 por kilómetro.", "Yes! We have a fast group, a 5:30 conversational pace group, and a run-walk group."),
            ("coffee-stop-after-run", "Does everyone really grab pastries and coffee together at the finish line?", "¿De verdad todos van por pan dulce y café juntos al llegar a la meta?", "🥐☕", "finish line", "línea de meta / final", "ˈfɪnɪʃ laɪn", "Pregunta por la tradición de tomar café juntos al terminar la carrera.", "I'm pacing the 5:30 group today! It's a flat loop along the river bridges."),
            ("bag-drop-in-van", "Can I leave my sweatshirt in the club's gear bag while we run?", "¿Puedo dejar mi sudadera en la bolsa del club mientras corremos?", "🧥🎒", "sweatshirt", "sudadera", "ˈswetʃɜːrt", "", ""),
            ("great-way-start-weekend", "Running with a group makes the kilometers fly by—see you next Saturday!", "Correr en grupo hace que los kilómetros pasen volando; ¡nos vemos el próximo sábado!", "🙌🏅", "fly by", "pasar volando (el tiempo)", "flaɪ baɪ", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "B1", "language-exchange-partner", "Setting up a language exchange", "Acordar dinámica de intercambio de idiomas",
        "Acuerda con tu compañero de intercambio hablar treinta minutos en español y treinta en inglés corrigiendo con confianza.",
        "language partner (Claire)", "learner", "First coffee meetup with a native English speaker learning Spanish.",
        [
            ("thirty-minutes-each-language", "How about we speak thirty minutes in Spanish first, and then thirty minutes in English?", "¿Qué te parece si hablamos treinta minutos en español primero y luego treinta en inglés?", "🗣️⏱️", "how about", "¿qué te parece si...?", "haʊ əˈbaʊt", "Propón hablar treinta minutos en español y luego treinta en inglés.", "It's so nice to finally meet in person! How would you like to structure our practice?"),
            ("set-a-phone-timer", "I'll set a gentle timer on my phone so neither language takes over the whole hour!", "Pondré un temporizador suave en mi teléfono para que ningún idioma acapare toda la hora.", "📱🔔", "takes over", "acaparar / dominar", "teɪks ˈoʊvər", "Sugiere poner un temporizador para dar el mismo tiempo a ambos idiomas.", "Splitting it fifty-fifty is super fair—otherwise I get lazy and switch back to English!"),
            ("correct-my-pronunciation", "Please feel free to correct my pronunciation or suggest a more natural phrase anytime.", "Por favor siéntete con total confianza de corregir mi pronunciación o sugerir una frase más natural.", "🎯💬", "anytime", "en cualquier momento", "ˈenitaɪm", "Pídele que corrija tu pronunciación o sugiera expresiones más naturales.", "How do you prefer to handle grammar or vocabulary corrections while we talk?"),
            ("write-down-new-idioms", "I brought a small notebook to jot down three new idioms from every session.", "Traje una libreta pequeña para anotar tres modismos nuevos en cada sesión.", "📓✍️", "jot down", "apuntar / anotar rápido", "dʒɑːt daʊn", "Muestra tu libreta donde anotarás tres expresiones nuevas cada semana.", "Same for me in Spanish! Tell me whenever a verb tense sounds unnatural."),
            ("pick-topic-for-next-week", "Next week we could talk about our favorite travel stories or movies.", "La próxima semana podríamos hablar de nuestras historias de viaje o películas favoritas.", "🌍🎬", "stories", "historias / anécdotas", "ˈstɔːriz", "", ""),
            ("same-cafe-next-wednesday", "This was so helpful and fun—same time and table next Wednesday?", "Esto fue muy útil y divertido; ¿misma hora y mesa el próximo miércoles?", "☕📅", "helpful", "útil / de gran ayuda", "ˈhelpfəl", "", ""),
        ],
    ),
    # B2 (4 new)
    (
        "social-and-smalltalk", "B2", "politely-declining-invitation", "Declining a destination wedding invite", "Declinar con tacto una invitación lejana",
        "Agradece de corazón la invitación a una boda en el extranjero, explica por qué no podrás viajar y organiza una cena para celebrar.",
        "engaged friend", "invited friend", "Phone call with a close friend getting married in Italy.",
        [
            ("touched-by-invitation", "We were so touched to receive your beautiful wedding invitation in the mail yesterday!", "¡Nos conmovió muchísimo recibir ayer por correo su hermosa invitación de boda!", "💌💍", "touched", "conmovidos / agradecidos de corazón", "tʌtʃt", "Expresa cuánto te emocionó recibir la invitación de boda.", "Hey! Did our Tuscany wedding save-the-date card arrive in the mail?"),
            ("prior-work-commitment", "Heartbreakingly, my sister's graduation falls on that exact weekend, so we won't be able to fly to Italy.", "Lamentablemente, la graduación de mi hermana cae ese mismo fin de semana, así que no podremos volar a Italia.", "🎓✈️", "falls on", "coincide en fecha con", "fɔːlz ɑːn", "Explica con cariño que coincide con la graduación de tu hermana y no podrán viajar.", "We'd love so much to have you two there celebrating with us in Florence!"),
            ("take-you-out-for-champagne", "We're gutted to miss it, so we insist on taking you both out for a celebratory champagne dinner before you leave!", "Nos da muchísima pena perdérnoslo, así que insistimos en invitarlos a cenar con champán antes de que viajen.", "🥂🍽️", "gutted", "muy apenados / tristes por perderse algo", "ˈɡʌtɪd", "Insiste en invitarlos a una cena de celebración con champán antes de su viaje.", "Oh, family graduation completely comes first—we totally understand!"),
            ("send-something-from-registry", "We've already picked out something special from your registry to toast to your new chapter.", "Ya elegimos algo especial de su mesa de regalos para brindar por esta nueva etapa.", "🎁✨", "registry", "lista / mesa de regalos de boda", "ˈredʒɪstri", "Menciona que ya eligieron un regalo especial de su lista de bodas.", "A dinner before we fly out in June sounds wonderful! Let's put it on the calendar."),
            ("cant-wait-to-see-photos", "Promise you'll send us photos from the vineyard ceremony!", "¡Prométanme que nos enviarán fotos de la ceremonia en el viñedo!", "📸🍇", "vineyard", "viñedo", "ˈvɪnjərd", "", ""),
            ("wishing-you-lifetime-joy", "We're wishing you both a lifetime of happiness and adventure!", "¡Les deseamos toda una vida de felicidad y aventuras juntos!", "❤️🌟", "lifetime", "toda una vida", "ˈlaɪftaɪm", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "B2", "resolving-roommate-chores", "Agreeing on shared apartment rules", "Acordar gastos y tareas con tu compañero de piso",
        "Conversa de forma constructiva con tu compañero de departamento para organizar la limpieza semanal y dividir recibos.",
        "flatmate (Jordan)", "roommate", "Chatting over coffee at the kitchen table on Sunday morning.",
        [
            ("clear-the-air-friendly", "Hey Jordan, got five minutes to chat about our kitchen routine so we keep the place feeling great?", "Hola Jordan, ¿tienes cinco minutos para charlar sobre nuestra rutina de cocina y mantener el depa impecable?", "🏠☕", "routine", "rutina / organización", "ruːˈtiːn", "Inicia la charla con buen ánimo para organizar la rutina de la cocina.", "Morning! Sure, grab a cup of coffee. What's on your mind?"),
            ("load-dishwasher-at-night", "Since we both cook in the evening, how about a rule that dishes go straight into the dishwasher before bed?", "Como ambos cocinamos de noche, ¿qué tal si acordamos meter los platos al lavavajillas antes de dormir?", "🍽️✨", "dishwasher", "lavavajillas", "ˈdɪʃwɔːʃər", "Propón que los platos entren directo al lavavajillas cada noche antes de dormir.", "Yeah, I know I left a couple of pans in the sink on Wednesday when I had a late deadline."),
            ("alternate-weekly-cleaning", "We could also alternate weeks for vacuuming and taking out the recycling—what do you think?", "También podríamos alternar semanas para aspirar y sacar el reciclaje; ¿qué opinas?", "🧹♻️", "alternate", "alternar / turnarse", "ˈɔːltərneɪt", "Sugiere turnarse cada semana para aspirar y sacar el reciclaje.", "Putting dishes straight into the dishwasher at night is super doable—I'm totally on board."),
            ("splitwise-for-utilities", "I set up a shared Splitwise group so we can log the electric bill and household supplies transparently.", "Creé un grupo compartido en Splitwise para registrar el recibo de luz y artículos de limpieza con transparencia.", "📱🧾", "supplies", "insumos / artículos del hogar", "səˈplaɪz", "Menciona el grupo en Splitwise para dividir recibos y compras del hogar.", "Alternating weeks on the fridge calendar makes it really clear whose turn it is."),
            ("heads-up-overnight-guests", "Giving each other a quick heads-up in the group chat before having weekend guests over works great too.", "Avisarnos por mensaje antes de recibir visitas de fin de semana también funciona genial.", "💬🙌", "heads-up", "aviso previo", "hedz ʌp", "", ""),
            ("glad-we-talked-openly", "Glad we can talk about this so openly—we make a great housemate team!", "Me alegra que podamos hablarlo con tanta confianza; ¡hacemos un gran equipo de casa!", "🤝😊", "openly", "abiertamente / con franqueza", "ˈoʊpənli", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "B2", "giving-wedding-toast", "Delivering a best-friend wedding toast", "Dar un brindis emotivo en una boda",
        "Pronuncia un brindis cálido y con humor en la boda de tus mejores amigos y pide a los invitados alzar sus copas.",
        "wedding guests & couple", "best friend giving toast", "Standing with a microphone at the head table during the wedding reception.",
        [
            ("for-those-who-dont-know", "Good evening, everyone! For those who haven't met me, I'm Marco, Leo's college roommate and partner in crime.", "¡Buenas noches a todos! Para quienes no me conocen, soy Marco, compañero de cuarto de Leo en la universidad.", "🎙️🥂", "partner in crime", "cómplice de aventuras / gran amigo", "ˈpɑːrtnər ɪn kraɪm", "Preséntate ante los invitados como el gran amigo de universidad de Leo.", "Ladies and gentlemen, please welcome Marco for our first toast of the evening!"),
            ("knew-from-first-date", "I knew Clara was the one when Leo actually showed up fifteen minutes early for their very first coffee date.", "Supe que Clara era la indicada cuando Leo llegó quince minutos temprano a su primera cita de café.", "☕😄", "the one", "la persona indicada / el amor de su vida", "ðə wʌn", "Cuenta con humor cómo supiste que Clara era la persona indicada desde la primera cita.", "(Laughter from the tables) Tell us how they first met!"),
            ("bring-out-the-best", "Jokes aside, the way you two ground each other and bring out the best in everyone around you is inspiring.", "Fuera de broma, la forma en que se complementan y sacan lo mejor de quienes los rodean es inspiradora.", "✨❤️", "bring out the best", "sacar lo mejor de alguien", "brɪŋ aʊt ðə best", "Destaca con emoción cómo ambos sacan lo mejor el uno del otro.", "(Smiles and applause from the couple at the head table)"),
            ("raise-your-glasses", "Everyone, please stand and raise your glasses to Clara and Leo—may your marriage be filled with laughter!", "Por favor pónganse de pie y alcen sus copas por Clara y Leo: ¡que su matrimonio esté lleno de risas!", "🥂🎉", "filled with", "lleno de / colmado de", "fɪld wɪð", "Invita a todos a ponerse de pie y alzar sus copas por los novios.", "Hear, hear! What is your wish for the newlyweds?"),
            ("always-have-a-couch", "Just remember I still claim permanent VIP rights to your guest sofa!", "¡Solo recuerden que conservo derecho VIP permanente en su sofá de visitas!", "🛋️😂", "claim", "reclamar en broma", "kleɪm", "", ""),
            ("to-the-happy-couple", "To Clara and Leo—salud and cheers!", "¡Por Clara y Leo: salud y felicidades!", "🥂🌟", "newlyweds", "recién casados", "ˈnuːliwedz", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "B2", "networking-mixer-followup", "Connecting at an industry mixer", "Conectar en un evento de networking",
        "Inicia una conversación natural tras una charla de diseño, intercambien LinkedIn y acuerden tomar un café.",
        "product designer", "conference attendee", "Evening rooftop networking reception after a tech & design summit.",
        [
            ("loved-your-panel-question", "Hi! I really enjoyed the question you asked during the accessibility panel earlier.", "¡Hola! Me gustó mucho la pregunta que hiciste hace rato durante el panel de accesibilidad.", "🎙️👏", "earlier", "hace rato / más temprano", "ˈɜːrliər", "Inicia la conversación comentando la buena pregunta que hizo en el panel.", "Oh, hi! Thank you—that panel on voice interfaces was super thought-provoking."),
            ("working-on-similar-challenge", "My team has been tackling a very similar onboarding challenge over the past quarter.", "Mi equipo ha estado abordando un reto de incorporación muy similar durante el último trimestre.", "🧩💡", "tackling", "abordando / resolviendo un reto", "ˈtæklɪŋ", "Comenta que tu equipo ha estado resolviendo un reto similar este trimestre.", "Are you working in product design or engineering yourself?"),
            ("swap-linkedin-qr", "I'd love to hear how your user testing went—shall we scan LinkedIn QR codes?", "Me encantaría saber cómo les fue en las pruebas de usuario; ¿escaneamos nuestros códigos QR de LinkedIn?", "📱🤝", "user testing", "pruebas con usuarios", "ˈjuːzər ˈtestɪŋ", "Propón intercambiar perfiles de LinkedIn para conversar sobre sus pruebas.", "No way! How did you approach simplifying the first-run screen?"),
            ("grab-coffee-next-week", "If you're in town on Tuesday, let's grab a coffee near the convention center and compare notes.", "Si sigues en la ciudad el martes, tomemos un café cerca del centro de convenciones e intercambiemos ideas.", "☕📅", "compare notes", "intercambiar experiencias / ideas", "kəmˈper noʊts", "Invítala a tomar un café el martes para intercambiar ideas.", "Connected on LinkedIn! Are you based here in the city or flying back tomorrow?"),
            ("introduce-to-colleague", "Before I head out, let me introduce you to our UX researcher, Priya.", "Antes de irme, déjame presentarte a nuestra investigadora de UX, Priya.", "👋👩‍💻", "head out", "retirarse / salir de un lugar", "hed aʊt", "", ""),
            ("shoot-you-a-message", "I'll shoot you a message tomorrow morning to lock in a time for Tuesday!", "¡Te escribo mañana temprano para confirmar la hora del martes!", "💬✅", "lock in", "confirmar / asegurar hora", "lɑːk ɪn", "", ""),
        ],
    ),
    # C1 (4 new)
    (
        "social-and-smalltalk", "C1", "moderating-book-discussion", "Moderating a literary book club", "Moderar un club de lectura literario",
        "Guía un debate sobre narradores poco fiables, simbolismo y estructura no lineal procurando que todos participen.",
        "book club member", "discussion moderator", "Evening literary circle in an independent bookstore.",
        [
            ("unreliable-narrator-device", "What fascinated me was how the author uses an unreliable narrator to make us question our own assumptions.", "Lo que me fascinó fue cómo la autora utiliza un narrador poco fiable para hacernos cuestionar nuestras suposiciones.", "📚🧐", "unreliable narrator", "narrador poco fiable", "ˌʌnrɪˈlaɪəbəl ˈnæreɪtər", "Abre el debate destacando el recurso del narrador poco fiable.", "Alright everyone, we've all finished the novel! What stood out to you about the protagonist's voice?"),
            ("nonlinear-flashbacks", "Do you feel the nonlinear flashbacks heightened the suspense, or did they fragment the emotional arc?", "¿Sienten que los saltos temporales aumentaron el suspenso o fragmentaron el arco emocional?", "⏳📖", "heightened", "intensificaron / aumentaron", "ˈhaɪtənd", "Pregunta al grupo si los saltos en el tiempo intensificaron el suspenso.", "I kept changing my mind about who was telling the truth in Part Two!"),
            ("ambiguous-final-chapter", "Rather than tying everything up neatly, the ambiguous ending forces the reader to sit with uncertainty.", "En lugar de atar todos los cabos, el final ambiguo obliga al lector a convivir con la incertidumbre.", "🌫️✨", "tying up neatly", "resolver todo de forma cerrada", "ˈtaɪɪŋ ʌp ˈniːtli", "Reflexiona sobre cómo el final abierto invita a convivir con la incertidumbre.", "The timeline shifts were dizzying at first, though that final chapter pulled the threads together."),
            ("hear-from-quiet-side", "Elena, you've been nodding thoughtfully—how did that closing metaphor land for you?", "Elena, has estado asintiendo pensativa; ¿cómo interpretaste esa metáfora final?", "🗣️🤝", "nodding", "asintiendo con la cabeza", "ˈnɑːdɪŋ", "Invita amablemente a participar a quien aún no ha tomado la palabra.", "Some of us loved the open ending, while others wanted a clear resolution!"),
            ("recurring-motif-water", "The recurring motif of rising tide water mirrors the family's unspoken secrets.", "El motivo recurrente de la marea refleja los secretos no dichos de la familia.", "🌊🔍", "motif", "motivo literario recurrente", "moʊˈtiːf", "", ""),
            ("vote-on-next-months-pick", "Before we wrap up, let's cast our votes for next month's biography shortlist.", "Antes de cerrar, votemos entre las biografías finalistas para el próximo mes.", "🗳️📅", "shortlist", "lista corta de finalistas", "ˈʃɔːrtlɪst", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "C1", "defusing-awkward-topic", "Gracefully pivoting a tense dinner topic", "Cambiar de tema con diplomacia en una cena",
        "Suaviza con humor y tacto una discusión acalorada en una cena, validando a ambos invitados y cambiando de tema.",
        "opinionated dinner guest", "diplomatic host", "Around a dinner party table when a political debate gets heated.",
        [
            ("passion-at-the-table", "It's clear you both care deeply about this issue—and we're definitely not solving municipal tax policy before dessert!", "Está claro que a ambos les importa mucho este tema, ¡y seguro no resolveremos la política fiscal antes del postre!", "🍷😊", "care deeply", "importar profundamente", "ker ˈdiːpli", "Reconoce con humor el entusiasmo de ambos para distender el ambiente.", "Well, I just think the city council's zoning plan is completely short-sighted!"),
            ("agree-to-disagree-gracefully", "Let's chalk that one up to a spirited 'agree to disagree' while the tiramisu is still chilled.", "Dejemos eso en un cordial 'acordemos disentir' mientras el tiramisú sigue frío.", "🍰🤝", "agree to disagree", "acordar disentir con respeto", "əˈɡriː tuː ˌdɪsəˈɡriː", "Invita a dejar el punto en un respetuoso 'acordemos disentir' para servir el postre.", "(Chuckles around the table) Fair enough, I might have gotten carried away on my soapbox!"),
            ("pivot-to-shared-passion", "Speaking of Italy, didn't you two both hike the Dolomites last autumn?", "Hablando de Italia, ¿no hicieron ambos senderismo en los Dolomitas el otoño pasado?", "🏔️🥾", "speaking of", "hablando de... (para cambiar de tema)", "ˈspiːkɪŋ əv", "Redirige la conversación hacia el viaje de senderismo que ambos hicieron en los Dolomitas.", "Thank you for rescuing us! That tiramisu looks incredible."),
            ("hear-about-mountain-huts", "Tell the table about those high-altitude refuges—we're planning a trip there in September!", "Cuéntenle a la mesa sobre esos refugios de montaña; ¡planeamos un viaje allá en septiembre!", "🏡🌄", "refuges", "refugios alpinos", "ˈrefjuːdʒɪz", "Pídeles que cuenten sobre los refugios de montaña para integrar a toda la mesa.", "Wait, you hiked the Alta Via 1 too? Which mountain hut was your favorite?"),
            ("refill-everyone-glasses", "Let me top up everyone's wine glasses while you compare trail routes.", "Déjenme rellenar las copas de todos mientras comparan rutas de montaña.", "🍷✨", "top up", "rellenar la copa", "tɑːp ʌp", "", ""),
            ("warmth-back-in-room", "Nothing brings a dinner table together quite like trading travel stories!", "Nada une tanto a una mesa como compartir historias de viaje.", "🌍❤️", "trading", "intercambiar (anécdotas)", "ˈtreɪdɪŋ", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "C1", "podcast-guest-banter", "Bantering as a culture podcast guest", "Conversar con agudeza en un pódcast cultural",
        "Conversa en un pódcast sobre el síndrome del impostor, la creatividad desconectada y los hábitos de atención.",
        "podcast host", "featured guest", "Recording studio with broadcast microphones and headphones.",
        [
            ("reclaiming-boredom", "We've optimized away every idle moment, yet productive boredom is where our best creative leaps happen.", "Hemos eliminado cada minuto libre, pero el aburrimiento productivo es donde surgen nuestros mejores saltos creativos.", "🎙️💡", "idle moment", "momento de ocio / sin estímulos", "ˈaɪdəl ˈmoʊmənt", "Reflexiona sobre cómo el aburrimiento productivo impulsa la creatividad.", "Welcome to the show! In your new essay, you argue that smartphones killed the daydream. Tell us more."),
            ("impostor-syndrome-signpost", "I've come to view impostor syndrome not as a flaw, but as a signpost that you're stretching beyond your comfort zone.", "He llegado a ver el síndrome del impostor no como un defecto, sino como señal de que estás saliendo de tu zona de confort.", "🧭🚀", "signpost", "señal indicadora", "ˈsaɪnpoʊst", "Replantea el síndrome del impostor como señal de crecimiento.", "That resonates with so many listeners. How do you handle self-doubt when starting a blank page?"),
            ("analog-morning-ritual", "Keeping the first hour of the morning strictly analog—just coffee and a fountain pen—protects deep focus.", "Mantener la primera hora de la mañana estrictamente analógica —solo café y pluma— protege la concentración profunda.", "☕✒️", "strictly analog", "100% libre de pantallas", "ˈstrɪktli ˈænəlɔːɡ", "Comparte tu ritual matutino sin pantallas para proteger la concentración.", "I love that reframe. What practical daily habit keeps your attention anchored?"),
            ("permission-to-write-bad-drafts", "Giving yourself permission to write a clumsy first draft takes the paralysis out of perfectionism.", "Darte permiso de escribir un primer borrador imperfecto elimina la parálisis del perfeccionismo.", "📝🙌", "clumsy", "torpe / imperfecto", "ˈklʌmzi", "Aconseja darse permiso de escribir un primer borrador imperfecto.", "Before we wrap up, what one piece of advice would you leave with aspiring creators?"),
            ("curiosity-over-certainty", "Leading with curiosity rather than performative certainty makes conversations infinitely richer.", "Guiarse por la curiosidad en vez de la certeza aparente hace las conversaciones mucho más ricas.", "🌱🗣️", "performative", "aparente / para la galería", "pərˈfɔːrmətɪv", "", ""),
            ("pleasure-being-on-show", "This hour flew by—thank you for such a thoughtful conversation!", "Esta hora se pasó volando; ¡gracias por una conversación tan profunda!", "🎧🌟", "thoughtful", "reflexiva / profunda", "ˈθɔːtfəl", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "C1", "mentoring-career-pivot", "Advising a friend on a career sabbatical", "Aconsejar a un amigo sobre un año sabático",
        "Escucha con empatía a un amigo agotado y ayúdale a estructurar una pausa sabática con propósito.",
        "close friend (Dani)", "supportive mentor", "Walking along the waterfront on a quiet Saturday morning.",
        [
            ("running-on-fumes", "Honestly, it sounds like you've been running on fumes for the past year—stepping back isn't quitting.", "Sinceramente, suena a que llevas un año al límite de tus fuerzas; tomar distancia no es rendirse.", "🌊🤝", "running on fumes", "al límite de energía / agotado", "ˈrʌnɪŋ ɑːn fjuːmz", "Valida su cansancio y recuérdale que hacer una pausa no es rendirse.", "I'm thinking of taking a six-month sabbatical, but part of me feels guilty stepping off the ladder."),
            ("intentional-sabbatical", "The key is framing the six months as an intentional sabbatical rather than an open-ended drift.", "La clave es plantear los seis meses como un sabático intencional y no como una deriva sin rumbo.", "🧭📅", "open-ended drift", "deriva sin rumbo definido", "ˈoʊpən ˈendɪd drɪft", "Aconseja estructurar los seis meses como un sabático con intención clara.", "How do I keep from feeling lost once the daily office structure disappears?"),
            ("financial-cushion-peace", "Since you've already built a twelve-month financial cushion, you've earned the breathing room to explore.", "Como ya construiste un colchón financiero de doce meses, te has ganado el respiro para explorar.", "🛡️🌱", "breathing room", "margen de respiro / tranquilidad", "ˈbriːðɪŋ ruːm", "Recuérdale que su colchón financiero le permite explorar con tranquilidad.", "I did save up a full year of living expenses specifically for this transition."),
            ("prototype-next-chapter", "Treat the second half of the break as a low-stakes lab to prototype what your next chapter looks like.", "Toma la segunda mitad de la pausa como un laboratorio sin presión para probar cómo será tu próxima etapa.", "🔬✨", "low-stakes", "de bajo riesgo / sin presión", "loʊ steɪks", "Sugiere usar la segunda mitad del sabático para experimentar su próximo paso.", "What should I focus on once I actually feel rested again?"),
            ("narrative-for-future-interviews", "Future employers respect candidates who take time to upskill and return with renewed clarity.", "Los futuros empleadores respetan a quienes toman tiempo para aprender y regresan con claridad renovada.", "💼🌟", "renewed clarity", "claridad renovada", "rɪˈnuːd ˈklærəti", "", ""),
            ("check-in-monthly-brunch", "Let's do a monthly brunch check-in so you have a sounding board along the way!", "Hagamos un brunch mensual para que tengas con quién contrastar ideas en el camino.", "🥞🙌", "sounding board", "interlocutor de confianza para rebotar ideas", "ˈsaʊndɪŋ bɔːrd", "", ""),
        ],
    ),
    # C2 (4 new)
    (
        "social-and-smalltalk", "C2", "philosophical-ethics-salon", "Debating moral luck and agency", "Debatir ética y responsabilidad en una tertulia",
        "Participa en una tertulia filosófica analizando el concepto de suerte moral de Bernard Williams y la meritocracia.",
        "philosophy professor", "salon participant", "An intimate evening humanities salon in a university library.",
        [
            ("moral-luck-paradox", "Bernard Williams's paradox of moral luck exposes how much of our ethical judgment hinges on outcomes beyond our control.", "La paradoja de la suerte moral de Bernard Williams expone cuánto de nuestro juicio ético depende de resultados fuera de nuestro control.", "⚖️📚", "hinges on", "depende fundamentalmente de", "ˈhɪndʒɪz ɑːn", "Introduce la paradoja de la suerte moral y cómo juzgamos según el resultado.", "Tonight's question is deceptively simple: should we judge actions solely by intent, or by their consequences?"),
            ("two-reckless-drivers", "Two equally negligent drivers deserve identical moral blame, even if only one happens to encounter a pedestrian.", "Dos conductores igualmente negligentes merecen idéntico reproche moral, aunque solo uno se cruce por azar con un peatón.", "🚗🎲", "blame", "reproche / culpa moral", "bleɪm", "Ilustra el argumento con el caso clásico de los dos conductores negligentes.", "Can you unpack how circumstantial luck complicates pure Kantian intention?"),
            ("hubris-of-meritocracy", "Recognizing constitutive luck—our temperament and upbringing—tempers the hubris of uncritical meritocracy.", "Reconocer la suerte constitutiva —temperamento y crianza— modera la arrogancia de la meritocracia acrítica.", "🏛️🌱", "hubris", "arrogancia / desmesura", "ˈhjuːbrɪs", "Conecta la suerte constitutiva con una visión más humilde de la meritocracia.", "If luck pervades both our starting point and our outcomes, does personal agency evaporate?"),
            ("agency-within-contingency", "Far from absolving us of responsibility, acknowledging contingency demands greater institutional empathy.", "Lejos de eximirnos de responsabilidad, reconocer la contingencia exige una mayor empatía institucional.", "🤝✨", "absolving", "eximir / absolver", "əbˈzɑːlvɪŋ", "Concluye que reconocer el azar no elimina la responsabilidad, sino que exige empatía.", "That's a crucial distinction—humility without fatalism."),
            ("epistemic-humility", "Epistemic humility reminds us that hindsight always makes contingent events look inevitable.", "La humildad epistémica nos recuerda que la retrospectiva hace parecer inevitable lo que fue azaroso.", "🔍⏳", "hindsight", "visión retrospectiva", "ˈhaɪndsaɪt", "", ""),
            ("stimulating-exchange", "Thank you all for such a rigorous yet generous exchange of ideas tonight.", "Gracias a todos por un intercambio de ideas tan riguroso y generoso esta noche.", "🥂📖", "rigorous", "riguroso", "ˈrɪɡərəs", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "C2", "satire-and-media-literacy", "Analyzing political satire and media literacy", "Analizar sátira y alfabetización mediática",
        "Debate la delgada línea entre la sátira política como válvula democrática y el cinismo que desmoviliza al ciudadano.",
        "cultural critic", "media essayist", "Live literary festival conversation on humor and public discourse.",
        [
            ("satire-punches-up", "At its best, satire punches up—puncturing institutional pomposity when straight reporting hits a wall.", "En su mejor expresión, la sátira apunta hacia arriba: desinfla la pomposidad del poder cuando el periodismo tradicional topa con pared.", "🎭📰", "puncturing", "desinflar / desmontar la solemnidad", "ˈpʌŋktʃərɪŋ", "Sostén que la buena sátira cuestiona al poder y desmonta la solemnidad.", "Does political satire sharpen civic awareness, or does it merely preach to the converted?"),
            ("corrosive-cynicism-trap", "Yet when irony becomes the default register for everything, it risks curdling into corrosive cynicism.", "Sin embargo, cuando la ironía se vuelve el tono por defecto para todo, corre el riesgo de volverse cinismo corrosivo.", "⚠️🗣️", "curdling into", "degenerar / agriarse en", "ˈkɜːrdlɪŋ ˈɪntuː", "Advierte que abusar de la ironía puede derivar en un cinismo paralizante.", "Where do you see the danger when audiences consume news primarily through late-night comedy?"),
            ("poes-law-online", "In an era of algorithmic outrage, Poe's Law means parody is routinely mistaken for literal endorsement.", "En una era de indignación algorítmica, la Ley de Poe hace que la parodia se confunda a menudo con una postura literal.", "🌐🤯", "mistaken for", "confundida con", "mɪˈsteɪkən fɔːr", "Explica cómo en redes sociales la parodia suele confundirse con afirmaciones literales.", "And social media strips away the contextual cues that used to signal 'this is a joke.'"),
            ("pair-wit-with-earnestness", "The antidote isn't abandoning wit, but pairing sharp critique with an earnest commitment to truth.", "El antídoto no es abandonar el ingenio, sino acompañar la crítica aguda con un compromiso genuino con la verdad.", "✨⚖️", "earnest", "genuino / serio y sincero", "ˈɜːrnɪst", "Concluye proponiendo unir el ingenio crítico con un compromiso sincero con la verdad.", "So how does a writer keep their edge without feeding into apathy?"),
            ("catharsis-versus-action", "Laughter provides vital catharsis, provided it doesn't become a substitute for civic participation.", "La risa brinda una catarsis vital, siempre que no sustituya la participación ciudadana.", "🗳️🎭", "catharsis", "catarsis / desahogo emocional", "kəˈθɑːrsɪs", "", ""),
            ("nuanced-media-diet", "Cultivating media literacy means savoring irony while still verifying primary sources.", "Cultivar la alfabetización mediática implica disfrutar la ironía verificando siempre las fuentes primarias.", "🔍📑", "savoring", "degustar / apreciar con matices", "ˈseɪvərɪŋ", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "C2", "urban-gentrification-panel", "Debating urban preservation and housing", "Debatir preservación cultural y vivienda urbana",
        "Analiza en un foro vecinal cómo equilibrar la revitalización de barrios históricos sin desplazar al comercio tradicional.",
        "neighborhood association chair", "urban sociologist", "Community townhall in a historic district undergoing rapid change.",
        [
            ("vitality-without-displacement", "The central dilemma is how we welcome public-realm investment without triggering residential displacement.", "El dilema central es cómo recibir inversión en el espacio público sin detonar el desplazamiento vecinal.", "🏘️⚖️", "displacement", "desplazamiento de residentes originales", "dɪsˈpleɪsmənt", "Plantea el reto de mejorar el espacio público sin desplazar a los vecinos.", "New cafes and transit upgrades are arriving fast, but long-time residents fear being priced out."),
            ("commercial-rent-stabilization", "Protecting legacy family bakeries and workshops requires commercial community land trusts, not just nostalgia.", "Proteger las panaderías y talleres históricos requiere fideicomisos comunitarios de suelo comercial, no solo nostalgia.", "🥖🏪", "land trusts", "fideicomisos comunitarios de tierra", "lænd trʌsts", "Propón fideicomisos de suelo comercial para proteger los comercios históricos del barrio.", "What concrete mechanisms can keep neighborhood artisans and family shops anchored here?"),
            ("gentle-infill-density", "Allowing gentle four-story infill near transit stops relieves pressure on existing rent-controlled apartments.", "Permitir vivienda de mediana altura cerca del transporte alivia la presión sobre los departamentos de renta protegida.", "🚊🏢", "infill", "densificación urbana armónica en huecos existentes", "ˈɪnfɪl", "Explica cómo la vivienda de mediana densidad junto al transporte reduce la presión inmobiliaria.", "Some preservationists oppose any new construction at all—doesn't freezing supply backfire?"),
            ("living-neighborhood-not-museum", "A historic quarter thrives as a living intergenerational community, never as a velvet-roped museum.", "Un barrio histórico prospera como una comunidad intergeneracional viva, nunca como un museo de vitrina.", "🌳🤝", "intergenerational", "intergeneracional", "ˌɪntərdʒenəˈreɪʃənəl", "Cierra afirmando que un barrio histórico debe ser una comunidad viva y no un museo.", "That balance between architectural heritage and affordable supply is exactly what our charter needs."),
            ("participatory-budgeting", "Allocating storefront improvement grants through participatory budgeting gives residents real agency.", "Asignar fondos de mejora de fachadas mediante presupuesto participativo da voz real a los vecinos.", "🗳️🏛️", "agency", "capacidad de decisión / protagonismo", "ˈeɪdʒənsi", "", ""),
            ("inclusive-urban-fabric", "When long-time elders and young families share the same square, the urban fabric stays resilient.", "Cuando los vecinos de toda la vida y las familias jóvenes comparten la plaza, el tejido urbano perdura.", "💛🏙️", "urban fabric", "tejido urbano y social", "ˈɜːrbən ˈfæbrɪk", "", ""),
        ],
    ),
    (
        "social-and-smalltalk", "C2", "eulogy-and-tribute-speech", "Delivering a lifetime achievement tribute", "Pronunciar un homenaje solemne a una mentora",
        "Rinde un homenaje elocuente a una profesora que se jubila tras cuarenta años formando generaciones.",
        "retiring professor (Dr. Lin)", "former mentee", "University auditorium tribute dinner celebrating Dr. Lin's forty-year career.",
        [
            ("measure-of-a-mentor", "The true measure of a scholar lies not merely in citations, but in the minds she has kindled.", "La verdadera medida de una académica no reside solo en sus citas, sino en las mentes que ha encendido.", "🕯️🎓", "kindled", "encendido / inspirado", "ˈkɪndəld", "Inicia el homenaje destacando que el legado de una mentora está en las mentes que inspira.", "Please welcome Dr. Lin's former doctoral advisee to deliver the closing tribute."),
            ("unflinching-red-pen", "Anyone who survived Dr. Lin's red pen knows she demanded rigor precisely because she believed in our potential.", "Cualquiera que haya sobrevivido a las correcciones de la Dra. Lin sabe que exigía rigor porque creía en nuestro potencial.", "✒️📄", "rigor", "rigor intelectual", "ˈrɪɡər", "Evoca con cariño sus exigentes correcciones como muestra de fe en sus alumnos.", "(Warm laughter and nodding across the auditorium)"),
            ("quiet-generosity-behind-scenes", "Behind the scenes, her quiet generosity opened doors for countless first-generation researchers.", "Tras bambalinas, su generosidad silenciosa abrió puertas a innumerables investigadores de primera generación.", "🚪🌟", "countless", "innumerables", "ˈkaʊntləs", "Resalta su generosidad silenciosa abriendo puertas a nuevos investigadores.", "What will you carry forward most from your years in her laboratory?"),
            ("enduring-intellectual-lineage", "Though you step down from the lecture hall tonight, your intellectual lineage spans four continents.", "Aunque hoy deje la cátedra, su linaje intelectual se extiende por cuatro continentes.", "🌍🥂", "lineage", "linaje / legado formativo", "ˈlɪniɪdʒ", "Brinda por su legado intelectual presente en cuatro continentes.", "(Standing ovation as Dr. Lin rises to the podium)"),
            ("endowed-fellowship-in-your-name", "In your honor, the alumni have endowed a fellowship for emerging scientists.", "En su honor, los exalumnos hemos constituido una beca para científicos emergentes.", "🏅🔬", "endowed", "dotado financieramente (un fondo o beca)", "ɪnˈdaʊd", "", ""),
            ("with-deepest-gratitude", "With our deepest gratitude, Dr. Lin—thank you for teaching us how to think.", "Con nuestra más profunda gratitud, Dra. Lin: gracias por enseñarnos a pensar.", "🙏❤️", "gratitude", "gratitud", "ˈɡrætɪtuːd", "", ""),
        ],
    ),
])

CELL_BLUEPRINTS.extend([
    # ==================== 5. WORK-AND-CAREER ====================
    # A1 (4 new)
    (
        "work-and-career", "A1", "office-printer-paper", "Finding office supplies", "Buscar papel y útiles de oficina",
        "Pregunta a una compañera dónde está el papel para la impresora, toma dos bolígrafos azules y agradece.",
        "coworker (Sarah)", "team member", "Office copy and supply room.",
        [
            ("printer-out-of-paper", "Excuse me, the printer is out of white paper.", "Disculpa, la impresora se quedó sin papel blanco.", "🖨️📄", "out of", "sin / agotado", "aʊt əv", "Explica que la impresora se quedó sin papel blanco.", "Hi! Having trouble with the office printer?"),
            ("supply-cabinet-key", "Where do we keep the boxes of copy paper?", "¿Dónde guardamos las cajas de papel para copias?", "📦🗄️", "keep", "guardar / mantener", "kiːp", "Pregunta dónde se guardan las cajas de papel.", "Oh, it just needs a new pack! Look in the tall grey cabinet."),
            ("take-two-blue-pens", "Can I also take two blue pens and a yellow notepad?", "¿Puedo tomar también dos bolígrafos azules y un bloc amarillo?", "🖊️📒", "notepad", "bloc de notas", "ˈnoʊtpæd", "Pregunta si puedes tomar dos bolígrafos azules y un bloc amarillo.", "Found the paper? The pens and sticky notes are on the top shelf."),
            ("load-the-paper-tray", "I will put the paper in the bottom tray now.", "Pondré el papel en la bandeja inferior ahora.", "📥🖨️", "tray", "bandeja", "treɪ", "Indica que pondrás el papel en la bandeja inferior.", "Of course! Take whatever supplies you need for your desk."),
            ("press-green-button", "Now I just press the green start button to print.", "Ahora solo presiono el botón verde de inicio para imprimir.", "🟢👆", "print", "imprimir", "prɪnt", "", ""),
            ("thanks-for-showing-me", "It is printing my pages now—thank you, Sarah!", "Ya está imprimiendo mis páginas; ¡gracias, Sarah!", "📄😊", "pages", "páginas / hojas", "ˈpeɪdʒɪz", "", ""),
        ],
    ),
    (
        "work-and-career", "A1", "leaving-for-the-day", "Saying goodbye after work", "Despedirse al terminar el trabajo",
        "Avisa a tu equipo que ya terminaste tus tareas del día, apaga tu computadora y despídete.",
        "team lead (Mark)", "employee", "Open office floor at 5:30 PM.",
        [
            ("finished-my-report", "Hi Mark, I finished all my emails and the daily table.", "Hola Mark, terminé todos mis correos y la tabla del día.", "✅💻", "finished", "terminé / completé", "ˈfɪnɪʃt", "Avisa que terminaste tus correos y la tabla del día.", "Hi! It's 5:30 already. How did your afternoon go?"),
            ("heading-home-now", "I am turning off my computer and heading home now.", "Estoy apagando mi computadora y ya me voy a casa.", "🖥️🏠", "heading home", "yendo a casa", "ˈhedɪŋ hoʊm", "Di que estás apagando tu computadora y te vas a casa.", "Great job on that table! Are you heading out for the evening?"),
            ("need-anything-before-i-go", "Do you need anything else from me today?", "¿Necesitas algo más de mi parte hoy?", "🙋‍♂️📋", "anything else", "algo más", "ˈeniθɪŋ els", "Pregunta si necesita algo más de ti hoy.", "All set on my side! Don't forget your umbrella by the door."),
            ("see-you-tomorrow-nine", "Thank you! Have a good evening, see you tomorrow at nine!", "¡Gracias! Que pases buena noche, ¡nos vemos mañana a las nueve!", "🌙👋", "evening", "tarde-noche", "ˈiːvnɪŋ", "Despídete deseándole buena noche hasta mañana a las nueve.", "Have a restful evening! See you tomorrow morning."),
            ("lock-my-desk-drawer", "I locked my desk drawer and took my badge.", "Cerré con llave el cajón de mi escritorio y tomé mi credencial.", "🔒🪪", "drawer", "cajón", "drɔːr", "", ""),
            ("catch-the-five-forty-train", "If I walk fast, I can catch the 5:40 train!", "Si camino rápido, ¡puedo alcanzar el tren de las 5:40!", "🚆🏃", "catch", "alcanzar / tomar (transporte)", "kætʃ", "", ""),
        ],
    ),
    (
        "work-and-career", "A1", "answering-office-phone", "Taking a phone message at work", "Tomar un recado telefónico en la oficina",
        "Contesta el teléfono de la oficina, explica que tu jefa está en una reunión y anota el nombre y número.",
        "caller (Mr. Evans)", "assistant", "At your office desk when the landline rings.",
        [
            ("good-morning-sales-desk", "Good morning, BrightTech office, how can I help you?", "Buenos días, oficina de BrightTech, ¿en qué puedo ayudarle?", "☎️🏢", "how can I help", "¿en qué puedo ayudarle?", "haʊ kæn aɪ help", "Contesta el teléfono saludando en nombre de la oficina.", "Hello, may I speak with Laura Gomez, please?"),
            ("she-is-in-a-meeting", "I am sorry, Laura is in a meeting until eleven.", "Lo siento, Laura está en una reunión hasta las once.", "🕚👥", "meeting", "reunión / junta", "ˈmiːtɪŋ", "Explica que Laura está en una reunión hasta las once.", "Oh, I see. When will she be back at her desk?"),
            ("can-i-take-a-message", "Can I take your name and phone number for her?", "¿Puedo tomar su nombre y número de teléfono para ella?", "📝📞", "phone number", "número de teléfono", "foʊn ˈnʌmbər", "Pregunta si puedes anotar su nombre y número de teléfono.", "Yes, please tell her Paul Evans called about the Friday order."),
            ("spell-your-last-name", "Could you spell your last name for me, please?", "¿Podría deletrearme su apellido, por favor?", "🔤✍️", "spell", "deletrear", "spel", "Pídele que deletree su apellido para anotarlo bien.", "Sure, it is E-V-A-N-S, and my number is 555-0192."),
            ("put-note-on-her-desk", "I will put this note on her desk right now.", "Pondré esta nota en su escritorio ahora mismo.", "📌🖥️", "note", "nota / recado", "noʊt", "", ""),
            ("she-will-call-you-back", "Thank you, Mr. Evans. She will call you back soon!", "Gracias, Sr. Evans. ¡Ella le devolverá la llamada pronto!", "📲✅", "call back", "devolver la llamada", "kɔːl bæk", "", ""),
        ],
    ),
    (
        "work-and-career", "A1", "it-password-reset", "Asking IT to reset a password", "Pedir soporte técnico para contraseña",
        "Pide ayuda al escritorio de soporte técnico porque tu contraseña de correo bloqueó tu cuenta.",
        "IT support technician", "employee", "Office IT help desk on the second floor.",
        [
            ("locked-out-of-email", "Hi! I cannot log in to my work email this morning.", "¡Hola! No puedo entrar a mi correo del trabajo esta mañana.", "💻🔒", "log in", "iniciar sesión", "lɑːɡ ɪn", "Explica que no puedes iniciar sesión en tu correo de trabajo.", "Hello! Welcome to the IT Help Desk. What seems to be the problem?"),
            ("forgot-new-password", "I typed my password three times and the screen locked.", "Escribí mi contraseña tres veces y la pantalla se bloqueó.", "⌨️❌", "typed", "escribí / tecleé", "taɪpt", "Cuenta que escribiste tu contraseña tres veces y se bloqueó.", "No problem, that happens all the time! What is your employee username?"),
            ("temporary-login-code", "Can you send a temporary code to my mobile phone?", "¿Puede enviar un código temporal a mi teléfono móvil?", "📱🔢", "temporary", "temporal / provisorio", "ˈtempəreri", "Pregunta si pueden enviar un código temporal a tu celular.", "I just unlocked your account and sent a six-digit reset code to your phone."),
            ("type-new-password-now", "It works now! I will type a new password right away.", "¡Ya funciona! Escribiré una contraseña nueva de inmediato.", "✅🔑", "right away", "de inmediato / ahora mismo", "raɪt əˈweɪ", "Confirma que ya funciona y crearás una contraseña nueva.", "Great! Just make sure your new password has at least eight letters and one number."),
            ("connect-to-office-wifi", "My laptop is also connected to the fast office Wi-Fi.", "Mi laptop también ya está conectada al wifi rápido de la oficina.", "📶💻", "connected", "conectada", "kəˈnektɪd", "", ""),
            ("thanks-it-help", "Thank you so much for fixing it so fast!", "¡Muchas gracias por arreglarlo tan rápido!", "🙌😊", "fixing", "reparar / arreglar", "ˈfɪksɪŋ", "", ""),
        ],
    ),
    # A2 (4 new)
    (
        "work-and-career", "A2", "requesting-vacation-days", "Requesting two vacation days", "Solicitar dos días de vacaciones",
        "Pide a tu supervisora tomar libres el viernes y el lunes próximos y explica quién cubrirá tus tareas.",
        "team manager", "employee", "Quick check-in at your manager's office.",
        [
            ("take-friday-monday-off", "Hi Elena, could I request this coming Friday and Monday as vacation days?", "Hola Elena, ¿podría solicitar este próximo viernes y lunes como días de vacaciones?", "🗓️✈️", "request", "solicitar / pedir", "rɪˈkwest", "Solicita tomar el viernes y el lunes como días de vacaciones.", "Hi! Come on in. What did you want to chat about?"),
            ("finish-tasks-by-thursday", "I will finish all my weekly reports before Thursday afternoon.", "Terminaré todos mis reportes semanales antes del jueves por la tarde.", "📊✅", "before", "antes de", "bɪˈfɔːr", "Asegura que terminarás todos tus reportes antes del jueves por la tarde.", "Let's look at the team calendar for next week. How are your current tasks looking?"),
            ("carlos-can-cover-urgent", "Carlos agreed to cover any urgent client emails while I'm away.", "Carlos aceptó cubrir cualquier correo urgente de clientes mientras no esté.", "🤝📧", "while I'm away", "mientras estoy ausente", "waɪl aɪm əˈweɪ", "Explica que Carlos cubrirá cualquier correo urgente en tu ausencia.", "That's great planning! Who can keep an eye on your client inbox on Friday?"),
            ("submit-in-hr-portal", "I'll submit the dates in the HR portal right now for your approval.", "Subiré las fechas en el portal de Recursos Humanos ahora mismo para tu aprobación.", "💻👍", "approval", "aprobación", "əˈpruːvəl", "Indica que registrarás las fechas en el portal de RR. HH. para su aprobación.", "Perfect! Go ahead and log the request in the system and I'll approve it today."),
            ("set-out-of-office-reply", "I'll also set up an automatic out-of-office email reply on Thursday evening.", "También activaré una respuesta automática fuera de la oficina el jueves por la tarde.", "📩🔄", "out-of-office", "respuesta automática de ausencia", "aʊt əv ˈɔːfɪs", "", ""),
            ("enjoy-the-long-weekend", "Thanks so much, Elena! I'm visiting my family by the coast.", "¡Muchas gracias, Elena! Visitaré a mi familia en la costa.", "🏖️😊", "coast", "costa", "koʊst", "", ""),
        ],
    ),
    (
        "work-and-career", "A2", "welcoming-client-visitor", "Welcoming a visiting client", "Recibir a un cliente en la oficina",
        "Recibe a una clienta en el vestíbulo, ofrécele agua o café y acompáñala a la sala de juntas.",
        "visiting client (Ms. Chen)", "account coordinator", "Company reception lobby before a 10 AM meeting.",
        [
            ("welcome-to-our-office", "Good morning, Ms. Chen! Welcome to our headquarters—it's great to meet you in person.", "¡Buenos días, Sra. Chen! Bienvenida a nuestra oficina central; qué gusto conocerla en persona.", "🏢🤝", "in person", "en persona", "ɪn ˈpɜːrsən", "Da la bienvenida a la Sra. Chen a la oficina.", "Good morning! I'm Mei Chen, here for the ten o'clock product meeting."),
            ("how-was-your-flight", "Did you have a smooth trip from the airport this morning?", "¿Tuvo un trayecto tranquilo desde el aeropuerto esta mañana?", "🚕☀️", "smooth", "sin contratiempos / fluido", "smuːð", "Pregunta si tuvo un buen traslado desde el aeropuerto.", "Great to meet you too! Your lobby is lovely."),
            ("hang-up-your-coat", "Let me take your coat, and can I get you a coffee or sparkling water?", "Permítame su abrigo, ¿y puedo ofrecerle un café o agua con gas?", "🧥☕", "let me", "permítame", "let miː", "Ofrécele guardar su abrigo y traerle café o agua con gas.", "Yes, the traffic wasn't bad at all today!"),
            ("conference-room-down-hall", "Our conference room is right down this hall on the left—after you!", "Nuestra sala de juntas está al final de este pasillo a la izquierda; ¡adelante!", "🚪➡️", "after you", "pase usted primero / adelante", "ˈæftər juː", "Invítala a pasar hacia la sala de juntas al final del pasillo.", "A cup of black coffee would be wonderful, thank you."),
            ("guest-wifi-on-board", "The guest Wi-Fi password is written on the whiteboard if you need it.", "La clave del wifi para visitas está escrita en el pizarrón por si la necesita.", "📶📋", "whiteboard", "pizarrón blanco", "ˈwaɪtbɔːrd", "", ""),
            ("team-joining-in-two-minutes", "The rest of the team will join us in just two minutes.", "El resto del equipo se nos unirá en solo dos minutos.", "👥⏱️", "the rest of", "el resto de", "ðə rest əv", "", ""),
        ],
    ),
    (
        "work-and-career", "A2", "submitting-expense-report", "Submitting travel expense receipts", "Subir recibos de gastos de viaje",
        "Pregunta a contabilidad cómo subir las fotos de los recibos del hotel y taxi en la aplicación de gastos.",
        "accounting specialist", "employee", "Stopping by the finance desk after a business trip.",
        [
            ("upload-trip-receipts", "Hi! Could you show me how to submit my receipts from the Boston conference?", "¡Hola! ¿Podrías mostrarme cómo subir mis recibos del congreso de Boston?", "🧾💼", "submit", "enviar / presentar", "səbˈmɪt", "Pide que te muestre cómo subir tus recibos del viaje a Boston.", "Hi! Welcome back from Boston. Ready to file your travel expenses?"),
            ("take-photo-with-app", "Can I just take a photo of the taxi and dinner receipts with the mobile app?", "¿Puedo simplemente tomar una foto de los recibos de taxi y cena con la app móvil?", "📱📸", "receipts", "recibos / comprobantes", "rɪˈsiːts", "Pregunta si puedes tomar fotos de los recibos desde la app móvil.", "It's super easy! Do you still have the paper receipts and hotel invoice?"),
            ("select-project-code", "Which project code should I choose from the dropdown menu?", "¿Qué código de proyecto debo elegir en el menú desplegable?", "💻📂", "dropdown menu", "menú desplegable", "ˈdrɑːpdaʊn ˈmenjuː", "Pregunta qué código de proyecto elegir en el menú desplegable.", "Yes, the app scans the date and total amount automatically from your photo."),
            ("reimbursed-next-paycheck", "Will the reimbursement be added to my next paycheck at the end of the month?", "¿El reembolso se sumará a mi próximo pago a fin de mes?", "🏦📅", "paycheck", "pago de nómina / sueldo", "ˈpeɪtʃek", "Pregunta si el reembolso saldrá en tu próximo pago de fin de mes.", "Select 'Q3-Events-204' and click 'Send to Manager'."),
            ("hotel-itemized-pdf", "I also attached the PDF invoice that the hotel emailed me.", "También adjunté la factura en PDF que me envió el hotel por correo.", "📎🏨", "attached", "adjunté", "əˈtætʃt", "", ""),
            ("thanks-that-was-easy", "Done! That took less than five minutes—thank you!", "¡Listo! Eso tomó menos de cinco minutos; ¡gracias!", "🙌✅", "less than", "menos de", "les ðæn", "", ""),
        ],
    ),
    (
        "work-and-career", "A2", "working-from-home-note", "Checking in when working remotely", "Avisar que trabajarás desde casa",
        "Avisa a tu líder de equipo que hoy trabajarás desde casa mientras reparan una tubería y que estás disponible en Slack.",
        "team lead", "remote employee", "Quick morning voice call from your home office.",
        [
            ("working-from-home-today", "Good morning! I'm working from home today because the plumber is coming at ten.", "¡Buenos días! Hoy trabajo desde casa porque el plomero viene a las diez.", "🏠💻", "plumber", "plomero / fontanero", "ˈplʌmər", "Avisa que hoy trabajarás desde casa porque viene el plomero a las diez.", "Morning! Thanks for calling. Everything okay at your apartment?"),
            ("online-on-slack-and-email", "I'm already logged in on Slack and email, so you can reach me anytime.", "Ya estoy conectado en Slack y en el correo, así que puedes contactarme en cualquier momento.", "💬🟢", "reach me", "contactarme / localizarme", "riːtʃ miː", "Confirma que ya estás conectado en Slack y correo para cualquier cosa.", "Oh, I hope the pipe is an easy fix! Will you be able to join the 11:00 AM call?"),
            ("join-all-video-meetings", "Yes, my internet is fast and I'll join all our video meetings on camera.", "Sí, mi internet es rápido y entraré a todas nuestras videollamadas con cámara.", "📹📶", "on camera", "con la cámara encendida", "ɑːn ˈkæmərə", "Asegura que entrarás a todas las videollamadas con cámara encendida.", "Awesome. Could you also update the shared spreadsheet before lunch?"),
            ("back-in-office-tomorrow", "I'll update the spreadsheet by noon, and I'll be back in the office tomorrow!", "Actualizaré la hoja de cálculo antes del mediodía y mañana estaré de vuelta en la oficina.", "📊🏢", "spreadsheet", "hoja de cálculo", "ˈspredʃiːt", "Promete actualizar la hoja antes del mediodía y volver mañana a la oficina.", "Thanks! Let me know if the plumber needs you to step away for fifteen minutes."),
            ("step-away-ten-minutes", "I'll post a quick note in the team channel when he arrives.", "Pondré un aviso rápido en el canal del equipo cuando él llegue.", "📝💬", "channel", "canal de chat", "ˈtʃænəl", "", ""),
            ("productive-quiet-morning", "Working from a quiet desk at home is great for finishing deep work!", "Trabajar desde un escritorio tranquilo en casa es genial para avanzar.", "🎧✨", "quiet", "tranquilo / silencioso", "ˈkwaɪət", "", ""),
        ],
    ),
    # B1 (4 new)
    (
        "work-and-career", "B1", "onboarding-new-colleague", "Onboarding a new team member", "Guiar a un nuevo compañero de equipo",
        "Muéstrale a un compañero nuevo cómo están organizadas las carpetas compartidas y las reuniones semanales.",
        "new hire (Lucas)", "onboarding buddy", "Sitting together at a shared desk during Lucas's first week.",
        [
            ("walk-through-shared-drive", "Welcome to the team, Lucas! Let me walk you through our shared Google Drive folders.", "¡Bienvenido al equipo, Lucas! Déjame mostrarte paso a paso nuestras carpetas compartidas.", "📂🤝", "walk you through", "explicarte paso a paso", "wɔːk juː θruː", "Dale la bienvenida y ofrécele mostrarle las carpetas compartidas.", "Thanks for being my onboarding buddy! Where do we keep the current project templates?"),
            ("active-client-templates", "All the active client presentations and brand guidelines live inside this '01-Current' folder.", "Todas las presentaciones activas y guías de marca están dentro de esta carpeta '01-Current'.", "📊🗂️", "guidelines", "lineamientos / guías", "ˈɡaɪdlaɪnz", "Explica que las presentaciones y guías están en la carpeta '01-Current'.", "That folder structure is super clean! How does the team track weekly tasks?"),
            ("monday-kickoff-board", "Every Monday at nine thirty, we review the Kanban board together to assign priorities.", "Cada lunes a las nueve y media revisamos juntos el tablero Kanban para asignar prioridades.", "📋🕤", "assign", "asignar", "əˈsaɪn", "Cuenta que los lunes a las 9:30 revisan el tablero para asignar prioridades.", "Got it—I'll bookmark the Kanban board in my browser right now."),
            ("ask-me-any-questions", "There's a lot to take in during week one, so ping me anytime if you get stuck!", "Hay mucho que asimilar en la primera semana, ¡así que escríbeme si te atoras en algo!", "💬🙌", "take in", "asimilar / procesar información", "teɪk ɪn", "Anímalo a escribirte en cualquier momento si tiene dudas durante la primera semana.", "Everyone has been so welcoming! What should I focus on finishing before Friday?"),
            ("shadow-tomorrows-call", "Tomorrow you can shadow our client discovery call just to see how we run it.", "Mañana puedes entrar como observador a nuestra llamada con el cliente para ver la dinámica.", "🎧📞", "shadow", "acompañar para aprender observando", "ˈʃædoʊ", "", ""),
            ("grab-team-lunch-today", "At noon the whole team is taking you out for tacos around the corner!", "¡Al mediodía todo el equipo te llevará a comer tacos a la vuelta de la esquina!", "🌮🎉", "around the corner", "a la vuelta de la esquina", "əˈraʊnd ðə ˈkɔːrnər", "", ""),
        ],
    ),
    (
        "work-and-career", "B1", "handling-audio-glitch", "Troubleshooting a video call glitch", "Resolver fallo de audio y pantalla en videollamada",
        "Resuelve con calma un eco en el micrófono y un problema al compartir pantalla durante una presentación remota.",
        "client on Zoom", "presenter", "Start of an online product demo call.",
        [
            ("hear-my-audio-clearly", "Hi everyone! Before I dive in, can you hear my audio clearly and see my slides?", "¡Hola a todos! Antes de comenzar de lleno, ¿escuchan bien mi audio y ven mis diapositivas?", "🎙️💻", "dive in", "entrar en materia / comenzar", "daɪv ɪn", "Pregunta si te escuchan con claridad y pueden ver tus diapositivas.", "Hi! We can hear you, though there's a slight echo, and the screen is still black."),
            ("switch-to-headset-mic", "Let me switch my audio input to my wired headset so we get rid of that echo.", "Déjenme cambiar la entrada de audio a mis audífonos con cable para eliminar ese eco.", "🎧🔧", "get rid of", "eliminar / deshacerse de", "ɡet rɪd əv", "Explica que cambiarás a tus audífonos con cable para quitar el eco.", "Much better—the echo is completely gone now! What about the slide deck?"),
            ("share-specific-window", "I'll stop sharing and share the browser window directly instead of my whole desktop.", "Dejaré de compartir y seleccionaré directamente la ventana del navegador en lugar de todo el escritorio.", "🖥️🔄", "instead of", "en lugar de", "ɪnˈsted əv", "Indica que compartirás directamente la ventana del navegador.", "Take your time, Zoom always acts up right before a demo!"),
            ("drop-link-in-chat", "There we go! I also dropped the PDF link in the chat in case anyone wants to follow along.", "¡Listo! También dejé el enlace del PDF en el chat por si alguien quiere seguirlo desde ahí.", "🔗✅", "follow along", "seguir la presentación al mismo tiempo", "ˈfɑːloʊ əˈlɔːŋ", "Confirma que ya se ve y menciona que pusiste el enlace del PDF en el chat.", "Crystal clear! We see the title slide in full screen now."),
            ("mute-when-not-speaking", "Feel free to unmute and jump in with questions as we go through each screen.", "Siéntanse libres de abrir su micrófono y hacer preguntas en cada pantalla.", "🗣️✨", "jump in", "intervenir en la conversación", "dʒʌmp ɪn", "", ""),
            ("thanks-for-patience-tech", "Thanks for bearing with me for thirty seconds—let's jump into the demo!", "Gracias por la paciencia estos treinta segundos; ¡vamos directo a la demostración!", "🚀👏", "bearing with me", "tenerme paciencia", "ˈberɪŋ wɪð miː", "", ""),
        ],
    ),
    (
        "work-and-career", "B1", "asking-for-feedback", "Requesting feedback after a presentation", "Pedir retroalimentación tras una presentación",
        "Pide a tu directora comentarios concretos después de tu primera presentación ante el comité.",
        "department director", "presenter", "Walking back from the conference room after a quarterly presentation.",
        [
            ("how-did-the-pitch-land", "Thanks for backing me up in there! Do you have two minutes to share how you felt the presentation went?", "¡Gracias por apoyarme ahí dentro! ¿Tienes dos minutos para contarme cómo sentiste que salió la presentación?", "📊🤝", "backing me up", "respaldarme / apoyarme", "ˈbækɪŋ miː ʌp", "Agradece su respaldo y pide dos minutos para saber cómo vio tu presentación.", "You handled the VP's tough question on the timeline really well!"),
            ("pacing-of-data-slides", "Did the pacing on the financial slides feel right, or did I rush through the charts?", "¿El ritmo en las diapositivas financieras se sintió bien, o pasé demasiado rápido por los gráficos?", "📈⏱️", "pacing", "ritmo de exposición", "ˈpeɪsɪŋ", "Pregunta si el ritmo en las diapositivas de datos fue adecuado.", "Your opening hook was strong. Where did you feel least comfortable?"),
            ("pause-after-key-numbers", "Next time I'll pause for three seconds after the key numbers so the takeaway sinks in.", "La próxima vez haré una pausa de tres segundos después de las cifras clave para que la idea se asiente.", "⏸️🎯", "sinks in", "asimilarse / quedar claro en la audiencia", "sɪŋks ɪn", "Toma nota de hacer una pausa después de las cifras clave.", "Pausing briefly on Slide 4 would help the executives digest the cost savings."),
            ("one-thing-to-improve", "Is there one specific thing I should tighten up before next month's steering committee?", "¿Hay algún punto específico que deba pulir antes del comité del próximo mes?", "🔧🌟", "tighten up", "pulir / ajustar mejor", "ˈtaɪtən ʌp", "Pregunta qué aspecto puntual deberías pulir para la reunión del próximo mes.", "Spot on. Overall, your confidence and structure were a huge step forward."),
            ("put-summary-up-front", "Putting the executive summary on the very first slide is a great tip.", "Poner el resumen ejecutivo en la primera diapositiva es un gran consejo.", "💡📑", "up front", "al principio / por delante", "ʌp frʌnt", "", ""),
            ("appreciate-honest-coaching", "I really appreciate your honest coaching—it helps me grow so much faster.", "Valoro muchísimo tu retroalimentación honesta; me ayuda a crecer mucho más rápido.", "🙏🚀", "coaching", "mentoría / guía", "ˈkoʊtʃɪŋ", "", ""),
        ],
    ),
    (
        "work-and-career", "B1", "cross-team-handoff", "Handing off design files to engineering", "Entregar archivos de diseño a ingeniería",
        "Explica al desarrollador principal cómo están organizados los componentes en Figma y los estados móviles.",
        "lead frontend developer", "product designer", "Design-to-engineering handoff call.",
        [
            ("annotated-figma-specs", "I've marked the checkout flow as 'Ready for Dev' in Figma with all spacing and color tokens.", "Marqué el flujo de pago como 'Listo para Desarrollo' en Figma con todos los espacios y colores.", "🎨💻", "tokens", "variables de diseño (colores, medidas)", "ˈtoʊkənz", "Explica que ya marcaste el flujo en Figma como listo para desarrollo.", "Hey! Our sprint starts tomorrow—are the new checkout screens ready to build?"),
            ("mobile-and-error-states", "Next to each desktop screen, I included the mobile view plus the empty and error states.", "Junto a cada pantalla de escritorio incluí la vista móvil además de los estados vacíos y de error.", "📱⚠️", "error states", "pantallas de estado de error", "ˈerər steɪts", "Detalla que incluiste vistas móviles y estados de error junto a cada pantalla.", "Having the design tokens mapped saves us so much guesswork! What about edge cases?"),
            ("exportable-svg-icons", "All the custom icons are grouped as exportable SVGs so you can grab them in one click.", "Todos los íconos personalizados están agrupados como SVG exportables para descargarlos en un clic.", "✨📥", "exportable", "listos para exportar", "ɪkˈspɔːrtəbəl", "Indica que todos los íconos están listos para exportar en formato SVG.", "Oh nice, engineers always forget to ask about the empty state until the last day!"),
            ("do-a-quick-qa-pass", "Once you deploy it to the staging link on Wednesday, let's do a fifteen-minute visual QA together.", "En cuanto lo suban al enlace de pruebas el miércoles, hagamos juntos una revisión visual de quince minutos.", "🔍✅", "staging", "entorno de pruebas previas", "ˈsteɪdʒɪŋ", "Propón hacer una revisión visual de 15 minutos cuando esté en el entorno de pruebas.", "Everything looks crystal clear. I'll ping you as soon as the staging build is live."),
            ("accessible-contrast-ratios", "I also verified that all button text meets double-A contrast ratios.", "También verifiqué que todos los botones cumplan el contraste de accesibilidad AA.", "👁️🛡️", "meets", "cumple con (un estándar)", "miːts", "", ""),
            ("ping-in-slack-thread", "If any interaction feels tricky to animate, just tag me in the Slack thread!", "Si alguna animación resulta compleja, ¡etiquétame en el hilo de Slack!", "💬🙌", "tricky", "complicado / con truco", "ˈtrɪki", "", ""),
        ],
    ),
    # B2 (4 new)
    (
        "work-and-career", "B2", "salary-review-discussion", "Presenting achievements for a salary review", "Presentar logros para revisión salarial",
        "Expón con datos concretos cómo ampliaste tus responsabilidades y lideraste proyectos clave para solicitar un ajuste salarial.",
        "engineering VP", "senior contributor", "Annual performance and compensation review meeting.",
        [
            ("expanded-scope-this-year", "Over the past year, my scope has expanded from individual feature delivery to leading our three-person billing pod.", "Durante el último año, mi alcance pasó de entregar funciones individuales a liderar nuestro equipo de tres personas de facturación.", "📈💼", "scope", "alcance de responsabilidades", "skoʊp", "Explica cómo tu alcance creció hasta liderar el equipo de facturación este año.", "Thanks for sending your self-assessment ahead of time. You've had a standout year!"),
            ("reduced-churn-and-latency", "By re-architecting the payment retry pipeline, we recovered four hundred thousand dollars in annual recurring revenue.", "Al rediseñar el flujo de reintentos de pago, recuperamos cuatrocientos mil dólares en ingresos anuales recurrentes.", "💡💵", "recovered", "recuperamos", "rɪˈkʌvərd", "Destaca que el rediseño de pagos recuperó $400,000 en ingresos recurrentes.", "The executive team noticed that metric right away—it made a huge dent in involuntary churn."),
            ("benchmark-compensation-band", "Given these results and my current responsibilities, I'd like to discuss aligning my base salary with the Senior Lead band.", "Dados estos resultados y mis responsabilidades actuales, me gustaría conversar sobre alinear mi salario base con la banda de Senior Lead.", "⚖️🎯", "aligning", "alinear / equiparar", "əˈlaɪnɪŋ", "Propón alinear tu salario base con la banda de Senior Lead.", "Where do you see your compensation sitting relative to market benchmarks?"),
            ("twelve-percent-adjustment", "Based on our internal leveling guide and market data, a twelve-percent adjustment to base plus equity refresh feels fair.", "Según nuestra guía interna de niveles y datos de mercado, un ajuste del doce por ciento más renovación de acciones parece justo.", "📊🤝", "adjustment", "ajuste salarial", "əˈdʒʌstmənt", "Plantea un ajuste del 12% apoyado en la guía interna de niveles.", "I agree you're already operating at that level. Let me take this proposal to HR and compensation committee."),
            ("timeline-for-hr-signoff", "When does the compensation committee finalize adjustments for the Q2 payroll cycle?", "¿Cuándo cierra el comité los ajustes para la nómina del segundo trimestre?", "🗓️🏦", "payroll cycle", "ciclo de nómina", "ˈpeɪroʊl ˈsaɪkəl", "", ""),
            ("excited-for-next-roadmap", "I appreciate your advocacy, and I'm really excited to lead the international checkout rollout next!", "Agradezco mucho tu respaldo y me entusiasma liderar el despliegue internacional.", "🚀🌟", "advocacy", "respaldo activo / defensa", "ˈædvəkəsi", "", ""),
        ],
    ),
    (
        "work-and-career", "B2", "de-escalating-client-call", "De-escalating an urgent client outage call", "Calmar a un cliente tras una caída del servicio",
        "Escucha sin ponernos a la defensiva a un cliente afectado por una interrupción de 20 minutos y explica el plan de prevención.",
        "enterprise client director", "account manager", "Urgent video call one hour after a 20-minute API outage.",
        [
            ("own-the-impact-fully", "First, I want to acknowledge the disruption this twenty-minute outage caused your support team during peak hours.", "Primero, quiero reconocer la afectación que esta interrupción de veinte minutos causó a su equipo en hora punta.", "🛡️🤝", "acknowledge", "reconocer abiertamente", "əkˈnɑːlɪdʒ", "Reconoce con empatía el impacto que tuvo la interrupción en su operación.", "Our checkout API threw 502 errors for twenty minutes this morning right during our flash sale!"),
            ("root-cause-connection-pool", "Our engineers identified the root cause—a database connection pool limit triggered during the traffic spike—and rolled out a fix.", "Nuestros ingenieros identificaron la causa raíz —un límite de conexiones durante el pico de tráfico— y aplicaron la corrección.", "🔍⚙️", "root cause", "causa raíz / origen del fallo", "ruːt kɔːz", "Explica la causa raíz detectada y confirma que la corrección ya fue aplicada.", "What actually happened under the hood, and how do we know it won't happen again tonight?"),
            ("automated-autoscaling-guard", "We've tripled the connection ceiling and added an automated alert at sixty-percent capacity so it scales ahead of demand.", "Triplicamos el tope de conexiones y agregamos una alerta automática al sesenta por ciento para escalar antes del pico.", "📈🔔", "ceiling", "tope máximo / límite", "ˈsiːlɪŋ", "Detalla que triplicaron la capacidad y activaron alertas preventivas al 60%.", "Tripling the ceiling helps, but my CFO is asking for a formal incident report."),
            ("written-rca-and-sla-credit", "You'll have our full written root-cause analysis by 4:00 PM today, and we're applying the SLA service credit to next month's invoice.", "Tendrán nuestro informe escrito de causa raíz hoy a las 4:00 PM, y aplicaremos el crédito de garantía SLA en su próxima factura.", "📑✅", "service credit", "bonificación en factura por nivel de servicio", "ˈsɜːrvɪs ˈkredɪt", "Compromete el informe escrito hoy a las 4:00 PM y la bonificación SLA en factura.", "Thank you for owning it directly and having the fix already in place."),
            ("dedicated-engineer-on-standby", "For the remainder of your flash sale through Sunday, we've assigned an on-call engineer to monitor your tenant.", "Durante el resto de su promoción hasta el domingo, asignamos un ingeniero de guardia para monitorear su cuenta.", "👨‍💻👀", "on-call", "de guardia", "ɑːn kɔːl", "", ""),
            ("follow-up-check-in-monday", "Let's do a quick fifteen-minute check-in on Monday morning to review the weekend telemetry.", "Hagamos una revisión breve de quince minutos el lunes para ver las métricas del fin de semana.", "📅📊", "telemetry", "métricas de monitoreo en tiempo real", "təˈlemətri", "", ""),
        ],
    ),
    (
        "work-and-career", "B2", "leading-retrospective", "Facilitating an agile sprint retrospective", "Liderar una retrospectiva de equipo",
        "Modera una retrospectiva enfocada en soluciones concretas sin buscar culpables tras un lanzamiento intenso.",
        "software engineer", "scrum facilitator", "Bi-weekly team retrospective meeting.",
        [
            ("focus-on-systems-not-blame", "Let's kick off our retro—remember, we're looking at our workflow and systems, not pointing fingers.", "Iniciemos nuestra retrospectiva; recuerden que analizamos nuestros procesos y sistemas, sin buscar culpables.", "🔄🤝", "pointing fingers", "echar culpas / señalar personas", "ˈpɔɪntɪŋ ˈfɪŋɡərz", "Abre la sesión recordando que el foco está en mejorar procesos sin buscar culpables.", "Glad we shipped the release, though Thursday night felt pretty chaotic with late QA changes!"),
            ("celebrate-what-went-well", "First, huge shout-out to the backend and QA pair for catching that currency rounding bug before launch.", "Primero, un gran reconocimiento a backend y QA por detectar ese error de redondeo de moneda antes del lanzamiento.", "👏🎯", "shout-out", "reconocimiento público", "ˈʃaʊt aʊt", "Reconoce el logro del equipo al detectar el error de moneda antes de salir a producción.", "Thanks! Pairing on the test cases definitely saved us on Friday."),
            ("freeze-scope-forty-eight-hours", "To avoid last-minute crunch, what if we freeze non-critical copy changes forty-eight hours before release?", "Para evitar prisas de última hora, ¿qué tal si congelamos cambios de texto no críticos cuarenta y ocho horas antes?", "❄️⏱️", "crunch", "sobrecarga de trabajo de última hora", "krʌntʃ", "Propón congelar cambios no críticos 48 horas antes del lanzamiento.", "The main bottleneck was getting five copy changes after code freeze had already started."),
            ("assign-one-clear-owner", "Let's turn that into a concrete action item with an owner so we test it in Sprint 14.", "Convirtamos eso en un acuerdo concreto con responsable para probarlo en el Sprint 14.", "✅📋", "action item", "acuerdo / tarea concreta", "ˈækʃən ˈaɪtəm", "Convierte la propuesta en un acuerdo concreto con responsable para el próximo sprint.", "A 48-hour copy freeze would make QA's life ten times easier—I can draft the checklist!"),
            ("automated-smoke-suite", "Automating the five core checkout smoke tests will also shave an hour off manual verification.", "Automatizar las cinco pruebas clave de compra también ahorrará una hora de revisión manual.", "⚡🤖", "shave off", "ahorrar / recortar tiempo", "ʃeɪv ɔːf", "", ""),
            ("wrap-up-on-high-note", "Two clear action items and five minutes to spare—thank you all for a candid retro!", "Dos acuerdos claros y cinco minutos de sobra; ¡gracias a todos por una retrospectiva tan franca!", "🌟🙌", "candid", "franca / sincera", "ˈkændɪd", "", ""),
        ],
    ),
    (
        "work-and-career", "B2", "pitching-internal-automation", "Pitching a workflow automation tool", "Proponer automatización para ahorrar tiempo",
        "Presenta una propuesta interna que ahorra diez horas semanales de carga manual de facturas con retorno en dos meses.",
        "operations director", "process lead", "15-minute internal pitch meeting with operations leadership.",
        [
            ("ten-hours-manual-entry", "Right now, our coordinators spend twelve hours every week manually copying invoice rows into the ERP.", "Actualmente, nuestros coordinadores dedican doce horas por semana a copiar manualmente facturas en el sistema ERP.", "⏱️📊", "manually", "de forma manual", "ˈmænjuəli", "Explica que el equipo pierde doce horas semanales copiando facturas a mano.", "You mentioned you found a bottleneck in our monthly vendor billing workflow. Walk me through it."),
            ("built-working-prototype", "I built a lightweight OCR script over two afternoons that extracts the fields with ninety-nine-percent accuracy.", "Construí un script ligero en dos tardes que extrae los campos con un noventa y nueve por ciento de precisión.", "🤖📄", "extracts", "extrae automáticamente", "ɪkˈstrækts", "Cuenta que creaste un prototipo que extrae los datos con 99% de precisión.", "Twelve hours a week is huge—and manual data entry always leads to typos. What's your proposed fix?"),
            ("human-in-the-loop-review", "A coordinator still reviews flagged exceptions, so we keep full financial control while cutting processing time by eighty percent.", "Un coordinador sigue revisando las excepciones marcadas, manteniendo control total y reduciendo el tiempo un ochenta por ciento.", "👁️🛡️", "exceptions", "casos atípicos / excepciones", "ɪkˈsepʃənz", "Aclara que un coordinador sigue aprobando las excepciones para mantener el control.", "How do we make sure an automated script doesn't approve a duplicate vendor bill?"),
            ("two-week-pilot-budget", "The cloud API costs just eighty dollars a month; can we run a two-week pilot with the regional team?", "La API cuesta solo ochenta dólares al mes; ¿podemos hacer un piloto de dos semanas con el equipo regional?", "🚀💵", "pilot", "prueba piloto", "ˈpaɪlət", "Solicita luz verde para un piloto de dos semanas con un costo de $80 al mes.", "Human-in-the-loop validation is smart. What's the software cost to test this?"),
            ("measure-error-reduction", "We'll track time saved and error rates before rolling it out globally in Q3.", "Mediremos el tiempo ahorrado y la reducción de errores antes de desplegarlo globalmente.", "📈🌍", "rolling it out", "desplegarlo / implementarlo", "ˈroʊlɪŋ ɪt aʊt", "", ""),
            ("green-light-for-pilot", "Awesome—I'll set up the pilot sandbox this afternoon and report back in two weeks!", "¡Excelente! Configuraré el entorno de prueba hoy mismo y presentaré resultados en dos semanas.", "✅🙌", "report back", "informar los resultados", "rɪˈpɔːrt bæk", "", ""),
        ],
    ),
    # C1 (4 new)
    (
        "work-and-career", "C1", "delivering-performance-review", "Delivering constructive coaching feedback", "Dar evaluación de desempeño constructiva",
        "Ofrece retroalimentación equilibrada a un ingeniero talentoso: reconoce su excelencia técnica y guíalo para delegar más.",
        "senior engineer (Alex)", "engineering manager", "Quarterly career growth and coaching 1-on-1.",
        [
            ("anchor-on-technical-impact", "First off, your architecture work on the real-time notification engine set a new bar for reliability across the org.", "Para empezar, tu trabajo de arquitectura en el motor de notificaciones marcó un nuevo estándar de fiabilidad en toda la empresa.", "🏆⚙️", "set a new bar", "marcar un nuevo estándar superior", "set ə nuː bɑːr", "Inicia reconociendo el impacto sobresaliente de su arquitectura técnica.", "Thanks for setting aside time for our quarterly growth chat. How am I tracking toward Staff Engineer?"),
            ("shift-from-hero-to-multiplier", "To make the leap to Staff Engineer, the shift is moving from being the go-to problem solver to being a force multiplier.", "Para dar el salto a Staff Engineer, la clave es pasar de resolver todo tú mismo a ser un multiplicador del equipo.", "🌱🚀", "force multiplier", "multiplicador de talento / impulsor del equipo", "fɔːrs ˈmʌltɪplaɪər", "Explica que el siguiente nivel requiere pasar de ejecutor individual a multiplicador del equipo.", "I'd love honest feedback on where my blind spots are for that Staff promotion."),
            ("delegate-design-docs", "When you jump in and rewrite junior engineers' PRs late at night, it unblocks the sprint but deprives them of the learning curve.", "Cuando entras a reescribir el código de los juniors de noche, destrabas el sprint pero les quitas la curva de aprendizaje.", "🔍🤝", "deprives", "priva de / quita la oportunidad", "dɪˈpraɪvz", "Señala con tacto que resolverles el código les resta oportunidad de aprendizaje.", "That's fair—sometimes I just fix it myself because it feels faster than explaining it."),
            ("co-author-next-rfc", "This quarter, let's have you mentor Maya as she authors the caching RFC while you guide the architectural trade-offs.", "Este trimestre, haz que Maya redacte la propuesta técnica de caché mientras tú la guías en las decisiones de arquitectura.", "📝🧭", "trade-offs", "compensaciones / pros y contras técnicos", "treɪd ɔːfs", "Propón que este trimestre guíe a Maya como autora del documento técnico.", "How can I practice that mentorship muscle on our upcoming Q3 project?"),
            ("document-promotion-packet", "Coaching her through that design review will be the centerpiece of your Staff promotion packet.", "Guiarla en esa revisión de diseño será la pieza central de tu expediente de promoción.", "📑🌟", "centerpiece", "pieza central / argumento clave", "ˈsentərpiːs", "", ""),
            ("check-in-biweekly", "We'll review how the delegation feels in our biweekly 1-on-1s—you're more than ready for this step.", "Revisaremos cómo avanza la delegación cada dos semanas; estás más que listo para este paso.", "🙌✅", "more than ready", "más que preparado", "mɔːr ðæn ˈredi", "", ""),
        ],
    ),
    (
        "work-and-career", "C1", "vendor-sla-renegotiation", "Renegotiating a cloud vendor SLA", "Renegociar penalizaciones de SLA con proveedor",
        "Exige mejoras contractuales y cláusulas de salida a un proveedor tras dos caídas que incumplieron el 99.9% de disponibilidad.",
        "vendor account executive", "head of infrastructure", "Contract renewal and SLA review meeting.",
        [
            ("fell-below-three-nines", "Twice in the past quarter, your EU-West cluster fell below the contractually guaranteed 99.9% uptime threshold.", "Dos veces en el último trimestre, su clúster europeo cayó por debajo del umbral garantizado del 99.9% de disponibilidad.", "📉☁️", "uptime threshold", "umbral mínimo de disponibilidad", "ˈʌptaɪm ˈθreʃhoʊld", "Expón que en dos ocasiones cayeron por debajo del 99.9% garantizado por contrato.", "We value your partnership and want to discuss your upcoming multi-year enterprise renewal."),
            ("token-credits-insufficient", "A five-percent invoice credit doesn't offset the engineering hours we burned failing over traffic manually.", "Un crédito del cinco por ciento en factura no compensa las horas de ingeniería que gastamos desviando tráfico manualmente.", "⚖️⏱️", "offset", "compensar / contrarrestar", "ˈɔːfset", "Deja claro que un 5% de descuento no compensa las horas de ingeniería invertidas.", "We did issue the standard five-percent SLA credit for last month's incident."),
            ("multi-region-active-failover", "Before we sign a renewal, we need multi-region active-active failover included at our current tier price.", "Antes de firmar la renovación, necesitamos respaldo activo-activo multirregión incluido al precio de nuestro plan actual.", "🌐🛡️", "failover", "conmutación automática por error", "ˈfeɪloʊvər", "Condiciona la renovación a que incluyan respaldo multirregión activo sin costo extra.", "What architectural and commercial terms would restore your confidence for the renewal?"),
            ("chronic-breach-termination-right", "We also require a termination-for-cause clause if latency or uptime breaches occur in two consecutive months.", "También exigimos una cláusula de rescisión sin penalización si ocurren incumplimientos en dos meses consecutivos.", "📑🔓", "breaches", "incumplimientos contractuales", "ˈbriːtʃɪz", "Exige incluir una cláusula de salida sin penalización ante fallos en dos meses seguidos.", "I can get VP approval to bundle active-active multi-region routing at your current rate."),
            ("fifteen-minute-incident-bridge", "Your enterprise SLA must also guarantee a live engineering bridge within fifteen minutes of a Sev-1 alert.", "Su SLA empresarial también debe garantizar un canal técnico en vivo en menos de quince minutos ante una alerta crítica.", "🚨📞", "Sev-1 alert", "alerta de severidad máxima", "sev wʌn əˈlɜːrt", "", ""),
            ("send-redlined-msa", "Our legal team will send the redlined Master Services Agreement by five o'clock.", "Nuestro equipo legal enviará el contrato marco con marcas de revisión antes de las cinco.", "✍️📄", "redlined", "con control de cambios jurídicos", "ˈredlaɪnd", "", ""),
        ],
    ),
    (
        "work-and-career", "C1", "managing-up-priorities", "Aligning competing executive priorities", "Alinear prioridades con directivos",
        "Plantea con claridad ante dos vicepresidentes que la capacidad de ingeniería es fija y deben elegir qué proyecto sale primero.",
        "VP of Marketing & VP of Sales", "product director", "Executive roadmap trade-off alignment session.",
        [
            ("fixed-engineering-bandwidth", "With our current engineering bandwidth, we can deliver either the self-serve onboarding flow or the Salesforce sync by May first—not both.", "Con nuestra capacidad actual de ingeniería, podemos entregar el flujo de autogestión o la integración con Salesforce para el primero de mayo, no ambos.", "⚖️🗓️", "bandwidth", "capacidad operativa disponible", "ˈbændwɪdθ", "Explica con claridad que con la capacidad actual solo uno de los dos proyectos puede salir el 1 de mayo.", "Both the enterprise Salesforce connector and the self-serve signup revamp are marked P0 for May!"),
            ("context-switching-tax", "Splitting the squad fifty-fifty across both initiatives would introduce a heavy context-switching tax and delay both into June.", "Dividir al equipo mitad y mitad entre ambas iniciativas generaría un alto costo por cambio de contexto y retrasaría ambas hasta junio.", "🔀⏳", "context-switching", "cambio constante de tarea", "ˈkɑːntekst ˈswɪtʃɪŋ", "Advierte que dividir al equipo retrasaría ambos lanzamientos hasta junio.", "Why can't we just have half the engineers work on each workstream in parallel?"),
            ("sequence-by-revenue-impact", "If we sequence the Salesforce sync first for the enterprise pipeline, we can ship it in three weeks and start self-serve immediately after.", "Si priorizamos primero la integración con Salesforce para ventas corporativas, la entregamos en tres semanas e iniciamos autogestión enseguida.", "📈🎯", "sequence", "secuenciar / ordenar en fila", "ˈsiːkwəns", "Propón entregar primero Salesforce en tres semanas y enseguida atacar autogestión.", "The enterprise quarter closes May 15th, so the Salesforce sync unlocks three immediate deals."),
            ("document-tradeoff-decision", "Great—let's lock in Salesforce as Priority 1 for April and publish the updated roadmap so the squad has unambiguous focus.", "Excelente: fijemos Salesforce como Prioridad 1 para abril y publiquemos la hoja de ruta para que el equipo tenga foco total.", "✅🧭", "unambiguous", "inequívoco / sin ambigüedades", "ˌʌnæmˈbɪɡjuəs", "Confirma el acuerdo de priorizar Salesforce en abril y documentarlo en la hoja de ruta.", "Sequencing them three weeks apart makes sense—Marketing can time the self-serve campaign for late May."),
            ("protect-sprint-from-scope-creep", "Any new requests during the next three weeks will go into the May backlog review.", "Cualquier solicitud nueva durante las próximas tres semanas pasará a la revisión de mayo.", "🛡️📋", "scope creep", "expansión descontrolada del alcance", "skoʊp kriːp", "", ""),
            ("appreciate-decisive-alignment", "Thank you both for making the trade-off call—this clarity sets the team up to execute fast.", "Gracias a ambos por tomar la decisión de priorización; esta claridad permite al equipo avanzar rápido.", "🤝🚀", "sets up", "prepara el terreno para el éxito", "sets ʌp", "", ""),
        ],
    ),
    (
        "work-and-career", "C1", "post-mortem-incident-lead", "Leading a blameless technical post-mortem", "Dirigir análisis post-mortem sin culpas",
        "Dirige una revisión técnica tras un incidente de base de datos, identificando brechas de monitoreo y acciones automáticas.",
        "platform engineer", "incident commander", "Engineering post-mortem review meeting.",
        [
            ("blameless-systemic-focus", "Our goal in this post-mortem is to uncover the systemic gaps that allowed a bad migration script to reach production.", "Nuestro objetivo en este análisis es descubrir las brechas sistémicas que permitieron que una migración defectuosa llegara a producción.", "🔍🛡️", "uncover", "descubrir / sacar a la luz", "ʌnˈkʌvər", "Establece que el objetivo es encontrar brechas del sistema y no señalar personas.", "The migration locked the orders table for twelve minutes before we rolled it back."),
            ("staging-lacked-production-volume", "Because our staging database only holds ten thousand rows, the table lock wasn't visible during pre-deploy checks.", "Como nuestra base de pruebas solo tiene diez mil filas, el bloqueo de tabla no fue visible en las validaciones previas.", "🗄️📊", "table lock", "bloqueo de escritura en tabla", "ˈteɪbəl lɑːk", "Explica por qué el entorno de pruebas no detectó el bloqueo por tener pocos datos.", "Why didn't the automated CI pipeline catch the full-table scan?"),
            ("add-linter-for-ddl-locks", "As our primary remediation, we're adding a migration linter in CI that rejects any schema change without a lock timeout.", "Como medida principal, agregaremos un validador en CI que rechace cualquier cambio de esquema sin tiempo límite de bloqueo.", "🤖✅", "remediation", "medida correctiva de fondo", "rɪˌmiːdiˈeɪʃən", "Propón un validador automático en CI que exija límite de tiempo en migraciones.", "That makes total sense. How do we prevent an unindexed alter-table from merging again?"),
            ("time-to-recovery-praise", "On the positive side, our automated canary alarm fired within ninety seconds and the rollback runbook worked flawlessly.", "En el lado positivo, nuestra alarma automática se activó en noventa segundos y el manual de reversión funcionó impecablemente.", "⏱️👏", "flawlessly", "sin fallos / impecablemente", "ˈflɔːləsli", "Destaca que la alerta temprana y el protocolo de reversión funcionaron en 90 segundos.", "We'll have that CI linter rule merged before tomorrow's deploy window."),
            ("synthetic-load-in-staging", "We'll also seed anonymized million-row tables in staging to mirror production query plans.", "También cargaremos tablas anónimas de un millón de filas en pruebas para reflejar el volumen real.", "📈🔬", "mirror", "reflejar / replicar fielmente", "ˈmɪrər", "", ""),
            ("publish-postmortem-to-wiki", "I'll publish the post-mortem summary and due dates to the engineering wiki today.", "Publicaré hoy el resumen del análisis y las fechas compromiso en la wiki de ingeniería.", "📑🌐", "wiki", "base de conocimiento interna", "ˈwɪki", "", ""),
        ],
    ),
    # C2 (4 new)
    (
        "work-and-career", "C2", "ma-due-diligence-brief", "Defending valuation in M&A due diligence", "Defender valuación en auditoría de compra (M&A)",
        "Defiende ante el comité de adquisiciones la retención neta de ingresos, la propiedad intelectual y las sinergias operativas.",
        "managing director (acquirer)", "chief strategy officer", "Confirmatory M&A due diligence session.",
        [
            ("net-dollar-retention-cohorts", "Across our enterprise cohorts, net dollar retention has compounded at a hundred and twenty-eight percent over twelve quarters.", "En nuestras cohortes empresariales, la retención neta en dólares se ha compuesto al ciento veintiocho por ciento durante doce trimestres.", "📈🏛️", "compounded", "crecido de forma compuesta", "kəmˈpaʊndɪd", "Destaca la retención neta de ingresos del 128% sostenida durante doce trimestres.", "Let's examine customer stickiness—how resilient is your recurring revenue if macro budgets tighten?"),
            ("clean-ip-chain-of-title", "Our external IP counsel completed a comprehensive open-source audit confirming an unencumbered chain of title across all core patents.", "Nuestros asesores de propiedad intelectual completaron una auditoría exhaustiva confirmando titularidad limpia en todas las patentes clave.", "⚖️🔐", "unencumbered", "libre de gravámenes o reclamos", "ˌʌnɪnˈkʌmbərd", "Confirma que la auditoría de propiedad intelectual verificó titularidad limpia.", "And did the technical audit surface any copyleft contamination in your proprietary inference engine?"),
            ("cross-sell-accretive-margin", "Integrating our compliance module into your global salesforce becomes accretive to EBITDA within two quarters of closing.", "Integrar nuestro módulo de cumplimiento en su fuerza de ventas global aporta positivamente al EBITDA en dos trimestres tras el cierre.", "💹🤝", "accretive", "que incrementa el valor / margen por acción", "əˈkriːtɪv", "Explica que la venta cruzada incrementará el EBITDA en solo dos trimestres.", "How quickly do the commercial synergies materialize post-acquisition?"),
            ("escrow-indemnity-cap", "Given the clean audit findings, we propose capping the general indemnity escrow at five percent with a twelve-month survival period.", "Dados los resultados limpios de la auditoría, proponemos topar el fideicomiso de garantía en cinco por ciento por doce meses.", "🏦✍️", "escrow", "depósito en garantía / fideicomiso", "ˈeskroʊ", "Propón limitar la retención en garantía al 5% durante doce meses.", "Our diligence committee is satisfied with both the cohort data and the IP clearance."),
            ("key-talent-vesting-retention", "Restructuring the unvested equity into milestone retention grants keeps the founding engineering leads locked in.", "Reestructurar las acciones en bonos por hitos asegura la permanencia de los líderes técnicos fundadores.", "🎯🔒", "unvested", "acciones aún en periodo de consolidación", "ʌnˈvestɪd", "", ""),
            ("proceed-to-definitive-spa", "We are aligned to instruct counsel to finalize the Share Purchase Agreement for Friday signature.", "Estamos alineados para instruir a los abogados a cerrar el contrato de compraventa este viernes.", "📄✅", "aligned", "en pleno acuerdo", "əˈlaɪnd", "", ""),
        ],
    ),
    (
        "work-and-career", "C2", "crisis-comms-press-briefing", "Leading a regulatory press briefing", "Liderar comunicación de crisis ante prensa",
        "Responde con aplomo y transparencia ante periodistas tras una auditoría regulatoria, detallando las medidas independientes adoptadas.",
        "financial journalist", "chief communications officer", "Live broadcast press briefing at company headquarters.",
        [
            ("proactive-self-disclosure", "Let me be unequivocal: we discovered the reporting anomaly internally and self-disclosed it to the regulator within twenty-four hours.", "Permítanme ser categórico: detectamos la anomalía internamente y la reportamos por iniciativa propia al regulador en veinticuatro horas.", "🎙️🏛️", "unequivocal", "categórico / inequívoco", "ˌʌnɪˈkwɪvəkəl", "Deja claro de forma categórica que la empresa detectó y reportó la anomalía por iniciativa propia.", "Did the company only disclose the accounting reclassification after regulators opened an inquiry?"),
            ("independent-forensic-review", "The audit committee immediately commissioned an independent forensic firm whose mandate is unrestricted.", "El comité de auditoría contrató de inmediato a una firma forense independiente con mandato irrestricto.", "🔍⚖️", "commissioned", "encargó oficialmente", "kəˈmɪʃənd", "Explica que el comité de auditoría encargó una revisión forense independiente sin restricciones.", "How can investors trust an internal review conducted by the same management team?"),
            ("zero-impact-customer-funds", "Crucially, this is a timing reclassification between fiscal quarters—customer deposits and cash reserves remain ring-fenced and intact.", "De manera crucial, se trata de una reclasificación temporal entre trimestres; los fondos de clientes y reservas permanecen intactos.", "🛡️🏦", "ring-fenced", "blindados en cuentas separadas", "rɪŋ fenst", "Subraya que los fondos de los clientes y reservas de efectivo están intactos.", "Does this restatement affect client balances or your liquidity covenants?"),
            ("publish-unredacted-findings", "We will publish the executive summary of the independent findings alongside our restated Q2 filings next Tuesday.", "Publicaremos el resumen ejecutivo del informe independiente junto con los estados financieros el próximo martes.", "📑🌐", "alongside", "junto con / de forma simultánea", "əˌlɔːŋˈsaɪd", "Compromete la publicación de las conclusiones independientes el próximo martes.", "When will the market see the final numbers and governance changes?"),
            ("remediate-internal-controls", "We have already separated the treasury sign-off chain to eliminate any single point of failure.", "Ya hemos separado la cadena de firmas de tesorería para eliminar cualquier punto único de fallo.", "🔒✅", "single point of failure", "punto único de fallo", "ˈsɪŋɡəl pɔɪnt əv ˈfeɪljər", "", ""),
            ("transparency-restores-trust", "Credibility is earned through verifiable action, and we will answer every question as the audit concludes.", "La credibilidad se gana con hechos verificables y responderemos cada pregunta al concluir la auditoría.", "🤝🌟", "verifiable", "verificable", "ˈverɪfaɪəbəl", "", ""),
        ],
    ),
    (
        "work-and-career", "C2", "shareholder-activist-qa", "Fielding shareholder questions at an AGM", "Responder a accionistas en asamblea anual",
        "Defiende en la asamblea anual de accionistas la inversión en I+D de largo plazo frente a recompras de acciones de corto plazo.",
        "institutional shareholder", "chief executive officer", "Annual General Meeting podium fielding live Q&A.",
        [
            ("balance-buybacks-with-rd", "Starving our R&D pipeline to fund short-term share buybacks would mortgage our competitive moat for a fleeting EPS bump.", "Recortar nuestra inversión en I+D para financiar recompras de corto plazo hipotecaría nuestra ventaja competitiva por un alza efímera.", "🏛️📈", "competitive moat", "ventaja competitiva sostenible / foso defensivo", "kəmˈpetətɪv moʊt", "Argumenta que recortar I+D por recompras de corto plazo hipotecaría la ventaja competitiva.", "Why is the board allocating eighteen percent of revenue to R&D instead of doubling the share buyback program?"),
            ("roic-hurdle-rate", "Every capital-allocation tranche must clear a twenty-percent return-on-invested-capital hurdle rate before release.", "Cada tramo de asignación de capital debe superar una tasa mínima de retorno del veinte por ciento antes de liberarse.", "🎯💹", "hurdle rate", "tasa mínima aceptable de rentabilidad", "ˈhɜːrdəl reɪt", "Explica que cada inversión debe superar una rentabilidad mínima del 20%.", "How do shareholders know that R&D spend is disciplined rather than pet projects?"),
            ("patents-driving-new-arr", "Forty percent of this year's net-new enterprise bookings came directly from products commercialized out of our lab two years ago.", "El cuarenta por ciento de las nuevas ventas corporativas de este año provino de productos creados en nuestro laboratorio hace dos años.", "🔬🚀", "commercialized", "llevados al mercado con éxito", "kəˈmɜːrʃəlaɪzd", "Demuestra con datos que el 40% de las nuevas ventas proviene de innovaciones de hace dos años.", "Can you point to tangible top-line revenue generated by those previous R&D cohorts?"),
            ("disciplined-dividend-growth", "Even while funding next-generation AI, we expanded free cash flow and raised our dividend for the ninth consecutive year.", "Incluso financiando la nueva generación tecnológica, ampliamos el flujo de caja libre y subimos el dividendo por noveno año consecutivo.", "🏦🌟", "consecutive", "consecutivo / seguido", "kənˈsekjətɪv", "Cierra destacando el crecimiento del flujo de caja libre y nueve años subiendo el dividendo.", "That conversion from lab to enterprise bookings is impressive context."),
            ("sunset-underperforming-bets", "We killed two underperforming initiatives in Q1 and redeployed those engineers to our highest-margin platform.", "Cerramos dos iniciativas de bajo rendimiento en el primer trimestre y reasignamos ese talento a la plataforma de mayor margen.", "🧭✂️", "redeployed", "reasignamos estratégicamente", "ˌriːdɪˈplɔɪd", "", ""),
            ("long-term-compounding-value", "Our mandate is compounding intrinsic value over decades, not optimizing for a single quarter's headline.", "Nuestro mandato es multiplicar el valor intrínseco por décadas, no optimizar el titular de un solo trimestre.", "🤝⏳", "intrinsic value", "valor intrínseco fundamental", "ɪnˈtrɪnzɪk ˈvæljuː", "", ""),
        ],
    ),
    (
        "work-and-career", "C2", "global-reorg-townhall", "Communicating a strategic reorganization", "Comunicar reestructuración global en townhall",
        "Explica en una asamblea global por qué la empresa pasa de silos regionales a unidades de producto globales sin recortes de personal.",
        "global employee", "chief operating officer", "Global all-hands townhall broadcast across twelve offices.",
        [
            ("shift-from-silos-to-pods", "Today we're realigning from regional silos into global product pods so decisions happen closest to the customer.", "Hoy pasamos de silos regionales a unidades globales de producto para que las decisiones se tomen más cerca del cliente.", "🌍🧭", "silos", "departamentos aislados / silos", "ˈsaɪloʊz", "Explica el paso de silos regionales a unidades globales cercanas al cliente.", "Thanks for hosting this townhall. Why are we changing our organizational structure right now?"),
            ("zero-headcount-reduction", "Let me state this upfront: this reorganization is about speed and clarity, with zero headcount reduction.", "Quiero decirlo desde el principio: esta reorganización busca velocidad y claridad, sin ningún recorte de personal.", "🛡️🤝", "upfront", "de entrada / con total franqueza", "ˌʌpˈfrʌnt", "Aclara desde el inicio que la reorganización no implica ningún recorte de personal.", "Whenever people hear the word 'reorg,' the first worry is layoffs—are any roles being eliminated?"),
            ("eliminate-duplicate-approvals", "Previously, launching a feature in three regions required fourteen sign-offs; under the new model, one pod lead owns it end-to-end.", "Antes, lanzar una función en tres regiones requería catorce firmas; bajo el nuevo modelo, un líder la gestiona de principio a fin.", "⚡✅", "end-to-end", "de principio a fin / integralmente", "end tuː end", "Ilustra cómo se eliminan catorce firmas burocráticas dando autonomía de principio a fin.", "How will this change our day-to-day workflow when shipping cross-border features?"),
            ("one-on-one-mapping-calls", "Every manager is holding 1-on-1 transition chats over the next forty-eight hours so everyone knows their pod and charter.", "Cada gerente tendrá reuniones individuales en las próximas cuarenta y ocho horas para que todos conozcan su equipo y misión.", "📅💬", "charter", "misión / mandato del equipo", "ˈtʃɑːrtər", "Informa que en las próximas 48 horas cada persona tendrá su reunión individual de transición.", "When will individual contributors find out which global pod they belong to?"),
            ("async-norms-across-timezones", "To protect work-life balance across time zones, we're adopting asynchronous decision memos before scheduling meetings.", "Para proteger el equilibrio entre zonas horarias, adoptaremos documentos de decisión asíncronos.", "🕒📝", "asynchronous", "asíncrono (sin exigir conexión simultánea)", "eɪˈsɪŋkrənəs", "", ""),
            ("open-office-hours-all-week", "My calendar is open for drop-in office hours all week—let's build this next chapter together.", "Mi agenda está abierta toda la semana para consultas directas; construyamos juntos esta etapa.", "🚪🌟", "drop-in", "de puertas abiertas / sin cita previa", "drɑːp ɪn", "", ""),
        ],
    ),
    # ==================== 6. HEALTH-AND-EMERGENCIES ====================
    # A1 (4 new)
    (
        "health-and-emergencies", "A1", "buying-sunscreen", "Buying sunscreen and aloe vera", "Comprar protector solar en la farmacia",
        "Pide un bloqueador solar factor 50 y gel de aloe vera para una quemadura de sol en la playa.",
        "pharmacist", "beachgoer", "A coastal pharmacy on a hot sunny day.",
        [
            ("sunscreen-fifty-spf", "Hello, do you have sunscreen with SPF 50?", "Hola, ¿tienen protector solar con factor 50?", "🧴☀️", "sunscreen", "protector / bloqueador solar", "ˈsʌnskriːn", "Pregunta si tienen protector solar con factor 50.", "Hello! Welcome to Beach Pharmacy. How can I help you?"),
            ("red-shoulders-from-sun", "My shoulders are red from the sun today.", "Mis hombros están rojos por el sol de hoy.", "🏖️🔴", "shoulders", "hombros", "ˈʃoʊldərz", "Explica que tus hombros están rojos por el sol.", "Yes, here is our waterproof SPF 50 lotion."),
            ("cooling-aloe-gel", "Do you have cold aloe vera gel for my skin?", "¿Tienen gel frío de aloe vera para mi piel?", "🌿🧊", "skin", "piel", "skɪn", "Pide gel frío de aloe vera para tu piel.", "Oh, a mild sunburn! You should put cooling gel on it."),
            ("drink-lots-of-water", "I will also buy two big bottles of water.", "También compraré dos botellas grandes de agua.", "💧🍾", "bottles", "botellas", "ˈbɑːtəlz", "Agrega dos botellas grandes de agua.", "This green aloe gel feels very cool and gentle."),
            ("wear-a-sun-hat", "Put the gel on three times a day.", "Aplique el gel tres veces al día.", "🕒👌", "three times", "tres veces", "θriː taɪmz", "", ""),
            ("thank-you-pharmacist", "Thank you! My skin will feel better tonight.", "¡Gracias! Mi piel se sentirá mejor esta noche.", "😌🌙", "tonight", "esta noche", "təˈnaɪt", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "A1", "headache-and-water", "Telling a guide you feel dizzy", "Avisar que tienes dolor de cabeza en un tour",
        "Dile al guía turístico que tienes dolor de cabeza por el calor y necesitas sentarte a la sombra.",
        "tour guide", "visitor", "Walking tour in a sunny historic square.",
        [
            ("have-a-headache", "Excuse me, I have a headache from the heat.", "Disculpe, tengo dolor de cabeza por el calor.", "🤕☀️", "headache", "dolor de cabeza", "ˈhedeɪk", "Dile al guía que tienes dolor de cabeza por el calor.", "Are you okay? You look a little pale."),
            ("sit-in-the-shade", "Can we sit on that bench in the shade?", "¿Podemos sentarnos en esa banca a la sombra?", "🪑🌳", "bench", "banca", "bentʃ", "Pide sentarte en la banca que está a la sombra.", "Of course! Let's stop right here under the trees."),
            ("need-some-water", "May I have some cold water, please?", "¿Me puede dar un poco de agua fría, por favor?", "💧🥤", "cold water", "agua fría", "koʊld ˈwɔːtər", "Pide un poco de agua fría.", "Sit down and take slow breaths. Here is a new bottle of water."),
            ("rest-for-ten-minutes", "I just need to rest here for ten minutes.", "Solo necesito descansar aquí diez minutos.", "⏱️😌", "rest", "descansar", "rest", "Indica que solo necesitas descansar diez minutos.", "Take all the time you need—the museum cafe is right behind us."),
            ("take-an-aspirin", "I have a mild pain pill in my small bag.", "Traigo una pastilla suave para el dolor en mi bolso.", "💊👜", "pill", "pastilla", "pɪl", "", ""),
            ("feeling-okay-now", "Thank you, the cool air helps a lot!", "¡Gracias, el aire fresco ayuda mucho!", "🌬️👍", "helps", "ayuda", "helps", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "A1", "lost-wallet-police", "Reporting a lost wallet to police", "Reportar pérdida de billetera a la policía",
        "Explica a un oficial de policía que perdiste tu billetera marrón cerca de la estación y deja tu teléfono.",
        "police officer", "visitor", "Police information booth near the main square.",
        [
            ("lost-my-wallet", "Excuse me, Officer. I lost my wallet in the park.", "Disculpe, oficial. Perdí mi billetera en el parque.", "👮‍♂️👛", "lost", "perdí", "lɔːst", "Dile al oficial que perdiste tu billetera en el parque.", "Hello! Stay calm, how can I help you today?"),
            ("small-brown-leather", "It is a small brown leather wallet with a zipper.", "Es una billetera pequeña de cuero marrón con cierre.", "🤎🔍", "leather", "cuero / piel", "ˈleðər", "Describe que es una billetera pequeña de cuero marrón.", "When did you last see it, and what does it look like?"),
            ("has-my-id-inside", "My ID card and bank card are inside it.", "Mi identificación y mi tarjeta del banco están adentro.", "🪪💳", "inside", "adentro / en el interior", "ɪnˈsaɪd", "Explica que adentro están tu identificación y tu tarjeta bancaria.", "Okay, let me check our lost-and-found desk log."),
            ("write-my-phone-number", "Here is my name and my hotel phone number.", "Aquí están mi nombre y el teléfono de mi hotel.", "📝🏨", "name", "nombre", "neɪm", "Deja tu nombre y el número de teléfono de tu hotel.", "Please lock your bank card on your phone app right now, and leave your contact info."),
            ("keep-passport-at-hotel", "Thankfully, my passport is safe at the hotel.", "Por suerte, mi pasaporte está seguro en el hotel.", "🛂✅", "safe", "seguro / a salvo", "seɪf", "", ""),
            ("call-if-someone-brings-it", "Thank you, Officer! Please call me if someone finds it.", "¡Gracias, oficial! Por favor llámeme si alguien la encuentra.", "📞🙏", "finds", "encuentra", "faɪndz", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "A1", "calling-ambulance-address", "Giving your address for an emergency", "Dar la dirección para una ambulancia",
        "Llama al número de emergencias para pedir una ambulancia e indica la calle y el número con claridad.",
        "emergency operator", "caller", "Calling emergency services from a store entrance.",
        [
            ("need-an-ambulance", "Hello, we need an ambulance right away, please.", "Hola, necesitamos una ambulancia de inmediato, por favor.", "🚑📞", "ambulance", "ambulancia", "ˈæmbjələns", "Pide una ambulancia de inmediato.", "Emergency services, do you need police, fire, or an ambulance?"),
            ("man-fell-on-stairs", "An older man fell on the stairs and hurt his leg.", "Un señor mayor se cayó en las escaleras y se lastimó la pierna.", "🪜🦵", "hurt", "lastimó / hirió", "hɜːrt", "Explica que un señor mayor cayó en las escaleras y se lastimó la pierna.", "What happened, and is the person awake and breathing?"),
            ("he-is-awake-and-talking", "Yes, he is awake and talking to us now.", "Sí, está despierto y hablando con nosotros ahora.", "🗣️✅", "awake", "despierto / consciente", "əˈweɪk", "Confirma que está despierto y hablando.", "Good. What is the exact street address where you are?"),
            ("forty-two-king-street", "We are at 42 King Street, in front of the bank.", "Estamos en el 42 de King Street, frente al banco.", "📍🏦", "street", "calle", "striːt", "Indica la dirección exacta: 42 King Street, frente al banco.", "The ambulance is on the way—it will be there in four minutes!"),
            ("stay-with-him-here", "We will stay with him until the paramedics arrive.", "Nos quedaremos con él hasta que lleguen los paramédicos.", "🤝🚑", "stay", "quedarse", "steɪ", "", ""),
            ("wave-at-the-corner", "My friend is waiting at the corner to wave to the driver.", "Mi amigo espera en la esquina para hacer señas al conductor.", "👋🚨", "corner", "esquina", "ˈkɔːrnər", "", ""),
        ],
    ),
    # A2 (4 new)
    (
        "health-and-emergencies", "A2", "stomach-flu-remedy", "Getting stomach remedies at a pharmacy", "Pedir suero oral por malestar estomacal",
        "Explica al farmacéutico que comiste algo que te cayó mal ayer y pide sales de rehidratación oral.",
        "pharmacist", "traveler", "Neighborhood pharmacy counter in the morning.",
        [
            ("upset-stomach-since-last-night", "Hi, I've had an upset stomach and nausea since dinner last night.", "Hola, tengo malestar estomacal y náuseas desde la cena de anoche.", "🤢💊", "upset stomach", "malestar estomacal / indigestión", "ʌpˈset ˈstʌmək", "Explica que tienes malestar estomacal y náuseas desde anoche.", "Good morning! How can I help you feel better today?"),
            ("rehydration-electrolyte-powder", "Do you have oral rehydration salts or electrolyte packets I can mix with water?", "¿Tienen sales de rehidratación oral o sobres de electrolitos para mezclar con agua?", "💧🥤", "packets", "sobres individuales", "ˈpækɪts", "Pregunta por sales de rehidratación o sobres de electrolitos.", "I'm sorry to hear that! Staying hydrated is the most important thing."),
            ("gentle-on-the-stomach", "Is there a mild tablet that helps stop nausea without making me sleepy?", "¿Hay alguna pastilla suave para las náuseas que no dé sueño?", "💊😌", "sleepy", "con sueño / somnoliento", "ˈsliːpi", "Pregunta si tienen alguna pastilla para las náuseas que no dé sueño.", "Yes, dissolve one of these lemon electrolyte sachets in a tall bottle of water."),
            ("stick-to-plain-toast", "Should I stick to plain toast, rice, and herbal tea for today?", "¿Debería comer solo pan tostado, arroz y té de hierbas por hoy?", "🍞🍵", "stick to", "limitarse a / mantenerse con", "stɪk tuː", "Pregunta si conviene comer solo pan tostado, arroz y té hoy.", "These ginger and vitamin B6 tablets calm the stomach and are non-drowsy."),
            ("no-fever-just-weak", "I don't have a fever, I just feel a bit tired and dehydrated.", "No tengo fiebre, solo me siento un poco cansado y deshidratado.", "🌡️👌", "fever", "fiebre / temperatura", "ˈfiːvər", "", ""),
            ("see-doctor-if-continues", "If it doesn't improve by tomorrow morning, I'll visit the walk-in clinic.", "Si no mejora para mañana temprano, iré a la clínica sin cita.", "🏥✅", "improve", "mejorar", "ɪmˈpruːv", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "A2", "eye-drops-allergy", "Buying allergy eye drops", "Pedir gotas para alergia ocular",
        "Pide gotas antihistamínicas porque el polen de primavera te causa picazón en los ojos.",
        "pharmacist", "customer", "Pharmacy counter during spring pollen season.",
        [
            ("itchy-watery-eyes", "Hello! The tree pollen is giving me very itchy, watery eyes today.", "¡Hola! El polen de los árboles me está causando mucha picazón y lagrimeo hoy.", "👁️🌸", "itchy", "con picazón / comezón", "ˈɪtʃi", "Explica que el polen te causa picazón y lagrimeo en los ojos.", "Hello! Spring allergy season is in full swing. What symptoms are bothering you?"),
            ("antihistamine-eye-drops", "Can I buy antihistamine eye drops without a doctor's prescription?", "¿Puedo comprar gotas antihistamínicas para los ojos sin receta médica?", "💧👁️", "prescription", "receta médica", "prɪˈskrɪpʃən", "Pregunta si venden gotas antihistamínicas sin receta médica.", "Yes, our over-the-counter allergy eye drops work within ten minutes!"),
            ("safe-with-contact-lenses", "I wear soft contact lenses—should I take them out before putting the drops in?", "Uso lentes de contacto blandos; ¿debo quitármelos antes de ponerme las gotas?", "👓💧", "take them out", "quitárselos / retirarlos", "teɪk ðem aʊt", "Pregunta si debes quitarte los lentes de contacto antes de aplicar las gotas.", "Here is a preservative-free bottle. Do you wear contact lenses?"),
            ("one-drop-twice-a-day", "So I put one drop in each eye in the morning and evening?", "¿Entonces pongo una gota en cada ojo por la mañana y por la noche?", "🕗🌙", "each", "cada", "iːtʃ", "Confirma la dosis de una gota en cada ojo mañana y noche.", "Yes, remove your contacts, put one drop in each eye, and wait fifteen minutes."),
            ("saline-nasal-spray", "I'll also take a simple saline nasal spray for my stuffy nose.", "También llevaré un spray nasal salino para la nariz tapada.", "👃🌿", "stuffy nose", "nariz tapada / congestión", "ˈstʌfi noʊz", "", ""),
            ("sunglasses-help-outside", "Wearing wrap-around sunglasses in the park helps block the pollen too!", "Usar lentes de sol en el parque también ayuda a frenar el polen.", "🕶️🌳", "block", "bloquear / frenar", "blɑːk", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "A2", "hotel-doctor-visit", "Asking the hotel for an English-speaking doctor", "Pedir en recepción un médico que hable inglés",
        "Llama a la recepción del hotel porque tu compañero tiene fiebre y dolor de oído y necesitan un médico.",
        "hotel concierge", "guest", "Calling the hotel concierge desk from your room.",
        [
            ("english-speaking-doctor", "Hello, does the hotel have an English-speaking doctor on call?", "Hola, ¿el hotel cuenta con un médico de guardia que hable inglés?", "🩺🏨", "on call", "disponible de guardia", "ɑːn kɔːl", "Pregunta si el hotel tiene contacto con un médico que hable inglés.", "Concierge desk, good afternoon! How may I assist you?"),
            ("earache-and-fever", "My travel partner has a strong earache and a fever of thirty-eight point five.", "Mi compañero de viaje tiene un fuerte dolor de oído y fiebre de treinta y ocho punto cinco.", "🤒👂", "earache", "dolor de oído", "ˈɪreɪk", "Explica que tu compañero tiene dolor de oído y fiebre de 38.5.", "Yes, we work with an international clinic two blocks away, or a doctor can visit your room."),
            ("come-to-our-room", "Could the doctor come to Room 508 this afternoon so he doesn't have to travel?", "¿Podría el médico venir a la habitación 508 esta tarde para que no tenga que salir?", "🚪🩺", "travel", "desplazarse / salir", "ˈtrævəl", "Pide que el médico acuda a la habitación 508 esta tarde.", "A room visit is very convenient when someone has a fever. Let me call Dr. Meyer right now."),
            ("printed-receipt-for-insurance", "Will the doctor give us an official medical receipt for our travel insurance?", "¿El médico nos dará un recibo oficial para nuestro seguro de viaje?", "🧾✈️", "official", "oficial / con sello", "əˈfɪʃəl", "Pregunta si el médico entregará recibo oficial para el seguro de viaje.", "Dr. Meyer can be at Room 508 in forty minutes. The consultation fee is ninety euros."),
            ("send-up-thermometer", "In the meantime, could housekeeping bring up extra bottled water?", "Mientras tanto, ¿podrían subirnos agua embotellada extra?", "💧🛎️", "in the meantime", "mientras tanto", "ɪn ðə ˈmiːntaɪm", "", ""),
            ("thank-you-for-arranging", "Thank you so much for arranging the visit so quickly!", "¡Muchas gracias por coordinar la visita tan rápido!", "🙏✨", "arranging", "coordinar / gestionar", "əˈreɪndʒɪŋ", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "A2", "reporting-stolen-phone", "Filing a police report for a stolen phone", "Obtener acta policial por robo de teléfono",
        "Solicita en la comisaría un acta policial con sello para que tu seguro te reponga el teléfono.",
        "desk officer", "tourist", "Tourist police station reception desk.",
        [
            ("report-stolen-phone", "Good afternoon, I need to file a police report for my stolen mobile phone.", "Buenas tardes, necesito levantar un acta policial por el robo de mi teléfono móvil.", "📱👮", "file a report", "levantar un reporte / denuncia", "faɪl ə rɪˈpɔːrt", "Explica que necesitas levantar un acta policial por el robo de tu teléfono.", "Good afternoon. Come to window two—are you safe and unharmed?"),
            ("taken-from-coat-pocket", "Someone took it from my coat pocket on the crowded tram around noon.", "Alguien lo sacó del bolsillo de mi abrigo en el tranvía lleno alrededor del mediodía.", "🚊🧥", "crowded", "lleno de gente / concurrido", "ˈkraʊdɪd", "Cuenta que lo sacaron de tu abrigo en el tranvía al mediodía.", "Yes, I'm glad you weren't hurt. Where and when did this happen?"),
            ("locked-via-find-my", "I already locked the screen remotely using my friend's tablet and wrote down the IMEI number.", "Ya bloqueé la pantalla a distancia con la tablet de mi amigo y anoté el número IMEI.", "🔒🔢", "remotely", "a distancia / remotamente", "rɪˈmoʊtli", "Indica que ya bloqueaste el equipo a distancia y tienes el número IMEI.", "Smart thinking! Having the serial or IMEI number helps our database a lot."),
            ("stamped-copy-for-insurance", "Could I get a stamped paper copy of the report to send to my insurance company?", "¿Podría darme una copia impresa y sellada del acta para enviarla a mi aseguradora?", "📑🖋️", "stamped", "sellada", "stæmpt", "Pide una copia impresa y sellada del reporte para tu seguro.", "I've typed all the details into the official incident form. Please sign at the bottom."),
            ("black-iphone-blue-case", "It is a black iPhone 15 in a dark blue silicone case.", "Es un iPhone 15 negro con una funda de silicona azul oscuro.", "📱🔵", "case", "funda protectora", "keɪs", "", ""),
            ("thank-you-for-your-help", "Thank you for your help and for printing the English version of the form!", "¡Gracias por su ayuda y por imprimir la versión en inglés del formulario!", "🤝📄", "version", "versión", "ˈvɜːrʒən", "", ""),
        ],
    ),
    # B1 (4 new)
    (
        "health-and-emergencies", "B1", "refilling-prescription", "Replacing lost medication while traveling", "Solicitar reposición de receta médica en viaje",
        "Explica en una clínica de viajeros que tu equipaje con tu medicamento para la presión se extravió y muestras la foto de tu receta.",
        "clinic physician", "traveler", "Walk-in travel clinic consultation room.",
        [
            ("airline-delayed-my-bag", "Hello Doctor. The airline delayed my suitcase containing my daily blood pressure medication.", "Hola doctor. La aerolínea demoró mi maleta donde venía mi medicamento diario para la presión.", "🧳💊", "blood pressure", "presión arterial", "blʌd ˈpreʃər", "Explica que la aerolínea demoró tu maleta con tu medicamento para la presión.", "Hello! Come sit down. What brings you to the travel clinic today?"),
            ("photo-of-prescription-label", "I have a clear photo on my phone showing the generic ingredient name and ten-milligram dosage.", "Tengo una foto clara en mi teléfono que muestra el nombre genérico y la dosis de diez miligramos.", "📱🔍", "dosage", "dosis", "ˈdoʊsɪdʒ", "Muestra en tu teléfono la foto con el ingrediente activo y la dosis de 10 mg.", "Never skip blood pressure medication! Do you know the exact chemical name and dose?"),
            ("two-week-supply-enough", "I only need a fourteen-day supply to cover the rest of my trip until I fly home.", "Solo necesito suministro para catorce días para cubrir el resto de mi viaje hasta regresar a casa.", "🗓️✈️", "supply", "suministro / cantidad de pastillas", "səˈplaɪ", "Indica que solo necesitas suministro para catorce días hasta volver a casa.", "Amlodipine 10mg—that is widely available here under the exact same generic name."),
            ("fill-at-pharmacy-next-door", "Can I take this local prescription straight to the pharmacy next door?", "¿Puedo llevar esta receta local directamente a la farmacia de al lado?", "🏥➡️", "next door", "de al lado / contigua", "nekst dɔːr", "Pregunta si puedes surtir esa receta en la farmacia de al lado.", "Let me check your blood pressure cuff reading quickly, and I'll write you a 14-day script."),
            ("take-every-morning-breakfast", "My blood pressure is 120 over 80—I take one tablet every morning with breakfast.", "Mi presión está en 120 sobre 80; tomo una pastilla cada mañana con el desayuno.", "🩺🥐", "tablet", "comprimido / pastilla", "ˈtæblət", "", ""),
            ("keep-meds-in-carryon", "From now on, I'll always pack my essential medications in my carry-on backpack!", "De ahora en adelante, ¡siempre llevaré mis medicamentos esenciales en la mochila de mano!", "🎒✅", "essential", "esenciales / indispensables", "ɪˈsenʃəl", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "B1", "minor-fender-bender", "Handling a minor parking lot bump", "Intercambiar datos tras un choque leve",
        "Mantén la calma tras un roce leve en un estacionamiento, verifica que todos estén bien y toma fotos del seguro.",
        "other driver", "driver", "Supermarket parking lot after a low-speed bumper scrape.",
        [
            ("everyone-okay-in-car", "First of all, are you and your passengers completely okay?", "Antes que nada, ¿usted y sus pasajeros están completamente bien?", "🚗🤝", "first of all", "antes que nada / lo primero", "fɜːrst əv ɔːl", "Pregunta primero si el otro conductor y sus pasajeros están bien.", "Oh gosh, I didn't see you backing out of that spot! Are you alright?"),
            ("just-a-paint-scrape", "Everyone is fine, thank goodness—it looks like just a minor paint scrape on the corner bumper.", "Todos estamos bien, por suerte; parece solo un raspón leve de pintura en la esquina del parachoques.", "🔍🚙", "scrape", "raspón / roce superficial", "skreɪp", "Tranquiliza al conductor indicando que solo es un raspón leve en el parachoques.", "Yes, we're fine! We were only moving at five miles an hour."),
            ("exchange-insurance-details", "Let's exchange photos of our driver's licenses, registration, and insurance cards.", "Intercambiemos fotos de nuestras licencias de conducir, registro y pólizas de seguro.", "🪪📸", "exchange", "intercambiar", "ɪksˈtʃeɪndʒ", "Propón intercambiar fotos de licencias, registro y seguro.", "Let's pull into these two empty spaces so we aren't blocking the lane."),
            ("take-wide-angle-photos", "I'll also take a few wide photos of both cars' positions for the rental agency's report.", "También tomaré unas fotos amplias de ambos autos para el reporte de la agencia de alquiler.", "📱🚗", "positions", "posiciones / ubicación", "pəˈzɪʃənz", "Toma fotos amplias de ambos autos para el reporte de la agencia.", "Here is my insurance card and phone number—feel free to snap a photo."),
            ("no-need-for-ambulance", "Since nobody is injured and both cars drive fine, we can file the claim online.", "Como nadie está herido y ambos autos circulan bien, podemos subir el reporte en línea.", "💻✅", "injured", "herido / lesionado", "ˈɪndʒərd", "", ""),
            ("drive-safely-home", "Thanks for handling this so calmly and politely—drive safely!", "Gracias por manejar esto con tanta calma y cortesía; ¡buen viaje!", "🙏🛣️", "calmly", "con calma", "ˈkɑːmli", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "B1", "bee-sting-swelling", "Treating an insect sting at urgent care", "Atender inflamación por picadura en urgencias",
        "Describe en un centro de atención rápida que te picó una avispa en el antebrazo y tienes inflamación local sin falta de aire.",
        "urgent care nurse", "patient", "Walk-in urgent care clinic near a national park.",
        [
            ("stung-by-wasp-on-trail", "Hi, I was stung on my forearm by a wasp about forty minutes ago while hiking.", "Hola, me picó una avispa en el antebrazo hace unos cuarenta minutos mientras caminaba.", "🐝💪", "stung", "picado (por abeja o avispa)", "stʌŋ", "Explica que te picó una avispa en el antebrazo hace cuarenta minutos.", "Come right in to Triage Room 2. What happened on the trail today?"),
            ("breathing-is-normal", "My breathing and swallowing are completely normal, so it's just localized swelling and heat.", "Mi respiración y deglución son totalmente normales; solo tengo inflamación y calor local.", "🫁✅", "swelling", "hinchazón / inflamación", "ˈswelɪŋ", "Aclara que respiras normal y solo tienes inflamación y calor local.", "First question: are you having any shortness of breath, dizziness, or throat tightness?"),
            ("stinger-came-out-clean", "We washed it with soap and water, and I don't see a stinger left in the skin.", "Lo lavamos con agua y jabón, y no veo que haya quedado aguijón en la piel.", "🧼🔍", "stinger", "aguijón", "ˈstɪŋər", "Menciona que lavaron la zona y no quedó aguijón adentro.", "Good—your oxygen saturation and pulse are rock-steady. Let me inspect your arm."),
            ("hydrocortisone-and-antihistamine", "Should I take an oral antihistamine and apply hydrocortisone cream to bring the redness down?", "¿Debo tomar un antihistamínico oral y aplicar crema de hidrocortisona para bajar el enrojecimiento?", "💊🧴", "redness", "enrojecimiento", "ˈrednəs", "Pregunta si debes tomar un antihistamínico y aplicar crema antiinflamatoria.", "Wasps don't leave a stinger behind, which is good. I'll put a cold compress on it now."),
            ("draw-pen-line-border", "Drawing a pen line around the red border helps track if the swelling spreads.", "Marcar con pluma el borde rojo ayuda a vigilar si la hinchazón avanza.", "🖊️📏", "spreads", "se extiende / propaga", "spredz", "", ""),
            ("feel-relief-already", "The ice pack and antihistamine are taking the sting away already—thank you!", "La compresa fría y el antihistamínico ya están aliviando el ardor; ¡gracias!", "🧊😌", "relief", "alivio", "rɪˈliːf", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "B1", "embassy-emergency-passport", "Applying for an emergency passport", "Tramitar pasaporte de emergencia en el consulado",
        "Acude a la sección consular con tu denuncia policial, fotos tamaño pasaporte y boleto de avión para obtener un pasaporte de emergencia.",
        "consular officer", "citizen abroad", "Embassy citizen services window.",
        [
            ("apply-emergency-travel-doc", "Good morning. My backpack was stolen yesterday, and I need an emergency passport to fly home on Friday.", "Buenos días. Ayer robaron mi mochila y necesito un pasaporte de emergencia para volar a casa el viernes.", "🛂✈️", "emergency passport", "pasaporte de emergencia", "ɪˈmɜːrdʒənsi ˈpæspɔːrt", "Explica que robaron tu mochila y necesitas un pasaporte de emergencia para volar el viernes.", "Good morning. Welcome to American Citizen Services. How can we assist you?"),
            ("police-report-and-copy", "I brought the official police report, two biometric passport photos, and a photocopy of my old passport.", "Traje el acta policial oficial, dos fotos biométricas y una fotocopia de mi pasaporte anterior.", "📑📸", "photocopy", "fotocopia / copia impresa", "ˈfoʊtoʊkɑːpi", "Presenta el acta policial, las dos fotografías y la copia de tu pasaporte anterior.", "Having a photocopy of your lost passport speeds up identity verification tremendously!"),
            ("confirmed-return-itinerary", "Here is my confirmed airline itinerary showing my departure flight in forty-eight hours.", "Aquí está mi itinerario aéreo confirmado que muestra mi vuelo de salida en cuarenta y ocho horas.", "🎫🕒", "itinerary", "itinerario de vuelo", "aɪˈtɪnəreri", "Muestra tu itinerario de vuelo confirmado para dentro de 48 horas.", "Thank you. May I also see proof of your urgent travel date?"),
            ("pick-up-this-afternoon", "Can the limited-validity passport be printed for pickup this afternoon?", "¿El pasaporte de validez limitada puede imprimirse para recogerlo hoy por la tarde?", "🖨️🕓", "pickup", "recogida en ventanilla", "ˈpɪkʌp", "Pregunta si el documento puede estar listo para recogerlo esta misma tarde.", "Everything is verified. Please pay the passport fee at Cashier Window 1."),
            ("valid-for-direct-return", "I understand this emergency book is valid for one year to complete my return journey.", "Entiendo que este pasaporte de emergencia es válido por un año para completar mi regreso.", "📘✅", "journey", "viaje / trayecto", "ˈdʒɜːrni", "", ""),
            ("huge-weight-off-shoulders", "Come back at 3:00 PM? That is a huge weight off my shoulders—thank you!", "¿Regresar a las 3:00 PM? Me quita un enorme peso de encima; ¡muchas gracias!", "😌🙌", "weight off my shoulders", "un gran peso de encima / alivio", "weɪt ɔːf maɪ ˈʃoʊldərz", "", ""),
        ],
    ),
    # B2 (4 new)
    (
        "health-and-emergencies", "B2", "pediatric-fever-triage", "Describing a child's fever at triage", "Explicar evolución de fiebre en triaje pediátrico",
        "Detalla al enfermero de triaje la curva de fiebre, el peso exacto de tu hijo y a qué hora tomó la última dosis de paracetamol.",
        "pediatric triage nurse", "parent", "Pediatric urgent care triage room.",
        [
            ("spiked-fever-last-night", "My six-year-old son spiked a thirty-nine-degree fever last night and has been complaining of pain when swallowing.", "Mi hijo de seis años subió a treinta y nueve grados de fiebre anoche y se queja de dolor al tragar.", "🌡️👦", "spiked a fever", "tuvo un pico de fiebre", "spaɪkt ə ˈfiːvər", "Explica que tu hijo de seis años subió a 39 grados y le duele al tragar.", "Hi there! Let's get your little guy checked out. What symptoms brought you in today?"),
            ("weight-and-last-dose", "He weighs twenty-two kilos, and we gave him weight-based liquid acetaminophen four hours ago.", "Pesa veintidós kilos y le dimos paracetamol líquido según su peso hace cuatro horas.", "⚖️🥄", "weight-based", "calculado según el peso corporal", "weɪt beɪzd", "Indica que pesa 22 kilos y tomó paracetamol hace cuatro horas.", "Good job tracking the temperature. When did he last have fever reducer, and what is his weight?"),
            ("keeping-fluids-down", "He's keeping water and popsicle fluids down well, and he has no rash or neck stiffness.", "Está reteniendo bien el agua y paletas de hielo, y no tiene sarpullido ni rigidez en el cuello.", "💧🍧", "keeping down", "retener líquidos sin vomitar", "ˈkiːpɪŋ daʊn", "Confirma que tolera bien los líquidos y no tiene sarpullido ni rigidez.", "The medicine brought his temp down to 37.8 right now. How is his hydration?"),
            ("rapid-strep-throat-swab", "Could we do a rapid strep throat swab to see if he needs antibiotics?", "¿Podríamos hacerle una prueba rápida de estreptococo en garganta para ver si requiere antibiótico?", "🧪🩺", "swab", "hisopado / muestra con hisopo", "swɑːb", "Pregunta si pueden hacerle una prueba rápida de estreptococo en la garganta.", "Looking at his tonsils, there are a few white spots, so a rapid strep test is the exact next step."),
            ("no-penicillin-allergy", "He has no known drug allergies and is fully up to date on his childhood vaccinations.", "No tiene alergias a medicamentos y tiene todas sus vacunas infantiles al día.", "🛡️✅", "up to date", "al día / actualizado", "ʌp tuː deɪt", "", ""),
            ("results-in-ten-minutes", "Thanks for being so gentle with him—we'll wait right here for the diez-minute swab result.", "Gracias por tratarlo con tanta dulzura; esperaremos aquí el resultado de diez minutos.", "🙏😊", "gentle", "cuidadoso / amable", "ˈdʒentəl", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "B2", "physical-therapy-rehab", "Adjusting a physical therapy rehab plan", "Ajustar ejercicios con el fisioterapeuta",
        "Explica a tu fisioterapeuta en qué ángulo sientes un pellizco en el hombro y ajusta la resistencia de las bandas.",
        "sports physiotherapist", "patient", "Outpatient sports rehabilitation clinic.",
        [
            ("range-of-motion-improved", "My overhead range of motion is noticeably smoother this week, especially after a warm shower.", "Mi rango de movimiento por encima de la cabeza se siente mucho más fluido esta semana.", "🏋️‍♀️📈", "range of motion", "rango de movilidad articular", "reɪndʒ əv ˈmoʊʃən", "Comenta que tu rango de movimiento mejoró notablemente esta semana.", "Welcome back for Week 3! How has the shoulder been responding to the home band routine?"),
            ("pinch-at-ninety-degrees", "However, I still feel a mild pinching sensation when I abduct my arm past ninety degrees.", "Sin embargo, aún siento un ligero pellizco cuando levanto el brazo lateralmente más allá de noventa grados.", "📐⚡", "pinching", "sensación de pellizco articular", "ˈpɪntʃɪŋ", "Explica que aún sientes un leve pellizco al elevar el brazo a más de 90 grados.", "Show me that lateral raise slowly—where does the impingement kick in?"),
            ("tuck-shoulder-blade-back", "When I focus on retracting my shoulder blade first, the pinch almost disappears.", "Cuando me concentro en retraer primero el omóplato, el pellizco casi desaparece.", "🦴✨", "shoulder blade", "omóplato / escápula", "ˈʃoʊldər bleɪd", "Comenta que al retraer primero el omóplato la molestia casi desaparece.", "Try setting your scapula down and back before lifting—how does that feel now?"),
            ("step-up-to-green-band", "Am I ready to progress from the yellow resistance band to the medium green band for external rotations?", "¿Ya estoy listo para pasar de la banda amarilla a la verde mediana en las rotaciones externas?", "🟢💪", "progress", "avanzar de nivel gradualmente", "prəˈɡres", "Pregunta si ya puedes avanzar a la banda elástica verde en rotaciones externas.", "Bingo! That scapular cue gives the rotator cuff tendon plenty of clearance."),
            ("three-sets-of-fifteen", "I'll stick to three sets of fifteen slow eccentric reps every other day.", "Mantendré tres series de quince repeticiones lentas un día sí y un día no.", "🔢⏱️", "every other day", "un día sí y otro no (días alternos)", "ˈevri ˈʌðər deɪ", "", ""),
            ("return-to-swimming-laps", "Hearing I can start light freestyle swimming next month is the best news!", "¡Escuchar que podré volver a nadar suave el próximo mes es la mejor noticia!", "🏊‍♂️🌟", "light", "suave / moderado", "laɪt", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "B2", "roadside-breakdown-tow", "Coordinating a highway roadside tow", "Coordinar grúa en carretera por avería",
        "Llama a asistencia vial tras una llanta ponchada en autopista, comparte las coordenadas del poste kilométrico y pide grúa de plataforma.",
        "roadside dispatch agent", "driver", "Pulled onto the wide shoulder of a highway with hazard lights on.",
        [
            ("pulled-onto-wide-shoulder", "Hi, we had a front tire blowout on Route 9, but we're safely pulled onto the wide paved shoulder with hazards on.", "Hola, se nos reventó una llanta delantera en la Ruta 9, pero ya estamos seguros en el acotamiento amplio con intermitentes.", "🚗🚨", "shoulder", "acotamiento / arcén de la carretera", "ˈʃoʊldər", "Avisa que tuvieron una ponchadura pero están seguros en el acotamiento con intermitentes.", "Roadside Assistance, hello! First, are you in a safe location away from moving traffic?"),
            ("mile-marker-forty-six", "We're northbound just two hundred meters past Mile Marker 46, before the River Exit.", "Vamos en dirección norte apenas doscientos metros después del poste kilométrico 46, antes de la salida del río.", "🪧🧭", "mile marker", "poste indicador de milla / kilómetro", "maɪl ˈmɑːrkər", "Indica tu ubicación exacta: dirección norte pasando el marcador 46.", "Glad you're well off the roadway. Can you see a mile marker or exit sign nearby?"),
            ("all-wheel-drive-flatbed", "Because this rental SUV is all-wheel drive, no spare tire is on board—we'll need a flatbed tow truck.", "Como esta camioneta de alquiler tiene tracción integral y no trae llanta de refacción, necesitaremos una grúa de plataforma.", "🛻⚙️", "flatbed", "grúa de plataforma plana", "ˈflætbed", "Explica que por ser tracción integral sin refacción requieren grúa de plataforma.", "Got your exact GPS pin at Mile 46.2! Does the vehicle have a spare tire in the trunk?"),
            ("ride-in-truck-cab", "Can the three of us ride in the tow truck cab to the tire service center in town?", "¿Podemos ir nosotros tres en la cabina de la grúa hasta el centro llantero del pueblo?", "👥🛻", "cab", "cabina del camión", "kæb", "Pregunta si los tres pueden viajar en la cabina de la grúa hasta el taller.", "Good call—towing an all-wheel-drive SUV on two wheels would damage the transmission."),
            ("stay-behind-guardrail", "We're waiting safely behind the metal guardrail while the truck is en route.", "Estamos esperando seguros detrás de la barrera metálica mientras llega la grúa.", "🛡️🛣️", "guardrail", "barrera metálica de contención", "ˈɡɑːrdreɪl", "", ""),
            ("live-tracker-sms-link", "I just received the SMS link showing the flatbed truck is eighteen minutes away—thank you!", "Ya recibí el enlace por SMS mostrando que la grúa llega en dieciocho minutos; ¡gracias!", "📲✅", "en route", "en camino", "ɑːn ruːt", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "B2", "food-allergy-epipen", "Post-EpiPen observation at the ER", "Explicar uso de EpiPen en sala de emergencias",
        "Explica al médico de urgencias que usaste tu autoinyector de epinefrina tras exposición accidental a maní y tus síntomas cedieron.",
        "ER attending physician", "patient", "Emergency room observation bay.",
        [
            ("accidental-peanut-exposure", "I had an accidental cross-contact exposure to peanuts at a restaurant thirty minutes ago.", "Tuve una exposición accidental por contaminación cruzada con maní en un restaurante hace treinta minutos.", "🥜🚨", "cross-contact", "contaminación cruzada involuntaria", "krɔːs ˈkɑːntækt", "Explica que tuviste exposición accidental a maní hace treinta minutos.", "We have your vitals monitor hooked up. Tell me when the reaction started and what you took."),
            ("administered-epipen-thigh", "As soon as I felt hives and throat tightness, I administered my EpiPen into my outer thigh at 7:15 PM.", "En cuanto sentí urticaria y opresión en la garganta, me apliqué el EpiPen en el muslo externo a las 7:15 PM.", "💉🦵", "hives", "urticaria / ronchas en la piel", "haɪvz", "Indica que te aplicaste el EpiPen en el muslo a las 7:15 PM al sentir urticaria.", "Using your epinephrine autoinjector immediately was the exact right decision!"),
            ("wheezing-subsided-quickly", "Within five minutes of the injection, the wheezing subsided and my airways felt completely clear.", "A los cinco minutos de la inyección, el silbido al respirar cedió y mis vías respiratorias se despejaron.", "🫁✅", "subsided", "cedió / disminuyó rápidamente", "səbˈsaɪdɪd", "Detalla que en cinco minutos cedió la dificultad respiratoria.", "Your lungs sound clear on the stethoscope now. How are you feeling overall?"),
            ("four-hour-biphasic-observation", "I know protocol calls for a four-hour observation window to watch for a biphasic rebound reaction.", "Sé que el protocolo indica cuatro horas de observación para descartar una reacción bifásica de rebote.", "⏱️🏥", "rebound", "efecto rebote / segunda fase", "ˈriːbaʊnd", "Menciona que conoces la necesidad de permanecer cuatro horas en observación.", "Just a bit shaky from the adrenaline, which is totally normal."),
            ("prescription-for-twin-pack", "Before I'm discharged tonight, could you write a replacement prescription for a two-pack of autoinjectors?", "Antes de darme de alta esta noche, ¿podría extenderme receta para reponer el paquete doble de inyectores?", "📋💊", "discharged", "dado de alta del hospital", "dɪsˈtʃɑːrdʒd", "", ""),
            ("carry-second-injector-always", "I'll hand the used injector to the nurse for sharps disposal—thank you, Doctor.", "Entregaré el inyector usado a la enfermera para el contenedor biológico; gracias, doctor.", "🗑️🤝", "sharps disposal", "contenedor de residuos punzocortantes", "ʃɑːrps dɪˈspoʊzəl", "", ""),
        ],
    ),
    # C1 (4 new)
    (
        "health-and-emergencies", "C1", "pre-authorization-mri", "Securing insurer pre-authorization for an MRI", "Gestionar preautorización urgente de resonancia",
        "Coordina con el departamento médico de tu aseguradora la aprobación urgente de una resonancia magnética ambulatoria.",
        "medical review coordinator", "insured patient", "Phone call with the international health insurer's clinical desk.",
        [
            ("expedited-pre-authorization", "I'm calling to request expedited pre-authorization for a contrast-enhanced lumbar MRI ordered by my neurologist.", "Llamo para solicitar preautorización urgente de una resonancia lumbar con contraste indicada por mi neurólogo.", "🧲📋", "expedited", "acelerada / de trámite urgente", "ˈekspədaɪtɪd", "Solicita preautorización urgente para una resonancia lumbar indicada por tu neurólogo.", "Clinical Pre-Authorization Desk, hello. I see your policy number on screen. What procedure was ordered?"),
            ("clinical-notes-uploaded", "The clinic already uploaded the ICD-10 diagnostic codes and clinical notes documenting acute radiculopathy.", "La clínica ya subió los códigos diagnósticos ICD-10 y las notas clínicas que documentan radiculopatía aguda.", "🩺💻", "acute", "aguda / de aparición intensa", "əˈkjuːt", "Confirma que la clínica ya subió los códigos diagnósticos y notas médicas.", "For expedited review, we need the ordering physician's clinical notes showing conservative care or red-flag symptoms."),
            ("in-network-imaging-facility", "Because the imaging center is in-network, only my hundred-dollar copay should apply once you issue the guarantee of payment.", "Como el centro de imagenología está dentro de la red, solo debe aplicar mi copago de cien dólares al emitir la carta garantía.", "🏥💳", "in-network", "dentro de la red médica afiliada", "ɪn ˈnetwɜːrk", "Verifica que al ser un centro de la red solo aplique el copago con carta garantía.", "I see the neurologist's PDF attachment right here—it clearly meets our urgent clinical criteria."),
            ("fax-authorization-to-radiology", "Could you transmit the authorization code directly to the radiology scheduling desk before my 3:00 PM slot?", "¿Podría enviar el código de autorización directamente a radiología antes de mi turno de las 3:00 PM?", "📠🕒", "transmit", "transmitir / enviar oficialmente", "trænzˈmɪt", "Pide que envíen el código de autorización a radiología antes de las 3:00 PM.", "Approved under Authorization #MR-9042! Would you like me to email the Guarantee of Payment to the clinic?"),
            ("cover-follow-up-consult", "Does this authorization bundle also cover Friday's follow-up consultation to review the scans?", "¿Esta autorización cubre también la consulta de seguimiento del viernes para revisar las imágenes?", "🗓️🔍", "follow-up", "consulta de seguimiento", "ˈfɑːloʊ ʌp", "", ""),
            ("relieved-it-cleared-today", "Having that guarantee letter in their inbox before I arrive saves so much stress—thank you!", "Tener esa carta garantía en su correo antes de llegar me ahorra muchísimo estrés; ¡gracias!", "😌🙌", "guarantee letter", "carta garantía de pago hospitalario", "ˌɡærənˈtiː ˈletər", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "C1", "ergonomic-workplace-assessment", "Consulting on workplace ergonomics", "Consulta de ergonomía y salud ocupacional",
        "Evalúa con un especialista en salud ocupacional el síndrome del túnel carpiano incipiente y ajustes de postura.",
        "occupational health physician", "remote professional", "Ergonomic and repetitive-strain consultation.",
        [
            ("tingling-in-index-finger", "Over the past month, I've noticed intermittent tingling in my right thumb and index finger after long coding sessions.", "Durante el último mes he notado hormigueo intermitente en el pulgar e índice derechos tras largas sesiones de código.", "🖐️💻", "tingling", "hormigueo / parestesia leve", "ˈtɪŋɡlɪŋ", "Describe que sientes hormigueo intermitente en el pulgar e índice tras programar.", "Welcome in. Tell me about the wrist and hand symptoms you've been experiencing at your desk."),
            ("catch-repetitive-strain-early", "I wanted to get evaluated early before mild median-nerve irritation progresses to chronic carpal tunnel syndrome.", "Quise evaluarme a tiempo antes de que una irritación leve del nervio mediano avance a túnel carpiano crónico.", "🩺⏱️", "early", "a tiempo / en etapa temprana", "ˈɜːrli", "Explica que buscaste consulta temprana para prevenir túnel carpiano crónico.", "Catching it at the intermittent stage makes conservative ergonomic intervention ninety percent effective."),
            ("split-tenting-keyboard", "Switching to a split tented keyboard and a vertical mouse should keep my forearms in a neutral pronation angle.", "Cambiar a un teclado dividido inclinado y un ratón vertical debería mantener mis antebrazos en un ángulo neutro.", "⌨️📐", "neutral", "posición anatómica neutra", "ˈnuːtrəl", "Propón usar teclado dividido e inclinado con ratón vertical para alinear el antebrazo.", "Right now, a flat laptop keyboard forces your wrists into ulnar deviation and extension."),
            ("ergonomic-grant-letter", "Could you provide a brief occupational health recommendation so my employer's ergonomic stipend covers the equipment?", "¿Podría darme una breve recomendación ocupacional para que el bono ergonómico de mi empresa cubra el equipo?", "📑🏢", "stipend", "asignación / bono corporativo para equipamiento", "ˈstaɪpend", "Solicita una constancia médica para que la empresa cubra el equipo ergonómico.", "I'll also show you three nerve-gliding stretches to do every ninety minutes."),
            ("neutral-nighttime-splint", "Wearing a neutral wrist splint at night prevents unconscious flexion while sleeping.", "Usar una férula neutra de muñeca por la noche evita doblarla inconscientemente al dormir.", "🌙🧤", "splint", "férula / muñequera estabilizadora", "splɪnt", "", ""),
            ("monitor-at-eye-level", "Raising the external monitor to eye level also took the strain off my cervical spine.", "Subir el monitor externo a la altura de los ojos también quitó tensión a mis cervicales.", "🖥️👀", "eye level", "a la altura de los ojos", "aɪ ˈlevəl", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "C1", "altitude-sickness-protocol", "Managing acute mountain sickness", "Protocolo médico por mal de altura",
        "Consulta en una posta médica andina por cefalea de altitud y saturación de oxígeno, coordinando oxigenoterapia y descenso.",
        "high-altitude physician", "trekker", "Mountain medical clinic at 3,800 meters elevation.",
        [
            ("throbbing-altitude-headache", "We ascended to thirty-eight hundred meters yesterday, and my companion developed a throbbing frontal headache and dizziness.", "Ascendimos ayer a tres mil ochocientos metros y mi compañero presentó dolor de cabeza pulsátil y mareo.", "⛰️🩺", "throbbing", "pulsátil / latente", "ˈθrɑːbɪŋ", "Explica que tras ascender ayer a 3,800 metros tu compañero tiene cefalea y mareo.", "Come sit by the heater. Let's clip the pulse oximeter onto his finger right away."),
            ("oxygen-saturation-eighty-four", "His portable oximeter reading dropped to eighty-four percent at rest, though his lungs sound clear without crackles.", "Su oxímetro portátil bajó a ochenta y cuatro por ciento en reposo, aunque sus pulmones se escuchan limpios.", "🫁📊", "at rest", "en reposo", "æt rest", "Indica que su saturación bajó a 84% en reposo pero sin estertores pulmonares.", "84% is low for Day 2—good thing his lungs are completely clear with no signs of pulmonary edema."),
            ("supplemental-oxygen-and-acetazolamide", "Would thirty minutes of supplemental oxygen combined with acetazolamide stabilize him before we descend to the valley?", "¿Treinta minutos de oxígeno suplementario combinados con acetazolamida lo estabilizarán antes de bajar al valle?", "💨💊", "descend", "descender a menor altitud", "dɪˈsend", "Pregunta si oxígeno suplementario y acetazolamida lo estabilizarán para descender al valle.", "We'll put him on two liters per minute of nasal oxygen right now."),
            ("descend-six-hundred-meters", "We've already arranged a vehicle to take us down six hundred meters to the Sacred Valley hotel for two nights.", "Ya coordinamos un vehículo para bajar seiscientos metros al hotel del valle por dos noches.", "🚐🏞️", "arranged", "coordinamos / organizamos", "əˈreɪndʒd", "Confirma que ya tienen vehículo para descender 600 metros hacia el valle.", "Descending six hundred meters is the gold-standard treatment—he'll feel like a new person by dinner!"),
            ("gradual-acclimatization-profile", "Once he's symptom-free for forty-eight hours, we'll keep our ascent profile under three hundred meters per day.", "Cuando lleve cuarenta y ocho horas sin síntomas, subiremos menos de trescientos metros por día.", "📈🧭", "acclimatization", "aclimatación progresiva", "əˌklaɪmətɪˈzeɪʃən", "", ""),
            ("saturation-back-to-ninety-five", "His color is back and the oximeter reads ninety-six percent on oxygen—thank you, Doctor!", "Ya recuperó el color y el oxímetro marca noventa y seis por ciento; ¡gracias, doctor!", "✅😊", "symptom-free", "libre de síntomas", "ˈsɪmptəm friː", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "C1", "ophthalmology-corneal-scratch", "Treating a corneal abrasion", "Consulta oftalmológica por abrasión corneal",
        "Describe al oftalmólogo fotofobia y sensación de cuerpo extraño tras un día ventoso, realizando tinción con fluoresceína.",
        "ophthalmologist", "patient", "Eye clinic examination room with a slit lamp.",
        [
            ("foreign-body-sensation", "A gust of wind blew grit into my left eye yesterday, and I still have a sharp foreign-body sensation every time I blink.", "Una ráfaga de viento metió tierra en mi ojo izquierdo ayer y sigo sintiendo una basurita cada vez que parpadeo.", "👁️🌬️", "blink", "parpadear", "blɪŋk", "Explica que entró polvo a tu ojo ayer y sientes molestia aguda al parpadear.", "Rest your chin on the slit-lamp frame for me. Did you rub the eye when the grit blew in?"),
            ("photophobia-and-tearing", "Bright light triggers immediate tearing and photophobia, though my central vision isn't blurry.", "La luz brillante me provoca lagrimeo inmediato y fotofobia, aunque mi visión central no está borrosa.", "☀️💧", "photophobia", "sensibilidad intensa a la luz", "ˌfoʊtəˈfoʊbiə", "Detalla que la luz te causa lagrimeo y sensibilidad, pero tu visión central es clara.", "I'm going to instill one anesthetic drop and a touch of orange fluorescein dye to inspect the cornea."),
            ("superficial-corneal-abrasion", "Does the cobalt-blue light show a retained speck under the upper lid, or just a superficial corneal scratch?", "¿La luz azul muestra alguna partícula bajo el párpado superior o solo un rasguño corneal superficial?", "🔬🔵", "superficial", "superficial", "ˌsuːpərˈfɪʃəl", "Pregunta si aún hay una partícula bajo el párpado o es solo una abrasión superficial.", "I flushed a tiny grain of quartz from under the upper tarsal plate, leaving a two-millimeter superficial abrasion."),
            ("antibiotic-ointment-no-contacts", "I'll apply the lubricating antibiotic ointment four times daily and stay out of contact lenses for a full week.", "Aplicaré el ungüento antibiótico lubricante cuatro veces al día y no usaré lentes de contacto en toda la semana.", "🧴👓", "ointment", "ungüento / pomada oftálmica", "ˈɔɪntmənt", "Confirma que aplicarás el ungüento cuatro veces al día y no usarás lentes de contacto.", "The corneal epithelium heals remarkably fast—usually within twenty-four to forty-eight hours."),
            ("wear-polarized-sunglasses", "Wearing polarized sunglasses outdoors will keep ciliary spasm to a minimum today.", "Usar gafas de sol polarizadas al aire libre reducirá el espasmo ocular hoy.", "🕶️🌤️", "outdoors", "al aire libre", "ˌaʊtˈdɔːrz", "", ""),
            ("recheck-in-forty-eight-hours", "I'll come back Friday morning so you can confirm the epithelium has closed completely.", "Regresaré el viernes por la mañana para confirmar que el epitelio cerró por completo.", "📅✅", "heals", "cicatriza / sana", "hiːlz", "", ""),
        ],
    ),
    # C2 (4 new)
    (
        "health-and-emergencies", "C2", "clinical-trial-informed-consent", "Evaluating clinical trial informed consent", "Evaluar consentimiento en ensayo clínico",
        "Analiza con el investigador principal el diseño cruzado del estudio, el perfil de efectos adversos y el derecho de retiro.",
        "principal investigator", "prospective participant", "Academic medical center clinical research consultation.",
        [
            ("crossover-arm-guarantee", "If I'm randomized into the placebo control arm initially, does the protocol guarantee open-label crossover at week twelve?", "Si soy asignado por azar al brazo placebo inicialmente, ¿el protocolo garantiza el cruce al fármaco activo en la semana doce?", "🧬🔬", "randomized", "asignado aleatoriamente", "ˈrændəmaɪzd", "Pregunta si quienes entran al grupo placebo pasan al tratamiento activo en la semana doce.", "Thank you for reviewing the informed consent dossier for our Phase III targeted biologics trial."),
            ("dose-limiting-toxicities", "What were the most prevalent dose-limiting toxicities observed during the Phase II dose-escalation cohort?", "¿Cuáles fueron las toxicidades limitantes de dosis más frecuentes observadas durante la Fase II?", "📊🩺", "prevalent", "frecuentes / prevalentes", "ˈprevələnt", "Pregunta qué efectos adversos limitantes se observaron durante la Fase II.", "Yes, every participant in the control arm transitions to the active biologic at the twelve-week mark."),
            ("unblind-in-emergency", "Should an unexpected adverse event arise, can my primary physician break the blind immediately?", "En caso de surgir un evento adverso imprevisto, ¿puede mi médico de cabecera abrir el ciego de inmediato?", "🔓🏥", "break the blind", "revelar la asignación del estudio por urgencia médica", "breɪk ðə blaɪnd", "Verifica que tu médico pueda conocer la asignación de inmediato ante cualquier urgencia.", "Phase II showed transient mild transaminase elevations in six percent of patients, all reversible."),
            ("withdraw-without-prejudice", "I appreciate that consent is voluntary and that I may withdraw at any point without affecting my standard clinical care.", "Valoro que el consentimiento sea voluntario y pueda retirarme en cualquier momento sin afectar mi atención médica habitual.", "✍️🛡️", "without prejudice", "sin perjuicio ni menoscabo de derechos", "wɪˈðaʊt ˈpredʒədɪs", "Confirma tu derecho a retirarte en cualquier momento sin afectar tu atención médica.", "24-hour emergency unblinding is built into the pharmacy portal, and you can withdraw at any time."),
            ("pharmacokinetic-blood-draws", "Are the biweekly pharmacokinetic blood draws coordinated with my regular morning lab visits?", "¿Las tomas de sangre quincuincales se coordinan con mis visitas habituales de laboratorio?", "🧪🕗", "biweekly", "cada dos semanas / quincenal", "baɪˈwiːkli", "", ""),
            ("sign-informed-consent", "All my questions have been addressed thoroughly—I'm ready to sign the consent form.", "Todas mis preguntas fueron respondidas con rigor; estoy listo para firmar el consentimiento.", "✅📄", "thoroughly", "a fondo / exhaustivamente", "ˈθɜːroʊli", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "C2", "medical-repatriation-logistics", "Coordinating an air-ambulance medevac", "Coordinar evacuación aeromédica entre hospitales",
        "Coordina como enlace médico-familiar el traslado en ambulancia aérea presurizada a nivel del mar de cama a cama.",
        "flight medical director", "patient advocate", "Coordinating a bed-to-bed international medical repatriation.",
        [
            ("bed-to-bed-transfer", "Have the sending and receiving ICU attendings completed the physician-to-physician handoff for a bed-to-bed transfer?", "¿Los médicos de terapia intensiva de origen y destino ya completaron la entrega clínica para el traslado cama a cama?", "🛩️🏥", "handoff", "entrega de guardia / traspaso clínico", "ˈhændɔːf", "Pregunta si los médicos de ambos hospitales ya hicieron el traspaso clínico directo.", "Our air-ambulance Learjet is positioned on the tarmac. Let's review the final clinical clearance."),
            ("sea-level-cabin-pressurization", "Given the patient's recent pneumothorax, the flight plan must maintain a sea-level cabin altitude throughout the cruise.", "Dado el neumotórax reciente del paciente, el plan de vuelo debe mantener presurización a nivel del mar durante todo el crucero.", "🫁✈️", "sea-level cabin", "cabina presurizada a altitud de nivel del mar", "siː ˈlevəl ˈkæbɪn", "Subraya la exigencia de mantener cabina presurizada a nivel del mar durante el vuelo.", "Yes, Dr. Morales in Zurich accepted the bed assignment and reviewed the chest CT scans."),
            ("continuous-telemetry-infusion", "Will the critical-care flight nurse bring dual syringe pumps and portable blood-gas monitoring for the tarmac transfer?", "¿El enfermero de vuelo llevará bombas de infusión dobles y monitor portátil de gases durante el traslado en pista?", "🩺🔋", "tarmac", "plataforma del aeropuerto / pista", "ˈtɑːrmæk", "Verifica que el equipo de vuelo lleve bombas de infusión y monitoreo continuo en pista.", "Our flight deck has filed a lower cruise profile to hold cabin pressure at sea level."),
            ("tarmac-customs-clearance", "Airport authorities approved direct ambulance ramp access so customs clears the passport bedside without delay.", "Las autoridades aeroportuarias aprobaron acceso directo de la ambulancia a pista para sellar pasaporte sin demora.", "🛂🚑", "bedside", "al pie de la camilla", "ˈbedsaɪd", "Confirma el acceso directo a plataforma para el trámite migratorio junto a la camilla.", "Our ICU flight nurse and respiratory therapist have redundant battery packs and telemetry ready."),
            ("dicom-imaging-uploaded", "All DICOM imaging files and medication administration records have been uploaded to the receiving hospital's portal.", "Todas las imágenes DICOM y registros de medicación ya se subieron al portal del hospital receptor.", "💻📂", "records", "expedientes / registros clínicos", "ˈrekərdz", "", ""),
            ("wheels-up-at-fourteen-hundred", "With all clinical and customs clearances green, we are set for wheels-up at 14:00.", "Con todas las autorizaciones clínicas y aduaneras listas, despegamos a las 14:00.", "🛫✅", "wheels-up", "hora exacta de despegue", "wiːlz ʌp", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "C2", "immunology-desensitization", "Discussing sublingual immunotherapy", "Analizar protocolo de inmunoterapia con alergólogo",
        "Debate con un inmunólogo las ventajas de la inmunoterapia sublingual frente a la subcutánea y el perfil de citoquinas.",
        "clinical immunologist", "patient", "University allergy and immunology specialty clinic.",
        [
            ("sublingual-versus-subcutaneous", "How does daily sublingual tablet immunotherapy compare to weekly subcutaneous injections in long-term immune tolerance?", "¿Cómo se compara la inmunoterapia sublingual diaria frente a las inyecciones subcutáneas semanales en tolerancia a largo plazo?", "🧬💊", "immune tolerance", "tolerancia inmunológica sostenida", "ɪˈmjuːn ˈtɑːlərəns", "Pregunta cómo se compara la vía sublingual frente a la subcutánea a largo plazo.", "Your IgE panel confirms severe sensitivity to birch and timothy grass pollen. Let's discuss desensitization."),
            ("first-dose-under-supervision", "I understand the initial sublingual tablet is administered here under thirty-minute observation before transitioning to home dosing.", "Entiendo que la primera tableta sublingual se administra aquí bajo observación de treinta minutos antes de pasar a casa.", "🏥⏱️", "observation", "observación médica preventiva", "ˌɑːbzərˈveɪʃən", "Confirma que la primera dosis se toma en clínica bajo treinta minutos de observación.", "After a three-year course, both modalities induce comparable IgG4 blocking antibodies, though sublingual is needle-free."),
            ("pre-seasonal-lead-time", "Starting the regimen sixteen weeks prior to spring pollination should significantly blunt peak mucosal inflammation.", "Iniciar el esquema dieciséis semanas antes de la polinización primaveral debería atenuar significativamente la inflamación.", "🌱🛡️", "blunt", "atenuar / amortiguar la intensidad", "blʌnt", "Destaca la ventaja de iniciar dieciséis semanas antes de la primavera.", "Exactly—once you tolerate Day 1 in the clinic, you take it at home each morning."),
            ("hold-dose-after-dental-work", "If I have dental work or a minor oral abrasion, I should pause the tablet for forty-eight hours so the mucosa heals.", "Si tengo un procedimiento dental o pequeña herida oral, debo pausar la tableta cuarenta y ocho horas hasta que sane.", "🦷✅", "pause", "pausar temporalmente", "pɔːz", "Verifica la indicación de pausar la tableta 48 horas tras cualquier procedimiento dental.", "Starting now in November gives your T-regulatory cells a full four-month head start before spring."),
            ("step-down-rescue-inhalers", "As desensitization progresses in Year 2, we can gradually taper my rescue antihistamines and nasal steroids.", "Conforme avance la desensibilización en el segundo año, podremos reducir gradualmente los antihistamínicos de rescate.", "📉🌿", "taper", "reducir la dosis de forma gradual", "ˈteɪpər", "", ""),
            ("begin-supervised-dose-today", "Let's administer the first sublingual dose today so we stay right on the pre-seasonal timeline.", "Administremos la primera dosis sublingual hoy mismo para cumplir con el calendario.", "🙌🔬", "timeline", "cronograma clínico", "ˈtaɪmlaɪn", "", ""),
        ],
    ),
    (
        "health-and-emergencies", "C2", "hospital-ethics-advocacy", "Advocating during multidisciplinary hospital rounds", "Defender plan de cuidado en junta médica",
        "Participa como representante familiar en el pase de visita multidisciplinario alineando cardiología, nefrología y rehabilitación.",
        "attending hospitalist", "family healthcare proxy", "Morning multidisciplinary bedside rounds.",
        [
            ("reconcile-conflicting-guidance", "Before we adjust the diuretic regimen, could we reconcile the fluid targets between cardiology and nephrology?", "Antes de ajustar el esquema de diuréticos, ¿podríamos conciliar las metas de líquidos entre cardiología y nefrología?", "🩺⚖️", "reconcile", "conciliar / armonizar criterios", "ˈrekənsaɪl", "Pide conciliar las metas de líquidos entre cardiología y nefrología.", "Good morning. We're reviewing your father's chart with the inpatient team today."),
            ("prioritize-functional-mobility", "My father's overarching goal is preserving independent mobility, so we want early bedside physical therapy prioritized.", "La prioridad fundamental de mi padre es conservar su movilidad independiente, por lo que pedimos priorizar fisioterapia temprana.", "🚶‍♂️🌟", "overarching", "primordial / rector", "ˌoʊvərˈɑːrtʃɪŋ", "Subraya que la prioridad es preservar su movilidad con fisioterapia temprana.", "Cardiology and nephrology just huddled—a gentle oral dose protects his kidney function while clearing congestion."),
            ("deprescribe-sedating-meds", "Could we also review his nighttime medication list to deprescribe any sedatives that heighten delirium risk?", "¿Podríamos también revisar su medicación nocturna para retirar sedantes que eleven el riesgo de desorientación?", "🌙💊", "deprescribe", "retirar medicamentos innecesarios de forma supervisada", "ˌdiːprɪˈskraɪb", "Solicita revisar la medicación nocturna para evitar fármacos que causen desorientación.", "We've ordered daily inpatient physical therapy starting at 10:00 AM today."),
            ("structured-discharge-milestones", "Let's define clear physiological and mobility milestones for Friday's transition to outpatient cardiac rehab.", "Definamos hitos fisiológicos y de movilidad claros para su transición del viernes a rehabilitación ambulatoria.", "📋🏠", "milestones", "hitos / metas clínicas verificables", "ˈmaɪlstoʊnz", "Propón definir metas claras para el alta hacia rehabilitación ambulatoria el viernes.", "Good catch—we'll discontinue the nighttime antihistamine sleep aid immediately."),
            ("single-point-of-contact", "Having the case manager send one consolidated afternoon update keeps our whole family aligned.", "Que la gestora de casos envíe un resumen diario por la tarde mantiene a toda la familia coordinada.", "📲🤝", "consolidated", "unificado / consolidado", "kənˈsɑːlɪdeɪtɪd", "", ""),
            ("grateful-for-collaborative-care", "We're deeply grateful for how collaboratively your teams are listening to his goals.", "Estamos profundamente agradecidos por la forma tan colaborativa en que escuchan sus prioridades.", "🙏❤️", "collaboratively", "de forma colaborativa", "kəˈlæbərətɪvli", "", ""),
        ],
    ),
])


def _compute_cloze(text: str) -> list[int]:
    words = text.split()
    n = len(words)
    if n <= 4:
        return [max(0, n - 2)]
    return sorted({min(n - 1, max(1, n // 3)), min(n - 1, max(2, (2 * n) // 3))})


def build_scenario_dict(bp: tuple) -> dict:
    topic, cefr, slug_suffix, title_en, title_es, description_es, ai_role, user_role, setting, items = bp
    scenario_id = f"{cefr.lower()}-{slug_suffix}".lower()
    phrases = []
    turns = []
    for idx, (pid, en_text, es_trans, hint, g_word, g_mean, g_ipa, u_goal, ai_line) in enumerate(items):
        phrases.append(
            {
                "id": re.sub(r"[^a-z0-9-]+", "-", pid.lower()).strip("-"),
                "text": en_text,
                "translation": es_trans,
                "visual_hint": hint,
                "cloze": _compute_cloze(en_text),
                "glossary": [{"word": g_word, "meaning": g_mean, "ipa": g_ipa}],
            }
        )
        if idx < 4:
            turns.append({"speaker": "ai", "text": ai_line})
            alt_line = items[min(len(items) - 1, idx + 1)][1]
            turns.append(
                {
                    "speaker": "user",
                    "goal": u_goal,
                    "suggested_lines": [en_text, alt_line],
                }
            )
    turns.append({"speaker": "ai", "text": "Wonderful! Everything is all set. Have a fantastic day!"})
    return {
        "id": scenario_id,
        "title": title_en,
        "title_es": title_es,
        "cefr": cefr,
        "topic": topic,
        "description": description_es,
        "phrases": phrases,
        "roleplay": {
            "ai_role": ai_role,
            "user_role": user_role,
            "setting": setting,
            "turns": turns,
        },
    }


def main() -> None:
    assert len(CELL_BLUEPRINTS) == 144, f"Expected 144 new scenarios, got {len(CELL_BLUEPRINTS)}"
    for bp in CELL_BLUEPRINTS:
        sc = build_scenario_dict(bp)
        path = SCENARIOS_DIR / f"{sc['id']}.yaml"
        path.write_text(yaml.safe_dump(sc, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")

    sys.path.insert(0, str(ROOT / "backend"))
    from app.content.repository import get_repository
    from app.content.schema import CEFR, TOPIC_MODULES

    get_repository.cache_clear()
    repo = get_repository()
    scenarios = repo.list()
    total_phrases = sum(len(s.phrases) for s in scenarios)
    print(f"Validated {len(scenarios)} total scenarios and {total_phrases} total phrases!")

    # Verify >= 5 scenarios for every (module, CEFR) pair!
    for topic in TOPIC_MODULES:
        for lv in CEFR:
            cell = [s for s in scenarios if s.topic == topic and s.cefr == lv]
            assert len(cell) >= 5, f"Cell ({topic}, {lv.value}) has only {len(cell)} scenarios!"
    print("Verified: every single (module, CEFR level) cell has 5 scenarios (30 per module, 30 per level, 180 total)!")

    # Sync FALLBACK_SCENARIOS in backend/app/static/index.html
    fallback_list = []
    for s in scenarios:
        d = s.model_dump(mode="json")
        d["band"] = s.cefr.band
        fallback_list.append(d)

    html = STATIC_INDEX.read_text(encoding="utf-8")
    pattern = re.compile(r"const FALLBACK_SCENARIOS = \[.*?\n    \];|const FALLBACK_SCENARIOS = \[.*?\];", re.DOTALL)
    replacement = "const FALLBACK_SCENARIOS = " + json.dumps(fallback_list, ensure_ascii=False, indent=6) + ";"
    new_html, count = pattern.subn(replacement, html, count=1)
    if count != 1:
        raise RuntimeError(f"Expected 1 FALLBACK_SCENARIOS replacement, got {count}")
    STATIC_INDEX.write_text(new_html, encoding="utf-8")
    print(f"Synced {len(fallback_list)} scenarios into {STATIC_INDEX}")


if __name__ == "__main__":
    main()
