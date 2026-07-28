/**
 * ats-scorer.ts
 * All scoring logic — formatting, keyword match, career gaps, quantification.
 */

import type { ParsedCV } from "./cv-parser";

// ── Types ─────────────────────────────────────────────────────────────────────
export interface FormattingScore {
  score: number; // 0-100
  details: {
    singleColumn: boolean;
    standardHeaders: boolean;
    contactDetected: boolean;
    reasonableLength: boolean;
    noArtifacts: boolean;
  };
  suggestions: string[];
}

export interface KeywordScore {
  score: number; // 0-100
  matched: string[];
  missing: string[];
  suggestions: string[];
}

export interface CareerGap {
  from: string;
  to: string;
  months: number;
}

export interface QuantificationResult {
  totalBullets: number;
  weakBullets: string[];
  strongBullets: string[];
  score: number; // 0-100
}

export interface ATSReport {
  formattingScore: FormattingScore;
  keywordScore: KeywordScore;
  careerGaps: CareerGap[];
  quantification: QuantificationResult;
  overallScore: number;
}

// ── Indonesian stopwords (minimal) ───────────────────────────────────────────
const STOPWORDS = new Set([
  "dan","yang","di","ke","dari","untuk","dengan","adalah","ini","itu","atau",
  "pada","dalam","oleh","sebagai","juga","telah","akan","lebih","dapat","tidak",
  "the","a","an","in","on","at","to","for","of","and","or","is","was","are",
  "were","has","have","had","with","by","as","at","this","that","be","been",
]);

// ── Known tech/skill keywords for extraction ─────────────────────────────────
const KNOWN_SKILLS = [
  "python","javascript","typescript","react","next.js","node.js","express","django",
  "fastapi","sql","postgresql","mysql","mongodb","redis","docker","kubernetes","aws",
  "gcp","azure","git","ci/cd","agile","scrum","figma","photoshop","excel","powerpoint",
  "tableau","power bi","machine learning","deep learning","tensorflow","pytorch",
  "nlp","data analysis","api","rest","graphql","java","kotlin","swift","flutter",
  "vue","angular","html","css","tailwind","bootstrap","linux","bash","data science",
  "project management","product management","ux","ui","leadership","communication",
  "problem solving","teamwork","manajemen","analisis","pengembangan","pemrograman",
];

