import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getReturn } from '../api/returns';
import { useTaxReturnStore } from '../stores/taxReturnStore';
import { useInterviewStore } from '../stores/interviewStore';
import { AppLayout } from '../components/layout/AppLayout';
import { PersonalInfoSection } from '../components/interview/PersonalInfoSection';
import { IncomeSection } from '../components/interview/IncomeSection';
import { DeductionsSection } from '../components/interview/DeductionsSection';
import { CreditsSection } from '../components/interview/CreditsSection';

export function InterviewPage() {
  const { returnId } = useParams<{ returnId: string }>();
  const navigate = useNavigate();
  const { setCurrentReturn } = useTaxReturnStore();
  const { activeSection, setActiveSection, markComplete } = useInterviewStore();

  const { data: taxReturn, isLoading } = useQuery({
    queryKey: ['return', returnId],
    queryFn: () => getReturn(returnId!),
    enabled: !!returnId,
  });

  useEffect(() => {
    if (taxReturn) setCurrentReturn(taxReturn);
  }, [taxReturn, setCurrentReturn]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <p className="text-gray-500">Loading return...</p>
      </div>
    );
  }

  if (!taxReturn || !returnId) return null;

  const handleNext = (currentSection: string) => {
    const order = ['personal_info', 'income', 'deductions', 'credits', 'review'] as const;
    const idx = order.indexOf(currentSection as typeof order[number]);
    markComplete(currentSection as typeof order[number]);
    if (idx < order.length - 1) {
      setActiveSection(order[idx + 1]);
    } else {
      navigate(`/return/${returnId}/review`);
    }
  };

  const handleBack = () => {
    const order = ['personal_info', 'income', 'deductions', 'credits', 'review'] as const;
    const idx = order.indexOf(activeSection);
    if (idx > 0) setActiveSection(order[idx - 1]);
  };

  const renderSection = () => {
    switch (activeSection) {
      case 'personal_info':
        return <PersonalInfoSection returnId={returnId} onNext={() => handleNext('personal_info')} />;
      case 'income':
        return <IncomeSection returnId={returnId} onNext={() => handleNext('income')} onBack={handleBack} />;
      case 'deductions':
        return <DeductionsSection returnId={returnId} onNext={() => handleNext('deductions')} onBack={handleBack} />;
      case 'credits':
        return <CreditsSection returnId={returnId} onNext={() => handleNext('credits')} onBack={handleBack} />;
      case 'review':
        navigate(`/return/${returnId}/review`);
        return null;
      default:
        return null;
    }
  };

  return (
    <AppLayout returnId={returnId}>
      {renderSection()}
    </AppLayout>
  );
}
