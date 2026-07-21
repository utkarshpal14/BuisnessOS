import React from 'react';

export interface EvidenceItem {
  source: string;
  data_point: string;
}

interface EvidenceTrailProps {
  evidence: EvidenceItem[];
}

export const EvidenceTrail: React.FC<EvidenceTrailProps> = ({ evidence }) => {
  return (
    <div className="p-4 bg-gray-900 text-gray-100 rounded-lg border border-gray-800">
      <h4 className="font-semibold text-sm mb-2 text-indigo-400">Evidence Trail & Reasoning</h4>
      <ul className="space-y-1 text-xs">
        {evidence.map((item, idx) => (
          <li key={idx} className="flex gap-2">
            <span className="font-medium text-gray-400">[{item.source}]:</span>
            <span>{item.data_point}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};
