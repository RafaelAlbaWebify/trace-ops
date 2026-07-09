export const generatedEndpoints: Record<string, string[]> = {
  "health": [
    "/api/health"
  ],
  "history": [
    "/api/logs/history"
  ],
  "shareAccess": [
    "/api/diagnostics/factoryops/computer",
    "/api/diagnostics/factoryops/file-share-access"
  ],
  "dns": [
    "/api/diagnostics/dns"
  ],
  "adUser": [
    "/api/diagnostics/ad-user-access",
    "/api/readiness/graph",
    "/api/readiness/local",
    "/api/readiness/ad"
  ],
  "readiness": []
};
