/**
 * @source Zustand v5 (client UI state only)
 * @invariant Server state managed by TanStack Query, never Zustand
 * @invariant Strict State Ownership Boundary (Playbook 00 + 07)
 * @invariant strictly < 150 lines
 */
import { create } from "zustand";

export interface Citation {
  document: string;
  page: number;
  chunk_id: string;
  relevance: number;
  snippet?: string;
}

export interface PdfViewerState {
  isOpen: boolean;
  documentId?: string;
  filename: string;
  pageNumber: number;
  chunkId?: string;
  highlightedText?: string;
}

export interface AuthUser {
  id: string;
  email?: string;
  name?: string;
  avatarUrl?: string;
}

export type DashboardTab = "chat" | "statements" | "comparison";
export type BackgroundTheme = "emerald" | "wallstreet" | "slate";
export type TypographyFont = "inter" | "outfit" | "roboto" | "mono";

interface FDISState {
  activeCitation: Citation | null;
  setActiveCitation: (citation: Citation | null) => void;

  pdfViewer: PdfViewerState;
  openPdfViewer: (state: Omit<PdfViewerState, "isOpen">) => void;
  closePdfViewer: () => void;

  currentUser: AuthUser | null;
  setCurrentUser: (user: AuthUser | null) => void;

  isAuthModalOpen: boolean;
  setAuthModalOpen: (open: boolean) => void;

  activeTab: DashboardTab;
  setActiveTab: (tab: DashboardTab) => void;

  activeBackground: BackgroundTheme;
  setActiveBackground: (bg: BackgroundTheme) => void;

  activeFont: TypographyFont;
  setActiveFont: (font: TypographyFont) => void;

  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;

  isUploadOpen: boolean;
  setUploadOpen: (open: boolean) => void;


  isExportModalOpen: boolean;
  setExportModalOpen: (open: boolean) => void;
}

export const useFDISStore = create<FDISState>((set) => ({
  activeCitation: null,
  setActiveCitation: (citation) => set({ activeCitation: citation }),

  pdfViewer: {
    isOpen: false,
    filename: "",
    pageNumber: 1,
  },
  openPdfViewer: (params) =>
    set({
      pdfViewer: { ...params, isOpen: true },
    }),
  closePdfViewer: () =>
    set((state) => ({
      pdfViewer: { ...state.pdfViewer, isOpen: false },
    })),

  currentUser: null,
  setCurrentUser: (user) => set({ currentUser: user }),

  isAuthModalOpen: false,
  setAuthModalOpen: (open) => set({ isAuthModalOpen: open }),

  activeTab: "chat",
  setActiveTab: (tab) => set({ activeTab: tab }),

  activeBackground: "emerald",
  setActiveBackground: (bg) => set({ activeBackground: bg }),

  activeFont: "inter",
  setActiveFont: (font) => set({ activeFont: font }),

  isSidebarCollapsed: false,
  toggleSidebar: () =>
    set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),

  isUploadOpen: false,
  setUploadOpen: (open) => set({ isUploadOpen: open }),


  isExportModalOpen: false,
  setExportModalOpen: (open) => set({ isExportModalOpen: open }),
}));
