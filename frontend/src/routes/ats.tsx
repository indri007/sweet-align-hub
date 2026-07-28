/**
 * ats.tsx — CV ATS Checker page
 * Route: /ats
 */
import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { parsePdfFn } from "@/lib/parse-pdf.functions";
import { useCallback, useRef, useState } from "react";
import { parseCV, type ParsedCV } from "@/lib/cv-parser";
import { runATSAnalysis, type ATSReport } from "@/lib/ats-scorer";
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Loader2,
  Download,
  BarChart3,
  Zap,
  Calendar,
  Hash,
  Target,
} from "lucide-react";

export const Route = createFileRoute("/ats")({
  component: ATSChecker,
});

// ── Colour helpers ────────────────────────────────────────────────────────────
function scoreColor(s: number): string {
  if (s >= 76) return "#22c55e";
  if (s >= 50) return "#eab308";
  return "#ef4444";
}

function scoreBg(s: number): string {
  if (s >= 76) return "rgba(34,197,94,0.12)";
  if (s >= 50) return "rgba(234,179,8,0.12)";
  return "rgba(239,68,68,0.12)";
}

function scoreLabel(s: number): string {
  if (s >= 76) return "Siap ATS";
  if (s >= 50) return "Perlu Perbaikan";
  return "Risiko Tinggi Terfilter";
}

// ── Radial Progress ───────────────────────────────────────────────────────────
function RadialScore({ score, size = 160 }: { score: number; size?: number }) {
  const r = (size / 2) * 0.75;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - score / 100);
  const color = scoreColor(score);
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1e293b" strokeWidth={14} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={14}
        strokeDasharray={circ}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: "stroke-dashoffset 0.8s ease" }}
      />
      <text
        x="50%"
        y="50%"
        textAnchor="middle"
        dominantBaseline="central"
        style={{
          fontSize: size * 0.2,
          fontWeight: 700,
          fill: color,
          transform: "rotate(90deg)",
          transformOrigin: "center",
        }}
      >
        {score}
      </text>
    </svg>
  );
}

// ── Collapsible Section ───────────────────────────────────────────────────────
function Section({
  title,
  icon,
  score,
  children,
  defaultOpen = false,
}: {
  title: string;
  icon: React.ReactNode;
  score?: number;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const color = score !== undefined ? scoreColor(score) : "#64748b";
  return (
    <div
      style={{
        background: "#0f172a",
        border: "1px solid #1e293b",
        borderRadius: 16,
        overflow: "hidden",
        marginBottom: 16,
      }}
    >
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "18px 22px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: "#e2e8f0",
          textAlign: "left",
        }}
      >
        <span style={{ color: "#60a5fa" }}>{icon}</span>
        <span style={{ flex: 1, fontWeight: 600, fontSize: 15 }}>{title}</span>
        {score !== undefined && (
          <span
            style={{
              fontSize: 13,
              fontWeight: 700,
              color,
              background: scoreBg(score),
              padding: "2px 10px",
              borderRadius: 99,
              marginRight: 8,
            }}
          >
            {score}/100
          </span>
        )}
        {open ? <ChevronUp size={18} color="#64748b" /> : <ChevronDown size={18} color="#64748b" />}
      </button>
      {open && (
        <div style={{ padding: "0 22px 22px", borderTop: "1px solid #1e293b" }}>
          {children}
        </div>
      )}
    </div>
  );
}

// ── Tag ───────────────────────────────────────────────────────────────────────
function Tag({ text, variant }: { text: string; variant: "green" | "red" | "yellow" | "blue" }) {
  const colors: Record<string, { bg: string; color: string }> = {
    green: { bg: "rgba(34,197,94,0.15)", color: "#22c55e" },
    red: { bg: "rgba(239,68,68,0.15)", color: "#ef4444" },
    yellow: { bg: "rgba(234,179,8,0.15)", color: "#eab308" },
    blue: { bg: "rgba(96,165,250,0.15)", color: "#60a5fa" },
  };
  const { bg, color } = colors[variant];
  return (
    <span
      style={{
        display: "inline-block",
        background: bg,
        color,
        borderRadius: 99,
        padding: "3px 10px",
        fontSize: 12,
        fontWeight: 600,
        margin: "3px 4px",
      }}
    >
      {text}
    </span>
  );
}

