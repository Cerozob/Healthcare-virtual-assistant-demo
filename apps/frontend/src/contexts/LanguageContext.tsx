import React, { createContext, useContext, ReactNode } from 'react';
import { es, Translations } from '../i18n';

interface LanguageContextType {
  t: Translations;
  locale: string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

interface LanguageProviderProps {
  children: ReactNode;
}

export const LanguageProvider: React.FC<LanguageProviderProps> = ({ children }) => {
  // For now, we only support Spanish (Latin American)
  // In the future, this could be extended to support multiple languages
  const value: LanguageContextType = {
    t: es,
    locale: 'es-MX', // Latin American Spanish
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
