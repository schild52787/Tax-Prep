import { create } from 'zustand';
import type { TaxReturn } from '../types/taxReturn';
import type { CalculationResult } from '../types/calculation';

interface TaxReturnState {
  currentReturn: TaxReturn | null;
  calculation: CalculationResult | null;
  currentSection: string;
  setCurrentReturn: (r: TaxReturn | null) => void;
  setCalculation: (c: CalculationResult | null) => void;
  setCurrentSection: (section: string) => void;
}

export const useTaxReturnStore = create<TaxReturnState>((set) => ({
  currentReturn: null,
  calculation: null,
  currentSection: 'personal_info',
  setCurrentReturn: (r) => set({ currentReturn: r }),
  setCalculation: (c) => set({ calculation: c }),
  setCurrentSection: (section) => set({ currentSection: section }),
}));
