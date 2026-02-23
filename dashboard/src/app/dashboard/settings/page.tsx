"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Save, RotateCcw } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch"; // Import Switch
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"; // Import Select components

const settingsSchema = z.object({
  DISCORD_TOKEN: z.string().min(1, "Discord token is required"),
  BOT_PREFIX: z.string().min(1).max(5),
  MAX_TOKENS: z.number().min(128).max(4096),
  SYSTEM_PROMPT: z.string().min(1),
  GEMINI_API_KEY: z.string(),
  GROQ_API_KEY: z.string(),
  OPENROUTER_API_KEY: z.string(),
  ANTHROPIC_API_KEY: z.string(),
  OPENAI_API_KEY: z.string(),
  WELCOME_CHANNEL_ID: z.string().optional(),
  WELCOME_MESSAGE: z.string().min(1, "Welcome message is required"),
  WELCOME_ENABLED: z.boolean(),
  DIGEST_CHANNEL_ID: z.string().optional(),
  DIGEST_TIME: z
    .string()
    .regex(/^([01]\d|2[0-3]):([0-5]\d)$/, "Invalid time format (HH:MM)")
    .optional(),
  DIGEST_ENABLED: z.boolean(),
  MODERATION_ENABLED: z.boolean(),
  MOD_LOG_CHANNEL_ID: z.string().optional(),
  MODERATION_SENSITIVITY: z.enum(["low", "medium", "high"]),
});

type SettingsForm = z.infer<typeof settingsSchema>;

const DEFAULTS: SettingsForm = {
  DISCORD_TOKEN: "",
  BOT_PREFIX: "!",
  MAX_TOKENS: 1024,
  SYSTEM_PROMPT:
    "You are SparkSage, a helpful and friendly AI assistant in a Discord server. Be concise, helpful, and engaging.",
  GEMINI_API_KEY: "",
  GROQ_API_KEY: "",
  OPENROUTER_API_KEY: "",
  ANTHROPIC_API_KEY: "",
  OPENAI_API_KEY: "",
  WELCOME_CHANNEL_ID: "",
  WELCOME_MESSAGE:
    "Welcome to the server, {user}! Please check out {server} rules and available channels.",
  WELCOME_ENABLED: false,
  DIGEST_CHANNEL_ID: "",
  DIGEST_TIME: "09:00",
  DIGEST_ENABLED: false,
  MODERATION_ENABLED: false,
  MOD_LOG_CHANNEL_ID: "",
  MODERATION_SENSITIVITY: "medium",
};

