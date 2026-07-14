import type { DashboardStats, TimelinePoint } from '@/lib/types';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const COLORS = ['#3b82f6', '#22c55e', '#a855f7', '#f97316', '#6b7280'];

export default function Charts({ stats, timeline }: { stats: DashboardStats | null; timeline: TimelinePoint[] }) {
  const typeData = stats
    ? Object.entries(stats.by_type).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Overview</h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-500 mb-2">By Document Type</p>
          {typeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={typeData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                  {typeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-gray-400 h-[200px] flex items-center justify-center">No data yet</p>
          )}
        </div>
        <div>
          <p className="text-sm text-gray-500 mb-2">Processing Timeline</p>
          {timeline.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-gray-400 h-[200px] flex items-center justify-center">No data yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
