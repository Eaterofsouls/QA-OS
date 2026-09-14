import { navLinks, site } from "@/lib/site";

export function Footer() {
  return (
    <footer className="border-t border-line bg-bg-elevated">
      <div className="mx-auto max-w-[1400px] px-6 py-14 md:px-10 md:py-16">
        <div className="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <p className="font-mono-label text-[13px] text-ink">{site.name}</p>
            <p className="mt-3 max-w-sm font-sans text-[14px] leading-relaxed text-ink-muted">
              Built by {site.author} — an independent implementation, open
              for technical collaboration.
            </p>
          </div>

          <div>
            <p className="font-mono-label text-[11px] text-ink-muted">Site</p>
            <ul className="mt-4 space-y-2">
              {navLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="font-sans text-[14px] text-ink-muted hover:opacity-70 hover:text-ink"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="font-mono-label text-[11px] text-ink-muted">Elsewhere</p>
            <ul className="mt-4 space-y-2">
              <li>
                <a
                  href={site.githubUrl}
                  className="font-sans text-[14px] text-ink-muted hover:opacity-70 hover:text-ink"
                >
                  GitHub ↗
                </a>
              </li>
              <li>
                <a
                  href={site.parentUrl}
                  className="font-sans text-[14px] text-ink-muted hover:opacity-70 hover:text-ink"
                >
                  {site.parentDomain} ↗
                </a>
              </li>
              <li>
                <a
                  href={`mailto:${site.contactEmail}`}
                  className="font-sans text-[14px] text-ink-muted hover:opacity-70 hover:text-ink"
                >
                  Contact
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 border-t border-line pt-6">
          <p className="font-mono-label text-[11px] text-ink-muted">
            No pricing. No demo bookings. No fake logos. Every claim on this
            site carries a status tag — that's the whole point.
          </p>
        </div>
      </div>
    </footer>
  );
}
