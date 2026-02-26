"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { ChannelItem } from "@/lib/api";
import { ChannelList } from "@/components/conversations/channel-list";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

export default function ConversationsPage() {
  const { data: session } = useSession();
  const [channels, setChannels] = useState<ChannelItem[]>([]);
  const [loading, setLoading] = useState(true);

  const token = (session as { accessToken?: string })?.accessToken;

  async function load() {
    if (!token) return;
    try {
      const result = await api.getConversations(token);
      setChannels(result.channels);
    } catch {
      toast.error("Failed to load conversations");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [token]);

  async function handleDelete(channelId: string) {
    if (!token) return;
    try {
      await api.deleteConversation(token, channelId);
      toast.success(`Cleared conversation for #${channelId}`);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete");
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
      <h1 className="text-2xl font-bold">Conversations</h1>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Channels</CardTitle>
        </CardHeader>
        <CardContent>
          <ChannelList channels={channels} onDelete={handleDelete} />
        </CardContent>
      </Card>
    </div>
  );
}
