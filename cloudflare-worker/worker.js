/**
 * EGX Data Proxy — Cloudflare Worker
 *
 * Forwards requests to investing.com's public OHLCV endpoint from Cloudflare's
 * own network, which bypasses Cloudflare's bot blocks on cloud IPs (Azure/AWS).
 *
 * Endpoints:
 *   GET /?iid=12865&points=160              → investing.com primary
 *   GET /tvc?iid=12865&points=160           → investing.com TVC fallback
 *
 * Auth: caller must send `X-Proxy-Token` header matching the PROXY_TOKEN secret.
 */

const INV_HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
  "Accept": "application/json, text/plain, */*",
  "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
  "Referer": "https://www.investing.com/",
  "Origin": "https://www.investing.com",
};

const ALLOWED_POINTS = new Set(["60", "70", "90", "110", "120", "140", "160"]);

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return corsPreflight();
    if (request.method !== "GET") return jsonResp({ error: "method not allowed" }, 405);

    // Auth gate
    if (!env.PROXY_TOKEN) {
      return jsonResp({ error: "PROXY_TOKEN not configured on worker" }, 500);
    }
    const token = request.headers.get("X-Proxy-Token");
    if (token !== env.PROXY_TOKEN) {
      return jsonResp({ error: "unauthorized" }, 401);
    }

    const url = new URL(request.url);
    const path = url.pathname.replace(/\/$/, "") || "/";
    const iid = url.searchParams.get("iid");
    let points = url.searchParams.get("points") || "160";
    if (!ALLOWED_POINTS.has(points)) points = "160";

    if (!iid || !/^\d+$/.test(iid)) {
      return jsonResp({ error: "missing or invalid iid" }, 400);
    }

    let target;
    if (path === "/" || path === "") {
      target = `https://api.investing.com/api/financialdata/${iid}/historical/chart/?interval=P1D&pointscount=${points}`;
    } else if (path === "/tvc") {
      const now = Math.floor(Date.now() / 1000);
      const frm = now - parseInt(points, 10) * 60 * 60 * 24 * 1.6;
      target = `https://tvc6.investing.com/4f9f4b3e0a5d5ebf3aa1f8c3eea9e34d/0/0/0/0/history?symbol=${iid}&resolution=D&from=${Math.floor(frm)}&to=${now}`;
    } else if (path === "/health") {
      return jsonResp({ ok: true, worker: "egx-data-proxy" });
    } else {
      return jsonResp({ error: "unknown route", path }, 404);
    }

    try {
      const upstream = await fetch(target, {
        headers: INV_HEADERS,
        cf: { cacheTtl: 300, cacheEverything: true },
      });
      const body = await upstream.text();
      return new Response(body, {
        status: upstream.status,
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          "Access-Control-Allow-Origin": "*",
          "X-Proxy-Source": new URL(target).host,
        },
      });
    } catch (err) {
      return jsonResp({ error: "upstream_fetch_failed", detail: String(err) }, 502);
    }
  },
};

function jsonResp(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
    },
  });
}

function corsPreflight() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "X-Proxy-Token, Content-Type",
      "Access-Control-Max-Age": "86400",
    },
  });
}
