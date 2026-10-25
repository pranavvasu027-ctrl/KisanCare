import React from 'react';
import OnboardingLoginPortal from './Onboarding/OnboardingLoginPortal';

export default function Onboarding({ onComplete }: { onComplete?: () => void }) {
  return <OnboardingLoginPortal initialMode="onboarding" onComplete={onComplete} />;
}
