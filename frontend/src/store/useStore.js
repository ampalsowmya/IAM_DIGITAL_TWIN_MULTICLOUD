import { create } from "zustand";

export const useStore = create((set) => ({
  riskScores: [],
  graph: { nodes: [], edges: [] },
  escalationPaths: [],
  setRiskScores: (riskScores) => set({ riskScores }),
  setGraph: (graph) => set({ graph }),
  setEscalationPaths: (escalationPaths) => set({ escalationPaths }),
}));

