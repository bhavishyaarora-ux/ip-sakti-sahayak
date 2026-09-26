import React, { useState } from 'react';
import { X, Send, UserCheck, CheckCircle, Download } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  category: string;
  query: string;
}

export const EscalationModal: React.FC<Props> = ({ isOpen, onClose, category, query }) => {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [submittedDocket, setSubmittedDocket] = useState<string | null>(null);
  const [dossierText, setDossierText] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleEscalate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/escalate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_query: query,
          product_category: category,
          applicant_name: name || 'AYUSH Innovator',
          contact_email: email,
        }),
      });
      const data = await res.json();
      setSubmittedDocket(data.docket_id);
      setDossierText(data.briefing_dossier);
    } catch {
      alert('Failed to submit escalation docket');
    } finally {
      setLoading(false);
    }
  };

  const downloadDossier = () => {
    if (!dossierText) return;
    const blob = new Blob([dossierText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${submittedDocket}_Briefing_Dossier.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6">
        <div className="flex justify-between items-center pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-slate-100">Empaneled Facilitator Escalation</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {submittedDocket ? (
          <div className="py-6 text-center space-y-4">
            <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto" />
            <div>
              <h4 className="text-sm font-bold text-slate-100">Docket Registered</h4>
              <div className="mt-2 p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-emerald-400">
                {submittedDocket}
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Your inquiry and formulation diagnostics have been securely formatted into a preliminary brief for an accredited patent agent.
            </p>
            <div className="flex gap-2 pt-2">
              <button
                onClick={downloadDossier}
                className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition"
              >
                <Download className="w-4 h-4" />
                <span>Download Dossier (.TXT)</span>
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleEscalate} className="mt-4 space-y-4">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
              <span className="text-slate-400">Classification: </span>
              <span className="font-semibold text-emerald-400">{category}</span>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Applicant / Entity Name</label>
              <input
                type="text"
                required
                placeholder="Dr. Rajesh Sharma"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:border-emerald-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Official Contact Email</label>
              <input
                type="email"
                required
                placeholder="rajesh@ayushbiotech.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:border-emerald-500 outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/50 transition"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{loading ? 'Generating Docket...' : 'Submit & Generate Dossier'}</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
};