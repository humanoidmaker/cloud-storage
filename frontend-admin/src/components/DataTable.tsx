import React from 'react';
interface Column { key: string; label: string; render?: (v: unknown, row: Record<string, unknown>) => React.ReactNode; }
interface DataTableProps { columns: Column[]; data: Record<string, unknown>[]; onSort?: (key: string) => void; emptyMessage?: string; }
export const DataTable: React.FC<DataTableProps> = ({ columns, data, onSort, emptyMessage = 'No data' }) => (
  <div className="overflow-x-auto" data-testid="data-table">
    <table className="w-full text-sm">
      <thead><tr className="border-b border-gray-200 dark:border-gray-700">{columns.map((c) => (
        <th key={c.key} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => onSort?.(c.key)}>{c.label}</th>
      ))}</tr></thead>
      <tbody className="divide-y divide-gray-100 dark:divide-gray-800">{data.length === 0 ? (
        <tr><td colSpan={columns.length} className="px-4 py-8 text-center text-gray-500">{emptyMessage}</td></tr>
      ) : data.map((row, i) => (
        <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-800">{columns.map((c) => (
          <td key={c.key} className="px-4 py-3 text-gray-900 dark:text-white">{c.render ? c.render(row[c.key], row) : String(row[c.key] ?? '')}</td>
        ))}</tr>
      ))}</tbody>
    </table>
  </div>
);
