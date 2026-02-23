const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions extends RequestInit {
  token?: string;
}

async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { token, headers: customHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((customHeaders as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    headers,
    ...rest,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `API error: ${res.status}`);
  }

  // Handle 204 No Content responses
  if (res.status === 204) {
    return null as T;
  }

  return res.json();
}

// Response types matching backend
export interface ProviderItem {
  name: string;
  display_name: string;
  model: string;
  free: boolean;
  configured: boolean;
  is_primary: boolean;
}

export interface ProvidersResponse {
  providers: ProviderItem[];
  fallback_order: string[];
}

export interface ChannelItem {
  channel_id: string;
  message_count: number;
  last_active: string;
}

export interface MessageItem {
  role: string;
  content: string;
  provider: string | null;
  type: string | null;
  created_at: string;
}

export interface GuildItem {
  id: string;
  name: string;
  member_count: number;
}

export interface BotStatus {
  online: boolean;
  username: string | null;
  latency: number | null;
  guild_count: number;
  guilds: GuildItem[];
  uptime: number | null;
}

export interface TestProviderResult {
  success: boolean;
  message: string;
  latency_ms?: number;
}

// FAQ interfaces
export interface FAQBase {
  question: string;
  answer: string;
  match_keywords: string;
}

export interface FAQCreate extends FAQBase {}

export interface FAQResponse extends FAQBase {
  id: number;
  guild_id: string;
  times_used: number;
  created_by: string | null;
  created_at: string;
}

// Command Permissions interfaces
export interface CommandPermissionBase {
  command_name: string;
  guild_id: string;
  role_id: string;
}

export interface CommandPermissionCreate extends CommandPermissionBase {}

export interface CommandPermissionResponse extends CommandPermissionBase {}

// Channel Prompt interfaces
export interface ChannelPromptBase {
  channel_id: string;
  guild_id: string;
  system_prompt: string;
}

export interface ChannelPromptCreate extends ChannelPromptBase {}

export interface ChannelPromptResponse extends ChannelPromptBase {}

export const api = {
  // Auth
  login: (password: string) =>
    apiFetch<{ access_token: string; token_type: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),

  me: (token: string) =>
    apiFetch<{ username: string; role: string }>("/api/auth/me", { token }),

  // Config
  getConfig: (token: string) =>
    apiFetch<{ config: Record<string, string> }>("/api/config", { token }),

  updateConfig: (token: string, values: Record<string, string>) =>
    apiFetch<{ status: string }>("/api/config", {
      method: "PUT",
      body: JSON.stringify({ values }),
      token,
    }),

  // Providers
  getProviders: (token: string) =>
    apiFetch<ProvidersResponse>("/api/providers", { token }),

  testProvider: (token: string, provider: string) =>
    apiFetch<TestProviderResult>("/api/providers/test", {
      method: "POST",
      body: JSON.stringify({ provider }),
      token,
    }),

  setPrimaryProvider: (token: string, provider: string) =>
    apiFetch<{ status: string; primary: string }>("/api/providers/primary", {
      method: "PUT",
      body: JSON.stringify({ provider }),
      token,
    }),

  // Bot
  getBotStatus: (token: string) =>
    apiFetch<BotStatus>("/api/bot/status", { token }),

  // Conversations
  getConversations: (token: string) =>
    apiFetch<{ channels: ChannelItem[] }>("/api/conversations", { token }),

  getConversation: (token: string, channelId: string) =>
    apiFetch<{ channel_id: string; messages: MessageItem[] }>(
      `/api/conversations/${channelId}`,
      { token }
    ),

  deleteConversation: (token: string, channelId: string) =>
    apiFetch<{ status: string }>(`/api/conversations/${channelId}`, {
      method: "DELETE",
      token,
    }),

  // Wizard
  getWizardStatus: (token: string) =>
    apiFetch<{ completed: boolean; current_step: number }>("/api/wizard/status", { token }),

  completeWizard: (token: string, data: Record<string, string>) =>
    apiFetch<{ status: string }>("/api/wizard/complete", {
      method: "POST",
      body: JSON.stringify({ config: data }),
      token,
    }),

  // FAQs
  listFaqs: (token: string, guildId: string | null = null) =>
    apiFetch<FAQResponse[]>("/api/faqs" + (guildId ? `?guild_id=${guildId}` : ""), { token }),

  createFaq: (token: string, guildId: string, faq: FAQCreate) =>
    apiFetch<FAQResponse>(`/api/faqs?guild_id=${guildId}`, {
      method: "POST",
      body: JSON.stringify(faq),
      token,
    }),

  deleteFaq: (token: string, guildId: string, faqId: number) =>
    apiFetch<void>(`/api/faqs/${faqId}?guild_id=${guildId}`, {
      method: "DELETE",
      token,
    }),

  // Permissions
  listCommandPermissions: (token: string, guildId: string) =>
    apiFetch<CommandPermissionResponse[]>(`/api/permissions?guild_id=${guildId}`, { token }),

  createCommandPermission: (token: string, permission: CommandPermissionCreate) =>
    apiFetch<CommandPermissionResponse>("/api/permissions", {
      method: "POST",
      body: JSON.stringify(permission),
      token,
    }),

  deleteCommandPermission: (token: string, commandName: string, guildId: string, roleId: string) =>
    apiFetch<void>(`/api/permissions/${commandName}/${roleId}?guild_id=${guildId}`, {
      method: "DELETE",
      token,
    }),

  // Channel Prompts
  listChannelPrompts: (token: string) =>
    apiFetch<{ channel_prompts: ChannelPromptResponse[] }>("/api/config/channel_prompts", { token }),
  
  createChannelPrompt: (token: string, prompt: ChannelPromptCreate) =>
    apiFetch<{ status: string }>("/api/config/channel_prompts", {
      method: "POST",
      body: JSON.stringify(prompt),
      token,
    }),

  deleteChannelPrompt: (token: string, channelId: string) =>
    apiFetch<{ status: string }>(`/api/config/channel_prompts/${channelId}`, {
      method: "DELETE",
      token,
    }),

  // Channel Providers
  listChannelProviders: (token: string) =>
    apiFetch<{ channel_providers: ChannelProviderResponse[] }>("/api/config/channel_providers", { token }),
  
  createChannelProvider: (token: string, provider: ChannelProviderCreate) =>
    apiFetch<{ status: string }>("/api/config/channel_providers", {
      method: "POST",
      body: JSON.stringify(provider),
      token,
    }),

  deleteChannelProvider: (token: string, channelId: string) =>
    apiFetch<{ status: string }>(`/api/config/channel_providers/${channelId}`, {
      method: "DELETE",
      token,
    }),
};


// Channel Provider interfaces
export interface ChannelProviderBase {
  channel_id: string;
  guild_id: string;
  provider_name: string;
}

export interface ChannelProviderCreate extends ChannelProviderBase {}

export interface ChannelProviderResponse extends ChannelProviderBase {}

