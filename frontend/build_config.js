const fs = require("fs");

const supabaseUrl = process.env.SUPABASE_URL || "";
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY || "";
const apiBase = process.env.API_BASE || "http://127.0.0.1:8000";

if (!supabaseUrl || !supabaseAnonKey || !apiBase) {
  throw new Error(
    "Missing SUPABASE_URL, SUPABASE_ANON_KEY, or API_BASE environment variable."
  );
}

const configContent = `window.APP_CONFIG = {
  SUPABASE_URL: "${supabaseUrl}",
  SUPABASE_ANON_KEY: "${supabaseAnonKey}",
  API_BASE: "${apiBase}",
};
`;

fs.writeFileSync("config.js", configContent);

console.log("config.js generated successfully for deployment.");