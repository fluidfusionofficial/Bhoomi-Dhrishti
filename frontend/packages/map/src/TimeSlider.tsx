'use client';

import * as React from 'react';

export interface TimelineEvent {
  timestamp: string;
  label: string;
  data: any;
}

export interface TimeSliderProps {
  events: TimelineEvent[];
  onEventChange?: (event: TimelineEvent, index: number) => void;
  className?: string;
}

export function TimeSlider({ events, onEventChange, className = '' }: TimeSliderProps) {
  const [currentIndex, setCurrentIndex] = React.useState(events.length - 1);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const index = parseInt(e.target.value);
    setCurrentIndex(index);
    if (onEventChange) {
      onEventChange(events[index], index);
    }
  };

  if (events.length === 0) return null;

  const currentEvent = events[currentIndex];
  const formattedDate = new Date(currentEvent.timestamp).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  return (
    <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
      <div className="mb-2 flex justify-between items-center">
        <span className="text-sm font-medium text-neutral-700">{currentEvent.label}</span>
        <span className="text-xs text-neutral-500">{formattedDate}</span>
      </div>

      <input
        type="range"
        min="0"
        max={events.length - 1}
        value={currentIndex}
        onChange={handleSliderChange}
        className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-[#1B4F72]"
      />

      <div className="mt-2 flex justify-between text-xs text-neutral-500">
        <span>{new Date(events[0].timestamp).getFullYear()}</span>
        <span>{new Date(events[events.length - 1].timestamp).getFullYear()}</span>
      </div>
    </div>
  );
}
