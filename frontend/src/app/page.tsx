'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { DashboardStats, Document, TimelinePoint } from '@/lib/types';
import StatsCards from '@/components/dashboard/StatsCards';
import RecentDocuments from '@/components/dashboard/RecentDocuments';
import Charts from '@/components/dashboard/Charts';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recent, setRecent] = useState<Document[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getStats(), api.getRecent(), api.getTimeline()])
      .then(([s, r, t]) => {
        setStats(s);
        setRecent(r.documents);
        setTimeline(t.timeline);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-500">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      {stats && <StatsCards stats={stats} />}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Charts stats={stats} timeline={timeline} />
        <RecentDocuments documents={recent} />
      </div>
    </div>
  );
}
