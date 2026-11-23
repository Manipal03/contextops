import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "ContextOps | Evidence-first knowledge API",
  description: "Explainable, multi-agent knowledge intelligence for trusted documents."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
