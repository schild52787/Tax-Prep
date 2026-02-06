export interface CalculationResult {
  id: string;
  return_id: string;
  calculated_at: string;
  total_income: number;
  agi: number;
  taxable_income: number;
  total_tax: number;
  total_credits: number;
  total_payments: number;
  refund_amount: number;
  amount_owed: number;
  effective_tax_rate: number;
  marginal_tax_rate: number;
  standard_deduction_amount: number;
  itemized_deduction_amount: number;
  deduction_method: string | null;
  form_results: Record<string, Record<string, number>> | null;
  required_forms: string[] | null;
  errors: string[] | null;
  warnings: string[] | null;
}
