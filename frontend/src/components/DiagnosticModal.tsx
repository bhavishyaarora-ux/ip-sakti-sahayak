import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, X, CornerDownLeft, Sparkles, HelpCircle } from 'lucide-react';

export interface Question {
  question_id: string;
  question: string;
  options: string[];
  legal_rationale: string;
}

interface Props {
  isOpen: boolean;
  questions: Question[];
  onSubmit: (answers: Record<string, string>) => void;
  onClose: () => void;
  lang?: string;
}

// Canonical statutory questions used when backend provides standard diagnostic gating
const DEFAULT_QUESTIONS: Question[] = [
  {
    question_id: 'q1',
    question: 'Is this exact formulation directly drawn from a First Schedule classical text?',
    legal_rationale: 'Classical recipes trigger Section 3(p) prior art bars via TKDL.',
    options: [
      'Yes, identical classical recipe (Charaka, Sharangadhara, Sahasrayogam)',
      'No, modified ratio / modern combination',
    ],
  },
  {
    question_id: 'q2',
    question: 'What is the physical nature of the active formulation?',
    legal_rationale: 'Purified fractions fall under CDSCO Phytopharmaceutical Rules (Rule 122E).',
    options: [
      'Whole herb / Traditional aqueous extract (Kwatha, Asava, Swarasa)',
      'Purified, standardized fraction with quantified marker compounds (HPLC/LC-MS)',
    ],
  },
  {
    question_id: 'q3',
    question: 'What is the commercial intended use and claim of the product?',
    legal_rationale: 'Therapeutic claims require CDSCO/AYUSH licensing; supplements fall under FSSAI.',
    options: [
      'Therapeutic medicine (cure, mitigation, or treatment of disease)',
      'Nutritional supplement / Daily wellness without disease claims (Ayurveda Aahara)',
      'Topical skin, hair, or oral hygiene (Cosmetic)',
    ],
  },
];

export const DiagnosticModal: React.FC<Props> = ({
  isOpen,
  questions,
  onSubmit,
  onClose,
}) => {
  const activeQuestions = questions && questions.length > 0 ? questions : DEFAULT_QUESTIONS;
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [customInput, setCustomInput] = useState('');

  useEffect(() => {
    if (isOpen) {
      setCurrentStep(0);
      setSelectedAnswers({});
      setCustomInput('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const currentQ = activeQuestions[currentStep];

  const handleSelectOption = (optionValue: string) => {
    const updated = { ...selectedAnswers, [currentQ.question_id]: optionValue };
    setSelectedAnswers(updated);

    // Auto-advance to next question; submit automatically on the final step
    if (currentStep < activeQuestions.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      onSubmit(updated);
    }
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customInput.trim()) return;
    handleSelectOption(customInput.trim());
    setCustomInput('');
  };

  const handleSkip = () => {
    if (currentStep < activeQuestions.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      onSubmit(selectedAnswers);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto my-3 animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="bg-[#0b140e] border border-[#1b3121] rounded-2xl shadow-2xl overflow-hidden">
        {/* Top Header: Question Prompt + Stepper Controls */}
        <div className="px-5 py-3.5 border-b border-[#14261a] flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shrink-0" />
            <span className="text-xs font-semibold text-slate-200 truncate">
              {currentQ.question}
            </span>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {/* Step Pagination < 1 of 3 > */}
            <div className="flex items-center gap-1.5 text-slate-400 text-xs font-mono">
              <button
                type="button"
                disabled={currentStep === 0}
                onClick={() => setCurrentStep((prev) => prev - 1)}
                className="p-1 rounded hover:bg-[#142318] disabled:opacity-30 disabled:hover:bg-transparent transition"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <span className="text-[11px] text-slate-300">
                {currentStep + 1} of {activeQuestions.length}
              </span>
              <button
                type="button"
                disabled={currentStep === activeQuestions.length - 1}
                onClick={() => setCurrentStep((prev) => prev + 1)}
                className="p-1 rounded hover:bg-[#142318] disabled:opacity-30 disabled:hover:bg-transparent transition"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Dismiss Button */}
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-[#142318] transition"
              title="Dismiss"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Numbered Option Pills (Auto-advancing on click) */}
        <div className="p-3 space-y-1.5">
          {currentQ.options.map((opt, idx) => {
            const isSelected = selectedAnswers[currentQ.question_id] === opt;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectOption(opt)}
                className={`w-full flex items-center justify-between p-3 rounded-xl border text-left transition duration-150 group ${
                  isSelected
                    ? 'bg-emerald-950/60 border-emerald-500/80 text-emerald-200'
                    : 'bg-[#0f1b13] border-[#162a1c] hover:bg-[#142419] hover:border-[#223d29] text-slate-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-6 h-6 rounded-lg text-xs font-mono font-bold flex items-center justify-center shrink-0 transition ${
                      isSelected
                        ? 'bg-emerald-500 text-slate-950'
                        : 'bg-[#182b1e] text-slate-400 group-hover:bg-[#203a28] group-hover:text-emerald-300'
                    }`}
                  >
                    {idx + 1}
                  </span>
                  <span className="text-xs font-medium leading-relaxed">
                    {opt}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Statutory Impact Note */}
        <div className="px-4 py-1.5 bg-[#080e0a]/50 text-[11px] text-slate-500 italic border-t border-[#14261a]/60">
          *Statutory Impact: {currentQ.legal_rationale}
        </div>

        {/* Footer: Custom Text Input + Skip Action */}
        <div className="px-4 py-3 bg-[#080e0a] border-t border-[#14261a] flex items-center justify-between gap-4">
          <form onSubmit={handleCustomSubmit} className="flex-1 flex items-center gap-2">
            <input
              type="text"
              value={customInput}
              onChange={(e) => setCustomInput(e.target.value)}
              placeholder="Or type custom specification directly..."
              className="w-full bg-transparent text-xs text-slate-200 placeholder-slate-500 outline-none"
            />
            {customInput.trim() && (
              <button
                type="submit"
                className="p-1 rounded bg-emerald-600 text-white hover:bg-emerald-500 transition"
              >
                <CornerDownLeft className="w-3 h-3" />
              </button>
            )}
          </form>

          <div className="flex items-center gap-3 text-[11px] text-slate-500 shrink-0">
            <span className="hidden sm:inline font-mono text-[10px]">
              Click option to advance
            </span>
            <button
              type="button"
              onClick={handleSkip}
              className="px-2.5 py-1 rounded-lg bg-[#111e14] hover:bg-[#172b1d] text-slate-400 hover:text-slate-200 transition"
            >
              Skip
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};