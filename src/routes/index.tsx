import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { sendMatchEmail } from "@/lib/send-match-email.functions";
import { downloadMatchPdf } from "@/lib/match-pdf";
import { useEffect, useRef, useState, type ReactNode } from "react";
import heroPhoto from "@/assets/hero-jobmatch.png.asset.json";

import {
  FileText,
  Sparkles,
  MessageSquare,
  TrendingUp,
  Upload,
  BarChart3,
  Mic,
  Menu,
  X,
  Check,
  Star,
  ArrowRight,
  Zap,
  Languages,
  Download,
  Wand2,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  GraduationCap,
  Target,
  XCircle,
  Percent,
  Linkedin,
  Instagram,
  Youtube,
} from "lucide-react";

export const Route = createFileRoute("/")({
  component: Landing,
});

/* ---------- Reveal ---------- */
function Reveal({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setShown(true);
          io.disconnect();
        }
      },
      { threshold: 0.12 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div
      ref={ref}
      style={{
        opacity: shown ? 1 : 0,
        transform: shown ? "translateY(0)" : "translateY(24px)",
        transition: `opacity 0.7s ease ${delay}ms, transform 0.7s ease ${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}

/* ---------- Logo ---------- */
function Logo({ dark = false }: { dark?: boolean }) {
  return (
    <a href="#top" className="flex items-center gap-2.5">
      <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#4285F4] shadow-sm">
        <Zap className="h-5 w-5 text-white" strokeWidth={2.5} />
      </div>
      <span
        className={`font-display text-xl font-bold tracking-tight ${
          dark ? "text-white" : "text-slate-900"
        }`}
      >
        JobMatch<span className="text-[#4285F4]">AI</span>
      </span>
    </a>
  );
}

/* ---------- Navbar ---------- */
function Navbar() {
  const [open, setOpen] = useState(false);
  const links = [
    { href: "#features", label: "Features" },
    { href: "#how", label: "How it works" },
    { href: "#generate", label: "Generate CV" },
    { href: "#match", label: "Match Job" },
    { href: "#testimonials", label: "Testimonials" },
  ];
  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-100">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 lg:px-6">
        <Logo />
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
          {links.map((l) => (
            <a key={l.href} href={l.href} className="hover:text-[#4285F4] transition-colors">
              {l.label}
            </a>
          ))}
        </nav>
        <button
          className="md:hidden rounded-lg p-2 text-slate-800"
          onClick={() => setOpen((v) => !v)}
          aria-label="Menu"
        >
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>
      {open && (
        <div className="md:hidden border-t border-gray-100 bg-white px-5 py-4 space-y-3">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="block text-sm font-medium text-slate-700"
            >
              {l.label}
            </a>
          ))}
        </div>
      )}
    </header>
  );
}

/* ---------- Dashboard mockup ---------- */
function DashboardMock() {
  return (
    <div className="relative">
      <div className="absolute -inset-4 bg-gradient-to-tr from-[#4285F4] to-[#34A853] opacity-20 blur-3xl rounded-full" />
      <div className="relative bg-slate-50 rounded-3xl border border-slate-200 shadow-2xl p-6 sm:p-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex gap-1.5">
            <div className="h-3 w-3 rounded-full bg-[#EA4335]" />
            <div className="h-3 w-3 rounded-full bg-[#FBBC05]" />
            <div className="h-3 w-3 rounded-full bg-[#34A853]" />
          </div>
          <div className="px-3 py-1 bg-white rounded-full text-[10px] font-mono text-slate-400 border border-slate-200">
            jobmatch.ai/dashboard
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-6 mb-8">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex-1">
            <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
              ATS Score
            </div>
            <div className="font-display text-5xl font-bold text-slate-900">
              87<span className="text-xl text-slate-400 font-normal">/100</span>
            </div>
            <div className="mt-4 h-2 w-full bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-[#4285F4] rounded-full" style={{ width: "87%" }} />
            </div>
          </div>
          <div className="flex-[2] flex flex-col justify-center">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
              Analysis
            </div>
            <div className="text-lg font-bold text-slate-900">Product Manager Role</div>
            <div className="mt-1 inline-flex items-center gap-1.5 text-sm text-[#34A853] font-semibold">
              <Check className="h-4 w-4" /> Optimized &amp; Ready
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex justify-between text-xs font-bold mb-1 text-slate-600">
                <span>Keywords match</span>
                <span className="text-[#34A853]">92%</span>
              </div>
              <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-[#34A853] rounded-full" style={{ width: "92%" }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs font-bold mb-1 text-slate-600">
                <span>Experience</span>
                <span className="text-[#FBBC05]">78%</span>
              </div>
              <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-[#FBBC05] rounded-full" style={{ width: "78%" }} />
              </div>
            </div>
          </div>

          <div className="bg-white/70 backdrop-blur p-4 rounded-xl border border-slate-100">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-4 w-4 text-[#4285F4]" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                AI Suggestions
              </span>
            </div>
            <ul className="text-xs space-y-2 text-slate-600">
              <li className="flex items-start gap-2">
                <Check className="h-3.5 w-3.5 mt-0.5 text-[#34A853] shrink-0" strokeWidth={3} />
                Add keyword <span className="font-semibold text-slate-900">"Agile roadmap"</span> ke summary section
              </li>
              <li className="flex items-start gap-2">
                <Check className="h-3.5 w-3.5 mt-0.5 text-[#34A853] shrink-0" strokeWidth={3} />
                Kuantifikasi impact di role terakhir (e.g. grew revenue 20%)
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Hero ---------- */
function Hero() {
  return (
    <section id="top" className="relative pt-14 pb-24 lg:pt-20 lg:pb-32 overflow-hidden">
      <div className="absolute inset-0 -z-10 hero-dots opacity-30" />
      <div className="absolute -top-24 -left-24 w-96 h-96 bg-[#4285F4]/5 rounded-full blur-3xl -z-10" />
      <div className="absolute top-1/2 -right-24 w-96 h-96 bg-[#FBBC05]/5 rounded-full blur-3xl -z-10" />

      <div className="mx-auto grid max-w-7xl gap-12 px-4 sm:px-5 lg:grid-cols-2 lg:items-center lg:gap-16 lg:px-6">
        <div>
          <Reveal>
            <div className="inline-flex items-center gap-2.5 rounded-full bg-[#4285F4]/10 border border-[#4285F4]/15 px-4 py-2 mb-5 sm:mb-6">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#4285F4] opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#4285F4]" />
              </span>
              <span className="text-xs sm:text-sm font-bold text-[#1557b0] uppercase tracking-wider">
                AI-Powered · Made in Indonesia 🇮🇩
              </span>
            </div>
          </Reveal>
          <Reveal delay={80}>
            <h1 className="font-display text-3xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold leading-[1.05] tracking-tight text-slate-900">
              Your CV Ditolak Robot Sebelum Sampai ke{" "}
              <span className="text-[#4285F4]">HRD.</span>
            </h1>
          </Reveal>
          <Reveal delay={160}>
            <p className="mt-5 sm:mt-6 max-w-xl text-base sm:text-lg leading-relaxed text-slate-600">
              JobMatch AI scan CV kamu persis kayak sistem ATS yang dipakai perusahaan — instant
              scoring, actionable insights, plus AI mock interview. Try it, gratis.
            </p>
          </Reveal>
          <Reveal delay={220}>
            <div className="mt-7 sm:mt-9 flex flex-col sm:flex-row gap-3 sm:items-center">
              <button className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#4285F4] px-6 sm:px-8 py-3.5 sm:py-4 text-sm sm:text-base font-bold text-white shadow-lg shadow-[#4285F4]/25 transition-all hover:-translate-y-0.5 hover:shadow-xl hover:shadow-[#4285F4]/30">
                Get My CV Score
                <ArrowRight className="h-5 w-5" />
              </button>
            </div>
          </Reveal>
          <Reveal delay={280}>
            <div className="mt-6 flex flex-wrap items-center gap-3 sm:gap-x-6 sm:gap-y-2">
              <span className="inline-flex items-center gap-2 rounded-lg bg-[#34A853]/10 border border-[#34A853]/15 px-3 py-2 text-xs sm:text-sm font-bold text-[#1b5e32]">
                <Check className="h-4 w-4 text-[#34A853] shrink-0" /> No credit card
              </span>
              <span className="inline-flex items-center gap-2 rounded-lg bg-[#34A853]/10 border border-[#34A853]/15 px-3 py-2 text-xs sm:text-sm font-bold text-[#1b5e32]">
                <Check className="h-4 w-4 text-[#34A853] shrink-0" /> Results in 2 minutes
              </span>
            </div>
          </Reveal>
        </div>

        <Reveal delay={200}>
          <div className="relative">
            {/* Blue panel background (Google blue gradient) */}
            <div className="relative rounded-[2rem] overflow-hidden shadow-2xl bg-gradient-to-br from-[#1a73e8] via-[#4285F4] to-[#1557b0] p-4 sm:p-8 lg:p-10">
              {/* subtle dot grid */}
              <div
                className="absolute inset-0 opacity-[0.08] pointer-events-none"
                style={{
                  backgroundImage:
                    "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
                  backgroundSize: "22px 22px",
                }}
              />
              {/* accent blobs */}
              <div className="absolute -top-16 -right-16 w-64 h-64 bg-[#FBBC05]/30 rounded-full blur-3xl" />
              <div className="absolute -bottom-20 -left-16 w-72 h-72 bg-[#34A853]/25 rounded-full blur-3xl" />

              <div className="relative rounded-2xl overflow-hidden border border-white/20 shadow-xl bg-white">
                <img
                  src={heroPhoto.url}
                  alt="Job seeker reviewing CV with JobMatch AI"
                  className="w-full h-auto object-cover"
                  loading="eager"
                />
                {/* Floating live badge — kept small so it doesn't obscure the photo */}
                <div className="absolute top-3 left-3 sm:top-4 sm:left-4 flex items-center gap-2 rounded-full bg-white/95 backdrop-blur px-3 py-1.5 shadow-lg border border-white/60">
                  <span className="flex h-2.5 w-2.5 rounded-full bg-[#34A853] animate-pulse" />
                  <span className="text-[11px] sm:text-xs font-bold text-slate-800 tracking-wide uppercase">
                    ATS Scan Live
                  </span>
                </div>
              </div>

              {/* Google Sign In sits below the photo, aligned with the panel */}
              <div className="relative mt-5 sm:mt-6">
                <button
                  type="button"
                  onClick={() => {
                    const el = document.getElementById("generate");
                    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
                  }}
                  className="group inline-flex w-full items-center justify-center gap-3 rounded-xl bg-white px-5 py-3.5 text-sm sm:text-base font-bold text-slate-800 shadow-xl border border-slate-200 hover:-translate-y-0.5 hover:shadow-2xl transition-all"
                  aria-label="Sign in with Google"
                >
                  <svg className="h-5 w-5 sm:h-6 sm:w-6" viewBox="0 0 48 48" aria-hidden="true">
                    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                  </svg>
                  <span>Sign in with Google</span>
                </button>
              </div>
            </div>

          </div>

        </Reveal>
      </div>
    </section>
  );
}

/* ---------- Problem ---------- */
function Problem() {
  return (
    <section className="py-24 bg-slate-50 border-y border-slate-100">
      <div className="mx-auto max-w-4xl px-5 text-center lg:px-6">
        <Reveal>
          <span className="inline-block rounded-full bg-[#EA4335]/10 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[#EA4335]">
            Real Talk
          </span>
        </Reveal>
        <Reveal delay={80}>
          <h2 className="mt-5 font-display text-4xl md:text-5xl font-bold text-slate-900">
            75% of CVs Never Get{" "}
            <span className="text-[#4285F4]">Read by a Human</span>
          </h2>
        </Reveal>
        <Reveal delay={140}>
          <p className="mt-6 text-lg md:text-xl leading-relaxed text-slate-600">
            Most companies filter kandidat pakai ATS software sebelum HRD sempet lirik. Wrong
            format, missing keywords, struktur yang messy — bisa bikin CV kamu{" "}
            <span className="text-[#EA4335] font-semibold">auto-rejected</span>, padahal
            qualification-nya sebenernya match.
          </p>
        </Reveal>
      </div>
    </section>
  );
}

/* ---------- Features ---------- */
const FEATURES = [
  {
    icon: FileText,
    color: "#4285F4",
    bg: "bg-[#4285F4]/10",
    hover: "hover:border-[#4285F4]/30 hover:shadow-blue-500/10",
    title: "ATS Score Check",
    desc: "Upload CV, get instant compatibility score lengkap dengan breakdown dan rekomendasi improvement.",
  },
  {
    icon: Sparkles,
    color: "#FBBC05",
    bg: "bg-[#FBBC05]/10",
    hover: "hover:border-[#FBBC05]/40 hover:shadow-yellow-500/10",
    title: "Smart CV Builder",
    desc: "Scan CV lama kamu (even dari foto atau PDF berantakan) — auto-rapikan jadi format yang ATS-friendly.",
  },
  {
    icon: MessageSquare,
    color: "#34A853",
    bg: "bg-[#34A853]/10",
    hover: "hover:border-[#34A853]/30 hover:shadow-green-500/10",
    title: "AI Mock Interview",
    desc: "Practice real-time sama AI interviewer — dapet feedback on tone, delivery, sampai konten jawaban kamu.",
  },
  {
    icon: TrendingUp,
    color: "#EA4335",
    bg: "bg-[#EA4335]/10",
    hover: "hover:border-[#EA4335]/30 hover:shadow-red-500/10",
    title: "Skill Gap Analysis",
    desc: "Tau exactly skill apa yang kurang buat role incaran, plus roadmap buat level up.",
  },
];

function Features() {
  return (
    <section id="features" className="py-24 lg:py-32 bg-white">
      <div className="mx-auto max-w-7xl px-5 lg:px-6">
        <Reveal>
          <div className="text-center mb-16 lg:mb-20">
            <h2 className="font-display text-4xl md:text-5xl font-bold text-slate-900">
              Everything you need to{" "}
              <span className="text-[#4285F4]">land the interview</span>
            </h2>
            <p className="mt-4 text-slate-500 max-w-2xl mx-auto">
              Four powerful tools designed for the modern Indonesian job market.
            </p>
          </div>
        </Reveal>
        <div className="grid gap-6 md:grid-cols-2">
          {FEATURES.map((f, i) => (
            <Reveal key={f.title} delay={i * 80}>
              <div
                className={`card-lift group h-full p-8 rounded-3xl border border-slate-100 bg-white transition-all hover:shadow-xl ${f.hover}`}
              >
                <div
                  className={`grid h-14 w-14 place-items-center rounded-2xl ${f.bg} transition-transform group-hover:scale-110`}
                >
                  <f.icon className="h-7 w-7" style={{ color: f.color }} strokeWidth={2} />
                </div>
                <h3 className="mt-6 font-display text-2xl font-bold text-slate-900">{f.title}</h3>
                <p className="mt-3 text-[15px] leading-relaxed text-slate-600">{f.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---------- How it works ---------- */
const STEPS = [
  { icon: Upload, color: "#4285F4", bg: "bg-[#4285F4]/10", title: "Upload your CV", desc: "PDF atau foto — kita handle semua format." },
  { icon: BarChart3, color: "#34A853", bg: "bg-[#34A853]/10", title: "Get your ATS score", desc: "Detailed insights + rekomendasi actionable." },
  { icon: Mic, color: "#EA4335", bg: "bg-[#EA4335]/10", title: "Practice interview", desc: "Sampai kamu bener-bener interview-ready." },
];

function HowItWorks() {
  return (
    <section id="how" className="py-24 lg:py-32 bg-slate-50 border-y border-slate-100">
      <div className="mx-auto max-w-7xl px-5 lg:px-6">
        <Reveal>
          <div className="text-center mb-16">
            <span className="inline-block rounded-full bg-[#34A853]/10 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[#34A853]">
              How It Works
            </span>
            <h2 className="mt-4 font-display text-4xl md:text-5xl font-bold text-slate-900">
              3 steps, <span className="text-[#4285F4]">no ribet</span>
            </h2>
          </div>
        </Reveal>
        <div className="grid gap-8 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <Reveal key={s.title} delay={i * 100}>
              <div className="relative h-full rounded-3xl bg-white border border-slate-100 p-8 text-center card-lift hover:shadow-xl">
                <div
                  className={`relative mx-auto grid h-16 w-16 place-items-center rounded-2xl ${s.bg}`}
                >
                  <s.icon className="h-7 w-7" style={{ color: s.color }} />
                  <span
                    className="absolute -right-2 -top-2 grid h-7 w-7 place-items-center rounded-full bg-white text-xs font-black shadow ring-1 ring-slate-200"
                    style={{ color: s.color }}
                  >
                    {i + 1}
                  </span>
                </div>
                <h3 className="mt-6 font-display text-xl font-bold text-slate-900">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{s.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---------- Generate ATS-Friendly CV ---------- */
const CV_CONTENT = {
  id: {
    badge: "Generate CV · Bahasa Indonesia 🇮🇩",
    heading: "Generate CV ATS-Friendly dalam ",
    headingAccent: "sekali klik",
    desc: "Cukup upload CV lama kamu, pilih bahasa, dan biarkan AI merapikannya jadi format yang lolos sistem ATS — lengkap dengan struktur, keyword, dan tone yang sesuai role incaran.",
    inputLabel: "Role yang dituju",
    inputPlaceholder: "cth. Product Manager di startup fintech",
    button: "Generate CV Sekarang",
    download: "Download PDF",
    langSwitch: "Bahasa",
    preview: {
      name: "Rania Putri",
      title: "Product Manager",
      email: "rania.putri@email.com",
      phone: "+62 812-3456-7890",
      location: "Jakarta, Indonesia",
      summaryLabel: "Ringkasan Profesional",
      summary:
        "Product Manager dengan 4+ tahun pengalaman meluncurkan produk digital di ekosistem startup Indonesia. Terbukti meningkatkan retensi pengguna hingga 32% melalui riset pengguna dan roadmap Agile.",
      expLabel: "Pengalaman Kerja",
      expRole: "Associate Product Manager · Tokopedia",
      expPeriod: "2022 — Sekarang",
      expBullets: [
        "Memimpin roadmap fitur checkout, meningkatkan konversi 18% dalam 2 kuartal.",
        "Berkolaborasi dengan 3 squad engineering menggunakan metodologi Agile.",
      ],
      eduLabel: "Pendidikan",
      edu: "S1 Sistem Informasi · Universitas Indonesia (2018–2022)",
      skillsLabel: "Keahlian",
      skills: ["Roadmap Agile", "User Research", "SQL", "Figma", "A/B Testing"],
    },
  },
  en: {
    badge: "Generate CV · English 🇬🇧",
    heading: "Generate an ATS-Friendly CV in ",
    headingAccent: "one click",
    desc: "Just upload your old CV, pick a language, and let AI restructure it into a format that passes ATS systems — with the right structure, keywords, and tone for your target role.",
    inputLabel: "Target role",
    inputPlaceholder: "e.g. Product Manager at a fintech startup",
    button: "Generate CV Now",
    download: "Download PDF",
    langSwitch: "Language",
    preview: {
      name: "Rania Putri",
      title: "Product Manager",
      email: "rania.putri@email.com",
      phone: "+62 812-3456-7890",
      location: "Jakarta, Indonesia",
      summaryLabel: "Professional Summary",
      summary:
        "Product Manager with 4+ years of experience launching digital products across the Indonesian startup ecosystem. Proven track record of increasing user retention by 32% through user research and Agile roadmapping.",
      expLabel: "Work Experience",
      expRole: "Associate Product Manager · Tokopedia",
      expPeriod: "2022 — Present",
      expBullets: [
        "Led the checkout feature roadmap, driving an 18% conversion lift within 2 quarters.",
        "Collaborated with 3 engineering squads using Agile methodology.",
      ],
      eduLabel: "Education",
      edu: "B.Sc. Information Systems · Universitas Indonesia (2018–2022)",
      skillsLabel: "Skills",
      skills: ["Agile Roadmap", "User Research", "SQL", "Figma", "A/B Testing"],
    },
  },
} as const;

function CVGenerator() {
  const [lang, setLang] = useState<"id" | "en">("id");
  const c = CV_CONTENT[lang];
  const p = c.preview;

  return (
    <section id="generate" className="py-24 lg:py-32 bg-white">
      <div className="mx-auto max-w-7xl px-5 lg:px-6">
        <div className="grid gap-14 lg:grid-cols-2 lg:items-center lg:gap-16">
          <div>
            <Reveal>
              <span className="inline-flex items-center gap-2 rounded-full bg-[#4285F4]/10 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[#4285F4]">
                <Wand2 className="h-3.5 w-3.5" />
                {c.badge}
              </span>
            </Reveal>
            <Reveal delay={80}>
              <h2 className="mt-5 font-display text-4xl md:text-5xl font-bold text-slate-900 leading-tight">
                {c.heading}
                <span className="text-[#4285F4]">{c.headingAccent}</span>.
              </h2>
            </Reveal>
            <Reveal delay={140}>
              <p className="mt-5 text-lg leading-relaxed text-slate-600">{c.desc}</p>
            </Reveal>

            <Reveal delay={200}>
              <div className="mt-8 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 p-1">
                <Languages className="ml-3 h-4 w-4 text-slate-500" />
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 mr-1">
                  {c.langSwitch}
                </span>
                {(["id", "en"] as const).map((code) => (
                  <button
                    key={code}
                    onClick={() => setLang(code)}
                    className={`rounded-full px-4 py-1.5 text-sm font-bold transition-all ${
                      lang === code
                        ? "bg-white text-[#4285F4] shadow-sm ring-1 ring-slate-200"
                        : "text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    {code === "id" ? "🇮🇩 Bahasa" : "🇬🇧 English"}
                  </button>
                ))}
              </div>
            </Reveal>

            <Reveal delay={260}>
              <div className="mt-6 max-w-md">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  {c.inputLabel}
                </label>
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    placeholder={c.inputPlaceholder}
                    className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4285F4]/30 focus:border-[#4285F4]"
                  />
                  <button className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#4285F4] px-5 py-3 text-sm font-bold text-white shadow-lg shadow-[#4285F4]/25 transition-all hover:-translate-y-0.5 hover:shadow-xl">
                    <Sparkles className="h-4 w-4" />
                    {c.button}
                  </button>
                </div>
              </div>
            </Reveal>

            <Reveal delay={320}>
              <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-sm font-medium text-slate-500">
                <span className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#34A853]" /> ATS-optimized layout
                </span>
                <span className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#34A853]" /> ID &amp; EN keywords
                </span>
              </div>
            </Reveal>
          </div>

          <Reveal delay={200}>
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-tr from-[#4285F4] to-[#FBBC05] opacity-15 blur-3xl rounded-full" />
              <div className="relative bg-white rounded-3xl border border-slate-200 shadow-2xl overflow-hidden">
                <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100 bg-slate-50">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-[#4285F4]" />
                    <span className="text-xs font-bold text-slate-600">
                      {lang === "id" ? "CV_Rania_ATS_ID.pdf" : "CV_Rania_ATS_EN.pdf"}
                    </span>
                  </div>
                  <button className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-[11px] font-bold text-slate-700 border border-slate-200 hover:bg-slate-50">
                    <Download className="h-3 w-3" />
                    {c.download}
                  </button>
                </div>

                <div className="p-6 sm:p-8 text-slate-800">
                  <div className="pb-4 border-b border-slate-200">
                    <div className="font-display text-2xl font-bold text-slate-900">{p.name}</div>
                    <div className="text-sm font-semibold text-[#4285F4] mt-0.5">{p.title}</div>
                    <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500">
                      <span className="flex items-center gap-1"><Mail className="h-3 w-3" />{p.email}</span>
                      <span className="flex items-center gap-1"><Phone className="h-3 w-3" />{p.phone}</span>
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{p.location}</span>
                    </div>
                  </div>

                  <div className="mt-5">
                    <div className="text-[10px] font-black uppercase tracking-widest text-[#4285F4]">
                      {p.summaryLabel}
                    </div>
                    <p className="mt-1.5 text-xs leading-relaxed text-slate-600">{p.summary}</p>
                  </div>

                  <div className="mt-5">
                    <div className="text-[10px] font-black uppercase tracking-widest text-[#4285F4] flex items-center gap-1.5">
                      <Briefcase className="h-3 w-3" /> {p.expLabel}
                    </div>
                    <div className="mt-2">
                      <div className="flex justify-between text-xs">
                        <span className="font-bold text-slate-900">{p.expRole}</span>
                        <span className="text-slate-500">{p.expPeriod}</span>
                      </div>
                      <ul className="mt-1.5 space-y-1 text-xs text-slate-600">
                        {p.expBullets.map((b) => (
                          <li key={b} className="flex gap-2">
                            <span className="text-[#34A853] mt-0.5">•</span>
                            <span>{b}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="mt-5">
                    <div className="text-[10px] font-black uppercase tracking-widest text-[#4285F4] flex items-center gap-1.5">
                      <GraduationCap className="h-3 w-3" /> {p.eduLabel}
                    </div>
                    <div className="mt-1.5 text-xs text-slate-700">{p.edu}</div>
                  </div>

                  <div className="mt-5">
                    <div className="text-[10px] font-black uppercase tracking-widest text-[#4285F4]">
                      {p.skillsLabel}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {p.skills.map((s) => (
                        <span
                          key={s}
                          className="rounded-full bg-[#4285F4]/10 px-2.5 py-0.5 text-[11px] font-semibold text-[#4285F4]"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

/* ---------- CV Match Job ---------- */


function CVMatchJob() {
  const [score, setScore] = useState(82);
  const [subScores, setSubScores] = useState({ skills: 88, experience: 78, cultureFit: 84 });
  const [jobTitle, setJobTitle] = useState("Product Manager");
  
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const matched = [
    "Product Roadmap",
    "Agile / Scrum",
    "User Research",
    "SQL",
    "A/B Testing",
    "Stakeholder Mgmt",
  ];
  const missing = ["Mixpanel", "SQL Advanced", "OKR Planning"];

  const send = useServerFn(sendMatchEmail);

  async function handleSend() {
    setStatus("sending");
    setErrorMsg("");
    try {
      await send({ data: { jobTitle: jobTitle || "Target Role", score, matched, missing, subScores } });
      setStatus("sent");
    } catch (e) {
      setStatus("error");
      setErrorMsg(e instanceof Error ? e.message : "Gagal mengirim email.");
    }
  }

  function handleAnalyze() {
    setScore(Math.floor(70 + Math.random() * 26));
    setSubScores({
      skills: Math.floor(70 + Math.random() * 26),
      experience: Math.floor(65 + Math.random() * 30),
      cultureFit: Math.floor(70 + Math.random() * 26),
    });
    setStatus("idle");
  }

  return (
    <section id="match" className="py-24 lg:py-32 bg-slate-50 border-y border-slate-100">
      <div className="mx-auto max-w-7xl px-5 lg:px-6">
        <div className="grid gap-14 lg:grid-cols-2 lg:items-center lg:gap-16">
          <Reveal>
            <div className="relative order-2 lg:order-1">
              <div className="absolute -inset-4 bg-gradient-to-tr from-[#34A853] to-[#4285F4] opacity-15 blur-3xl rounded-full" />
              <div className="relative bg-white rounded-3xl border border-slate-200 shadow-2xl overflow-hidden">
                <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100 bg-slate-50">
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4 text-[#34A853]" />
                    <span className="text-xs font-bold text-slate-600">
                      CV × {jobTitle || "Target Role"}
                    </span>
                  </div>
                  <span className="rounded-full bg-[#34A853]/10 px-2.5 py-0.5 text-[10px] font-black uppercase tracking-wider text-[#34A853]">
                    Live Match
                  </span>
                </div>

                <div className="p-6 sm:p-8">
                  <div className="flex items-center gap-5">
                    <div className="relative h-24 w-24 shrink-0">
                      <svg viewBox="0 0 40 40" className="h-full w-full -rotate-90">
                        <circle cx="20" cy="20" r="16" className="fill-none stroke-slate-100" strokeWidth="4" />
                        <circle
                          cx="20"
                          cy="20"
                          r="16"
                          className="fill-none"
                          stroke="#34A853"
                          strokeWidth="4"
                          strokeLinecap="round"
                          strokeDasharray={`${(score / 100) * 100.5} 100.5`}
                          style={{ transition: "stroke-dasharray 0.6s ease" }}
                        />
                      </svg>
                      <div className="absolute inset-0 grid place-items-center">
                        <div className="text-center">
                          <div className="font-display text-2xl font-bold text-slate-900 leading-none">
                            {score}
                          </div>
                          <div className="text-[9px] font-bold text-slate-400">MATCH</div>
                        </div>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">
                        Compatibility
                      </div>
                      <div className="font-display text-lg font-bold text-slate-900">
                        {score >= 80 ? "Strong Match 🎯" : score >= 60 ? "Good Match 👍" : "Needs Work ⚡"}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        CV kamu cocok untuk {score}% requirement role ini.
                      </div>
                    </div>
                  </div>

                  <div className="mt-6">
                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#34A853]">
                      <Check className="h-3.5 w-3.5" /> Matched Keywords
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {matched.map((k) => (
                        <span
                          key={k}
                          className="inline-flex items-center gap-1 rounded-full bg-[#34A853]/10 px-2.5 py-0.5 text-[11px] font-semibold text-[#1E7A38]"
                        >
                          <Check className="h-3 w-3" /> {k}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="mt-5">
                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#EA4335]">
                      <XCircle className="h-3.5 w-3.5" /> Missing / Weak
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {missing.map((k) => (
                        <span
                          key={k}
                          className="inline-flex items-center gap-1 rounded-full bg-[#EA4335]/10 px-2.5 py-0.5 text-[11px] font-semibold text-[#B4271C]"
                        >
                          {k}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="mt-6 grid grid-cols-3 gap-3">
                    {([
                      ["Skills", subScores.skills, "#4285F4"],
                      ["Experience", subScores.experience, "#FBBC05"],
                      ["Culture Fit", subScores.cultureFit, "#34A853"],
                    ] as const).map(([l, v, c]) => (
                      <div key={l} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                          {l}
                        </div>
                        <div className="mt-1 font-display text-xl font-bold" style={{ color: c }}>
                          {v}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </Reveal>

          <div className="order-1 lg:order-2">
            <Reveal>
              <span className="inline-flex items-center gap-2 rounded-full bg-[#34A853]/10 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[#34A853]">
                <Target className="h-3.5 w-3.5" />
                CV × Job Match
              </span>
            </Reveal>
            <Reveal delay={80}>
              <h2 className="mt-5 font-display text-4xl md:text-5xl font-bold text-slate-900 leading-tight">
                Cek Seberapa <span className="text-[#34A853]">Match</span> CV Kamu sama Job Impian.
              </h2>
            </Reveal>
            <Reveal delay={140}>
              <p className="mt-5 text-lg leading-relaxed text-slate-600">
                Paste job description, AI langsung analisa fit-score, matched keywords, plus skill
                yang masih kurang — dan bisa langsung kirim ringkasan (ID + EN) ke email kamu.
              </p>
            </Reveal>

            <Reveal delay={200}>
              <div className="mt-8 space-y-3">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                  Target Role
                </label>
                <input
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  placeholder="e.g. Product Manager @ Gojek"
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#34A853]/30 focus:border-[#34A853]"
                />

                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 pt-2">
                  Paste Job Description
                </label>
                <textarea
                  rows={4}
                  placeholder="cth. We're looking for a Product Manager with 3+ years of experience in mobile products, strong analytical skills, familiarity with SQL, Mixpanel, and Agile methodology..."
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#34A853]/30 focus:border-[#34A853] resize-none"
                />

                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={handleAnalyze}
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#34A853] px-6 py-3 text-sm font-bold text-white shadow-lg shadow-[#34A853]/25 transition-all hover:-translate-y-0.5 hover:shadow-xl"
                  >
                    <Percent className="h-4 w-4" />
                    Analyze Match Score
                  </button>
                  <button
                    onClick={() =>
                      downloadMatchPdf({ jobTitle: jobTitle || "Target Role", score, matched, missing, subScores })
                    }
                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-bold text-slate-900 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md hover:border-[#4285F4]"
                  >
                    <Download className="h-4 w-4 text-[#4285F4]" />
                    Download PDF
                  </button>
                </div>
              </div>
            </Reveal>

            <Reveal delay={260}>
              <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5">
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-[#4285F4]" />
                  <div className="text-sm font-bold text-slate-900">
                    Kirim hasil analisis ke email
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Ringkasan lengkap (🇮🇩 Bahasa + 🇬🇧 English) + breakdown score dikirim ke inbox owner (ravipridh88@gmail.com).
                </p>
                <div className="mt-3 flex flex-col sm:flex-row gap-2">
                  <button
                    onClick={handleSend}
                    disabled={status === "sending"}
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#4285F4] px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-[#4285F4]/25 transition-all hover:-translate-y-0.5 disabled:opacity-60 disabled:hover:translate-y-0"
                  >
                    <Mail className="h-4 w-4" />
                    {status === "sending" ? "Mengirim..." : "Send Report to Owner Inbox"}
                  </button>
                </div>
                {status === "sent" && (
                  <div className="mt-3 flex items-center gap-2 rounded-lg bg-[#34A853]/10 px-3 py-2 text-xs font-semibold text-[#1E7A38]">
                    <Check className="h-4 w-4" /> Terkirim! Cek inbox owner (mungkin di folder Promotions).
                  </div>
                )}
                {status === "error" && (
                  <div className="mt-3 flex items-start gap-2 rounded-lg bg-[#EA4335]/10 px-3 py-2 text-xs font-semibold text-[#B4271C]">
                    <XCircle className="h-4 w-4 mt-0.5 shrink-0" /> {errorMsg}
                  </div>
                )}
              </div>
            </Reveal>

            <Reveal delay={320}>
              <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-sm font-medium text-slate-500">
                <span className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#34A853]" /> Instant fit-score
                </span>
                <span className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#34A853]" /> Bilingual email report
                </span>
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}

function Stats() {
  const items: [string, string, string][] = [
    ["10,000+", "CVs Analyzed", "#4285F4"],
    ["85%", "Pass Rate Improvement", "#34A853"],
    ["4.8/5", "User Rating", "#FBBC05"],
  ];
  return (
    <section className="py-16 lg:py-20 bg-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-5 text-center sm:grid-cols-3 lg:px-6">
        {items.map(([n, l, c], i) => (
          <Reveal key={l} delay={i * 100}>
            <div>
              <div className="font-display text-5xl font-bold tracking-tight" style={{ color: c }}>
                {n}
              </div>
              <div className="mt-2 text-sm font-semibold uppercase tracking-wider text-slate-500">
                {l}
              </div>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

/* ---------- Testimonials ---------- */
const TESTIMONIALS = [
  {
    name: "Rania Putri",
    role: "Fresh Graduate · UI Designer",
    quote:
      "CV gue di-ghost 20+ perusahaan. Setelah pakai JobMatch AI, ATS score naik dari 42 ke 89. Minggu depannya langsung 3 interview call.",
    avatar: "https://i.pravatar.cc/120?img=47",
    accent: "#4285F4",
  },
  {
    name: "Michael Santoso",
    role: "Product Manager",
    quote:
      "Mock interview-nya seriously game-changer. Feedback-nya detail sampai ke intonasi. Confidence naik banget pas interview beneran.",
    avatar: "https://i.pravatar.cc/120?img=12",
    accent: "#34A853",
  },
  {
    name: "Dinda Ayu",
    role: "Data Analyst · Ex-Big 4",
    quote:
      "Skill gap analysis-nya spot on. Tau exactly course apa yang harus gue ambil buat switch career ke data role.",
    avatar: "https://i.pravatar.cc/120?img=32",
    accent: "#EA4335",
  },
];

function Testimonials() {
  return (
    <section id="testimonials" className="py-24 lg:py-32 bg-white">
      <div className="mx-auto max-w-7xl px-5 lg:px-6">
        <Reveal>
          <div className="text-center mb-16">
            <span className="inline-block rounded-full bg-[#FBBC05]/15 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[#B58600]">
              Loved by job seekers
            </span>
            <h2 className="mt-4 font-display text-4xl md:text-5xl font-bold text-slate-900">
              Real people, <span className="text-[#4285F4]">real offers</span>
            </h2>
          </div>
        </Reveal>
        <div className="grid gap-6 md:grid-cols-3">
          {TESTIMONIALS.map((t, i) => (
            <Reveal key={t.name} delay={i * 100}>
              <div className="card-lift h-full rounded-3xl border border-slate-100 bg-white p-7 hover:shadow-xl transition-all">
                <div className="flex items-center gap-1 text-[#FBBC05]">
                  {Array.from({ length: 5 }).map((_, k) => (
                    <Star key={k} className="h-4 w-4 fill-current" />
                  ))}
                </div>
                <p className="mt-4 text-[15px] leading-relaxed text-slate-700">"{t.quote}"</p>
                <div className="mt-6 flex items-center gap-3 border-t border-slate-100 pt-4">
                  <img
                    src={t.avatar}
                    alt={t.name}
                    className="h-11 w-11 rounded-full object-cover ring-2"
                    style={{ boxShadow: `0 0 0 2px ${t.accent}` }}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-900">{t.name}</div>
                    <div className="text-xs text-slate-500">{t.role}</div>
                  </div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---------- Final CTA ---------- */
function FinalCTA() {
  return (
    <section className="py-24 px-5 lg:px-6 bg-white">
      <div className="mx-auto max-w-5xl bg-slate-900 rounded-[2rem] md:rounded-[3rem] p-10 md:p-20 text-center relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#4285F4] opacity-20 blur-[100px]" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-[#34A853] opacity-20 blur-[100px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 w-72 h-72 bg-[#FBBC05] opacity-10 blur-[100px]" />

        <Reveal>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-white relative">
            Stop Guessing Why Your CV Gets Rejected
          </h2>
        </Reveal>
        <Reveal delay={80}>
          <p className="mt-5 text-lg md:text-xl text-slate-400 relative max-w-2xl mx-auto">
            Ribuan job seekers udah pakai JobMatch AI buat pass first screening.
          </p>
        </Reveal>
        <Reveal delay={140}>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 relative">
            <button className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[#4285F4] px-8 py-4 text-base font-bold text-white shadow-lg transition-all hover:-translate-y-0.5 hover:shadow-xl">
              Start Free Now
              <ArrowRight className="h-5 w-5" />
            </button>
          </div>
        </Reveal>
        <Reveal delay={200}>
          <p className="mt-6 text-sm text-slate-500 relative">
            Start for free · No credit card required
          </p>
        </Reveal>
      </div>
    </section>
  );
}

/* ---------- Social icons ---------- */
function WhatsAppIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.751.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.134 1.588 5.945L0 24l6.335-1.652c1.746.953 3.71 1.457 5.711 1.458h.004c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z" />
    </svg>
  );
}

function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.57-1.48-3.85-4.13-3.65-6.89.15-2.05 1.21-3.96 2.84-5.21 1.41-1.08 3.17-1.58 4.91-1.54.02 1.54-.03 3.09-.02 4.63-.04.22-.13.44-.3.6-.47.45-1.25.52-1.82.24-.56-.27-.94-.83-1.02-1.44-.16-1.08.55-2.15 1.56-2.5 1.05-.36 2.27.09 2.86 1.03.31.52.41 1.14.41 1.75 0 1.99-.01 3.98.01 5.97.02 1.22-.39 2.45-1.23 3.34-.85.9-2.05 1.39-3.27 1.39-1.88 0-3.6-1.05-4.5-2.72-1.03-1.93-.88-4.32.39-6.1 1.1-1.53 2.99-2.49 4.95-2.54z" />
    </svg>
  );
}

function ThreadsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12.186 24h-.007c-3.581-.024-6.182-2.574-6.182-6.279 0-3.42 2.51-5.735 5.995-5.743 2.51-.005 4.603 1.016 5.565 2.79.533 1.031.696 2.23.696 3.57 0 .305-.011.61-.011.915v.052c-.02 2.577-1.678 4.59-4.348 5.35-.6.174-1.22.267-1.85.346zm.007-10.5c-2.552.006-4.116 1.624-4.116 4.221 0 2.548 1.55 4.279 4.04 4.279 1.963 0 3.39-1.146 3.82-3.01.12-.526.18-1.08.18-1.64 0-.37-.02-.74-.06-1.1-.32-2.93-2.43-4.73-4.86-4.74zM24 12.5c0-1.15-.09-2.27-.27-3.36-.5-3.16-2.07-5.2-4.53-5.96-.63-.19-1.29-.29-1.97-.32-.1 0-.2-.01-.3-.01h-.11c-.66 0-1.32.06-1.96.19-2.5.55-4.22 2.43-4.86 5.35-.14.64-.2 1.31-.2 2.01 0 .35.01.7.04 1.05.19 2.45 1.47 4.45 3.44 5.39.63.3 1.31.49 2.03.56.31.03.62.05.94.05.35 0 .7-.02 1.04-.07 2.64-.39 4.64-2.36 5.21-5.13.12-.57.19-1.16.19-1.76h.04zm-2.5 0c0 .38-.03.76-.1 1.13-.39 2.2-1.79 3.76-3.7 4.04-.25.04-.5.06-.76.06-.23 0-.46-.01-.68-.04-.52-.06-1.01-.2-1.46-.42-1.38-.65-2.24-2.02-2.37-3.69-.03-.36-.04-.72-.04-1.08 0-.55.05-1.08.16-1.59.44-2.07 1.88-3.46 3.84-3.72.24-.03.49-.05.74-.05.22 0 .44.01.65.04.55.07 1.07.23 1.55.49 1.33.72 2.09 2.06 2.09 3.68v.23z" />
    </svg>
  );
}

function SocialLinks() {
  const links = [
    { name: "LinkedIn", href: "#", Icon: Linkedin },
    { name: "WhatsApp", href: "#", Icon: WhatsAppIcon },
    { name: "Instagram", href: "#", Icon: Instagram },
    { name: "TikTok", href: "#", Icon: TikTokIcon },
    { name: "YouTube", href: "#", Icon: Youtube },
    { name: "Threads", href: "#", Icon: ThreadsIcon },
  ];

  return (
    <div className="flex flex-col gap-3">
      <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Follow us</span>
      <div className="flex flex-wrap items-center gap-3">
        {links.map(({ name, href, Icon }) => (
          <a
            key={name}
            href={href}
            aria-label={name}
            className="grid h-10 w-10 place-items-center rounded-full bg-slate-100 text-slate-600 transition-all hover:scale-110 hover:bg-slate-200 hover:text-[#4285F4]"
          >
            <Icon className="h-5 w-5" />
          </a>
        ))}
      </div>
    </div>
  );
}

/* ---------- Footer ---------- */
function Footer() {
  return (
    <footer className="py-14 border-t border-slate-100 bg-white">
      <div className="mx-auto max-w-7xl px-5 lg:px-6">
        <div className="flex flex-col gap-10 md:flex-row md:items-start md:justify-between">
          <div className="max-w-sm">
            <Logo />
            <p className="mt-4 text-sm leading-relaxed text-slate-500">
              JobMatch AI — Built for Indonesian job seekers yang capek CV-nya di-ghost sama sistem.
            </p>
          </div>
          <div className="flex flex-col gap-8 sm:flex-row sm:gap-16">
            <div className="flex flex-wrap gap-x-8 gap-y-3 text-sm font-medium text-slate-600 sm:flex-col sm:gap-3">
              <a href="#" className="hover:text-[#4285F4] transition-colors">Privacy Policy</a>
              <a href="#" className="hover:text-[#4285F4] transition-colors">Terms</a>
              <a href="#" className="hover:text-[#4285F4] transition-colors">Contact</a>
            </div>
            <SocialLinks />
          </div>
        </div>
        <div className="mt-10 border-t border-slate-100 pt-6 text-xs text-slate-400">
          © {new Date().getFullYear()} JobMatch AI. Proudly built in Indonesia.
        </div>
      </div>
    </footer>
  );
}

function Landing() {
  return (
    <div className="min-h-screen bg-white overflow-x-hidden">
      <Navbar />
      <main>
        <Hero />
        <Problem />
        <Features />
        <HowItWorks />
        <CVGenerator />
        <CVMatchJob />
        <Stats />
        <Testimonials />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
