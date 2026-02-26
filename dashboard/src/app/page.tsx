"use client";

import { useEffect } from "react";
import { SessionProvider, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";

function RootRedirect() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "loading") return;
    if (!session) {
      router.replace("/login");
      return;
    }

    const token = (session as { accessToken?: string })?.accessToken;
    if (!token) {
      router.replace("/login");
      return;
    }

    api
      .getWizardStatus(token)
      .then((wizardStatus) => {
        if (!wizardStatus.completed) {
          router.replace("/wizard");
        } else {
          router.replace("/dashboard");
        }
      })
      .catch(() => {
        // If API is down, go to dashboard anyway
        router.replace("/dashboard");
      });
  }, [session, status, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  );
}

export default function RootPage() {
  return (
    <SessionProvider>
      <RootRedirect />
    </SessionProvider>
  );
}
