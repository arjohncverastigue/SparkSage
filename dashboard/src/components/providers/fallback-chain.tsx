"use client";

import { ArrowRight } from "lucide-react";
import type { ProviderItem } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface FallbackChainProps {
  fallbackOrder: string[];
  providers: ProviderItem[];
}

export function FallbackChain({ fallbackOrder, providers }: FallbackChainProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {fallbackOrder.map((name, i) => {
        const prov = providers.find((p) => p.name === name);
        return (
          <div key={name} className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5">
              <div
                className={`h-2 w-2 rounded-full ${
                  prov?.configured ? "bg-green-500" : "bg-gray-300"
                }`}
              />
              <span className="text-sm">{prov?.display_name || name}</span>
              {prov?.is_primary && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  Primary
                </Badge>
              )}
            </div>
            {i < fallbackOrder.length - 1 && (
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        );
      })}
    </div>
  );
}
