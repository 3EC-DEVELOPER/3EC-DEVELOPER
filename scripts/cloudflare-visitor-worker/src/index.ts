interface Env {
  VISITOR_STATS_KV: KVNamespace;
  ANALYTICS_SALT: string;
  ADMIN_API_TOKEN: string;
  PROFILE_NAME: string;
  LINKEDIN_URL: string;
}

interface StatsSummary {
  totalVisitors: number;
  uniqueVisitors: number;
  linkedinClicks: number;
  firstSeenDate: string;
  lastUpdatedAt: string;
}

const SUMMARY_KEY = "stats:summary";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/visitor-stats.svg") {
      return handleVisitorStatsSvg(request, env);
    }

    if (request.method === "GET" && url.pathname === "/r/linkedin") {
      return handleLinkedInRedirect(env);
    }

    if (request.method === "POST" && url.pathname === "/events/linkedin") {
      return handleLinkedInEvent(request, env);
    }

    if (request.method === "GET" && url.pathname === "/health") {
      return Response.json({ ok: true, service: "visitor-analytics-worker" });
    }

    return new Response("Not found", { status: 404 });
  },
};

async function handleVisitorStatsSvg(request: Request, env: Env): Promise<Response> {
  const now = new Date();
  const fingerprint = await createVisitorFingerprint(request, env.ANALYTICS_SALT);
  const uniqueKey = `unique:v1:${fingerprint}`;

  const [existingUnique, summary] = await Promise.all([
    env.VISITOR_STATS_KV.get(uniqueKey),
    getStatsSummary(env),
  ]);

  let uniqueVisitors = summary.uniqueVisitors;
  if (!existingUnique) {
    uniqueVisitors += 1;
    await env.VISITOR_STATS_KV.put(
      uniqueKey,
      JSON.stringify({ firstSeenAt: now.toISOString() }),
    );
  }

  const nextSummary: StatsSummary = {
    totalVisitors: summary.totalVisitors + 1,
    uniqueVisitors,
    linkedinClicks: summary.linkedinClicks,
    firstSeenDate: summary.firstSeenDate || getUtcDate(now),
    lastUpdatedAt: now.toISOString(),
  };

  await env.VISITOR_STATS_KV.put(SUMMARY_KEY, JSON.stringify(nextSummary));

  const dailyAverage = calculateDailyAverage(
    nextSummary.totalVisitors,
    nextSummary.firstSeenDate,
    now,
  );

  const svg = renderSvg({
    totalVisitors: nextSummary.totalVisitors,
    uniqueVisitors: nextSummary.uniqueVisitors,
    linkedinClicks: nextSummary.linkedinClicks,
    dailyAverage,
  });

  return new Response(svg, {
    headers: {
      "Content-Type": "image/svg+xml; charset=utf-8",
      "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
      Pragma: "no-cache",
      Expires: "0",
    },
  });
}

async function handleLinkedInRedirect(env: Env): Promise<Response> {
  const summary = await getStatsSummary(env);

  const nextSummary: StatsSummary = {
    ...summary,
    linkedinClicks: summary.linkedinClicks + 1,
    lastUpdatedAt: new Date().toISOString(),
  };

  await env.VISITOR_STATS_KV.put(SUMMARY_KEY, JSON.stringify(nextSummary));

  return Response.redirect(env.LINKEDIN_URL, 302);
}

async function handleLinkedInEvent(request: Request, env: Env): Promise<Response> {
  const authHeader = request.headers.get("Authorization");
  const expected = `Bearer ${env.ADMIN_API_TOKEN}`;

  if (authHeader !== expected) {
    return new Response("Unauthorized", { status: 401 });
  }

  const summary = await getStatsSummary(env);

  const nextSummary: StatsSummary = {
    ...summary,
    linkedinClicks: summary.linkedinClicks + 1,
    lastUpdatedAt: new Date().toISOString(),
  };

  await env.VISITOR_STATS_KV.put(SUMMARY_KEY, JSON.stringify(nextSummary));

  return Response.json({
    ok: true,
    linkedinClicks: nextSummary.linkedinClicks,
  });
}

