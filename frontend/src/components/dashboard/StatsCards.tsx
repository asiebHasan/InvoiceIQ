import type { DashboardStats } from '@/lib/types';

export default function StatsCards({ stats }: { stats: DashboardStats }) {
  const cards = [
    { label: 'Total Documents', value: stats.total_documents, color: 'text-brand-600' },
    { label: 'Processed', value: stats.processed_count, color: 'text-green-600' },
    { label: 'Processing', value: stats.processing_count, color: 'text-yellow-600' },
    { label: 'Failed', value: stats.failed_count, color: 'text-red-600' },
    { label: 'Anomalies', value: stats.anomaly_count, color: 'text-orange-600' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="card p-4">
          <p className="text-sm text-gray-500">{card.label}</p>
          <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
        </div>
      ))}
    </div>
  );
}
