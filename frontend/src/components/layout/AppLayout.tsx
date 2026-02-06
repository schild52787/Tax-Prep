import type { ReactNode } from 'react';
import { StepperNav } from './StepperNav';
import { TaxSummaryCard } from './TaxSummaryCard';
import { useInterviewStore, SECTIONS } from '../../stores/interviewStore';
import { useTaxReturnStore } from '../../stores/taxReturnStore';

interface Props {
  children: ReactNode;
  returnId: string;
  showSidebar?: boolean;
}

export function AppLayout({ children, returnId: _returnId, showSidebar = true }: Props) {
  const { activeSection, completedSections, setActiveSection } = useInterviewStore();
  const { currentReturn, calculation } = useTaxReturnStore();

  return (
    <div className="min-h-screen bg-surface">
      {/* Top bar */}
      <header className="bg-primary text-white px-6 py-3 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold tracking-tight">Tax Prep</h1>
          {currentReturn && (
            <span className="text-sm opacity-80">
              {currentReturn.return_name} ({currentReturn.tax_year})
            </span>
          )}
        </div>
        <a href="/" className="text-sm hover:underline opacity-80">
          Dashboard
        </a>
      </header>

      <div className="flex">
        {showSidebar && (
          <aside className="w-64 min-h-[calc(100vh-52px)] bg-white border-r border-border p-4 flex flex-col gap-4">
            <StepperNav
              sections={SECTIONS}
              activeSection={activeSection}
              completedSections={completedSections}
              onSelect={setActiveSection}
            />
            <div className="mt-auto">
              <TaxSummaryCard calculation={calculation} />
            </div>
          </aside>
        )}
        <main className="flex-1 p-6 max-w-4xl">{children}</main>
      </div>
    </div>
  );
}
