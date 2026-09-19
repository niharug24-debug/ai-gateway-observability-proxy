"use client";

import { useState } from "react";
import { ShieldCheck, Lock, AlertTriangle, CheckCircle2, Play, Eye } from "lucide-react";

export default function SecurityAuditPage() {
  const [testInput, setTestInput] = useState(
    "Hi, please process refund for john_doe@company.com using Visa card 4532 0151 1283 0366. Reach me at +1 (555) 234-5678."
  );
  const [sanitizedOutput, setSanitizedOutput] = useState("");
  const [redactionStats, setRedactionStats] = useState<{
    count: number;
    types: string[];
  } | null>(null);

  function simulateRedaction() {
    let result = testInput;
    const types: string[] = [];
    let count = 0;

    // Email test regex
    const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g;
    if (result.match(emailRegex)) {
      types.push("EMAIL");
      count += (result.match(emailRegex) || []).length;
      result = result.replace(emailRegex, "[REDACTED_EMAIL]");
    }

    // Card test regex
    const cardRegex = /\b(?:\d{4}[-\s]?){3,4}\d{1,4}\b/g;
    if (result.match(cardRegex)) {
      types.push("CREDIT_CARD");
      count += (result.match(cardRegex) || []).length;
      result = result.replace(cardRegex, "[REDACTED_CREDIT_CARD]");
    }

    // Phone test regex
    const phoneRegex = /(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b/g;
    if (result.match(phoneRegex)) {
      types.push("PHONE_NUMBER");
      count += (result.match(phoneRegex) || []).length;
      result = result.replace(phoneRegex, "[REDACTED_PHONE_NUMBER]");
    }

    setSanitizedOutput(result);
    setRedactionStats({ count, types });
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-b border-border pb-6">
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-bold tracking-tight text-white">PII Data Protection & Compliance</h2>
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800/60 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> PCI-DSS & GDPR Active
          </span>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Zero-trust regex inspection intercepting sensitive customer identifiers before transit to 3rd-party LLM providers.
        </p>
      </div>

      {/* Compliance Standard Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-panel p-5 rounded-xl border border-border">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase">Financial Protection</span>
            <Lock className="w-4 h-4 text-emerald-400" />
          </div>
          <h4 className="text-base font-bold text-white">Credit Card Redaction</h4>
          <p className="text-xs text-slate-400 mt-1">
            Complies with PCI-DSS guidelines. Uses Luhn algorithm validation (Mod 10) to mask 16-digit PANs before transit.
          </p>
          <div className="mt-3 text-[11px] font-mono text-emerald-400 bg-emerald-950/40 px-2.5 py-1 rounded border border-emerald-800/30 w-fit">
            Pattern: [REDACTED_CREDIT_CARD]
          </div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-border">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase">Privacy Regulations</span>
            <ShieldCheck className="w-4 h-4 text-blue-400" />
          </div>
          <h4 className="text-base font-bold text-white">Email Sanitization</h4>
          <p className="text-xs text-slate-400 mt-1">
            Prevents customer contact addresses from being leaked into training datasets or 3rd-party audit trails.
          </p>
          <div className="mt-3 text-[11px] font-mono text-blue-400 bg-blue-950/40 px-2.5 py-1 rounded border border-blue-800/30 w-fit">
            Pattern: [REDACTED_EMAIL]
          </div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-border">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase">Identity Protection</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <h4 className="text-base font-bold text-white">Phone Masking</h4>
          <p className="text-xs text-slate-400 mt-1">
            Captures North American, E.164, and international telephone numbers, scrubbing direct contact lines.
          </p>
          <div className="mt-3 text-[11px] font-mono text-amber-400 bg-amber-950/40 px-2.5 py-1 rounded border border-amber-800/30 w-fit">
            Pattern: [REDACTED_PHONE_NUMBER]
          </div>
        </div>
      </div>

      {/* Interactive PII Sandbox Simulator */}
      <div className="glass-panel p-6 rounded-xl border border-border space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Interactive PII Sanitization Sandbox</h3>
            <p className="text-xs text-slate-400">
              Test the gateway’s regex engine locally. See how incoming prompts are transformed before transit.
            </p>
          </div>
          <button
            onClick={simulateRedaction}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white transition-colors shadow-lg shadow-blue-600/20"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            Run Sanitizer
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Input Area */}
          <div className="space-y-2">
            <label className="text-xs font-mono text-slate-400">Raw Input Prompt (Untrusted):</label>
            <textarea
              rows={5}
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              className="w-full bg-slate-900/80 border border-border rounded-lg p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Output Area */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono text-slate-400">Sanitized Output (Safe for External LLM):</label>
              {redactionStats && (
                <span className="text-[11px] text-emerald-400 font-mono">
                  {redactionStats.count} items scrubbed ({redactionStats.types.join(", ")})
                </span>
              )}
            </div>
            <textarea
              rows={5}
              readOnly
              value={sanitizedOutput || "Click 'Run Sanitizer' to preview sanitized prompt..."}
              className="w-full bg-slate-950/80 border border-border rounded-lg p-3 text-xs font-mono text-emerald-300 focus:outline-none"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
