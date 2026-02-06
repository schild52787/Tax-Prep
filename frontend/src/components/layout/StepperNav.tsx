import { cn } from '../../lib/utils';
import type { InterviewSection } from '../../stores/interviewStore';
import { CheckCircle2, Circle } from 'lucide-react';

interface Props {
  sections: { id: InterviewSection; label: string }[];
  activeSection: InterviewSection;
  completedSections: Set<InterviewSection>;
  onSelect: (section: InterviewSection) => void;
}

export function StepperNav({ sections, activeSection, completedSections, onSelect }: Props) {
  return (
    <nav className="flex flex-col gap-1">
      {sections.map((section, idx) => {
        const isActive = section.id === activeSection;
        const isCompleted = completedSections.has(section.id);

        return (
          <button
            key={section.id}
            onClick={() => onSelect(section.id)}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left',
              isActive
                ? 'bg-accent/10 text-accent'
                : isCompleted
                  ? 'text-success hover:bg-gray-50'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
            )}
          >
            <span className="flex-shrink-0">
              {isCompleted ? (
                <CheckCircle2 className="w-5 h-5 text-success" />
              ) : (
                <Circle
                  className={cn('w-5 h-5', isActive ? 'text-accent' : 'text-gray-300')}
                />
              )}
            </span>
            <span>
              {idx + 1}. {section.label}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
