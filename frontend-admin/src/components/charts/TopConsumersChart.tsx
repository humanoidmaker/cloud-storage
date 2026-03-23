import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, BarChart, Bar, LineChart, Line } from 'recharts';

interface TopConsumersChartProps { data: Record<string, unknown>[]; }

export const TopConsumersChart: React.FC<TopConsumersChartProps> = ({ data }) => (
  <div className="h-64" data-testid="topconsumerschart">
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Area type="monotone" dataKey="value" stroke="#3B82F6" fill="#93C5FD" />
      </AreaChart>
    </ResponsiveContainer>
  </div>
);
