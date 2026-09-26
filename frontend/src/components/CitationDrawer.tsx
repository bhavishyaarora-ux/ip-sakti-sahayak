import React from 'react';
import { X, ExternalLink, Bookmark, Scale } from 'lucide-react';

export interface RetrievedChunk {
  chunk_id: string;
  score: number;
  citation_anchor: string;
  jurisdiction: string;
  regime: string;
  compliance_tag: string;
  content: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  chunk: RetrievedChunk | null;
}

export const CitationDrawer: React.FC<Props> = ({ isOpen, onClose, chunk }) => {
  if (!isOpen || !chunk) return null;

  const getRegistryUrl = (jurisdiction: string, anchor: string) => {
    if (jurisdiction === 'INT') {
      return 'https://www.wipo.int/patents/en/topics/traditional_knowledge.html';
    }
    if (anchor.includes('Patents Act')) {
      return 'https://ipindiaservices.gov.in/publicsearch';
    }
    if (anchor.includes('Biological Diversity') || anchor.includes('BD Rules')) {
      return 'https://nbaindia.org';
    }
    return 'https://www.indiacode.nic.in';
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm transition-opacity">
      <div className="fixed inset-y-0 right-0 max-w-xl w-full bg-slate-900 border-l border-slate-800 shadow-2xl p-6 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Scale className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-slate-100">Statutory Record Inspector</h3>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="mt-5 space-y-4">
            <div>
              <span className="text-xs uppercase tracking-wider font-semibold text-emerald-400">
                Official Citation Anchor
              </span>
              <h4 className="text-lg font-bold text-slate-100 mt-0.5">{chunk.citation_anchor}</h4>
            </div>

            <div className="flex flex-wrap gap-2">
              <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
                Scope: {chunk.jurisdiction === 'IN' ? 'Domestic (India)' : 'International / Cross-Border'}
              </span>
              <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-800">
                Tag: {chunk.compliance_tag}
              </span>
              <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-sky-950/60 text-sky-300 border border-sky-800">
                Match Score: {(chunk.score * 100).toFixed(1)}%
              </span>
            </div>

            <div className="mt-4">
              <span className="text-xs font-semibold text-slate-400">Verified Legal Text:</span>
              <div className="mt-2 p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs leading-relaxed text-slate-300 max-h-80 overflow-y-auto whitespace-pre-wrap">
                {chunk.content}
              </div>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Bookmark className="w-4 h-4 text-slate-500" />
            <span>Tamper-proof vector record</span>
          </div>
          <a
            href={getRegistryUrl(chunk.jurisdiction, chunk.citation_anchor)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition"
          >
            <span>Verify on Official Registry</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
};