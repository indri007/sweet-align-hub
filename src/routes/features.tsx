import { createFileRoute } from "@tanstack/react-router";
import { PageShell, Features, HowItWorks } from "./index";

export const Route = createFileRoute("/features")({
  head: () => ({
    meta: [
      { title: "Features — JobMatch AI" },
      { name: "description", content: "Semua fitur JobMatch AI: ATS Score Check, Smart CV Builder, AI Mock Interview, dan Skill Gap Analysis." },
      { property: "og:title", content: "Features — JobMatch AI" },
      { property: "og:description", content: "Semua fitur JobMatch AI untuk lolos ATS dan dapetin interview." },
    ],
  }),
  component: FeaturesPage,
});

function FeaturesPage() {
  return (
    <PageShell>
      <Features />
      <HowItWorks />
    </PageShell>
  );
}
