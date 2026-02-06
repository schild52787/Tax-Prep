import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getReturn } from '../api/returns';
import { runCalculation, getFormsPdfUrl, getSummaryPdfUrl } from '../api/calculations';
import { useTaxReturnStore } from '../stores/taxReturnStore';
import { AppLayout } from '../components/layout/AppLayout';
import { TaxSummaryCard } from '../components/layout/TaxSummaryCard';
import { formatCurrency, formatPercent } from '../lib/utils';
import { Download, Calculator, ArrowLeft } from 'lucide-react';

export function ReviewPage() {
  const { returnId } = useParams<{ returnId: string }>();
  const navigate = useNavigate();
  const { setCurrentReturn, calculation, setCalculation } = useTaxReturnStore();

  const { data: taxReturn } = useQuery({
    queryKey: ['return', returnId],
    queryFn: () => getReturn(returnId!),
    enabled: !!returnId,
  });

  useEffect(() => {
    if (taxReturn) setCurrentReturn(taxReturn);
  }, [taxReturn, setCurrentReturn]);

  const calcMutation = useMutation({
    mutationFn: () => runCalculation(returnId!),
    onSuccess: (data) => setCalculation(data),
  });

  if (!returnId) return null;

  return (
    <AppLayout returnId={returnId} showSidebar={false}>
      <div className="max-w-3xl mx-auto">
        <button
          onClick={() => navigate(`/return/${returnId}`)}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Interview
        </button>

        <h2 className="text-2xl font-bold text-gray-800 mb-6">Review & File</h2>

        {/* Calculate button */}
        <div className="bg-white rounded-lg border border-border p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-800">Calculate Your Taxes</h3>
              <p className="text-sm text-gray-500 mt-1">
                Run the tax engine to compute your return and see your refund or amount owed.
              </p>
            </div>
            <button
              onClick={() => calcMutation.mutate()}
              disabled={calcMutation.isPending}
              className="flex items-center gap-2 bg-accent text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-accent/90 disabled:opacity-50 transition-colors"
            >
              <Calculator className="w-4 h-4" />
              {calcMutation.isPending ? 'Calculating...' : 'Calculate'}
            </button>
          </div>
        </div>

        {calcMutation.isError && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6 text-sm">
            Error calculating taxes. Make sure you have entered all required information.
          </div>
        )}

        {calculation && (
          <>
            {/* Result card */}
            <div className="mb-6">
              <TaxSummaryCard calculation={calculation} />
            </div>

            {/* Detailed breakdown */}
            <div className="bg-white rounded-lg border border-border p-6 mb-6">
              <h3 className="font-semibold text-gray-800 mb-4">Tax Breakdown</h3>
              <div className="space-y-2 text-sm">
                <Row label="Total Income" value={formatCurrency(calculation.total_income)} />
                <Row label="Adjusted Gross Income (AGI)" value={formatCurrency(calculation.agi)} />
                <hr className="border-border" />
                <Row
                  label={`Deduction (${calculation.deduction_method === 'itemized' ? 'Itemized' : 'Standard'})`}
                  value={
                    calculation.deduction_method === 'itemized'
                      ? formatCurrency(calculation.itemized_deduction_amount)
                      : formatCurrency(calculation.standard_deduction_amount)
                  }
                />
                <Row label="Taxable Income" value={formatCurrency(calculation.taxable_income)} bold />
                <hr className="border-border" />
                <Row label="Tax" value={formatCurrency(calculation.total_tax)} />
                <Row label="Credits" value={formatCurrency(calculation.total_credits)} />
                <Row label="Total Payments" value={formatCurrency(calculation.total_payments)} />
                <hr className="border-border" />
                {calculation.refund_amount > 0 && (
                  <Row label="Refund" value={formatCurrency(calculation.refund_amount)} bold className="text-success" />
                )}
                {calculation.amount_owed > 0 && (
                  <Row label="Amount Owed" value={formatCurrency(calculation.amount_owed)} bold className="text-danger" />
                )}
                <hr className="border-border" />
                <Row label="Effective Tax Rate" value={formatPercent(calculation.effective_tax_rate)} />
                <Row label="Marginal Tax Rate" value={formatPercent(calculation.marginal_tax_rate)} />
              </div>
            </div>

            {/* Download buttons */}
            <div className="bg-white rounded-lg border border-border p-6">
              <h3 className="font-semibold text-gray-800 mb-4">Download Your Return</h3>
              <div className="flex gap-3">
                <a
                  href={getSummaryPdfUrl(returnId)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 bg-accent text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Summary Report
                </a>
                <a
                  href={getFormsPdfUrl(returnId)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 bg-primary text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-primary-light transition-colors"
                >
                  <Download className="w-4 h-4" />
                  IRS Forms (PDF)
                </a>
              </div>
              <p className="text-xs text-gray-400 mt-3">
                IRS forms require templates. Run scripts/download_irs_templates.py if not available.
              </p>
            </div>
          </>
        )}
      </div>
    </AppLayout>
  );
}

function Row({ label, value, bold, className }: { label: string; value: string; bold?: boolean; className?: string }) {
  return (
    <div className={`flex justify-between ${bold ? 'font-semibold' : ''} ${className ?? ''}`}>
      <span className="text-gray-600">{label}</span>
      <span>{value}</span>
    </div>
  );
}
