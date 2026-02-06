import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listReturns, createReturn, deleteReturn } from '../api/returns';
import type { FilingStatus } from '../types/taxReturn';
import { Plus, Trash2, FileText } from 'lucide-react';

export function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [filingStatus, setFilingStatus] = useState<FilingStatus>('single');

  const { data: returns = [], isLoading } = useQuery({
    queryKey: ['returns'],
    queryFn: listReturns,
  });

  const createMutation = useMutation({
    mutationFn: () => createReturn({ return_name: name, filing_status: filingStatus }),
    onSuccess: (newReturn) => {
      queryClient.invalidateQueries({ queryKey: ['returns'] });
      setShowCreate(false);
      setName('');
      navigate(`/return/${newReturn.id}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteReturn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['returns'] }),
  });

  return (
    <div className="min-h-screen bg-surface">
      <header className="bg-primary text-white px-6 py-4">
        <h1 className="text-xl font-semibold">Tax Prep - 2025 Federal Tax Return</h1>
        <p className="text-sm opacity-80 mt-1">Prepare and file your individual Form 1040</p>
      </header>

      <div className="max-w-3xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-800">Your Tax Returns</h2>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 bg-accent text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Return
          </button>
        </div>

        {showCreate && (
          <div className="bg-white rounded-lg border border-border p-4 mb-6">
            <h3 className="font-medium mb-3">Create New Return</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Return Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., My 2025 Tax Return"
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Filing Status</label>
                <select
                  value={filingStatus}
                  onChange={(e) => setFilingStatus(e.target.value as FilingStatus)}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                >
                  <option value="single">Single</option>
                  <option value="married_filing_jointly">Married Filing Jointly</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => createMutation.mutate()}
                  disabled={!name.trim() || createMutation.isPending}
                  className="bg-accent text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-accent/90 disabled:opacity-50 transition-colors"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create'}
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : returns.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-border">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No tax returns yet. Create one to get started.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {returns.map((ret) => (
              <div
                key={ret.id}
                className="bg-white rounded-lg border border-border p-4 flex items-center justify-between hover:border-accent/30 transition-colors"
              >
                <button
                  onClick={() => navigate(`/return/${ret.id}`)}
                  className="flex-1 text-left"
                >
                  <div className="font-medium text-gray-800">{ret.return_name}</div>
                  <div className="text-sm text-gray-500 mt-0.5">
                    {ret.filing_status === 'married_filing_jointly'
                      ? 'Married Filing Jointly'
                      : 'Single'}
                    {' - '}
                    {ret.status === 'completed' ? (
                      <span className="text-success">Completed</span>
                    ) : (
                      <span className="text-warning">In Progress</span>
                    )}
                    {' - Created '}
                    {new Date(ret.created_at).toLocaleDateString()}
                  </div>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Delete this return?')) deleteMutation.mutate(ret.id);
                  }}
                  className="p-2 text-gray-400 hover:text-danger transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
