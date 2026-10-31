import React, { createContext, useContext, useEffect, useState } from 'react';
import { Case } from '../types';
import { api } from '../services/api';

interface CaseContextType {
  cases: Case[];
  activeCaseId: string | null;
  activeCase: Case | null;
  loading: boolean;
  health: any;
  refreshCases: () => Promise<void>;
  setActiveCaseId: (id: string | null) => void;
}

const CaseContext = createContext<CaseContextType | undefined>(undefined);

export const CaseProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cases, setCases] = useState<Case[]>([]);
  const [activeCaseId, setActiveCaseIdState] = useState<string | null>(() => {
    return localStorage.getItem('text_detective_active_case') || null;
  });
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<any>(null);

  const refreshCases = async () => {
    try {
      const list = await api.listCases();
      setCases(list);
      if (list.length > 0 && !activeCaseId) {
        setActiveCaseIdState(list[0].case_id);
      }
    } catch (e) {
      console.error('Failed to load cases:', e);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const [h, list] = await Promise.all([
          api.getHealth().catch(() => null),
          api.listCases().catch(() => []),
        ]);
        setHealth(h);
        setCases(list);
        if (list.length > 0) {
          if (!activeCaseId || !list.some((c: Case) => c.case_id === activeCaseId)) {
            setActiveCaseIdState(list[0].case_id);
          }
        }
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const setActiveCaseId = (id: string | null) => {
    setActiveCaseIdState(id);
    if (id) {
      localStorage.setItem('text_detective_active_case', id);
    } else {
      localStorage.removeItem('text_detective_active_case');
    }
  };

  const activeCase = cases.find((c) => c.case_id === activeCaseId) || null;

  return (
    <CaseContext.Provider
      value={{
        cases,
        activeCaseId,
        activeCase,
        loading,
        health,
        refreshCases,
        setActiveCaseId,
      }}
    >
      {children}
    </CaseContext.Provider>
  );
};

export const useCase = () => {
  const context = useContext(CaseContext);
  if (!context) {
    throw new Error('useCase must be used within a CaseProvider');
  }
  return context;
};
