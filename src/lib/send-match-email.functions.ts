import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

// Hardcoded owner recipient — Resend's onboarding@resend.dev sender only
// delivers to the account owner anyway. Locking the recipient server-side
// prevents this endpoint from being abused as an open email relay.
const OWNER_EMAIL = "ravipridh88@gmail.com";

const InputSchema = z.object({
  jobTitle: z.string().min(1).max(200).default("Target Role"),
  score: z.number().min(0).max(100),
  matched: z.array(z.string().max(80)).max(30),
  missing: z.array(z.string().max(80)).max(30),
  subScores: z.object({
    skills: z.number().min(0).max(100),
    experience: z.number().min(0).max(100),
    cultureFit: z.number().min(0).max(100),
  }),
});

type Input = z.infer<typeof InputSchema>;

// Escape user-controlled strings before interpolating into HTML.
function esc(s: string) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Best-effort in-memory throttle per worker instance.
const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 5;
const hits: number[] = [];
function checkRate() {
  const now = Date.now();
  while (hits.length && now - hits[0] > RATE_WINDOW_MS) hits.shift();
  if (hits.length >= RATE_MAX) return false;
  hits.push(now);
  return true;
}

function renderHtml(d: Input) {
  const jobTitle = esc(d.jobTitle);
  const chip = (t: string, color: string) =>
    `<span style="display:inline-block;background:${color}1a;color:${color};font-size:12px;font-weight:600;padding:4px 10px;border-radius:999px;margin:2px 4px 2px 0">${esc(t)}</span>`;

  const matchedChips = d.matched.map((k) => chip(k, "#34A853")).join("");
  const missingChips = d.missing.map((k) => chip(k, "#EA4335")).join("");

  const sub = (label: string, val: number, color: string) => `
    <td style="padding:12px;border:1px solid #eef2f7;border-radius:12px;text-align:center;width:33%">
      <div style="font-size:10px;font-weight:700;color:#64748b;letter-spacing:1px;text-transform:uppercase">${esc(label)}</div>
      <div style="font-size:22px;font-weight:800;color:${color};margin-top:4px">${val}%</div>
    </td>`;

  const matchedList = esc(d.matched.slice(0, 3).join(", ") || "—");
  const missingList = esc(d.missing.join(", ") || "—");

  return `<!doctype html><html><body style="margin:0;background:#f8fafc;font-family:'Helvetica Neue',Arial,sans-serif;color:#0f172a">
<div style="max-width:640px;margin:0 auto;padding:24px">
  <div style="background:white;border-radius:24px;padding:32px;border:1px solid #e2e8f0">
    <div style="font-size:12px;font-weight:800;letter-spacing:2px;color:#4285F4;text-transform:uppercase">JobMatch AI · Hasil Analisis</div>
    <h1 style="font-size:26px;margin:8px 0 4px">Match Report — ${jobTitle}</h1>
    <p style="color:#64748b;margin:0 0 24px">Score kompatibilitas CV kamu dengan role ini.</p>

    <div style="display:flex;align-items:center;gap:16px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:16px;padding:20px">
      <div style="font-size:44px;font-weight:800;color:#34A853;line-height:1">${d.score}</div>
      <div>
        <div style="font-size:14px;font-weight:700">${d.score >= 80 ? "Strong Match 🎯" : d.score >= 60 ? "Good Match 👍" : "Needs Work ⚡"}</div>
        <div style="font-size:13px;color:#475569">CV kamu cocok untuk ${d.score}% requirement role ini.</div>
      </div>
    </div>

    <h3 style="font-size:12px;letter-spacing:1px;color:#34A853;margin:24px 0 8px;text-transform:uppercase">✓ Matched Keywords</h3>
    <div>${matchedChips || '<span style="color:#94a3b8;font-size:13px">—</span>'}</div>

    <h3 style="font-size:12px;letter-spacing:1px;color:#EA4335;margin:20px 0 8px;text-transform:uppercase">✗ Missing / Weak</h3>
    <div>${missingChips || '<span style="color:#94a3b8;font-size:13px">—</span>'}</div>

    <table role="presentation" cellspacing="8" style="width:100%;margin-top:24px;border-collapse:separate"><tr>
      ${sub("Skills", d.subScores.skills, "#4285F4")}
      ${sub("Experience", d.subScores.experience, "#FBBC05")}
      ${sub("Culture Fit", d.subScores.cultureFit, "#34A853")}
    </tr></table>

    <hr style="border:none;border-top:1px solid #e2e8f0;margin:32px 0"/>

    <h2 style="font-size:18px;margin:0 0 8px">🇮🇩 Ringkasan (Bahasa Indonesia)</h2>
    <p style="color:#334155;font-size:14px;line-height:1.6">
      CV kamu memiliki compatibility <b>${d.score}%</b> untuk role <b>${jobTitle}</b>.
      Kamu sudah memenuhi ${d.matched.length} keyword utama seperti ${matchedList}.
      Untuk meningkatkan peluang lolos ATS, fokus tambahkan ${d.missing.length} skill berikut: <b>${missingList}</b>.
      Highlight pencapaian dengan angka konkret dan gunakan action verbs.
    </p>

    <h2 style="font-size:18px;margin:20px 0 8px">🇬🇧 Summary (English)</h2>
    <p style="color:#334155;font-size:14px;line-height:1.6">
      Your CV has a <b>${d.score}%</b> compatibility for the <b>${jobTitle}</b> role.
      You already cover ${d.matched.length} key requirements including ${matchedList}.
      To improve ATS pass rate, prioritize adding these ${d.missing.length} skills: <b>${missingList}</b>.
      Quantify achievements with concrete numbers and use strong action verbs.
    </p>

    <div style="margin-top:32px;padding-top:20px;border-top:1px solid #e2e8f0;color:#94a3b8;font-size:12px;text-align:center">
      Sent by JobMatch AI · Made in Indonesia 🇮🇩
    </div>
  </div>
</div></body></html>`;
}

export const sendMatchEmail = createServerFn({ method: "POST" })
  .inputValidator((data: unknown) => InputSchema.parse(data))
  .handler(async ({ data }) => {
    if (!checkRate()) {
      throw new Error("Rate limit exceeded. Please try again in a minute.");
    }

    const apiKey = process.env.RESEND_API_KEY;
    if (!apiKey) throw new Error("RESEND_API_KEY not configured");

    const safeTitle = data.jobTitle.replace(/[\r\n]+/g, " ").slice(0, 120);

    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "JobMatch AI <onboarding@resend.dev>",
        to: [OWNER_EMAIL],
        subject: `Your JobMatch Report — ${data.score}% match for ${safeTitle}`,
        html: renderHtml(data),
      }),
    });

    if (!res.ok) {
      const body = await res.text();
      console.error(`Resend failed [${res.status}]: ${body}`);
      throw new Error(`Email send failed: ${res.status}`);
    }

    return { sent: true as const };
  });
