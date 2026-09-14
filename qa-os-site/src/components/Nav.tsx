"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { navLinks, site } from "@/lib/site";

export function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname?.startsWith(href);
  };

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-bg">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-4 md:px-10">
        <Link
          href="/"
          className="font-mono-label text-[13px] tracking-[0.08em] text-ink hover:opacity-70"
        >
          {site.name}
          <span className="text-ink-muted"> / qa</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {navLinks.map((link) => {
            const active = isActive(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`border-b-[1.5px] pb-[2px] font-sans text-[14px] ${
                  active
                    ? "border-ink text-ink"
                    : "border-transparent text-ink-muted hover:text-ink"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
          <a
            href={site.parentUrl}
            className="border-b-[1.5px] border-transparent pb-[2px] font-sans text-[14px] text-ink-muted hover:text-ink"
          >
            {site.parentDomain} ↗
          </a>
        </nav>

        <button
          className="flex flex-col gap-[5px] p-2 md:hidden"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <span
            className={`h-[1.5px] w-5 bg-ink transition-transform duration-200 ${
              open ? "translate-y-[3.5px] rotate-45" : ""
            }`}
          />
          <span
            className={`h-[1.5px] w-5 bg-ink duration-200 ${
              open ? "opacity-0" : "opacity-100"
            }`}
          />
          <span
            className={`h-[1.5px] w-5 bg-ink transition-transform duration-200 ${
              open ? "-translate-y-[3.5px] -rotate-45" : ""
            }`}
          />
        </button>
      </div>

      {open && (
        <nav className="flex flex-col border-t border-line px-6 pb-6 pt-2 md:hidden">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`border-b border-line py-3 font-sans text-[16px] ${
                isActive(link.href) ? "font-medium text-ink" : "text-ink-muted"
              }`}
            >
              {link.label}
            </Link>
          ))}
          <a href={site.parentUrl} className="py-3 font-sans text-[16px] text-ink-muted">
            {site.parentDomain} ↗
          </a>
        </nav>
      )}
    </header>
  );
}
