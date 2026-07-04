/**
 * Select environment config by hostname, then expose globals used by index.html / upload.html.
 * Override: set localStorage.vizzel_config_env = "staging" | "production" | "local" | "legacy"
 */
(function (global) {
  const CONFIGS = {
    production: {
      ENV: "production",
      FRONTEND_BASE_URL: "https://sale.vizzeltrack.com/",
      API: "https://sale-api.vizzeltrack.com",
      LIFF_ID: "2010133685-tke1EWht",
      APP_BOOT_VERSION: "20260703-selfhost",
    },
    staging: {
      ENV: "staging",
      FRONTEND_BASE_URL: "https://staging-sale.vizzeltrack.com/",
      API: "https://staging-sale-api.vizzeltrack.com",
      LIFF_ID: "2010133685-tke1EWht",
      APP_BOOT_VERSION: "20260703-selfhost-staging",
    },
    local: {
      ENV: "local",
      FRONTEND_BASE_URL: "http://127.0.0.1:5500/",
      API: "http://127.0.0.1:8080",
      LIFF_ID: "2010133685-tke1EWht",
      APP_BOOT_VERSION: "20260703-local",
    },
    legacy: {
      ENV: "legacy",
      FRONTEND_BASE_URL: "https://vizzelintel.github.io/vizzel-sales-frontend/",
      API: "https://vizzel-sales-api.fly.dev",
      LIFF_ID: "2010133685-tke1EWht",
      APP_BOOT_VERSION: "20260703-legacy",
    },
  };

  function detectEnv() {
    try {
      const override = global.localStorage && global.localStorage.getItem("vizzel_config_env");
      if (override && CONFIGS[override]) return override;
    } catch (_) { /* private mode */ }

    const host = (global.location && global.location.hostname) || "";
    if (host === "staging-sale.vizzeltrack.com") return "staging";
    if (host === "sale.vizzeltrack.com") return "production";
    if (host === "localhost" || host === "127.0.0.1") return "local";
    if (host.includes("github.io")) return "legacy";
    return "production";
  }

  const cfg = Object.assign({}, CONFIGS[detectEnv()]);
  cfg.API_BASE = cfg.API + "/api/v1";
  cfg.LIFF_OPEN_URL = "https://liff.line.me/" + cfg.LIFF_ID;

  global.VIZZEL_CONFIG = cfg;
  global.FRONTEND_BASE_URL = cfg.FRONTEND_BASE_URL;
  global.LIFF_ID = cfg.LIFF_ID;
  global.LIFF_OPEN_URL = cfg.LIFF_OPEN_URL;
  global.APP_BOOT_VERSION = cfg.APP_BOOT_VERSION;
  global.API = cfg.API;
  global.API_BASE = cfg.API_BASE;
})(typeof window !== "undefined" ? window : globalThis);
