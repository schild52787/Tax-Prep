import { ArrowLeft, ArrowRight } from 'lucide-react';

interface Props {
  returnId: string;
  onNext: () => void;
  onBack: () => void;
}

export function DeductionsSection({ returnId: _returnId, onNext, onBack }: Props) {
  return (
    <div>
      <h2 className="text-xl font-bold text-gray-800 mb-1">Deductions</h2>
      <p className="text-sm text-gray-500 mb-6">
        Enter your itemized deductions if applicable. The system will automatically compare
        your itemized deductions with the standard deduction and choose the larger amount.
      </p>

      <div className="bg-white rounded-lg border border-border p-6 text-center text-gray-500">
        <p>Deduction entry forms coming soon.</p>
        <p className="text-xs mt-2">
          Standard deduction will be applied automatically if you skip this section.
        </p>
      </div>

      <div className="flex justify-between pt-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <button
          onClick={onNext}
          className="flex items-center gap-2 bg-accent text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors"
        >
          Continue
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
