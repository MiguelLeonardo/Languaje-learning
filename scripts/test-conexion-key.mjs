import { consultarAsistente } from "../miServicioDeIA.js";

// Ejecuta la función pasando la API Key de terceros y la consulta
const respuesta = await consultarAsistente(
  "npm_key_live_example_9876543210abc", // Mapeado internamente a 'apiKey'
  "Necesito un script básico de Node.js para conectar un cliente HTTP" // Mapeado a 'userQuery'
);

console.log("Respuesta del Asistente:", respuesta);
process.exit(0);
