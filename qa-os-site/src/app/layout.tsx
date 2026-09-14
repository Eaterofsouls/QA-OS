import type { Metadata } from "next";
import { Nav } from "@/components/Nav";
import { Footer } from "@/components/Footer";
import { PageTransition } from "@/components/PageTransition";
import "./globals.css";

export const metadata: Metadata = {
  title: "QA OS — an architecture for QA reasoning that remembers",
  description:
    "A deep, honest engineering showcase for QA OS: a persistent, retrievable reasoning layer for the QA lifecycle. Every capability claim is tagged Vision, Implemented, Partial, or Planned — no exceptions.",
  metadataBase: new URL("https://qa.buildwithdaksh.com"),
  openGraph: {
    title: "QA OS — an architecture for QA reasoning that remembers",
    description:
      "One system, in extreme depth. Real architecture, an honest capability ledger, and a dependency-aware roadmap.",
    url: "https://qa.buildwithdaksh.com",
    siteName: "QA OS",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "QA OS — an architecture for QA reasoning that remembers",
    description:
      "Real architecture, an honest capability ledger, and a dependency-aware roadmap.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link rel="preconnect" href="https://api.fontshare.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,300..600,0..100,0..1;1,9..144,300..600,0..100,0..1&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <link
          rel="stylesheet"
          href="https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600&display=swap"
        />
      </head>
      <body className="bg-bg text-ink">
        <a
          href="#main"
          className="sr-only-focusable fixed left-4 top-4 z-[100] bg-ink px-4 py-2 font-sans text-[13px] text-bg"
        >
          Skip to content
        </a>
        <Nav />
        <main id="main">
          <PageTransition>{children}</PageTransition>
        </main>
        <Footer />
      </body>
    </html>
  );
}
