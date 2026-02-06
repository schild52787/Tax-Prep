import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, ArrowRight, Plus, Trash2 } from 'lucide-react';
import api from '../../api/client';

interface Props {
  returnId: string;
  onNext: () => void;
  onBack: () => void;
}

interface DependentForm {
  first_name: string;
  last_name: string;
  relationship_to_taxpayer: string;
  date_of_birth: string;
  months_lived_with: number;
}

export function CreditsSection({ returnId, onNext, onBack }: Props) {
  const [showDepForm, setShowDepForm] = useState(false);
  const queryClient = useQueryClient();

  const { data: dependents = [] } = useQuery({
    queryKey: ['dependents', returnId],
    queryFn: async () => {
      const { data } = await api.get(`/returns/${returnId}/taxpayer/dependents`);
      return data;
    },
  });

  const { register, handleSubmit, reset } = useForm<DependentForm>();

  const addDepMutation = useMutation({
    mutationFn: (data: DependentForm) =>
      api.post(`/returns/${returnId}/taxpayer/dependents`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dependents', returnId] });
      setShowDepForm(false);
      reset();
    },
  });

  const deleteDepMutation = useMutation({
    mutationFn: (depId: string) =>
      api.delete(`/returns/${returnId}/taxpayer/dependents/${depId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dependents', returnId] }),
  });

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-800 mb-1">Credits</h2>
      <p className="text-sm text-gray-500 mb-6">
        Tax credits reduce your tax bill dollar-for-dollar. Start by adding any dependents
        who may qualify for the Child Tax Credit.
      </p>

      {/* Dependents */}
      <div className="mb-8">
        <h3 className="font-semibold text-gray-700 mb-3">Dependents</h3>
        <p className="text-xs text-gray-500 mb-3">
          Each qualifying child under 17 may qualify for a $2,200 Child Tax Credit.
        </p>

        {dependents.length > 0 && (
          <div className="space-y-2 mb-4">
            {dependents.map((dep: { id: string; first_name: string; last_name: string; relationship_to_taxpayer: string; date_of_birth: string }) => (
              <div key={dep.id} className="bg-white border border-border rounded-lg p-3 flex items-center justify-between">
                <div>
                  <span className="font-medium text-gray-800">{dep.first_name} {dep.last_name}</span>
                  <span className="text-sm text-gray-500 ml-2">
                    ({dep.relationship_to_taxpayer || 'Dependent'})
                    {dep.date_of_birth && ` - DOB: ${dep.date_of_birth}`}
                  </span>
                </div>
                <button
                  onClick={() => { if (confirm('Remove this dependent?')) deleteDepMutation.mutate(dep.id); }}
                  className="p-1 text-gray-400 hover:text-danger transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {!showDepForm ? (
          <button onClick={() => setShowDepForm(true)}
            className="flex items-center gap-2 border-2 border-dashed border-border rounded-lg px-4 py-3 w-full text-sm text-gray-500 hover:border-accent/30 hover:text-accent transition-colors">
            <Plus className="w-4 h-4" /> Add Dependent
          </button>
        ) : (
          <div className="bg-white border border-border rounded-lg p-4">
            <form onSubmit={handleSubmit((data) => addDepMutation.mutate(data))} className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                  <input {...register('first_name', { required: true })}
                    className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                  <input {...register('last_name', { required: true })}
                    className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Relationship</label>
                  <select {...register('relationship_to_taxpayer')}
                    className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50">
                    <option value="son">Son</option>
                    <option value="daughter">Daughter</option>
                    <option value="stepchild">Stepchild</option>
                    <option value="foster_child">Foster Child</option>
                    <option value="sibling">Sibling</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
                  <input type="date" {...register('date_of_birth')}
                    className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Months Lived With You</label>
                  <input type="number" min="0" max="12" defaultValue={12} {...register('months_lived_with', { valueAsNumber: true })}
                    className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
                </div>
              </div>
              <div className="flex gap-2">
                <button type="submit" disabled={addDepMutation.isPending}
                  className="bg-accent text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-accent/90 disabled:opacity-50 transition-colors">
                  {addDepMutation.isPending ? 'Saving...' : 'Add Dependent'}
                </button>
                <button type="button" onClick={() => { setShowDepForm(false); reset(); }}
                  className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition-colors">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* Education Credits info */}
      <div className="bg-white border border-border rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-gray-700 mb-2">Education Credits</h3>
        <p className="text-sm text-gray-500">
          American Opportunity Credit (up to $2,500) and Lifetime Learning Credit (up to $2,000)
          entry forms coming in a future update. The tax engine supports both credits.
        </p>
      </div>

      {/* Retirement savings credit info */}
      <div className="bg-white border border-border rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-gray-700 mb-2">Retirement Savings Credit</h3>
        <p className="text-sm text-gray-500">
          If you contributed to an IRA or employer retirement plan, you may qualify for the
          Saver's Credit. Entry forms coming in a future update.
        </p>
      </div>

      <div className="flex justify-between pt-6">
        <button onClick={onBack}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <button onClick={onNext}
          className="flex items-center gap-2 bg-accent text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors">
          Continue to Review <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
