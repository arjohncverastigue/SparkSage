import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface WizardData {
  discordToken: string;
  providers: Record<string, string>; // provider_id -> api_key
  primaryProvider: string;
  botPrefix: string;
  maxTokens: number;
  systemPrompt: string;
}

interface WizardState {
  currentStep: number;
  data: WizardData;
  setStep: (step: number) => void;
  updateData: (partial: Partial<WizardData>) => void;
  reset: () => void;
}

const defaultData: WizardData = {
  discordToken: "",
  providers: {},
  primaryProvider: "gemini",
  botPrefix: "!",
  maxTokens: 1024,
  systemPrompt:
    "You are SparkSage, a helpful and friendly AI assistant in a Discord server. Be concise, helpful, and engaging.",
};

export const useWizardStore = create<WizardState>()(
  persist(
    (set) => ({
      currentStep: 0,
      data: { ...defaultData },
      setStep: (step) => set({ currentStep: step }),
      updateData: (partial) =>
        set((state) => ({
          data: { ...state.data, ...partial },
        })),
      reset: () => set({ currentStep: 0, data: { ...defaultData } }),
    }),
    {
      name: "sparksage-wizard",
    }
  )
);
