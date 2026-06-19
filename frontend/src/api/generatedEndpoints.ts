export const generatedEndpoints: Record<string, string[]> = {
  "health": [
    "/api/health"
  ],
  "history": [
    "/api/scan/user-access",
    "/api/history",
    "/api/history/{history_id}/report.json",
    "/api/history/{history_id}/report.html"
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