// ── Suggestion Box ────────────────────────────────────────────────────────────
function SuggestionBox({ items }: { items: string[] }) {
  if (!items.length) return null;
  return (
    <div style={{ marginTop: 14 }}>
      {items.map((s, i) => (
        <div
          key={i}
          style={{
            display: "flex",
            gap: 10,
            padding: "10px 14px",
            background: "rgba(234,179,8,0.08)",
            borderLeft: "3px solid #eab308",
            borderRadius: "0 8px 8px 0",
            marginBottom: 8,
            fontSize: 13,
            color: "#cbd5e1",
            lineHeight: 1.6,
          }}
        >
          <AlertCircle size={16} color="#eab308" style={{ flexShrink: 0, marginTop: 2 }} />
          <span>{s}</span>
        </div>
      ))}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
function ATSChecker() {
  const parsePdf = useServerFn(parsePdfFn);

  const [file, setFile] = useState<File | null>(null);
  const [jobDesc, setJobDesc] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [cv, setCv] = useState<ParsedCV | null>(null);
  const [report, setReport] = useState<ATSReport | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File) => {
    if (!f.name.endsWith(".pdf") && !f.name.endsWith(".docx")) {
      setError("Hanya mendukung file .pdf dan .docx");
      return;
    }
    setFile(f);
    setError("");
    setReport(null);
    setCv(null);
  }, []);

  const analyze = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      // Gunakan parser bersih dari cv-parser.ts (me-lempar parsePdf function dari TanStack Start)
      const { parseCV } = await import("@/lib/cv-parser");
      const parsedCV = await parseCV(file, parsePdf);

      const atsReport = runATSAnalysis(parsedCV, jobDesc);
      setCv(parsedCV);
      setReport(atsReport);
    } catch (e: any) {
      setError(e.message || "Terjadi kesalahan saat memproses CV.");
    } finally {
      setLoading(false);
    }
  };

  const printReport = () => window.print();

  // ── Upload zone ──────────────────────────────────────────────────────────
  const uploadZone = (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const f = e.dataTransfer.files[0];
        if (f) handleFile(f);
      }}
      onClick={() => inputRef.current?.click()}
      style={{
        border: `2px dashed ${dragOver ? "#60a5fa" : file ? "#22c55e" : "#334155"}`,
        borderRadius: 16,
        padding: "48px 32px",
        textAlign: "center",
        cursor: "pointer",
        background: dragOver ? "rgba(96,165,250,0.06)" : file ? "rgba(34,197,94,0.05)" : "#0f172a",
        transition: "all 0.2s ease",
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        style={{ display: "none" }}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
      />
      {file ? (
        <>
          <FileText size={48} color="#22c55e" style={{ margin: "0 auto 12px" }} />
          <p style={{ color: "#22c55e", fontWeight: 600, fontSize: 16 }}>{file.name}</p>
          <p style={{ color: "#64748b", fontSize: 13, marginTop: 4 }}>
            Klik untuk ganti file
          </p>
        </>
      ) : (
        <>
          <Upload size={48} color="#334155" style={{ margin: "0 auto 12px" }} />
          <p style={{ color: "#94a3b8", fontWeight: 600, fontSize: 16 }}>
            Seret CV ke sini atau klik untuk unggah
          </p>
          <p style={{ color: "#475569", fontSize: 13, marginTop: 6 }}>
            Mendukung .PDF dan .DOCX • Maks. 10 MB
          </p>
        </>
      )}
    </div>
  );

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #020617 0%, #0a0a1a 60%, #0f172a 100%)",
        color: "#e2e8f0",
        fontFamily: "'Inter', 'Segoe UI', sans-serif",
        padding: "0 0 80px",
      }}
    >
      {/* ── Header ── */}
      <div
        style={{
          background: "rgba(15,23,42,0.9)",
          borderBottom: "1px solid #1e293b",
          backdropFilter: "blur(12px)",
          position: "sticky",
          top: 0,
          zIndex: 100,
          padding: "0 24px",
        }}
      >
        <div style={{ maxWidth: 900, margin: "0 auto", display: "flex", alignItems: "center", height: 64, gap: 12 }}>
          <div style={{ background: "linear-gradient(135deg, #3b82f6, #06b6d4)", borderRadius: 10, padding: 8 }}>
            <BarChart3 size={22} color="white" />
          </div>
          <span style={{ fontWeight: 700, fontSize: 18, letterSpacing: "-0.3px" }}>CV ATS Checker</span>
          <span style={{ marginLeft: 4, fontSize: 12, background: "rgba(96,165,250,0.15)", color: "#60a5fa", padding: "2px 10px", borderRadius: 99, fontWeight: 600 }}>
            Beta
          </span>
          <a href="/" style={{ marginLeft: "auto", color: "#64748b", fontSize: 13, textDecoration: "none" }}>
            ← Kembali ke Beranda
          </a>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "40px 24px 0" }}>

        {/* ── Hero ── */}
        {!report && (
          <div style={{ textAlign: "center", marginBottom: 40 }}>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                background: "rgba(96,165,250,0.1)",
                border: "1px solid rgba(96,165,250,0.2)",
                borderRadius: 99,
                padding: "6px 16px",
                fontSize: 13,
                color: "#60a5fa",
                marginBottom: 20,
                fontWeight: 600,
              }}
            >
              <Zap size={14} /> Analisis CV Instan — Gratis
            </div>
            <h1
              style={{
                fontSize: "clamp(28px, 5vw, 48px)",
                fontWeight: 800,
                letterSpacing: "-1px",
                margin: "0 0 16px",
                lineHeight: 1.15,
                background: "linear-gradient(135deg, #e2e8f0 30%, #60a5fa 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Seberapa Siap CV Kamu<br />Lolos Filter ATS?
            </h1>
            <p style={{ color: "#64748b", fontSize: 16, maxWidth: 520, margin: "0 auto" }}>
              Upload CV (.pdf/.docx), tempelkan deskripsi pekerjaan, dan dapatkan skor ATS lengkap dalam hitungan detik.
            </p>
          </div>
        )}

        {/* ── Input Panel ── */}
        {!report && (
          <div
            style={{
              background: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: 20,
              padding: 28,
              marginBottom: 24,
            }}
          >
            {uploadZone}
            <div style={{ marginTop: 24 }}>
              <label style={{ display: "block", fontWeight: 600, fontSize: 14, marginBottom: 8, color: "#94a3b8" }}>
                Deskripsi Pekerjaan (opsional, untuk analisis keyword)
              </label>
              <textarea
                value={jobDesc}
                onChange={(e) => setJobDesc(e.target.value)}
                placeholder="Tempelkan deskripsi pekerjaan di sini untuk mendapatkan analisis keyword yang akurat..."
                style={{
                  width: "100%",
                  minHeight: 160,
                  background: "#020617",
                  border: "1px solid #1e293b",
                  borderRadius: 12,
                  padding: 16,
                  color: "#e2e8f0",
                  fontSize: 14,
                  fontFamily: "inherit",
                  resize: "vertical",
                  outline: "none",
                  lineHeight: 1.6,
                  boxSizing: "border-box",
                }}
              />
            </div>

            {error && (
              <div
                style={{
                  marginTop: 12,
                  padding: "12px 16px",
                  background: "rgba(239,68,68,0.1)",
                  border: "1px solid rgba(239,68,68,0.3)",
                  borderRadius: 10,
                  color: "#ef4444",
                  fontSize: 14,
                  display: "flex",
                  gap: 8,
                  alignItems: "center",
                }}
              >
                <XCircle size={16} /> {error}
              </div>
            )}

            <button
              onClick={analyze}
              disabled={!file || loading}
              style={{
                marginTop: 20,
                width: "100%",
                padding: "16px 0",
                background:
                  !file || loading
                    ? "#1e293b"
                    : "linear-gradient(135deg, #3b82f6, #06b6d4)",
                color: !file || loading ? "#475569" : "white",
                border: "none",
                borderRadius: 12,
                fontWeight: 700,
                fontSize: 16,
                cursor: !file || loading ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 10,
                transition: "all 0.2s",
              }}
            >
              {loading ? (
                <>
                  <Loader2 size={20} className="animate-spin" style={{ animation: "spin 1s linear infinite" }} />
                  Menganalisis CV...
                </>
              ) : (
                <>
                  <Target size={20} /> Analisis Sekarang
                </>
              )}
            </button>
          </div>
        )}

        {/* ── Results Dashboard ── */}
        {report && cv && (
          <>
            {/* Overall Score Hero */}
            <div
              style={{
                background: "linear-gradient(135deg, #0f172a, #1e293b)",
                border: `1px solid ${scoreColor(report.overallScore)}40`,
                borderRadius: 24,
                padding: "36px 28px",
                marginBottom: 24,
                display: "flex",
                alignItems: "center",
                gap: 32,
                flexWrap: "wrap",
              }}
            >
              <RadialScore score={report.overallScore} size={150} />
              <div style={{ flex: 1, minWidth: 220 }}>
                <p style={{ color: "#64748b", fontSize: 13, marginBottom: 4 }}>Skor ATS Keseluruhan</p>
                <h2
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    margin: "0 0 6px",
                    color: scoreColor(report.overallScore),
                  }}
                >
                  {scoreLabel(report.overallScore)}
                </h2>
                <p style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.6 }}>
                  Skor dihitung dari: Format (30%) + Keyword (50%) + Kuantifikasi (20%)
                </p>
                <div style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap" }}>
                  <Tag text={`Format: ${report.formattingScore.score}`} variant={report.formattingScore.score >= 76 ? "green" : report.formattingScore.score >= 50 ? "yellow" : "red"} />
                  <Tag text={`Keyword: ${report.keywordScore.score}`} variant={report.keywordScore.score >= 76 ? "green" : report.keywordScore.score >= 50 ? "yellow" : "red"} />
                  <Tag text={`Kuantifikasi: ${report.quantification.score}`} variant={report.quantification.score >= 76 ? "green" : report.quantification.score >= 50 ? "yellow" : "red"} />
                </div>
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <button
                  onClick={() => { setReport(null); setCv(null); setFile(null); }}
                  style={{
                    padding: "10px 18px",
                    background: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: 10,
                    color: "#94a3b8",
                    cursor: "pointer",
                    fontSize: 14,
                    fontWeight: 600,
                  }}
                >
                  Analisis Ulang
                </button>
                <button
                  onClick={printReport}
                  style={{
                    padding: "10px 18px",
                    background: "linear-gradient(135deg, #3b82f6, #06b6d4)",
                    border: "none",
                    borderRadius: 10,
                    color: "white",
                    cursor: "pointer",
                    fontSize: 14,
                    fontWeight: 600,
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <Download size={16} /> Unduh Laporan
                </button>
              </div>
            </div>

            {/* Formatting Score */}
            <Section title="Format & Struktur CV" icon={<FileText size={18} />} score={report.formattingScore.score} defaultOpen>
              <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {Object.entries(report.formattingScore.details).map(([key, val]) => {
                  const labels: Record<string, string> = {
                    singleColumn: "Layout Satu Kolom",
                    standardHeaders: "Heading Section Standar",
                    contactDetected: "Kontak Terdeteksi",
                    reasonableLength: `Panjang Ideal (${cv.wordCount} kata)`,
                    noArtifacts: "Bebas Artefak Tabel/Grafis",
                  };
                  return (
                    <div
                      key={key}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        padding: "10px 14px",
                        background: val ? "rgba(34,197,94,0.06)" : "rgba(239,68,68,0.06)",
                        border: `1px solid ${val ? "rgba(34,197,94,0.2)" : "rgba(239,68,68,0.2)"}`,
                        borderRadius: 10,
                        fontSize: 13,
                        color: "#cbd5e1",
                      }}
                    >
                      {val ? <CheckCircle size={16} color="#22c55e" /> : <XCircle size={16} color="#ef4444" />}
                      {labels[key] || key}
                    </div>
                  );
                })}
              </div>
              <SuggestionBox items={report.formattingScore.suggestions} />
            </Section>

            {/* Keyword Score */}
            <Section title="Kesesuaian Kata Kunci" icon={<Hash size={18} />} score={report.keywordScore.score}>
              {!jobDesc.trim() ? (
                <p style={{ color: "#64748b", fontSize: 14, marginTop: 14 }}>
                  ℹ️ Tempelkan deskripsi pekerjaan untuk mendapatkan analisis keyword yang lengkap.
                </p>
              ) : (
                <>
                  <div style={{ marginTop: 16 }}>
                    <p style={{ color: "#22c55e", fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
                      ✅ Ditemukan di CV ({report.keywordScore.matched.length} keyword)
                    </p>
                    <div>{report.keywordScore.matched.map((k) => <Tag key={k} text={k} variant="green" />)}</div>
                  </div>
                  {report.keywordScore.missing.length > 0 && (
                    <div style={{ marginTop: 16 }}>
                      <p style={{ color: "#ef4444", fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
                        ❌ Tidak ditemukan di CV ({report.keywordScore.missing.length} keyword)
                      </p>
                      <div>{report.keywordScore.missing.map((k) => <Tag key={k} text={k} variant="red" />)}</div>
                    </div>
                  )}
                </>
              )}
              <SuggestionBox items={report.keywordScore.suggestions} />
            </Section>

            {/* Career Gaps */}
            <Section title="Deteksi Jeda Karir" icon={<Calendar size={18} />}>
              <div style={{ marginTop: 16 }}>
                {report.careerGaps.length === 0 ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#22c55e", fontSize: 14 }}>
                    <CheckCircle size={18} /> Tidak ditemukan jeda karir lebih dari 3 bulan — bagus!
                  </div>
                ) : (
                  <>
                    <p style={{ color: "#ef4444", fontSize: 13, marginBottom: 12 }}>
                      Ditemukan {report.careerGaps.length} jeda karir &gt;3 bulan:
                    </p>
                    {report.careerGaps.map((g, i) => (
                      <div
                        key={i}
                        style={{
                          display: "flex",
                          gap: 12,
                          padding: "12px 16px",
                          background: "rgba(239,68,68,0.07)",
                          border: "1px solid rgba(239,68,68,0.2)",
                          borderRadius: 10,
                          marginBottom: 8,
                          fontSize: 13,
                          color: "#cbd5e1",
                        }}
                      >
                        <Calendar size={16} color="#ef4444" style={{ flexShrink: 0, marginTop: 1 }} />
                        <span>
                          <strong>{g.from}</strong> — <strong>{g.to}</strong> &nbsp;
                          <span style={{ color: "#ef4444" }}>({g.months} bulan)</span>
                        </span>
                      </div>
                    ))}
                    <SuggestionBox items={["Tambahkan penjelasan singkat untuk setiap jeda karir (freelance, kursus, keluarga, dll.) agar tidak terlihat mencurigakan oleh rekruter."]} />
                  </>
                )}
              </div>
            </Section>

            {/* Quantification */}
            <Section title="Kuantifikasi Pencapaian" icon={<BarChart3 size={18} />} score={report.quantification.score}>
              <p style={{ fontSize: 13, color: "#64748b", marginTop: 14 }}>
                {report.quantification.totalBullets} poin pekerjaan terdeteksi — {report.quantification.strongBullets.length} mengandung angka/metrik.
              </p>
              {report.quantification.weakBullets.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <p style={{ color: "#eab308", fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
                    ⚠️ Poin Lemah (belum ada metrik terukur):
                  </p>
                  {report.quantification.weakBullets.map((b, i) => (
                    <div
                      key={i}
                      style={{
                        padding: "10px 14px",
                        background: "rgba(234,179,8,0.07)",
                        border: "1px solid rgba(234,179,8,0.2)",
                        borderRadius: 8,
                        marginBottom: 6,
                        fontSize: 13,
                        color: "#cbd5e1",
                        lineHeight: 1.5,
                      }}
                    >
                      {b}
                    </div>
                  ))}
                  <SuggestionBox items={["Ubah poin lemah di atas dengan menambahkan angka konkret. Contoh: 'Meningkatkan penjualan 35%' atau 'Mengelola tim 12 orang'."]} />
                </div>
              )}
              {report.quantification.strongBullets.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <p style={{ color: "#22c55e", fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
                    ✅ Poin Kuat (sudah ada metrik):
                  </p>
                  {report.quantification.strongBullets.map((b, i) => (
                    <div
                      key={i}
                      style={{
                        padding: "10px 14px",
                        background: "rgba(34,197,94,0.07)",
                        border: "1px solid rgba(34,197,94,0.2)",
                        borderRadius: 8,
                        marginBottom: 6,
                        fontSize: 13,
                        color: "#cbd5e1",
                        lineHeight: 1.5,
                      }}
                    >
                      {b}
                    </div>
                  ))}
                </div>
              )}
            </Section>
          </>
        )}
      </div>

      {/* Print styles */}
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @media print {
          body { background: white !important; color: black !important; }
          button { display: none !important; }
          a[href="/""] { display: none !important; }
        }
      `}</style>
    </div>
  );
}