// ── Keyword extractor ─────────────────────────────────────────────────────────
function extractKeywords(text: string): string[] {
  const words = text
    .toLowerCase()
    .replace(/[^a-z0-9\s.+#/-]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOPWORDS.has(w));

  const found = new Set<string>();

  // Match known skills (including multi-word)
  for (const skill of KNOWN_SKILLS) {
    if (text.toLowerCase().includes(skill)) {
      found.add(skill);
    }
  }

  // Add remaining non-stopword tokens
  for (const w of words) {
    if (!STOPWORDS.has(w)) found.add(w);
  }

  return Array.from(found);
}

// ── 1. Formatting Score ───────────────────────────────────────────────────────
export function scoreFormatting(cv: ParsedCV): FormattingScore {
  const suggestions: string[] = [];

  const singleColumn = !cv.hasTableArtifacts;
  if (!singleColumn)
    suggestions.push("CV terdeteksi menggunakan layout multi-kolom atau tabel. Gunakan format satu kolom agar ATS dapat membaca teks secara linear.");

  const standardHeaders =
    cv.sections.workExperience.length > 0 ||
    cv.sections.education.length > 0 ||
    cv.sections.skills.length > 0;
  if (!standardHeaders)
    suggestions.push("Heading section tidak terdeteksi (Pengalaman Kerja, Pendidikan, Keahlian). Pastikan heading ditulis dengan istilah standar.");

  const emailRegex = /[\w.-]+@[\w.-]+\.\w+/;
  const phoneRegex = /(\+62|0)[0-9\s\-().]{7,}/;
  const contactDetected =
    emailRegex.test(cv.sections.contactInfo) ||
    phoneRegex.test(cv.sections.contactInfo) ||
    emailRegex.test(cv.rawText.slice(0, 500));
  if (!contactDetected)
    suggestions.push("Email atau nomor telepon tidak terdeteksi di bagian kontak. Pastikan data kontak ditulis sebagai teks biasa, bukan gambar.");

  // ~250–750 words ≈ 1-2 pages
  const reasonableLength = cv.wordCount >= 200 && cv.wordCount <= 900;
  if (!reasonableLength) {
    if (cv.wordCount < 200)
      suggestions.push(`CV terlalu pendek (${cv.wordCount} kata). CV ideal memiliki 300-750 kata (1-2 halaman).`);
    else
      suggestions.push(`CV terlalu panjang (${cv.wordCount} kata). Rekruter dan ATS lebih menyukai CV 1-2 halaman.`);
  }

  const noArtifacts = !cv.hasTableArtifacts;
  if (!noArtifacts)
    suggestions.push("Terdeteksi karakter khusus berlebih dari tabel/text-box. Hapus elemen grafis dan gunakan teks biasa.");

  const checks = [singleColumn, standardHeaders, contactDetected, reasonableLength, noArtifacts];
  const passCount = checks.filter(Boolean).length;
  const score = Math.round((passCount / checks.length) * 100);

  return {
    score,
    details: { singleColumn, standardHeaders, contactDetected, reasonableLength, noArtifacts },
    suggestions,
  };
}

// ── 2. Keyword Match Score ────────────────────────────────────────────────────
export function scoreKeywords(cvText: string, jobDescription: string): KeywordScore {
  if (!jobDescription.trim()) {
    return {
      score: 0,
      matched: [],
      missing: [],
      suggestions: ["Tempelkan deskripsi pekerjaan untuk mendapatkan analisis keyword."],
    };
  }

  const jdKeywords = extractKeywords(jobDescription);
  const cvLower = cvText.toLowerCase();

  const matched: string[] = [];
  const missing: string[] = [];

  for (const kw of jdKeywords) {
    if (cvLower.includes(kw)) {
      matched.push(kw);
    } else {
      missing.push(kw);
    }
  }

  const score = jdKeywords.length > 0 ? Math.round((matched.length / jdKeywords.length) * 100) : 0;

  const suggestions: string[] = [];
  if (missing.length > 0) {
    suggestions.push(`Tambahkan kata kunci berikut yang ada di JD namun tidak ditemukan di CV: ${missing.slice(0, 8).join(", ")}.`);
  }
  if (score < 50) {
    suggestions.push("Sesuaikan bahasa di CV agar lebih dekat dengan istilah yang digunakan pada deskripsi pekerjaan.");
  }

  return { score, matched, missing, suggestions };
}

// ── 3. Career Gap Detector ────────────────────────────────────────────────────
const MONTH_MAP: Record<string, number> = {
  jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,oct:9,nov:10,dec:11,
  januari:0,februari:1,maret:2,april:3,mei:4,juni:5,juli:6,agustus:7,
  september:8,oktober:9,november:10,desember:11,
};

function parseDate(str: string): Date | null {
  const s = str.trim().toLowerCase();
  if (s === "present" || s === "sekarang" || s === "now") return new Date();

  // "Jan 2020" or "January 2020"
  const monthYear = s.match(/([a-z]+)\s+(\d{4})/);
  if (monthYear) {
    const m = MONTH_MAP[monthYear[1].slice(0, 3)];
    if (m !== undefined) return new Date(Number(monthYear[2]), m, 1);
  }

  // "2020" only
  const yearOnly = s.match(/^(\d{4})$/);
  if (yearOnly) return new Date(Number(yearOnly[1]), 0, 1);

  // "2020-01" or "01/2020"
  const isoMonth = s.match(/(\d{4})[-/](\d{1,2})/);
  if (isoMonth) return new Date(Number(isoMonth[1]), Number(isoMonth[2]) - 1, 1);

  return null;
}

export function detectCareerGaps(workExperienceText: string): CareerGap[] {
  const dateRangePattern =
    /([a-z]+ \d{4}|\d{4})\s*[-–—]\s*([a-z]+ \d{4}|\d{4}|present|sekarang)/gi;

  const ranges: { start: Date; end: Date }[] = [];

  let match;
  while ((match = dateRangePattern.exec(workExperienceText)) !== null) {
    const start = parseDate(match[1]);
    const end = parseDate(match[2]);
    if (start && end) ranges.push({ start, end });
  }

  // Sort chronologically
  ranges.sort((a, b) => a.start.getTime() - b.start.getTime());

  const gaps: CareerGap[] = [];
  for (let i = 1; i < ranges.length; i++) {
    const prevEnd = ranges[i - 1].end;
    const nextStart = ranges[i].start;
    const diffMonths =
      (nextStart.getFullYear() - prevEnd.getFullYear()) * 12 +
      (nextStart.getMonth() - prevEnd.getMonth());

    if (diffMonths > 3) {
      gaps.push({
        from: prevEnd.toLocaleDateString("id-ID", { month: "long", year: "numeric" }),
        to: nextStart.toLocaleDateString("id-ID", { month: "long", year: "numeric" }),
        months: diffMonths,
      });
    }
  }

  return gaps;
}

// ── 4. Quantification Checker ─────────────────────────────────────────────────
const METRIC_PATTERN = /\d+(%|x|×|persen|juta|ribu|rb|k\b|m\b|\+|users?|client|project|produk)/i;
const NUMBER_PATTERN = /\d+/;

export function checkQuantification(workExperienceText: string): QuantificationResult {
  const bullets = workExperienceText
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.startsWith("-") || l.startsWith("•") || l.startsWith("*") || /^\w/.test(l))
    .filter((l) => l.length > 20);

  const weakBullets: string[] = [];
  const strongBullets: string[] = [];

  for (const b of bullets) {
    if (METRIC_PATTERN.test(b) || NUMBER_PATTERN.test(b)) {
      strongBullets.push(b);
    } else {
      weakBullets.push(b);
    }
  }

  const total = bullets.length || 1;
  const score = Math.round((strongBullets.length / total) * 100);

  return {
    totalBullets: bullets.length,
    weakBullets: weakBullets.slice(0, 8),
    strongBullets: strongBullets.slice(0, 8),
    score,
  };
}

// ── 5. Overall Score (weighted) ───────────────────────────────────────────────
export function calculateOverallScore(
  formattingScore: number,
  keywordScore: number,
  quantScore: number
): number {
  return Math.round(formattingScore * 0.3 + keywordScore * 0.5 + quantScore * 0.2);
}

// ── Main: run all checks ──────────────────────────────────────────────────────
export function runATSAnalysis(cv: ParsedCV, jobDescription: string): ATSReport {
  const formattingScore = scoreFormatting(cv);
  const keywordScore = scoreKeywords(cv.rawText, jobDescription);
  const careerGaps = detectCareerGaps(cv.sections.workExperience);
  const quantification = checkQuantification(cv.sections.workExperience);
  const overallScore = calculateOverallScore(
    formattingScore.score,
    keywordScore.score,
    quantification.score
  );

  return { formattingScore, keywordScore, careerGaps, quantification, overallScore };
}
