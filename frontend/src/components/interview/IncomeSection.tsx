import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listW2s, createW2, deleteW2 } from '../../api/income';
import { useForm } from 'react-hook-form';
import { Plus, Trash2, ArrowLeft, ArrowRight } from 'lucide-react';
import { DocumentUploader } from './DocumentUploader';

interface Props {
  returnId: string;
  onNext: () => void;
  onBack: () => void;
}

interface W2Form {
  employer_name: string;
  employer_ein: string;
  box_1_wages: number;
  box_2_fed_tax_withheld: number;
  box_3_ss_wages: number;
  box_4_ss_tax: number;
  box_5_medicare_wages: number;
  box_6_medicare_tax: number;
  state: string;
  state_wages: number;
  state_tax_withheld: number;
}

export function IncomeSection({ returnId, onNext, onBack }: Props) {
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  const { data: w2s = [] } = useQuery({
    queryKey: ['w2s', returnId],
    queryFn: () => listW2s(returnId),
  });

  const { register, handleSubmit, reset } = useForm<W2Form>();

  const createMutation = useMutation({
    mutationFn: (data: W2Form) => createW2(returnId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['w2s', returnId] });
      setShowForm(false);
      reset();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (w2Id: string) => deleteW2(returnId, w2Id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['w2s', returnId] }),
  });

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-800 mb-1">Income</h2>
      <p className="text-sm text-gray-500 mb-6">
        Enter your W-2 wage statements from each employer, or upload a PDF to auto-extract.
      </p>

      {/* Document Upload */}
      <div className="mb-6 bg-surface-dark rounded-lg p-4">
        <DocumentUploader returnId={returnId} />
      </div>

      {/* Existing W-2s */}
      {w2s.length > 0 && (
        <div className="space-y-3 mb-6">
          {w2s.map((w2) => (
            <div
              key={w2.id}
              className="bg-white border border-border rounded-lg p-4 flex items-center justify-between"
            >
              <div>
                <div className="font-medium text-gray-800">
                  {w2.employer_name || 'Unnamed Employer'}
                </div>
                <div className="text-sm text-gray-500 mt-0.5">
                  Wages: ${w2.box_1_wages.toLocaleString()} | Withheld: ${w2.box_2_fed_tax_withheld.toLocaleString()}
                </div>
              </div>
              <button
                onClick={() => {
                  if (confirm('Delete this W-2?')) deleteMutation.mutate(w2.id);
                }}
                className="p-2 text-gray-400 hover:text-danger transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {!showForm ? (
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 border-2 border-dashed border-border rounded-lg px-4 py-3 w-full text-sm text-gray-500 hover:border-accent/30 hover:text-accent transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add W-2
        </button>
      ) : (
        <div className="bg-white border border-border rounded-lg p-4">
          <h3 className="font-medium mb-3">New W-2</h3>
          <form
            onSubmit={handleSubmit((data) => createMutation.mutate(data))}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Employer Name</label>
                <input
                  {...register('employer_name')}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Employer EIN</label>
                <input
                  {...register('employer_ein')}
                  placeholder="XX-XXXXXXX"
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Box 1 - Wages *</label>
                <input
                  type="number"
                  step="0.01"
                  {...register('box_1_wages', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Box 2 - Federal Tax Withheld</label>
                <input
                  type="number"
                  step="0.01"
                  {...register('box_2_fed_tax_withheld', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Box 3 - SS Wages</label>
                <input
                  type="number"
                  step="0.01"
                  {...register('box_3_ss_wages', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Box 4 - SS Tax Withheld</label>
                <input
                  type="number"
                  step="0.01"
                  {...register('box_4_ss_tax', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Box 5 - Medicare Wages</label>
                <input
                  type="number"
                  step="0.01"
                  {...register('box_5_medicare_wages', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Box 6 - Medicare Tax</label>
                <input
                  type="number"
                  step="0.01"
                  {...register('box_6_medicare_tax', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                <input
                  {...register('state')}
                  maxLength={2}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State Wages</label>
                <input
                  type="number"
                  step="0.01"
                  {...register('state_wages', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State Tax Withheld</label>
                <input
                  type="number"
                  step="0.01"
                  {...register('state_tax_withheld', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>

            <div className="flex gap-2">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="bg-accent text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-accent/90 disabled:opacity-50 transition-colors"
              >
                {createMutation.isPending ? 'Saving...' : 'Save W-2'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  reset();
                }}
                className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <button
          onClick={onNext}
          className="flex items-center gap-2 bg-accent text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors"
        >
          Continue
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
