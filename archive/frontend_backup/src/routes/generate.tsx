import { createFileRoute } from "@tanstack/react-router";
import { PageShell, CVGenerator } from "./index";

export const Route = createFileRoute("/generate")({
  head: () => ({
    meta: [
      { title: "Generate CV ATS-Friendly — JobMatch AI" },
      { name: "description", content: "Generate CV ATS-friendly Bahasa Indonesia atau English dalam sekali klik. Upload CV lama, pilih role, AI merapikan strukturnya." },
      { property: "og:title", content: "Generate CV ATS-Friendly — JobMatch AI" },
      { property: "og:description", content: "AI CV generator untuk pencari kerja Indonesia. Format ATS-friendly, sekali klik." },
    ],
  }),
  component: GeneratePage,
});

function GeneratePage() {
  return (
    <PageShell>
      <CVGenerator />
    </PageShell>
  );
}
