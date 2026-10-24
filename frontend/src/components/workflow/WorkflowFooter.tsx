import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, ArrowLeft, LayoutDashboard, Sparkles, CheckCircle2 } from 'lucide-react';

interface StepInfo {
  label: string;
  labelMr?: string;
  path: string;
  description?: string;
}

interface WorkflowFooterProps {
  currentStageNumber?: number;
  currentStageName?: string;
  completedActionMessage?: string | null;
  prevStep?: StepInfo;
  nextStep: StepInfo;
  alternativeNextStep?: StepInfo;
}

export const WorkflowFooter: React.FC<WorkflowFooterProps> = ({
  currentStageNumber,
  currentStageName,
  completedActionMessage,
  prevStep,
  nextStep,
  alternativeNextStep
}) => {
  const navigate = useNavigate();

  return (
    <div className="mt-8 pt-6 border-t border-[#E6ECE3] bg-gradient-to-r from-emerald-50/70 via-white to-emerald-50/70 p-5 rounded-2xl border border-[#E6ECE3] shadow-xs">
      {completedActionMessage && (
        <div className="mb-4 p-3 bg-emerald-100/70 border border-emerald-300 text-emerald-900 rounded-xl flex items-center gap-2.5 text-xs font-semibold animate-fadeIn shadow-2xs">
          <CheckCircle2 size={18} className="text-emerald-700 shrink-0" />
          <span>{completedActionMessage}</span>
        </div>
      )}

      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        {/* Left Side: Current context & Back button */}
        <div className="flex items-center gap-3">
          {prevStep ? (
            <button
              onClick={() => navigate(prevStep.path)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-[#E6ECE3] bg-white text-[#103D2C] hover:bg-emerald-50 text-xs font-semibold transition-all cursor-pointer shadow-2xs"
            >
              <ArrowLeft size={14} />
              <span>Previous: {prevStep.label}</span>
            </button>
          ) : (
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-[#E6ECE3] bg-white text-[#103D2C] hover:bg-emerald-50 text-xs font-semibold transition-all cursor-pointer shadow-2xs"
            >
              <LayoutDashboard size={14} />
              <span>Dashboard</span>
            </button>
          )}

          {currentStageName && (
            <span className="text-xs text-[#19241B]/60 hidden sm:inline font-medium">
              {currentStageNumber ? `Stage ${currentStageNumber}: ` : ''}{currentStageName}
            </span>
          )}
        </div>

        {/* Right Side: Next Step in Workflow */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto justify-end">
          {alternativeNextStep && (
            <button
              onClick={() => navigate(alternativeNextStep.path)}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-emerald-700 bg-white text-emerald-800 hover:bg-emerald-50 text-xs font-bold transition-all cursor-pointer shadow-2xs"
            >
              <span>{alternativeNextStep.label}</span>
              <ArrowRight size={14} />
            </button>
          )}

          <button
            onClick={() => navigate(nextStep.path)}
            className="flex-1 md:flex-initial flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-[#103D2C] hover:bg-emerald-800 text-white text-xs font-bold transition-all shadow-md hover:shadow-lg hover:scale-[1.01] cursor-pointer"
          >
            <Sparkles size={14} className="text-amber-300" />
            <div className="text-left">
              <span className="block text-[9px] text-emerald-200 uppercase font-bold tracking-wider">
                Next in Seasonal Flow
              </span>
              <span>{nextStep.label} {nextStep.labelMr ? `(${nextStep.labelMr})` : ''}</span>
            </div>
            <ArrowRight size={16} className="ml-1" />
          </button>
        </div>
      </div>
    </div>
  );
};
