import { create } from 'zustand';

export type InterviewSection =
  | 'personal_info'
  | 'income'
  | 'deductions'
  | 'credits'
  | 'review';

export const SECTIONS: { id: InterviewSection; label: string }[] = [
  { id: 'personal_info', label: 'Personal Info' },
  { id: 'income', label: 'Income' },
  { id: 'deductions', label: 'Deductions' },
  { id: 'credits', label: 'Credits' },
  { id: 'review', label: 'Review & File' },
];

interface InterviewState {
  activeSection: InterviewSection;
  completedSections: Set<InterviewSection>;
  setActiveSection: (section: InterviewSection) => void;
  markComplete: (section: InterviewSection) => void;
  reset: () => void;
}

export const useInterviewStore = create<InterviewState>((set) => ({
  activeSection: 'personal_info',
  completedSections: new Set(),
  setActiveSection: (section) => set({ activeSection: section }),
  markComplete: (section) =>
    set((state) => ({
      completedSections: new Set([...state.completedSections, section]),
    })),
  reset: () =>
    set({ activeSection: 'personal_info', completedSections: new Set() }),
}));
