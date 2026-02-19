"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { MessageItem } from "@/lib/api";
import { MessageList } from "@/components/conversations/message-list";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

export default function ConversationDetailPage() {
  const params = useParams();
  const channelId = params.channelId as string;
  const { data: session } = useSession();
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [loading, setLoading] = useState(true);

  const token = (session as { accessToken?: string })?.accessToken;

  useEffect(() => {
    if (!token || !channelId) return;
    api
      .getConversation(token, channelId)
      .then((result) => setMessages(result.messages))
      .catch(() => toast.error("Failed to load messages"))
      .finally(() => setLoading(false));
  }, [token, channelId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/dashboard/conversations">
            <ArrowLeft className="mr-1 h-4 w-4" /> Back
          </Link>
        </Button>
        <h1 className="text-2xl font-bold">Channel #{channelId}</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Messages ({messages.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <MessageList messages={messages} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
