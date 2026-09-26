import React, { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, ChevronDown, ChevronUp, Bot, Scale, Cpu, ShieldAlert } from 'lucide-react';

export interface StepStatus {
  id: string;
  agent: string;
  action: string;
  icon: React.ReactNode;
}

interface AgentReasoningTraceProps {
  isActive: boolean;
  activeNode: string | null;
  completedNodes: string[];
  jurisdiction: 'IN' | 'INT';
}

export const AgentReasoningTrace: React.FC<AgentReasoningTraceProps> = ({
  isActive,
  activeNode,
  completedNodes,
  jurisdiction,
}) => {
  const [isOpen, setIsOpen] = useState(true);

  // Auto-expand when active, stay toggleable when complete
  useEffect(() => {
    if (isActive) setIsOpen(true);
  }, [isActive]);

  const steps: StepStatus[] = [
    {
      id: 'classify',
      agent: 'Product Classification Agent',
      action: 'Validating against D&C First Schedule (54 classical texts) & setting legal bounds',
      icon: <Bot className="w-3.5 h-3.5 text-emerald-400" />,
    },
    {
      id: 'route',
      agent: 'Jurisdiction Router',
      action: `Filtering corpus for ${
        jurisdiction === 'INT'
          ? 'Cross-Border (WIPO GRATK 2024 / Nagoya / US FDA)'
          : 'National Track (Patents Act 1970 / BDA 2023)'
      }`,
      icon: <Scale className="w-3.5 h-3.5 text-sky-400" />,
    },
    {
      id: 'dispatch',
      agent: 'Hybrid Retrieval & Knowledge Graph',
      action: 'Traversing Neo4j prior art triples & executing Qdrant dense vector search',
      icon: <Cpu className="w-3.5 h-3.5 text-purple-400" />,
    },
    {
      id: 'synthesis',
      agent: 'Statutory Synthesis & Watermark',
      action: 'Evaluating Section 3(p)/3(d) exclusions and generating grounded statutory brief',
      icon: <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />,
    },
  ];

  if (!activeNode && completedNodes.length === 0) return null;

  const isAllComplete = completedNodes.length >= steps.length;

  return (
    <div className="w-full max-w-3xl mx-auto my-3 animate-in fade-in duration-200">
      {/* 1. Sleek Expandable Trigger Bar (Image 2 style) */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-[#0c160f] hover:bg-[#101e15] border border-[#182c1e] text-xs transition"
      >
        <div className="flex items-center gap-2">
          {isActive ? (
            <Loader2 className="w-3.5 h-3.5 text-emerald-400 animate-spin" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          )}
          <span className="text-slate-300 font-medium">
            {isActive
              ? 'Executing LangGraph Multi-Agent Pipeline...'
              : 'Verified across 4 LangGraph agents & statutory corpus'}
          </span>
          <span className="text-slate-500">
            {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </span>
        </div>

        <span className="text-[11px] font-mono text-emerald-400/90 font-semibold">
          {completedNodes.length}/{steps.length} {isActive ? 'Running' : 'Done'}
        </span>
      </button>

      {/* 2. Collapsible Reasoning Tray */}
      {isOpen && (
        <div className="mt-2 p-3.5 rounded-xl bg-[#09110c] border border-[#16271a] space-y-2">
          {steps.map((step) => {
            const isDone = completedNodes.includes(step.id);
            const isCurrent =
              isActive &&
              (activeNode === step.id ||
                (!isDone && activeNode === null && completedNodes.length === 0 && step.id === 'classify'));

            return (
              <div
                key={step.id}
                className={`flex items-start justify-between p-2 rounded-lg text-xs transition ${
                  isCurrent
                    ? 'bg-[#102216] border border-emerald-500/30 text-slate-100'
                    : isDone
                    ? 'text-slate-300'
                    : 'opacity-40 text-slate-600'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <div className="mt-0.5">
                    {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                    {isCurrent && <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />}
                    {!isDone && !isCurrent && <div className="w-3.5 h-3.5 rounded-full border border-slate-700" />}
                  </div>

                  <div>
                    <div className="flex items-center gap-1.5 font-semibold text-slate-200">
                      {step.icon}
                      <span>{step.agent}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                      {step.action}
                    </div>
                  </div>
                </div>

                <span className="text-[10px] font-mono shrink-0">
                  {isDone && <span className="text-emerald-500 font-bold">VERIFIED</span>}
                  {isCurrent && <span className="text-amber-400 font-bold animate-pulse">RUNNING</span>}
                  {!isDone && !isCurrent && <span className="text-slate-600">QUEUED</span>}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};