import { create } from 'zustand';

interface AppState {
  isOffline: boolean;
  selectedSchoolId: number | null;
  selectedAcademicYear: string;
  notificationCount: number;
  setOffline: (offline: boolean) => void;
  setSelectedSchoolId: (id: number | null) => void;
  setAcademicYear: (year: string) => void;
  setNotificationCount: (count: number) => void;
  decrementNotifications: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  isOffline: false,
  selectedSchoolId: null,
  selectedAcademicYear: '2024-25',
  notificationCount: 0,

  setOffline: (offline) => set({ isOffline: offline }),
  setSelectedSchoolId: (id) => set({ selectedSchoolId: id }),
  setAcademicYear: (year) => set({ selectedAcademicYear: year }),
  setNotificationCount: (count) => set({ notificationCount: count }),
  decrementNotifications: () => {
    const current = get().notificationCount;
    set({ notificationCount: Math.max(0, current - 1) });
  },
}));