async function getStatsSummary(env: Env): Promise<StatsSummary> {
  const raw = await env.VISITOR_STATS_KV.get(SUMMARY_KEY);

  if (!raw) {
    return {
      totalVisitors: 0,
      uniqueVisitors: 0,
      linkedinClicks: 0,
      firstSeenDate: getUtcDate(new Date()),
      lastUpdatedAt: new Date(0).toISOString(),
    };
  }

  const parsed = JSON.parse(raw) as Partial<StatsSummary>;

  return {
    totalVisitors: parsed.totalVisitors ?? 0,
    uniqueVisitors: parsed.uniqueVisitors ?? 0,
    linkedinClicks: parsed.linkedinClicks ?? 0,
    firstSeenDate: parsed.firstSeenDate ?? getUtcDate(new Date()),
    lastUpdatedAt: parsed.lastUpdatedAt ?? new Date(0).toISOString(),
  };
}

async function createVisitorFingerprint(request: Request, salt: string): Promise<string> {
  const ip =
    request.headers.get("CF-Connecting-IP") ??
    request.headers.get("x-forwarded-for") ??
    "unknown-ip";

  const userAgent = request.headers.get("user-agent") ?? "unknown-ua";
  const acceptLanguage = request.headers.get("accept-language") ?? "unknown-lang";

  const source = `${salt}|${ip}|${userAgent}|${acceptLanguage}`;
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(source));

  return [...new Uint8Array(digest)]
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("");
}

function getUtcDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function calculateDailyAverage(totalVisitors: number, firstSeenDate: string, now: Date): string {
  const start = new Date(`${firstSeenDate}T00:00:00.000Z`);
  const elapsedMs = now.getTime() - start.getTime();
  const elapsedDays = Math.max(1, Math.floor(elapsedMs / 86400000) + 1);
  const average = totalVisitors / elapsedDays;

  return average.toFixed(1);
}

function renderSvg(stats: {
  totalVisitors: number;
  uniqueVisitors: number;
  linkedinClicks: number;
  dailyAverage: string;
}): string {
  const eyePath =
    "M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zm0 12.5c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z";
  const personPath =
    "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z";
  const linkedinPath =
    "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z";

  const cards = [
    {
      x: 12,
      centerX: 108,
      label: "TOTAL VISITORS",
      value: String(stats.totalVisitors),
      icon: `<g transform="translate(94,29) scale(1.1667)" fill="#8b949e"><path d="${eyePath}"/></g>`,
    },
    {
      x: 215,
      centerX: 311,
      label: "UNIQUE",
      value: String(stats.uniqueVisitors),
      icon: `<g transform="translate(297,29) scale(1.1667)" fill="#8b949e"><path d="${personPath}"/></g>`,
    },
    {
      x: 418,
      centerX: 514,
      label: "LINKEDIN",
      value: String(stats.linkedinClicks),
      icon: `<g transform="translate(500,29) scale(1.1667)" fill="#0A66C2" fill-rule="evenodd"><path d="${linkedinPath}"/></g>`,
    },
    {
      x: 621,
      centerX: 717,
      label: "DAILY AVG",
      value: stats.dailyAverage,
      icon:
        '<rect x="703" y="43" width="6" height="14" rx="1" fill="#3fb950"/>' +
        '<rect x="712" y="29" width="6" height="28" rx="1" fill="#f85149"/>' +
        '<rect x="721" y="36" width="6" height="21" rx="1" fill="#58a6ff"/>',
    },
  ];

  const cardMarkup = cards
    .map((card) => {
      const fontSize = getValueFontSize(card.value);

      return `
  <rect x="${card.x}" y="12" width="193" height="151" rx="8" fill="#252c37"/>
  ${card.icon}
  <text x="${card.centerX}" y="82" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="10" fill="#8b949e" letter-spacing="1.5" font-weight="600">${escapeXml(card.label)}</text>
  <text x="${card.centerX}" y="130" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="${fontSize}" font-weight="700" fill="#f0f6fc">${escapeXml(card.value)}</text>`;
    })
    .join("");

  return `<svg width="830" height="175" viewBox="0 0 830 175" xmlns="http://www.w3.org/2000/svg">
  <rect width="830" height="175" rx="12" fill="#1b1f24"/>
  ${cardMarkup}
</svg>`;
}

function getValueFontSize(value: string): number {
  if (value.length <= 4) {
    return 40;
  }

  if (value.length <= 6) {
    return 32;
  }

  return 24;
}

function escapeXml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}
