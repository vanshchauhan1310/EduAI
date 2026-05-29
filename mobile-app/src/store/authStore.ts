import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { AuthUser, AuthTokens } from '../types';
import { TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY } from '../constants';

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (tokens: AuthTokens) => Promise<void>;
  clearAuth: () => Promise<void>;
  loadStoredAuth: () => Promise<void>;
  updateUser: (user: Partial<AuthUser>) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,

  setAuth: async (tokens: AuthTokens) => {
    await SecureStore.setItemAsync(TOKEN_KEY, tokens.access_token);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, tokens.refresh_token);
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(tokens.user));
    set({
      user: tokens.user,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      isAuthenticated: true,
    });
  },

  clearAuth: async () => {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);
    set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
  },

  loadStoredAuth: async () => {
    try {
      const token = await SecureStore.getItemAsync(TOKEN_KEY);
      const refresh = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
      const userJson = await SecureStore.getItemAsync(USER_KEY);

      if (token && refresh && userJson) {
        const user = JSON.parse(userJson) as AuthUser;
        set({ user, accessToken: token, refreshToken: refresh, isAuthenticated: true });
      }
    } catch {
      // Stored auth is invalid, start fresh
    } finally {
      set({ isLoading: false });
    }
  },

  updateUser: (updates: Partial<AuthUser>) => {
    const current = get().user;
    if (current) {
      set({ user: { ...current, ...updates } });
    }
  },
}));
