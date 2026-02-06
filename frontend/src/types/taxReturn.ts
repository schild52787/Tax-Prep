export type FilingStatus = 'single' | 'married_filing_jointly';
export type ReturnStatus = 'in_progress' | 'completed';

export interface TaxReturn {
  id: string;
  return_name: string;
  tax_year: number;
  filing_status: FilingStatus;
  status: ReturnStatus;
  created_at: string;
  updated_at: string;
}

export interface TaxReturnCreate {
  return_name: string;
  tax_year?: number;
  filing_status?: FilingStatus;
}

export interface TaxReturnUpdate {
  return_name?: string;
  filing_status?: FilingStatus;
  status?: ReturnStatus;
}
