export interface BotConfig {
  discord_token: string;
  ai_provider: string;
  bot_prefix: string;
  max_tokens: number;
  system_prompt: string;
  gemini_api_key: string;
  gemini_model: string;
  groq_api_key: string;
  groq_model: string;
  openrouter_api_key: string;
  openrouter_model: string;
  anthropic_api_key: string;
  anthropic_model: string;
  openai_api_key: string;
  openai_model: string;
}

export interface WizardStatus {
  completed: boolean;
  current_step: number;
}

export interface BotStatus {
  online: boolean;
  latency: number | null;
  guilds: number;
  uptime: number | null;
}
