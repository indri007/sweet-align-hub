import { createFileRoute } from "@tanstack/react-router";
import { PageShell, CVMatchJob } from "./index";

export const Route = createFileRoute("/match")({
  head: () => ({
    meta: [
      { title: "Match CV × Job — JobMatch AI" },
      { name: "description", content: "Cocokkan CV kamu dengan job description. Dapatkan match score, keyword gap, dan rekomendasi improvement dari AI." },
      { property: "og:title", content: "Match CV × Job — JobMatch AI" },
      { property: "og:description", content: "Analisa kecocokan CV dengan job description via AI. Instant, actionable, gratis." },
    ],
  }),
  component: MatchPage,
});

function MatchPage() {
  return (
    <PageShell>
      <CVMatchJob />
    </PageShell>
  );
}
