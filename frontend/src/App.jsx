import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatTab from './components/ChatTab';
import PolicyLibraryTab from './components/PolicyLibraryTab';
import AdminTab from './components/AdminTab';
import DeveloperTab from './components/DeveloperTab';
import { getHealth, getDocuments } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('assistant');
  const [health, setHealth] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [initialChatQuery, setInitialChatQuery] = useState('');

  const refreshData = async () => {
    try {
      const h = await getHealth();
      setHealth(h);
    } catch (e) {
      setHealth({ status: 'offline' });
    }

    try {
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (e) {
      console.warn("Could not fetch documents:", e);
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 20000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectPolicyForChat = (docName) => {
    setInitialChatQuery(`What are the primary regulations and disciplinary rules defined in ${docName}?`);
    setActiveTab('assistant');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800">
      <Header 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        health={health} 
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Student Interface */}
        {activeTab === 'assistant' && (
          <ChatTab 
            onDocumentView={() => setActiveTab('library')} 
            initialQuery={initialChatQuery}
          />
        )}
        {activeTab === 'library' && (
          <PolicyLibraryTab 
            documents={documents} 
            onSelectPolicyForChat={handleSelectPolicyForChat}
          />
        )}

        {/* Administrative Interface */}
        {activeTab === 'admin' && (
          <AdminTab 
            documents={documents} 
            onRefresh={refreshData} 
          />
        )}

        {/* Developer Interface */}
        {activeTab === 'developer' && (
          <DeveloperTab 
            health={health} 
            onRefreshHealth={refreshData}
          />
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-3 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-2">
          <div>
            PolicyPilot • University Policy Discovery Assistant • Evidence-Grounded RAG with Citations
          </div>
          <div className="flex items-center space-x-3 text-[11px]">
            <button
              onClick={() => setActiveTab('assistant')}
              className={`hover:text-slate-600 ${activeTab === 'assistant' ? 'font-semibold text-sky-600' : ''}`}
            >
              Policy Assistant
            </button>
            <span>•</span>
            <button
              onClick={() => setActiveTab('library')}
              className={`hover:text-slate-600 ${activeTab === 'library' ? 'font-semibold text-sky-600' : ''}`}
            >
              Policy Library
            </button>
            <span>•</span>
            <button
              onClick={() => setActiveTab('admin')}
              className={`hover:text-slate-600 ${activeTab === 'admin' ? 'font-semibold text-amber-600' : ''}`}
            >
              Admin [Proto]
            </button>
            <span>•</span>
            <button
              onClick={() => setActiveTab('developer')}
              className={`hover:text-slate-600 ${activeTab === 'developer' ? 'font-semibold text-indigo-600' : ''}`}
            >
              Developer Lab
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
