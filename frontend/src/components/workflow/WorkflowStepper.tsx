import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Check, ChevronRight, LayoutDashboard, ArrowRight, ArrowLeft } from 'lucide-react';

export interface WorkflowStage {
  id: number;
  name: string;
  nameMr: string;
  description: string;
  primaryRoute: string;
  routes: string[];
}

export const WORKFLOW_STAGES: WorkflowStage[] = [
  {
    id: 1,
    name: 'Farm & Soil',
    nameMr: 'शेत व माती',
    description: 'Set boundaries & soil health',
    primaryRoute: '/farm-setup',
    routes: ['/farm-setup', '/digital-twin', '/soil', '/soil-intelligence']
  },
  {
    id: 2,
    name: 'Crop Planning',
    nameMr: 'पीक नियोजन',
    description: 'AI recommendation & comparison',
    primaryRoute: '/crop-recommendation',
    routes: ['/crop-recommendation', '/crop-comparison']
  },
  {
    id: 3,
    name: 'Crop Care',
    nameMr: 'हंगामी निगा',
    description: 'Weather, irrigation & disease',
    primaryRoute: '/irrigation',
    routes: ['/irrigation', '/disease', '/recommendations']
  },
  {
    id: 4,
    name: 'Simulation & ROI',
    nameMr: 'नफा व जोखीम',
    description: 'What-If scenarios & economics',
    primaryRoute: '/simulator',
    routes: ['/simulator', '/economics']
  },
  {
    id: 5,
    name: 'Market & Storage',
    nameMr: 'बाजार व साठवणूक',
    description: 'Mandi prices, storage & schemes',
    primaryRoute: '/market',
    routes: ['/market', '/post-harvest', '/schemes']
  }
];

interface WorkflowStepperProps {
  currentStageId?: number;
  compact?: boolean;
}

export const WorkflowStepper: React.FC<WorkflowStepperProps> = ({ currentStageId, compact = false }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Auto-detect stage from current URL path if not explicitly provided
  const activeStageId = currentStageId || WORKFLOW_STAGES.find(s =>
    s.routes.some(r => location.pathname === r || location.pathname.startsWith(`${r}/`))
  )?.id || 1;

  return (
    <div className="agri-card p-4 mb-6 bg-white border border-[#E6ECE3]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-[#E6ECE3] gap-2">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 animate-pulse"></span>
          <span className="text-xs font-bold uppercase tracking-wider text-[#103D2C]">
            Seasonal Agriculture Lifecycle &bull; हंगाम चक्र
          </span>
          <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2.5 py-0.5 rounded-full">
            Stage {activeStageId} of 5
          </span>
        </div>
        <button
          onClick={() => navigate('/')}
          className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 flex items-center gap-1.5 transition-colors self-start sm:self-auto cursor-pointer"
        >
          <LayoutDashboard size={14} />
          <span>Dashboard Overview</span>
        </button>
      </div>

      {/* Stepper Steps */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 sm:gap-3">
        {WORKFLOW_STAGES.map((stage) => {
          const isCompleted = stage.id < activeStageId;
          const isCurrent = stage.id === activeStageId;
          const isFuture = stage.id > activeStageId;

          return (
            <div
              key={stage.id}
              onClick={() => navigate(stage.primaryRoute)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer select-none flex flex-col justify-between ${
                isCurrent
                  ? 'bg-[#103D2C] text-white border-[#103D2C] shadow-md shadow-emerald-950/20 ring-2 ring-emerald-500/40 scale-[1.02]'
                  : isCompleted
                  ? 'bg-emerald-50/70 hover:bg-emerald-100/70 text-[#103D2C] border-emerald-200/80'
                  : 'bg-[#F8FAF7] hover:bg-emerald-50/50 text-[#19241B]/60 border-[#E6ECE3]'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    isCurrent
                      ? 'bg-emerald-400 text-[#072F22]'
                      : isCompleted
                      ? 'bg-emerald-600 text-white'
                      : 'bg-[#E6ECE3] text-[#19241B]/50'
                  }`}
                >
                  {isCompleted ? <Check size={12} strokeWidth={3} /> : stage.id}
                </span>
                <span
                  className={`text-[9px] font-bold uppercase tracking-wider ${
                    isCurrent ? 'text-emerald-200' : isCompleted ? 'text-emerald-700' : 'text-[#19241B]/40'
                  }`}
                >
                  {isCurrent ? 'Active' : isCompleted ? 'Done' : `Stage ${stage.id}`}
                </span>
              </div>

              <div>
                <h4
                  className={`text-xs font-heading font-bold leading-tight ${
                    isCurrent ? 'text-white' : 'text-[#103D2C]'
                  }`}
                >
                  {stage.name}
                </h4>
                <p
                  className={`text-[10px] mt-0.5 line-clamp-1 ${
                    isCurrent ? 'text-emerald-100/80' : 'text-[#19241B]/60'
                  }`}
                >
                  {stage.nameMr}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
