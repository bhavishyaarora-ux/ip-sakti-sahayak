import React from 'react';
import { Shield, Globe } from 'lucide-react';

export type JurisdictionMode = 'IN' | 'INT';

interface Props {
  selected: JurisdictionMode;
  onChange: (mode: JurisdictionMode) => void;
}

export const JurisdictionSwitch: React.FC<Props> = ({ selected, onChange }) => {
  const options: { id: JurisdictionMode; label: string; icon: React.ReactNode; desc: string }[] = [
    {
      id: 'IN',
      label: 'India Domestic',
      icon: <Shield className="w-4 h-4" />,
      desc: 'Patents Act 1970, BDA 2023, FSSAI',
    },
    {
      id: 'INT',
      label: 'Cross-Border',
      icon: <Globe className="w-4 h-4" />,
      desc: 'WIPO GRATK, US FDA, Nagoya',
    },
  ];

  return (
    <div className="inline-flex p-1.5 bg-slate-900/80 backdrop-blur border border-slate-800 rounded-xl shadow-inner">
      {options.map((opt) => {
        const active = selected === opt.id;
        const activeColor =
          opt.id === 'INT'
            ? 'bg-sky-600 text-white shadow-md shadow-sky-950/50'
            : 'bg-emerald-600 text-white shadow-md shadow-emerald-950/50';

        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => onChange(opt.id)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${
              active
                ? activeColor
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            {opt.icon}
            <div className="text-left">
              <div>{opt.label}</div>
            </div>
          </button>
        );
      })}
    </div>
  );
};