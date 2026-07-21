import { jsPDF } from "jspdf";

type MatchData = {
  jobTitle: string;
  score: number;
  matched: string[];
  missing: string[];
  subScores: { skills: number; experience: number; cultureFit: number };
};

export function downloadMatchPdf(d: MatchData) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const margin = 48;
  let y = margin;

  const status =
    d.score >= 80 ? "Strong Match" : d.score >= 60 ? "Good Match" : "Needs Work";

  // Header
  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.setTextColor(15, 23, 42);
  doc.text("JobMatch AI — CV x Job Match Report", margin, y);
  y += 18;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(100, 116, 139);
  doc.text(
    `Target Role: ${d.jobTitle}   |   Generated: ${new Date().toLocaleString()}`,
    margin,
    y
  );
  y += 20;

  // Divider
  doc.setDrawColor(226, 232, 240);
  doc.line(margin, y, pageW - margin, y);
  y += 22;

  // Score block
  doc.setFillColor(52, 168, 83);
  doc.roundedRect(margin, y, 90, 60, 8, 8, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(26);
  doc.text(`${d.score}`, margin + 45, y + 32, { align: "center" });
  doc.setFontSize(8);
  doc.text("MATCH %", margin + 45, y + 48, { align: "center" });

  doc.setTextColor(15, 23, 42);
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text(`Compatibility: ${status}`, margin + 108, y + 22);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(71, 85, 105);
  doc.text(
    `CV kamu cocok untuk ${d.score}% requirement role ini.`,
    margin + 108,
    y + 40
  );
  y += 82;

  // Sub-scores
  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.setTextColor(15, 23, 42);
  doc.text("Sub-scores", margin, y);
  y += 14;
  const subs: [string, number, [number, number, number]][] = [
    ["Skills", d.subScores.skills, [66, 133, 244]],
    ["Experience", d.subScores.experience, [251, 188, 5]],
    ["Culture Fit", d.subScores.cultureFit, [52, 168, 83]],
  ];
  const cellW = (pageW - margin * 2 - 20) / 3;
  subs.forEach(([label, val, rgb], i) => {
    const x = margin + i * (cellW + 10);
    doc.setDrawColor(226, 232, 240);
    doc.setFillColor(248, 250, 252);
    doc.roundedRect(x, y, cellW, 48, 6, 6, "FD");
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(100, 116, 139);
    doc.text(label.toUpperCase(), x + 10, y + 16);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(16);
    doc.setTextColor(rgb[0], rgb[1], rgb[2]);
    doc.text(`${val}%`, x + 10, y + 36);
  });
  y += 66;

  // Keyword chips helper
  const drawChips = (
    title: string,
    items: string[],
    color: [number, number, number]
  ) => {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(color[0], color[1], color[2]);
    doc.text(title, margin, y);
    y += 12;
    let cx = margin;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    items.forEach((k) => {
      const w = doc.getTextWidth(k) + 16;
      if (cx + w > pageW - margin) {
        cx = margin;
        y += 20;
      }
      doc.setFillColor(color[0], color[1], color[2]);
      doc.setDrawColor(color[0], color[1], color[2]);
      doc.roundedRect(cx, y, w, 16, 8, 8, "F");
      doc.setTextColor(255, 255, 255);
      doc.text(k, cx + 8, y + 11);
      cx += w + 6;
    });
    y += 26;
  };

  drawChips("Matched Keywords", d.matched, [52, 168, 83]);
  drawChips("Missing / Weak Skills", d.missing, [234, 67, 53]);
  y += 6;

  // Bilingual summary
  const addSummary = (heading: string, paragraphs: string[]) => {
    if (y > pageH - 140) {
      doc.addPage();
      y = margin;
    }
    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.setTextColor(15, 23, 42);
    doc.text(heading, margin, y);
    y += 14;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.setTextColor(51, 65, 85);
    paragraphs.forEach((p) => {
      const lines = doc.splitTextToSize(p, pageW - margin * 2);
      doc.text(lines, margin, y);
      y += lines.length * 13 + 6;
    });
    y += 6;
  };

  const missingText =
    d.missing.length > 0 ? d.missing.join(", ") : "tidak ada gap besar";
  const missingTextEn =
    d.missing.length > 0 ? d.missing.join(", ") : "no major gaps";

  addSummary("Ringkasan (Bahasa Indonesia)", [
    `CV kamu punya kecocokan ${d.score}% untuk role ${d.jobTitle} — tergolong "${status}".`,
    `Kekuatan utama ada di ${d.matched.slice(0, 3).join(", ")} yang udah match sama requirement kunci role ini.`,
    `Yang perlu ditambah / diperkuat: ${missingText}. Rekomendasi: masukin keyword tersebut secara natural di bagian Experience atau Skills, dan tambahkan angka/impact biar makin ATS-friendly.`,
  ]);

  addSummary("Summary (English)", [
    `Your CV shows a ${d.score}% compatibility for the ${d.jobTitle} role — categorized as "${status}".`,
    `Top strengths: ${d.matched.slice(0, 3).join(", ")}, which align with the role's key requirements.`,
    `Areas to improve: ${missingTextEn}. Recommendation: weave these keywords naturally into your Experience or Skills section, and back them up with metrics for a stronger ATS score.`,
  ]);

  // Footer
  doc.setFont("helvetica", "italic");
  doc.setFontSize(8);
  doc.setTextColor(148, 163, 184);
  doc.text(
    "Generated by JobMatch AI — ATS-friendly report. jobmatch.ai",
    margin,
    pageH - 24
  );

  const safeTitle = d.jobTitle.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
  doc.save(`jobmatch-report-${safeTitle || "role"}.pdf`);
}
