import { create } from "zustand";
import { CitationItem } from "@/lib/api";

interface FDISState {
  selectedDocIds: string[];
  activeCitation: CitationItem | null;
  selectedModel: string;
  toggleSelectDoc: (id: string) => void;
  selectAllDocs: (allIds: string[]) => void;
  clearSelectedDocs: () => void;
  setActiveCitation: (cit: CitationItem | null) => void;
  setSelectedModel: (model: string) => void;
}

export const useFDISStore = create<FDISState>((set) => ({
  selectedDocIds: [],
  activeCitation: null,
  selectedModel: "groq/qwen3.8-27b",
  toggleSelectDoc: (id: string) =>
    set((state) => ({
      selectedDocIds: state.selectedDocIds.includes(id)
        ? state.selectedDocIds.filter((d) => d !== id)
        : [...state.selectedDocIds, id],
    })),
  selectAllDocs: (allIds: string[]) => set({ selectedDocIds: allIds }),
  clearSelectedDocs: () => set({ selectedDocIds: [] }),
  setActiveCitation: (cit: CitationItem | null) => set({ activeCitation: cit }),
  setSelectedModel: (model: string) => set({ selectedModel: model }),
}));
