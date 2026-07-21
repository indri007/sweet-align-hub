import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          This page didn't load
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Something went wrong on our end. You can try refreshing or head back home.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Try again
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Go home
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Cek Skor ATS CV Gratis - JobMatch AI" },
      { name: "description", content: "Tingkatkan peluang lolos seleksi kerja dengan JobMatch AI. Analisis skor ATS CV Anda, optimalkan format, dan temukan kecocokan profil secara akurat." },
      { name: "author", content: "JobMatch AI" },
      { name: "robots", content: "index, follow" },
      { property: "og:title", content: "Cek Skor ATS CV Gratis - JobMatch AI" },
      { property: "og:description", content: "Tingkatkan peluang lolos seleksi kerja dengan JobMatch AI. Analisis skor ATS CV Anda, optimalkan format, dan temukan kecocokan profil secara akurat." },
      { property: "og:type", content: "website" },
      { property: "og:image", content: "https://cv-coach-id.lovable.app/hero.png" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:title", content: "Cek Skor ATS CV Gratis - JobMatch AI" },
      { name: "twitter:description", content: "Tingkatkan peluang lolos seleksi kerja dengan JobMatch AI. Analisis skor ATS CV Anda, optimalkan format, dan temukan kecocokan profil secara akurat." },
      { name: "twitter:image", content: "https://cv-coach-id.lovable.app/hero.png" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
      { rel: "canonical", href: "https://cv-coach-id.lovable.app/" },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Merriweather:wght@400;700&display=swap" },
    ],
    scripts: [
      {
        type: "application/ld+json",
        children: JSON.stringify({
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "SoftwareApplication",
              name: "JobMatch AI",
              applicationCategory: "BusinessApplication",
              operatingSystem: "Web",
              description: "AI-powered CV analyzer untuk job seekers Indonesia. Cek ATS score, rapikan CV, dan latihan mock interview bareng AI.",
              offers: { "@type": "Offer", price: "0", priceCurrency: "IDR" },
              aggregateRating: {
                "@type": "AggregateRating",
                ratingValue: "4.9",
                ratingCount: "1284"
              }
            },
            {
              "@type": "WebSite",
              name: "JobMatch AI",
              url: "https://cv-coach-id.lovable.app",
              potentialAction: {
                "@type": "SearchAction",
                target: "https://cv-coach-id.lovable.app/?q={search_term_string}",
                "query-input": "required name=search_term_string",
              },
            }
          ],
        }),
      },
    ],

  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      {/* Required: nested routes render here. Removing <Outlet /> breaks all child routes. */}
      <Outlet />
    </QueryClientProvider>
  );
}
