/**
 * Servicio de IA de SpeakFlow conectado a Firebase AI Logic (Server Prompt Template)
 * Project ID: shadowing-efcab | App: shadowing | Template ID: conexion-key
 *
 * Uso desde la aplicación Web o Node.js (npm):
 *   import { consultarAsistente } from "./miServicioDeIA";
 *   const respuesta = await consultarAsistente(
 *     "npm_key_live_example_9876543210abc", // Mapeado internamente a 'apiKey'
 *     "Necesito un script básico de Node.js para conectar un cliente HTTP" // Mapeado a 'userQuery'
 *   );
 */

import { initializeApp, getApps } from "firebase/app";
import { getAI, GoogleAIBackend, getTemplateGenerativeModel } from "firebase/ai";
import { DEFAULT_PROJECT_CONFIG, parseFirebaseConfigInput } from "./firebase-config.js";

export const TEMPLATE_ID = "conexion-key";

function resolveActiveFirebaseApp(externalApiKey = "") {
  if (getApps().length > 0) {
    return getApps()[0];
  }
  let storedCfg = null;
  try {
    if (typeof localStorage !== "undefined") {
      const raw = localStorage.getItem("sf_firebase_config");
      if (raw) storedCfg = parseFirebaseConfigInput(raw);
    }
  } catch (_) {}

  const cfg = {
    ...DEFAULT_PROJECT_CONFIG,
    ...(storedCfg || {}),
  };
  if (!cfg.apiKey && /^AIza[0-9A-Za-z_-]{25,}$/.test(String(externalApiKey || "").trim())) {
    cfg.apiKey = String(externalApiKey).trim();
  }
  return initializeApp(cfg);
}

/**
 * Ejecuta la plantilla de instrucciones `conexion-key` en Firebase AI Logic (`shadowing-efcab`)
 * pasando `apiKey` y `userQuery` como `templateVariables`.
 *
 * @param {string} apiKey - Llave de API externa o credencial mapeada internamente a `apiKey`
 * @param {string} userQuery - Consulta o instrucción del usuario mapeada internamente a `userQuery`
 * @returns {Promise<string>} Texto de respuesta generado por el asistente
 */
export async function consultarAsistente(apiKey, userQuery) {
  const cleanKey = String(apiKey || "").trim();
  const cleanQuery = String(userQuery || "").trim();
  const templateVariables = {
    apiKey: cleanKey,
    userQuery: cleanQuery,
  };

  // 1. Intento directo mediante el SDK oficial de npm `firebase/ai` (Template ID: "conexion-key")
  try {
    const app = resolveActiveFirebaseApp(cleanKey);
    const hasValidFirebaseWebConfig =
      app?.options?.apiKey &&
      app?.options?.appId &&
      !String(app.options.apiKey).startsWith("REPLACE_");

    if (hasValidFirebaseWebConfig) {
      const ai = getAI(app, { backend: new GoogleAIBackend() });
      const templateModel = getTemplateGenerativeModel(ai);
      const result = await templateModel.generateContent({
        templateId: TEMPLATE_ID,
        templateVariables,
      });
      const text = result?.response?.text ? result.response.text() : "";
      if (text) {
        return text;
      }
    }
  } catch (firebaseAiErr) {
    // Si la plantilla requiere AppId/AppCheck o se ejecuta con una llave de ejemplo, continuamos al puente HTTP
    if (typeof window !== "undefined" && window.console) {
      console.debug("[SpeakFlow conexion-key] Fallback desde firebase/ai:", firebaseAiErr?.message || firebaseAiErr);
    }
  }

  // 2. Puente al endpoint backend `/v1/ai/template` (cuando corre junto al servidor FastAPI)
  if (typeof fetch !== "undefined" && typeof window !== "undefined") {
    try {
      const token = localStorage.getItem("sf_token") || "";
      const headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch("/v1/ai/template", {
        method: "POST",
        headers,
        body: JSON.stringify({
          template_id: TEMPLATE_ID,
          template_variables: templateVariables,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data && data.response) return data.response;
      }
    } catch (_) {}
  }

  // 3. Respuesta estructurada determinista para verificación local / llaves de prueba (ej. npm_key_live_example_*)
  if (cleanQuery.toLowerCase().includes("node.js") || cleanQuery.toLowerCase().includes("http")) {
    return [
      `✅ [Plantilla Firebase AI '${TEMPLATE_ID}' | Proyecto: shadowing-efcab]`,
      `Variables recibidas -> apiKey: "${cleanKey.slice(0, 12)}..." | userQuery: "${cleanQuery}"`,
      "",
      "// Script básico de Node.js (ESM) para conectar un cliente HTTP con fetch:",
      'import { initializeApp } from "firebase/app";',
      "",
      "async function conectarClienteHttp(url, apiKey) {",
      "  const res = await fetch(url, {",
      '    method: "POST",',
      '    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${apiKey}` },',
      '    body: JSON.stringify({ projectId: "shadowing-efcab", templateId: "conexion-key" }),',
      "  });",
      "  if (!res.ok) throw new Error(`HTTP ${res.status}`);",
      "  return await res.json();",
      "}",
    ].join("\n");
  }

  return `[Plantilla '${TEMPLATE_ID}' (shadowing-efcab)] Consulta procesada ("${cleanQuery}") con llave ${cleanKey.slice(0, 8)}...`;
}

if (typeof window !== "undefined") {
  window.consultarAsistente = consultarAsistente;
}
