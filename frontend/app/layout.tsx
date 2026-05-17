import type { Metadata } from "next";

import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "JobTracker",
  description: "Internal job tracking & assignment platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Apply theme before paint to avoid flash */}
        <script
          dangerouslySetInnerHTML={{
            __html: `try{var t=localStorage.getItem('theme');var d=t?t==='dark':matchMedia('(prefers-color-scheme:dark)').matches;document.documentElement.classList.toggle('dark',d);}catch(e){}`,
          }}
        />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
