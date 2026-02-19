"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { ProvidersResponse } from "@/lib/api";
import { ProviderCard } from "@/components/providers/provider-card";
import { FallbackChain } from "@/components/providers/fallback-chain";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

export default function ProvidersPage() {
  const { data: session } = useSession();
  const [data, setData] = useState<ProvidersResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const token = (session as { accessToken?: string })?.accessToken;

  async function load() {
    if (!token) return;
    try {
      const result = await api.getProviders(token);
      setData(result);
    } catch {
      toast.error("Failed to load providers");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [token]);

  async function handleSetPrimary(name: string) {
    if (!token) return;
    try {
      await api.setPrimaryProvider(token, name);
      toast.success(`Set ${name} as primary provider`);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to set primary");
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Providers</h1>

      {/* Fallback chain */}
      {data && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Fallback Chain</CardTitle>
          </CardHeader>
          <CardContent>
            <FallbackChain
              fallbackOrder={data.fallback_order}
              providers={data.providers}
            />
            <p className="mt-2 text-xs text-muted-foreground">
              When the primary provider fails, requests automatically fall through to the next available provider.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Provider grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data?.providers.map((provider) => (
          <ProviderCard
            key={provider.name}
            provider={provider}
            token={token!}
            onSetPrimary={handleSetPrimary}
          />
        ))}
      </div>
    </div>
  );
}
