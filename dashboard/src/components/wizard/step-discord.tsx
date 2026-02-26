"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { Eye, EyeOff, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { useWizardStore } from "@/stores/wizard-store";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function StepDiscord() {
  const { data: session } = useSession();
  const { data, updateData } = useWizardStore();
  const [showToken, setShowToken] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const token = (session as { accessToken?: string })?.accessToken;

  async function handleTest() {
    if (!data.discordToken || !token) return;
    setTesting(true);
    setTestResult(null);
    try {
      // We test the Discord token via the config update endpoint
      // For now, just verify it looks like a valid token format
      const isValidFormat = data.discordToken.length > 50;
      setTestResult({
        success: isValidFormat,
        message: isValidFormat
          ? "Token format looks valid. It will be verified when the bot starts."
          : "Token seems too short. Discord tokens are typically 70+ characters.",
      });
    } catch {
      setTestResult({ success: false, message: "Failed to validate token" });
    } finally {
      setTesting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Discord Bot Token</CardTitle>
        <CardDescription>
          Enter your Discord bot token. You can get one from the{" "}
          <a
            href="https://discord.com/developers/applications"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary underline"
          >
            Discord Developer Portal
          </a>
          .
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="discord-token">Bot Token</Label>
          <div className="relative">
            <Input
              id="discord-token"
              type={showToken ? "text" : "password"}
              placeholder="Paste your Discord bot token here"
              value={data.discordToken}
              onChange={(e) => updateData({ discordToken: e.target.value })}
              className="pr-20"
            />
            <div className="absolute right-1 top-1 flex gap-1">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setShowToken(!showToken)}
                className="h-7 w-7 p-0"
              >
                {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTest}
            disabled={!data.discordToken || testing}
          >
            {testing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Test Token
          </Button>
          {testResult && (
            <div className={`flex items-center gap-1.5 text-sm ${testResult.success ? "text-green-600" : "text-destructive"}`}>
              {testResult.success ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
              {testResult.message}
            </div>
          )}
        </div>

        <p className="text-xs text-muted-foreground">
          Your token is stored securely and never shared. Make sure your bot has been invited to
          your server with the Message Content intent enabled.
        </p>
      </CardContent>
    </Card>
  );
}
