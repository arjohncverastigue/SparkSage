"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { PlusCircle, Loader2, Trash } from "lucide-react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api"; // Assuming api.ts will be updated to include channel prompt calls
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from "@/components/ui/dialog";

// Interface for Channel Prompt data
interface ChannelPromptResponse {
  channel_id: string;
  guild_id: string;
  system_prompt: string;
  channel_name?: string; // Optional: To store the resolved channel name
}

export default function ChannelPromptManagementPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const { toast } = useToast();

  const [channelPrompts, setChannelPrompts] = useState<ChannelPromptResponse[]>([]);
  const [resolvedChannelNames, setResolvedChannelNames] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [newChannelId, setNewChannelId] = useState("");
  const [newSystemPrompt, setNewSystemPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // TODO: Implement proper guild selection. For now, hardcode or assume a default.
  // This needs to be dynamic based on the connected bot's guilds.
  const GUILD_ID = "YOUR_GUILD_ID_HERE"; // Placeholder

  const token = (session as { accessToken?: string })?.accessToken;

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const fetchAllData = async () => {
      try {
        setLoading(true);
        const promptsResponse = await api.listChannelPrompts(token);
        setChannelPrompts(promptsResponse.channel_prompts);

        const uniqueChannelIds = [
          ...new Set(promptsResponse.channel_prompts.map((p) => p.channel_id)),
        ];
        if (uniqueChannelIds.length > 0) {
          const namesResponse = await api.resolveChannels(token, uniqueChannelIds);
          setResolvedChannelNames(namesResponse.resolved_names);
        }
      } catch (err) {
        setError("Failed to fetch channel prompts or resolve channel names.");
        console.error("Failed to fetch data:", err);
        toast({
          title: "Error",
          description: "Failed to fetch channel prompts or resolve channel names.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
  }, [token, toast]);

  const handleAddChannelPrompt = async () => {
    if (!token || !GUILD_ID || !newChannelId || !newSystemPrompt) {
      toast({
        title: "Error",
        description: "Please fill in all fields for the new channel prompt.",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      const newPrompt = {
        channel_id: newChannelId,
        guild_id: GUILD_ID, // Use the placeholder GUILD_ID
        system_prompt: newSystemPrompt,
      };
      await api.createChannelPrompt(token, newPrompt);
      setChannelPrompts((prev) => [...prev, newPrompt]); // Add to local state
      setNewChannelId("");
      setNewSystemPrompt("");
      toast({
        title: "Success",
        description: "Channel prompt added successfully!",
      });
    } catch (err) {
      setError("Failed to add channel prompt.");
      console.error("Failed to add channel prompt:", err);
      toast({
        title: "Error",
        description: "Failed to add channel prompt.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteChannelPrompt = async (channelId: string) => {
    if (!token) {
      toast({
        title: "Error",
        description: "Authentication token is missing.",
        variant: "destructive",
      });
      return;
    }

    if (!confirm("Are you sure you want to delete this channel prompt?")) {
      return;
    }

    try {
      await api.deleteChannelPrompt(token, channelId);
      setChannelPrompts((prev) => prev.filter((prompt) => prompt.channel_id !== channelId));
      toast({
        title: "Success",
        description: "Channel prompt deleted successfully!",
      });
    } catch (err) {
      setError("Failed to delete channel prompt.");
      console.error("Failed to delete channel prompt:", err);
      toast({
        title: "Error",
        description: "Failed to delete channel prompt.",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error) {
    return <p className="text-red-500">{error}</p>;
  }

  if (!token) {
    return <p>Please log in to manage channel prompts.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Channel Prompt Management</h2>
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" /> Add New Channel Prompt
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Add New Channel Prompt</DialogTitle>
              <DialogDescription>
                Set a custom system prompt for a specific channel.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="channel-id" className="text-right">
                  Channel ID
                </Label>
                <Input
                  id="channel-id"
                  value={newChannelId}
                  onChange={(e) => setNewChannelId(e.target.value)}
                  className="col-span-3"
                  placeholder="e.g., 123456789012345678"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="system-prompt" className="text-right">
                  System Prompt
                </Label>
                <Textarea
                  id="system-prompt"
                  value={newSystemPrompt}
                  onChange={(e) => setNewSystemPrompt(e.target.value)}
                  className="col-span-3"
                  rows={5}
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleAddChannelPrompt} disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Add Channel Prompt
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Existing Channel Prompts</CardTitle>
          <CardDescription>
            Manage custom AI system prompts for individual channels.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px]">Channel Name</TableHead>
                <TableHead>System Prompt</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {channelPrompts.map((prompt) => (
                <TableRow key={prompt.channel_id}>
                  <TableCell className="font-medium">
                    {resolvedChannelNames[prompt.channel_id] || prompt.channel_id}
                  </TableCell>
                  <TableCell>{prompt.system_prompt.length > 70 ? `${prompt.system_prompt.slice(0, 70)}...` : prompt.system_prompt}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeleteChannelPrompt(prompt.channel_id)}
                    >
                      <Trash className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}