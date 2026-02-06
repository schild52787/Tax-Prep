import type { CalculationResult } from '../../types/calculation';
import { formatCurrency, formatPercent } from '../../lib/utils';

interface Props {
  calculation: CalculationResult | null;
}

export function TaxSummaryCard({ calculation }: Props) {
  if (!calculation) {
    return (
      <div className="bg-surface-dark rounded-lg p-4 text-center text-sm text-gray-500">
        Complete sections to see your tax summary
      </div>
    );
  }

  const isRefund = calculation.refund_amount > 0;

  return (
    <div className="bg-white border border-border rounded-lg p-4 space-y-3">
      <h3 className="text-xs font-semibold uppercase text-gray-400 tracking-wider">
        Estimated Result
      </h3>
      <div
        className={`text-2xl font-bold ${isRefund ? 'text-success' : 'text-danger'}`}
      >
        {isRefund
          ? `Refund: ${formatCurrency(calculation.refund_amount)}`
          : `Owed: ${formatCurrency(calculation.amount_owed)}`}
      </div>
      <div className="text-xs text-gray-500 space-y-1">
        <div className="flex justify-between">
          <span>Total Income</span>
          <span>{formatCurrency(calculation.total_income)}</span>
        </div>
        <div className="flex justify-between">
          <span>AGI</span>
          <span>{formatCurrency(calculation.agi)}</span>
        </div>
        <div className="flex justify-between">
          <span>Taxable Income</span>
          <span>{formatCurrency(calculation.taxable_income)}</span>
        </div>
        <div className="flex justify-between">
          <span>Total Tax</span>
          <span>{formatCurrency(calculation.total_tax)}</span>
        </div>
        <div className="flex justify-between">
          <span>Effective Rate</span>
          <span>{formatPercent(calculation.effective_tax_rate)}</span>
        </div>
      </div>
    </div>
  );
}
