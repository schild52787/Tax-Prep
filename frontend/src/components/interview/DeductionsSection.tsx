import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../api/client';
import { formatCurrency } from '../../lib/utils';
import { ArrowLeft, ArrowRight } from 'lucide-react';

interface Props {
  returnId: string;
  onNext: () => void;
  onBack: () => void;
}

interface ItemizedForm {
  medical_expenses: number;
  state_income_tax_paid: number;
  real_estate_tax_paid: number;
  personal_property_tax: number;
  mortgage_interest_1098: number;
  mortgage_interest_not_1098: number;
  mortgage_points: number;
  investment_interest: number;
  cash_charitable: number;
  noncash_charitable: number;
  carryover_charitable: number;
  casualty_loss: number;
  other_deductions: number;
}

export function DeductionsSection({ returnId, onNext, onBack }: Props) {
  const [wantsItemized, setWantsItemized] = useState(false);
  const queryClient = useQueryClient();

  const { data: existing } = useQuery({
    queryKey: ['deductions', returnId],
    queryFn: async () => {
      try {
        const { data } = await api.get(`/returns/${returnId}/deductions`);
        return data;
      } catch {
        return null;
      }
    },
  });

  const { register, handleSubmit } = useForm<ItemizedForm>({
    values: existing ?? undefined,
  });

  const saveMutation = useMutation({
    mutationFn: (data: ItemizedForm) =>
      api.put(`/returns/${returnId}/deductions`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deductions', returnId] });
      onNext();
    },
  });

  // Standard deduction amounts for reference
  const standardDeduction = { single: 15750, mfj: 31500 };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-800 mb-1">Deductions</h2>
      <p className="text-sm text-gray-500 mb-6">
        Most taxpayers take the standard deduction. If your itemized deductions exceed the
        standard deduction, itemizing will save you money.
      </p>

      {/* Standard deduction info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-medium text-blue-800 text-sm">2025 Standard Deduction</h3>
        <div className="text-sm text-blue-700 mt-1">
          <span className="mr-6">Single: {formatCurrency(standardDeduction.single)}</span>
          <span>Married Filing Jointly: {formatCurrency(standardDeduction.mfj)}</span>
        </div>
        <p className="text-xs text-blue-600 mt-2">
          The tax engine will automatically compare and use whichever is larger.
        </p>
      </div>

      {/* Toggle */}
      <div className="mb-6">
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={wantsItemized}
            onChange={(e) => setWantsItemized(e.target.checked)}
            className="w-4 h-4 accent-accent"
          />
          <span className="text-sm font-medium text-gray-700">
            I want to enter itemized deductions
          </span>
        </label>
      </div>

      {wantsItemized && (
        <form onSubmit={handleSubmit((data) => saveMutation.mutate(data))} className="space-y-6">
          {/* Medical */}
          <fieldset className="bg-white border border-border rounded-lg p-4">
            <legend className="text-sm font-semibold text-gray-700 px-2">Medical and Dental Expenses</legend>
            <p className="text-xs text-gray-500 mb-3">Only the amount exceeding 7.5% of AGI is deductible.</p>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Total Medical Expenses</label>
              <input type="number" step="0.01" {...register('medical_expenses', { valueAsNumber: true })}
                className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
            </div>
          </fieldset>

          {/* SALT */}
          <fieldset className="bg-white border border-border rounded-lg p-4">
            <legend className="text-sm font-semibold text-gray-700 px-2">State and Local Taxes (SALT)</legend>
            <p className="text-xs text-gray-500 mb-3">Combined SALT deduction is capped at $40,000 for 2025.</p>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">State/Local Income Tax</label>
                <input type="number" step="0.01" {...register('state_income_tax_paid', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Real Estate Tax</label>
                <input type="number" step="0.01" {...register('real_estate_tax_paid', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Personal Property Tax</label>
                <input type="number" step="0.01" {...register('personal_property_tax', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
            </div>
          </fieldset>

          {/* Interest */}
          <fieldset className="bg-white border border-border rounded-lg p-4">
            <legend className="text-sm font-semibold text-gray-700 px-2">Interest You Paid</legend>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Mortgage Interest (Form 1098)</label>
                <input type="number" step="0.01" {...register('mortgage_interest_1098', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Mortgage Interest (not 1098)</label>
                <input type="number" step="0.01" {...register('mortgage_interest_not_1098', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Points Paid</label>
                <input type="number" step="0.01" {...register('mortgage_points', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Investment Interest</label>
                <input type="number" step="0.01" {...register('investment_interest', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
            </div>
          </fieldset>

          {/* Charitable */}
          <fieldset className="bg-white border border-border rounded-lg p-4">
            <legend className="text-sm font-semibold text-gray-700 px-2">Gifts to Charity</legend>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Cash/Check</label>
                <input type="number" step="0.01" {...register('cash_charitable', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Non-Cash</label>
                <input type="number" step="0.01" {...register('noncash_charitable', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Carryover</label>
                <input type="number" step="0.01" {...register('carryover_charitable', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
            </div>
          </fieldset>

          {/* Other */}
          <fieldset className="bg-white border border-border rounded-lg p-4">
            <legend className="text-sm font-semibold text-gray-700 px-2">Other</legend>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Casualty/Theft Losses</label>
                <input type="number" step="0.01" {...register('casualty_loss', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Other Deductions</label>
                <input type="number" step="0.01" {...register('other_deductions', { valueAsNumber: true })}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50" />
              </div>
            </div>
          </fieldset>

          <button
            type="submit"
            disabled={saveMutation.isPending}
            className="bg-accent text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-accent/90 disabled:opacity-50 transition-colors"
          >
            {saveMutation.isPending ? 'Saving...' : 'Save Deductions'}
          </button>
        </form>
      )}

      <div className="flex justify-between pt-6">
        <button onClick={onBack}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <button onClick={onNext}
          className="flex items-center gap-2 bg-accent text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors">
          Continue <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
