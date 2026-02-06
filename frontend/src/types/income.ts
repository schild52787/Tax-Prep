export interface W2Income {
  id: string;
  return_id: string;
  employer_name: string | null;
  employer_ein: string | null;
  box_1_wages: number;
  box_2_fed_tax_withheld: number;
  box_3_ss_wages: number;
  box_4_ss_tax: number;
  box_5_medicare_wages: number;
  box_6_medicare_tax: number;
  state: string | null;
  state_wages: number;
  state_tax_withheld: number;
}

export interface Interest1099 {
  id: string;
  return_id: string;
  payer_name: string | null;
  box_1_interest: number;
  box_4_fed_tax_withheld: number;
}

export interface Dividend1099 {
  id: string;
  return_id: string;
  payer_name: string | null;
  box_1a_ordinary_dividends: number;
  box_1b_qualified_dividends: number;
  box_4_fed_tax_withheld: number;
}

export interface CapitalAssetSale {
  id: string;
  return_id: string;
  description: string | null;
  date_acquired: string | null;
  date_sold: string | null;
  proceeds: number;
  cost_basis: number;
  holding_period: 'short_term' | 'long_term' | null;
}
