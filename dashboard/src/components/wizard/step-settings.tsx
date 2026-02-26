"use client";

import { useWizardStore } from "@/stores/wizard-store";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function StepSettings() {
  const { data, updateData } = useWizardStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Bot Settings</CardTitle>
        <CardDescription>
          Customize how SparkSage behaves. These can all be changed later from the dashboard.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Prefix */}
        <div className="space-y-2">
          <Label htmlFor="prefix">Command Prefix</Label>
          <Input
            id="prefix"
            value={data.botPrefix}
            onChange={(e) => updateData({ botPrefix: e.target.value })}
            placeholder="!"
            className="w-24"
          />
          <p className="text-xs text-muted-foreground">
            The character(s) that trigger bot commands (e.g., !help)
          </p>
        </div>

        {/* Max Tokens */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Max Tokens</Label>
            <span className="text-sm font-mono tabular-nums text-muted-foreground">
              {data.maxTokens}
            </span>
          </div>
          <Slider
            value={[data.maxTokens]}
            onValueChange={([value]) => updateData({ maxTokens: value })}
            min={128}
            max={4096}
            step={64}
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>128 (short)</span>
            <span>4096 (long)</span>
          </div>
        </div>

        {/* System Prompt */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="system-prompt">System Prompt</Label>
            <span className="text-xs text-muted-foreground">
              {data.systemPrompt.length} characters
            </span>
          </div>
          <Textarea
            id="system-prompt"
            value={data.systemPrompt}
            onChange={(e) => updateData({ systemPrompt: e.target.value })}
            rows={4}
            placeholder="Describe how the bot should behave..."
          />
          <p className="text-xs text-muted-foreground">
            This prompt is sent to the AI provider with every message to set the bot&apos;s personality and behavior.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
