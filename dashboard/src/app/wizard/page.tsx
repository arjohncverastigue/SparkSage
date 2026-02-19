"use client";

import { SessionProvider } from "next-auth/react";
import { WizardShell } from "@/components/wizard/wizard-shell";

export default function WizardPage() {
  return (
    <SessionProvider>
      <WizardShell />
    </SessionProvider>
  );
}
