export interface Provider {
  id: string;
  name: string;
  model: string;
  api_key_set: boolean;
  free: boolean;
  is_primary: boolean;
}

export interface ProviderTestResult {
  success: boolean;
  message: string;
  latency_ms?: number;
}

export const PROVIDER_INFO: Record<
  string,
  { name: string; description: string; getKeyUrl: string; defaultModel: string; free: boolean }
> = {
  gemini: {
    name: "Google Gemini",
    description: "Free: 10 RPM, 250 req/day (Gemini 2.5 Flash)",
    getKeyUrl: "https://aistudio.google.com/apikey",
    defaultModel: "gemini-2.5-flash",
    free: true,
  },
  groq: {
    name: "Groq",
    description: "Free: 30 RPM, 1000 req/day (Llama 3.3 70B)",
    getKeyUrl: "https://console.groq.com/keys",
    defaultModel: "llama-3.3-70b-versatile",
    free: true,
  },
  openrouter: {
    name: "OpenRouter",
    description: "Free: 20 RPM, 200 req/day (many free models)",
    getKeyUrl: "https://openrouter.ai/keys",
    defaultModel: "deepseek/deepseek-r1:free",
    free: true,
  },
  anthropic: {
    name: "Anthropic Claude",
    description: "Paid: Premium Claude models",
    getKeyUrl: "https://console.anthropic.com/",
    defaultModel: "claude-sonnet-4-6",
    free: false,
  },
  openai: {
    name: "OpenAI",
    description: "Paid: GPT-4o and more",
    getKeyUrl: "https://platform.openai.com/api-keys",
    defaultModel: "gpt-4o-mini",
    free: false,
  },
};
