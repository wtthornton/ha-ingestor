/**
 * Global State Management with Zustand
 */

import { create } from 'zustand';
import type { Suggestion, ScheduleInfo, AnalysisStatus } from './types';

interface AppState {
  // Suggestions
  suggestions: Suggestion[];
  setSuggestions: (suggestions: Suggestion[]) => void;
  
  // Schedule
  scheduleInfo: ScheduleInfo | null;
  setScheduleInfo: (info: ScheduleInfo | null) => void;
  
  // Analysis Status
  analysisStatus: AnalysisStatus | null;
  setAnalysisStatus: (status: AnalysisStatus | null) => void;
  
  // UI State
  darkMode: boolean;
  toggleDarkMode: () => void;
  
  selectedStatus: 'pending' | 'approved' | 'rejected' | 'deployed';
  setSelectedStatus: (status: 'pending' | 'approved' | 'rejected' | 'deployed') => void;
  
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Suggestions
  suggestions: [],
  setSuggestions: (suggestions) => set({ suggestions }),
  
  // Schedule
  scheduleInfo: null,
  setScheduleInfo: (info) => set({ scheduleInfo: info }),
  
  // Analysis Status
  analysisStatus: null,
  setAnalysisStatus: (status) => set({ analysisStatus: status }),
  
  // UI State
  darkMode: localStorage.getItem('darkMode') === 'true',
  toggleDarkMode: () => set((state) => {
    const newDarkMode = !state.darkMode;
    localStorage.setItem('darkMode', String(newDarkMode));
    return { darkMode: newDarkMode };
  }),
  
  selectedStatus: 'pending',
  setSelectedStatus: (status) => set({ selectedStatus: status }),
  
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
}));

