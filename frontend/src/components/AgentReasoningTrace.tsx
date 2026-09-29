import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  Loader2,
  ChevronDown,
  ChevronUp,
  Bot,
  Scale,
  Cpu,
  ShieldCheck,
  FileCheck2,
  Globe2,
  Sparkles,
  MinusCircle,
  Terminal,
} from 'lucide-react';

export interface StepStatus {
  id: string;
  agent: string;
  action: string;
  icon: React.ReactNode;
  isSubAgent?: boolean;
}

export interface PipelineData {
  target_agents?: string[];
  reasoning_trace?: string[];
  classification?: {
    category?: string;
    is_definitive?: boolean;
  };
  routing?: {
    selected_track?: string;
    target_filter?: string;
  };
}

interface AgentReasoningTraceProps {
  isActive?: boolean;
  activeNode?: string | null;
  completedNodes?: string[];
  jurisdiction?: 'IN' | 'INT' | 'DUAL';
  targetAgents?: string[];
  pipeline?: PipelineData;
}

export const AgentReasoningTrace: React.FC<AgentReasoningTraceProps> = ({
  isActive = false,
  activeNode = null,
  completedNodes = [],
  jurisdiction = 'IN',
  targetAgents: propTargetAgents,
  pipeline,
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [showTraceLogs, setShowTraceLogs] = useState(false);

  // Auto-expand when active
  useEffect(() => {
    if (isActive) setIsOpen(true);
  }, [isActive]);

  // Merge target agents from direct props or pipeline payload
  const effectiveTargetAgents =
    propTargetAgents || pipeline?.target_agents || ['ip_agent', 'abs_agent'];

  const reasoningTraces = pipeline?.reasoning_trace || [];

  const steps: StepStatus[] = [
    {
      id: 'classify',
      agent: 'Product Classification Agent',
      action: pipeline?.classification?.category
        ? `Categorized as: ${String(pipeline.classification.category).replace('_', ' ')}`
        : 'Classifying under Drugs & Cosmetics First Schedule (54 classical texts) or FSSAI',
      icon: <Bot className="w-3.5 h-3.5 text-emerald-400" />,
    },
    {
      id: 'route',
      agent: 'Jurisdiction Router',
      action: `Routing track: ${
        pipeline?.routing?.selected_track ||
        (jurisdiction === 'INT'
          ? 'Cross-Border (WIPO GRATK 2024 / Nagoya / US FDA)'
          : jurisdiction === 'DUAL'
          ? 'Dual Comparison (India Domestic vs. International)'
          : 'National Track (Patents Act 1970 / BDA 2023)')
      }`,
      icon: <Scale className="w-3.5 h-3.5 text-sky-400" />,
    },
    {
      id: 'retrieve',
      agent: 'Hybrid Retrieval & Knowledge Graph',
      action: 'Traversing root Ayurvedic texts & retrieving verified statutory clauses',
      icon: <Cpu className="w-3.5 h-3.5 text-purple-400" />,
    },
    {
      id: 'ip_agent',
      agent: 'IP Specialist Agent',
      action: 'Evaluating Sec 3(p) TKDL exclusions, Sec 3(e) synergy & TM Class 5/30',
      icon: <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />,
      isSubAgent: true,
    },
    {
      id: 'abs_agent',
      agent: 'ABS & Compliance Agent',
      action: 'Verifying Biological Diversity Act 2023 (Sec 6 NBA Form III vs Sec 7 SBB)',
      icon: <FileCheck2 className="w-3.5 h-3.5 text-teal-400" />,
      isSubAgent: true,
    },
    {
      id: 'export_agent',
      agent: 'Export / Global Agent',
      action: 'Assessing WIPO GRATK (2024) Art. 3 origin disclosure & US FDA Botanical IND',
      icon: <Globe2 className="w-3.5 h-3.5 text-blue-400" />,
      isSubAgent: true,
    },
    {
      id: 'synthesis',
      agent: 'Statutory Synthesis & Guardrails',
      action: 'Enforcing NeMo citation verification, DPDP sanitization & watermark disclaimer',
      icon: <Sparkles className="w-3.5 h-3.5 text-amber-400" />,
    },
  ];

  // Map alternative node names that might be passed by API streaming
  const isNodeComplete = (nodeId: string) => {
    if (completedNodes.includes(nodeId)) return true;
    if (nodeId === 'retrieve' && completedNodes.includes('dispatch')) return true;
    if (nodeId === 'classify' && completedNodes.includes('classifier')) return true;
    if (nodeId === 'route' && completedNodes.includes('router')) return true;
    if (nodeId === 'synthesis' && completedNodes.includes('synthesizer')) return true;
    return false;
  };

  const isNodeActive = (nodeId: string) => {
    if (activeNode === nodeId) return true;
    if (nodeId === 'retrieve' && activeNode === 'dispatch') return true;
    if (nodeId === 'classify' && activeNode === 'classifier') return true;
    if (nodeId === 'route' && activeNode === 'router') return true;
    if (nodeId === 'synthesis' && activeNode === 'synthesizer') return true;
    return false;
  };

  // If component has no data and isn't active, don't show
  if (!activeNode && completedNodes.length === 0 && !pipeline) return null;

  // Active steps count excluding explicitly bypassed agents
  const relevantSteps = steps.filter(
    (s) => !s.isSubAgent || effectiveTargetAgents.includes(s.id)
  );
  const completedCount = steps.filter((s) => isNodeComplete(s.id)).length;
  const isAllComplete = completedCount >= relevantSteps.length;

  return (
    <div className="w-full max-w-3xl mx-auto my-3 animate-in fade-in duration-200">
      {/* 1. Sleek Expandable Trigger Bar */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-[#0c160f] hover:bg-[#101e15] border border-[#182c1e] text-xs transition shadow-sm"
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
              : 'Verified across LangGraph specialized agents & statutory corpus'}
          </span>
          <span className="text-slate-500">
            {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono border border-emerald-500/20">
            {effectiveTargetAgents.length} Active Agents
          </span>
          <span className="text-[11px] font-mono text-emerald-400/90 font-semibold">
            {completedCount}/{relevantSteps.length} {isActive ? 'Running' : 'Done'}
          </span>
        </div>
      </button>

      {/* 2. Collapsible Reasoning Tray */}
      {isOpen && (
        <div className="mt-2 p-3.5 rounded-xl bg-[#09110c] border border-[#16271a] space-y-2">
          {steps.map((step) => {
            const isSub = step.isSubAgent;
            const isTargeted = !isSub || effectiveTargetAgents.includes(step.id);
            const isBypassed = isSub && !isTargeted;
            const isDone = isNodeComplete(step.id);
            const isCurrent = isActive && isNodeActive(step.id);

            return (
              <div
                key={step.id}
                className={`flex items-start justify-between p-2 rounded-lg text-xs transition ${
                  isBypassed
                    ? 'opacity-35 bg-black/20 text-slate-500'
                    : isCurrent
                    ? 'bg-[#102216] border border-emerald-500/30 text-slate-100'
                    : isDone
                    ? 'text-slate-300 bg-slate-950/40'
                    : 'opacity-50 text-slate-500'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <div className="mt-0.5">
                    {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                    {isCurrent && <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />}
                    {isBypassed && <MinusCircle className="w-3.5 h-3.5 text-slate-600" />}
                    {!isDone && !isCurrent && !isBypassed && (
                      <div className="w-3.5 h-3.5 rounded-full border border-slate-700" />
                    )}
                  </div>

                  <div>
                    <div className="flex items-center gap-1.5 font-semibold text-slate-200">
                      {step.icon}
                      <span className={isBypassed ? 'line-through text-slate-500' : ''}>
                        {step.agent}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                      {isBypassed
                        ? 'Bypassed by router (out of query scope)'
                        : step.action}
                    </div>
                  </div>
                </div>

                <span className="text-[10px] font-mono shrink-0 ml-2">
                  {isBypassed && <span className="text-slate-600 font-semibold">BYPASSED</span>}
                  {!isBypassed && isDone && <span className="text-emerald-500 font-bold">VERIFIED</span>}
                  {!isBypassed && isCurrent && (
                    <span className="text-amber-400 font-bold animate-pulse">RUNNING</span>
                  )}
                  {!isBypassed && !isDone && !isCurrent && (
                    <span className="text-slate-600">QUEUED</span>
                  )}
                </span>
              </div>
            );
          })}

          {/* 3. Optional Reasoning Trace Log Terminal Drawer */}
          {reasoningTraces.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-[#16271a]">
              <button
                type="button"
                onClick={() => setShowTraceLogs(!showTraceLogs)}
                className="w-full flex items-center justify-between text-[11px] font-mono text-slate-400 hover:text-slate-200 transition py-1"
              >
                <div className="flex items-center gap-1.5">
                  <Terminal className="w-3 h-3 text-emerald-400" />
                  <span>State Machine Execution Trace ({reasoningTraces.length} steps)</span>
                </div>
                <span>{showTraceLogs ? 'Hide' : 'Inspect'}</span>
              </button>

              {showTraceLogs && (
                <div className="mt-2 p-2.5 rounded-lg bg-black/60 border border-slate-800/80 font-mono text-[11px] space-y-1 text-slate-300 max-h-40 overflow-y-auto">
                  {reasoningTraces.map((trace, idx) => (
                    <div key={idx} className="flex items-start gap-1.5">
                      <span className="text-emerald-500 select-none">›</span>
                      <span>{trace}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};