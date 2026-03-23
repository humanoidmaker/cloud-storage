import React from 'react';
const presets = [{ label: '1 GB', value: 1073741824 }, { label: '5 GB', value: 5368709120 }, { label: '10 GB', value: 10737418240 }, { label: '50 GB', value: 53687091200 }, { label: '100 GB', value: 107374182400 }, { label: 'Unlimited', value: 0 }];
interface QuotaSliderProps { value: number; onChange: (v: number) => void; }
export const QuotaSlider: React.FC<QuotaSliderProps> = ({ value, onChange }) => (
  <div data-testid="quota-slider">
    <div className="flex gap-2 flex-wrap">{presets.map((p) => (
      <button key={p.label} onClick={() => onChange(p.value)} className={`px-3 py-1 text-sm rounded-lg border ${value === p.value ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 text-gray-700 hover:bg-gray-50'}`}>{p.label}</button>
    ))}</div>
    <input type="range" min={0} max={107374182400} step={1073741824} value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full mt-2" />
    <p className="text-sm text-gray-500 mt-1">{value === 0 ? 'Unlimited' : `${(value / 1073741824).toFixed(0)} GB`}</p>
  </div>
);
