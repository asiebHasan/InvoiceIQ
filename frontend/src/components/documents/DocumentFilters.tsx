interface Props {
  filters: Record<string, string>;
  onChange: (filters: Record<string, string>) => void;
}

export default function DocumentFilters({ filters, onChange }: Props) {
  const set = (key: string, value: string) => {
    const next = { ...filters };
    if (value) next[key] = value;
    else delete next[key];
    onChange(next);
  };

  return (
    <div className="card p-4 flex flex-wrap gap-4">
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Type</label>
        <select
          value={filters.type || ''}
          onChange={(e) => set('type', e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">All Types</option>
          <option value="invoice">Invoice</option>
          <option value="receipt">Receipt</option>
          <option value="purchase_order">Purchase Order</option>
          <option value="bank_statement">Bank Statement</option>
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
        <select
          value={filters.status || ''}
          onChange={(e) => set('status', e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="processing">Processing</option>
          <option value="failed">Failed</option>
        </select>
      </div>
    </div>
  );
}
