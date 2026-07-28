/**
 * cv-parser.ts
 * Heuristic CV section extractor + file-to-text conversion helpers.
 * Works fully client-side for DOCX (mammoth) and server-side for PDF.
 */

export interface ParsedCV {
  rawText: string;
  sections: {
    contactInfo: string;
    summary: string;
    workExperience: string;
    education: string;
    skills: string;
  };
  wordCount: number;
  hasTableArtifacts: boolean;
}

// ── Section header patterns (Indonesian + English) ────────────────────────────
const SECTION_PATTERNS: Record<keyof ParsedCV["sections"], RegExp[]> = {
  contactInfo: [
    /^(kontak|contact|informasi kontak|contact info|personal info|data diri)/im,
  ],
  summary: [
    /^(ringkasan|profil|summary|profile|objective|tujuan|tentang saya|about me)/im,
  ],
  workExperience: [
    /^(pengalaman kerja|pengalaman|work experience|experience|riwayat pekerjaan|riwayat karir|employment)/im,
  ],
  education: [
    /^(pendidikan|education|riwayat pendidikan|academic|akademik)/im,
  ],
  skills: [
    /^(keahlian|skills|skill|kemampuan|kompetensi|technical skills|hard skills|soft skills)/im,
  ],
};

// ── Extract sections from raw text ────────────────────────────────────────────
export function extractSections(text: string): ParsedCV["sections"] {
  const lines = text.split("\n");
  const sections: ParsedCV["sections"] = {
    contactInfo: "",
    summary: "",
    workExperience: "",
    education: "",
    skills: "",
  };

  let currentSection: keyof ParsedCV["sections"] | null = null;
  const buffer: Record<keyof ParsedCV["sections"], string[]> = {
    contactInfo: [],
    summary: [],
    workExperience: [],
    education: [],
    skills: [],
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      if (currentSection) buffer[currentSection].push("");
      continue;
    }

    // Detect section heading
    let matched = false;
    for (const [sectionKey, patterns] of Object.entries(SECTION_PATTERNS)) {
      if (patterns.some((p) => p.test(trimmed))) {
        currentSection = sectionKey as keyof ParsedCV["sections"];
        matched = true;
        break;
      }
    }

    if (!matched && currentSection) {
      buffer[currentSection].push(trimmed);
    }
  }

  // Fallback: if contactInfo is empty, pull the first 5 lines as contact
  if (buffer.contactInfo.length === 0) {
    buffer.contactInfo = lines.slice(0, 5).map((l) => l.trim()).filter(Boolean);
  }

  for (const key of Object.keys(buffer) as (keyof ParsedCV["sections"])[]) {
    sections[key] = buffer[key].join("\n").trim();
  }

  return sections;
}

// ── Detect table/text-box artifacts ──────────────────────────────────────────
export function detectTableArtifacts(text: string): boolean {
  const pipeCount = (text.match(/\|/g) || []).length;
  const tabCount = (text.match(/\t/g) || []).length;
  // Multi-column layouts often produce lots of pipe chars or tab-separated columns
  return pipeCount > 10 || tabCount > 20;
}

// ── Parse DOCX in browser using mammoth (CDN/dynamic import) ─────────────────
export async function parseDOCX(file: File): Promise<string> {
  // mammoth must be available — installed separately or via CDN
  // @ts-ignore — dynamic import for browser
  const mammoth = await import("mammoth");
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer });
  return result.value;
}

// ── Parse PDF via server API route ────────────────────────────────────────────
export async function parsePDFViaAPI(file: File, parsePdfFn?: (args: any) => Promise<{text: string}>): Promise<string> {
  if (!parsePdfFn) {
    throw new Error("Fungsi parsePdf server function wajib disertakan untuk membaca PDF.");
  }

  const base64 = await new Promise<string>((res, rej) => {
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      res(dataUrl.split(",")[1]);
    };
    reader.onerror = rej;
    reader.readAsDataURL(file);
  });

  const result = await parsePdfFn({ data: { base64, filename: file.name } });
  return result.text;
}

// ── Main entry: file → ParsedCV ───────────────────────────────────────────────
export async function parseCV(file: File, parsePdfFn?: (args: any) => Promise<{text: string}>): Promise<ParsedCV> {
  let rawText = "";

  if (file.name.endsWith(".docx")) {
    rawText = await parseDOCX(file);
  } else if (file.name.endsWith(".pdf")) {
    rawText = await parsePDFViaAPI(file, parsePdfFn);
  } else {
    throw new Error("Format tidak didukung. Gunakan .pdf atau .docx");
  }

  const sections = extractSections(rawText);
  const wordCount = rawText.split(/\s+/).filter(Boolean).length;
  const hasTableArtifacts = detectTableArtifacts(rawText);

  return { rawText, sections, wordCount, hasTableArtifacts };
}
