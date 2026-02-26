"use client";

import { useWizardStore } from "@/stores/wizard-store";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { StepDiscord } from "./step-discord";
import { StepProviders } from "./step-providers";
import { StepSettings } from "./step-settings";
import { StepReview } from "./step-review";

const STEPS = [
  { title: "Discord Token", description: "Connect your Discord bot" },
  { title: "AI Providers", description: "Configure API keys" },
  { title: "Bot Settings", description: "Customize behavior" },
  { title: "Review", description: "Confirm your setup" },
];

const STEP_COMPONENTS = [StepDiscord, StepProviders, StepSettings, StepReview];

export function WizardShell() {
  const { currentStep, setStep } = useWizardStore();
  const progress = ((currentStep + 1) / STEPS.length) * 100;
  const StepComponent = STEP_COMPONENTS[currentStep];

  return (
    <div className="space-y-8">
      {/* Step indicator */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">
            Step {currentStep + 1} of {STEPS.length}: {STEPS[currentStep].title}
          </span>
          <span className="text-muted-foreground">
            {STEPS[currentStep].description}
          </span>
        </div>
        <Progress value={progress} className="h-2" />
        <div className="flex justify-between">
          {STEPS.map((step, i) => (
            <button
              key={step.title}
              onClick={() => i < currentStep && setStep(i)}
              className={`text-xs transition-colors ${
                i === currentStep
                  ? "font-medium text-foreground"
                  : i < currentStep
                  ? "text-primary cursor-pointer hover:underline"
                  : "text-muted-foreground"
              }`}
              disabled={i > currentStep}
            >
              {step.title}
            </button>
          ))}
        </div>
      </div>

      {/* Step content */}
      <StepComponent />

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t">
        <Button
          variant="outline"
          onClick={() => setStep(currentStep - 1)}
          disabled={currentStep === 0}
        >
          Back
        </Button>
        {currentStep < STEPS.length - 1 && (
          <Button onClick={() => setStep(currentStep + 1)}>
            Continue
          </Button>
        )}
      </div>
    </div>
  );
}
