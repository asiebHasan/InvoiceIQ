import type { Anomaly } from '@/lib/types';
import { anomalySeverityColor } from '@/lib/utils';

export default function AnomalyBadge({ anomaly }: { anomaly: Anomaly }) {
  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${anomalySeverityColor(anomaly.severity)}`}>
      <span className="text-lg shrink-0">
        {anomaly.severity === 'critical' ? '🔴' : anomaly.severity === 'high' ? '🟠' : anomaly.severity === 'medium' ? '🟡' : '🔵'}
      </span>
      <div>
        <p className="text-sm font-medium">{anomaly.description}</p>
        <p className="text-xs opacity-75 mt-0.5">{anomaly.anomaly_type.replace(/_/g, ' ')}</p>
      </div>
    </div>
  );
}