export default function SettingsPage() {
  const { data: session } = useSession();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const token = (session as { accessToken?: string })?.accessToken;

  const form = useForm<SettingsForm>({
    resolver: zodResolver(settingsSchema),
    defaultValues: DEFAULTS,
  });

  useEffect(() => {
    if (!token) return;
    api
      .getConfig(token)
      .then(({ config }) => {
        const mapped: Partial<SettingsForm> = {};
        for (const key of Object.keys(DEFAULTS) as (keyof SettingsForm)[]) {
          if (config[key] !== undefined) {
            if (key === "MAX_TOKENS") {
              mapped[key] = Number(config[key]);
            } else if (key === "WELCOME_ENABLED" || key === "DIGEST_ENABLED" || key === "MODERATION_ENABLED") {
                mapped[key] = config[key] === "True";
            } else {
              (mapped as Record<string, string>)[key] = config[key];
            }
          }
        }
        form.reset({ ...DEFAULTS, ...mapped });
      })
      .catch(() => toast.error("Failed to load settings"))
      .finally(() => setLoading(false));
  }, [token, form]);

  async function onSubmit(values: SettingsForm) {
    if (!token) return;
    setSaving(true);
    try {
      // Convert to string values for the API, skip masked values (***...)
      const payload: Record<string, string> = {};
      for (const [key, val] of Object.entries(values)) {
        // Special handling for boolean fields
        if (key === "WELCOME_ENABLED" || key === "DIGEST_ENABLED" || key === "MODERATION_ENABLED") {
            payload[key] = (val as boolean) ? "True" : "False";
        } else if (!String(val).startsWith("***")) { // Check for masked string values
          payload[key] = String(val);
        }
      }
      await api.updateConfig(token, payload);
      toast.success("Settings saved successfully");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    form.reset(DEFAULTS);
  }

  const maxTokens = form.watch("MAX_TOKENS");
  const systemPrompt = form.watch("SYSTEM_PROMPT");

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Settings</h1>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleReset}>
            <RotateCcw className="mr-1 h-3 w-3" /> Reset to Defaults
          </Button>
        </div>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Discord */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Discord</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="discord-token">Bot Token</Label>
              <Input
                id="discord-token"
                type="password"
                {...form.register("DISCORD_TOKEN")}
              />
              {form.formState.errors.DISCORD_TOKEN && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.DISCORD_TOKEN.message}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Bot Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Bot Behavior</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="prefix">Command Prefix</Label>
              <Input
                id="prefix"
                {...form.register("BOT_PREFIX")}
                className="w-24"
              />
              {form.formState.errors.BOT_PREFIX && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.BOT_PREFIX.message}
                </p>
              )}
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Max Tokens</Label>
                <span className="text-sm font-mono tabular-nums text-muted-foreground">
                  {maxTokens}
                </span>
              </div>
              <Slider
                value={[maxTokens]}
                onValueChange={([val]) => form.setValue("MAX_TOKENS", val)}
                min={128}
                max={4096}
                step={64}
              />
            </div>

            <Separator />

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="system-prompt">System Prompt</Label>
                <span className="text-xs text-muted-foreground">
                  {systemPrompt?.length || 0} characters
                </span>
              </div>
              <Textarea
                id="system-prompt"
                {...form.register("SYSTEM_PROMPT")}
                rows={4}
              />
            </div>
          </CardContent>
        </Card>

        {/* Onboarding Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Onboarding</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="welcome-enabled">Enable Welcome Messages</Label>
              <Switch
                id="welcome-enabled"
                checked={form.watch("WELCOME_ENABLED")}
                onCheckedChange={(checked) => form.setValue("WELCOME_ENABLED", checked)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="welcome-channel-id">Welcome Channel ID</Label>
              <Input
                id="welcome-channel-id"
                {...form.register("WELCOME_CHANNEL_ID")}
                placeholder="e.g., 123456789012345678"
              />
              {form.formState.errors.WELCOME_CHANNEL_ID && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.WELCOME_CHANNEL_ID.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="welcome-message">Welcome Message Template</Label>
              <Textarea
                id="welcome-message"
                {...form.register("WELCOME_MESSAGE")}
                rows={3}
                placeholder="Welcome, {user}! Check out {server} rules."
              />
              <p className="text-xs text-muted-foreground">
                Use `{"{user}"}` for user mention and `{"{server}"}` for server name.
              </p>
              {form.formState.errors.WELCOME_MESSAGE && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.WELCOME_MESSAGE.message}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Daily Digest Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Daily Digest</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="digest-enabled">Enable Daily Digest</Label>
              <Switch
                id="digest-enabled"
                checked={form.watch("DIGEST_ENABLED")}
                onCheckedChange={(checked) => form.setValue("DIGEST_ENABLED", checked)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="digest-channel-id">Digest Channel ID</Label>
              <Input
                id="digest-channel-id"
                {...form.register("DIGEST_CHANNEL_ID")}
                placeholder="e.g., 123456789012345678"
              />
              {form.formState.errors.DIGEST_CHANNEL_ID && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.DIGEST_CHANNEL_ID.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="digest-time">Digest Time (HH:MM)</Label>
              <Input
                id="digest-time"
                {...form.register("DIGEST_TIME")}
                placeholder="e.g., 09:00"
              />
              {form.formState.errors.DIGEST_TIME && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.DIGEST_TIME.message}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Content Moderation Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Content Moderation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="moderation-enabled">Enable Moderation</Label>
              <Switch
                id="moderation-enabled"
                checked={form.watch("MODERATION_ENABLED")}
                onCheckedChange={(checked) => form.setValue("MODERATION_ENABLED", checked)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="mod-log-channel-id">Mod Log Channel ID</Label>
              <Input
                id="mod-log-channel-id"
                {...form.register("MOD_LOG_CHANNEL_ID")}
                placeholder="e.g., 123456789012345678"
              />
              {form.formState.errors.MOD_LOG_CHANNEL_ID && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.MOD_LOG_CHANNEL_ID.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="moderation-sensitivity">Moderation Sensitivity</Label>
              <Select
                value={form.watch("MODERATION_SENSITIVITY")}
                onValueChange={(value: "low" | "medium" | "high") =>
                  form.setValue("MODERATION_SENSITIVITY", value)
                }
              >
                <SelectTrigger id="moderation-sensitivity">
                  <SelectValue placeholder="Select sensitivity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
              {form.formState.errors.MODERATION_SENSITIVITY && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.MODERATION_SENSITIVITY.message}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* API Keys */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">API Keys</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs text-muted-foreground">
              Masked values (***...) are not overwritten on save. Enter a new value to update.
            </p>
            {(
              [
                ["GEMINI_API_KEY", "Gemini"],
                ["GROQ_API_KEY", "Groq"],
                ["OPENROUTER_API_KEY", "OpenRouter"],
                ["ANTHROPIC_API_KEY", "Anthropic"],
                ["OPENAI_API_KEY", "OpenAI"],
              ] as const
            ).map(([key, label]) => (
              <div key={key} className="space-y-1">
                <Label htmlFor={key}>{label}</Label>
                <Input
                  id={key}
                  type="password"
                  {...form.register(key)}
                  className="font-mono text-sm"
                />
              </div>
            ))}
          </CardContent>
        </Card>

        <Button type="submit" disabled={saving} className="w-full">
          {saving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Save Settings
        </Button>
      </form>
    </div>
  );
}
