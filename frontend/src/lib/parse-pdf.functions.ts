import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

/**
 * parse-pdf.functions.ts
 * Server-side PDF text extraction using pdf-parse.
 * Called from the client via useServerFn hook.
 */

export const parsePdfFn = createServerFn({ method: "POST" })
  .validator(z.object({ base64: z.string(), filename: z.string() }))
  .handler(async ({ data }) => {
    // Dynamically import pdf-parse (server-only)
    const pdfParse = (await import("pdf-parse")).default;
    const buffer = Buffer.from(data.base64, "base64");
    const result = await pdfParse(buffer);
    return { text: result.text };
  });
