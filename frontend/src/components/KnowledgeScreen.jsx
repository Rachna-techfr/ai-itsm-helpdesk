import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Search,
  Tag,
  CheckCircle2,
  AlertCircle,
  FileText,
  ChevronRight,
  Database,
  Cpu,
  Layers,
  Sparkles,
} from 'lucide-react';
import { fetchKnowledge, searchKnowledge } from '../api';

export default function KnowledgeScreen() {
  const [articles, setArticles] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await fetchKnowledge();
        setArticles(data);
        if (data.length > 0) setSelectedArticle(data[0]);
      } catch (err) {
        console.error('Failed to load KB articles:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      setSearching(true);
      const res = await searchKnowledge(searchQuery, 4);
      setSearchResults(res);
    } catch (err) {
      console.error('RAG Search error:', err);
    } finally {
      setSearching(false);
    }
  };

  const categories = ['All', 'Network', 'Identity', 'Collaboration', 'End User Computing', 'Software'];

  const filteredArticles = articles.filter((a) => {
    if (selectedCategory === 'All') return true;
    return a.category.toLowerCase().includes(selectedCategory.toLowerCase());
  });

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* HEADER WITH RAG VECTOR SEARCH TESTER */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.85rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BookOpen size={20} style={{ color: '#38bdf8' }} />
              Enterprise Knowledge Base & RAG Vector Engine
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Dense 384-dimensional embeddings (sentence-transformers/all-MiniLM-L6-v2) with Cosine Semantic Search.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.72rem', backgroundColor: '#0f291e', color: '#34d399', padding: '0.3rem 0.65rem', borderRadius: '9999px', border: '1px solid #05966940' }}>
              • {articles.length} IT Runbooks Indexed
            </span>
            <span style={{ fontSize: '0.72rem', backgroundColor: '#1e1b4b', color: '#a78bfa', padding: '0.3rem 0.65rem', borderRadius: '9999px', border: '1px solid #6366f140' }}>
              • Hallucination Threshold: 0.18
            </span>
          </div>
        </div>

        {/* Live RAG Vector Search Box */}
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.6rem' }}>
          <div style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '0.6rem 0.85rem',
          }}>
            <Search size={16} style={{ color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Test RAG Vector Search (e.g. 'How do I rebuild Outlook ost cache?' or 'VPN 809 error')..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ backgroundColor: 'transparent', border: 'none', outline: 'none', color: '#fff', fontSize: '0.85rem', width: '100%' }}
            />
          </div>
          <button
            type="submit"
            disabled={searching || !searchQuery.trim()}
            style={{
              backgroundColor: 'var(--accent-blue)',
              color: '#fff',
              border: 'none',
              padding: '0.6rem 1.25rem',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '0.82rem',
              cursor: searching ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <Sparkles size={14} />
            {searching ? 'Computing Embeddings...' : 'Semantic Search'}
          </button>
        </form>

        {/* RAG Search Results Drawer */}
        {searchResults && (
          <div style={{
            backgroundColor: 'var(--bg-card)',
            border: searchResults.knows ? '1px solid #3b82f660' : '1px solid #ef444460',
            borderRadius: '8px',
            padding: '0.85rem',
            marginTop: '0.35rem',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8' }}>
                  RETRIEVED VECTOR CHUNKS FOR:
                </span>
                <span style={{ fontSize: '0.75rem', color: '#fff', fontStyle: 'italic' }}>"{searchResults.query}"</span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  padding: '0.15rem 0.5rem',
                  borderRadius: '4px',
                  backgroundColor: searchResults.knows ? '#064e3b' : '#7f1d1d',
                  color: searchResults.knows ? '#34d399' : '#fca5a5',
                }}>
                  {searchResults.knows ? '✓ Grounded Match' : '⚠️ Insufficient KB Grounding (Safety Refusal)'}
                </span>
                <span style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 600 }}>
                  Confidence: {Math.round(searchResults.confidence * 100)}%
                </span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.6rem' }}>
              {searchResults.results.map((res, i) => (
                <div
                  key={i}
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    padding: '0.65rem',
                    borderRadius: '6px',
                    borderLeft: `3px solid ${res.score > 0.4 ? '#10b981' : '#f59e0b'}`,
                    fontSize: '0.75rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, color: '#38bdf8' }}>
                    <span>[{res.id}] {res.title}</span>
                    <span style={{ color: 'var(--text-muted)' }}>Score: {res.score}</span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', marginTop: '0.3rem', fontSize: '0.72rem' }}>
                    {res.excerpt}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* CATEGORY TABS */}
      <div style={{ display: 'flex', gap: '0.4rem', overflowX: 'auto', paddingBottom: '0.2rem' }}>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            style={{
              padding: '0.4rem 0.85rem',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              backgroundColor: selectedCategory === cat ? 'var(--accent-blue)' : 'var(--bg-secondary)',
              color: selectedCategory === cat ? '#fff' : 'var(--text-secondary)',
              fontSize: '0.78rem',
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* MAIN TWO-COLUMN CONTENT: ARTICLES LIST & RUNBOOK VIEWER */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '1.25rem' }}>
        {/* ARTICLE LIST */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', maxHeight: '600px', overflowY: 'auto' }}>
          {filteredArticles.map((art) => {
            const isSelected = selectedArticle?.id === art.id;
            return (
              <div
                key={art.id}
                onClick={() => setSelectedArticle(art)}
                style={{
                  backgroundColor: isSelected ? 'var(--bg-card-hover)' : 'var(--bg-secondary)',
                  border: isSelected ? '1px solid var(--accent-blue)' : '1px solid var(--border-color)',
                  borderRadius: '10px',
                  padding: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, color: '#38bdf8', fontSize: '0.82rem' }}>{art.id}</span>
                  <span style={{
                    fontSize: '0.68rem',
                    backgroundColor: '#1e293b',
                    color: '#94a3b8',
                    padding: '0.1rem 0.4rem',
                    borderRadius: '4px',
                  }}>
                    {art.category}
                  </span>
                </div>
                <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.85rem', marginTop: '0.3rem' }}>
                  {art.title}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '0.25rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {art.symptoms}
                </div>
              </div>
            );
          })}
        </div>

        {/* SELECTED ARTICLE DETAILED RUNBOOK */}
        {selectedArticle ? (
          <div style={{
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#38bdf8' }}>{selectedArticle.id}</span>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>• Owned by {selectedArticle.owner}</span>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>• Updated {selectedArticle.updated}</span>
              </div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>
                {selectedArticle.title}
              </h3>
            </div>

            {/* Symptoms */}
            <div style={{ backgroundColor: 'var(--bg-card)', padding: '0.85rem', borderRadius: '8px', borderLeft: '3px solid #f59e0b' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase' }}>
                Reported Symptoms & Diagnostics:
              </span>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                {selectedArticle.symptoms}
              </p>
            </div>

            {/* Step-by-Step Resolution Runbook */}
            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                Verified Standard Operating Procedure (SOP):
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', marginTop: '0.5rem' }}>
                {selectedArticle.steps?.map((st, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.6rem',
                      fontSize: '0.8rem',
                      backgroundColor: 'var(--bg-card)',
                      padding: '0.55rem 0.75rem',
                      borderRadius: '6px',
                    }}
                  >
                    <span style={{
                      backgroundColor: 'var(--accent-blue)',
                      color: '#fff',
                      width: 18,
                      height: 18,
                      borderRadius: '50%',
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}>
                      {i + 1}
                    </span>
                    <span style={{ color: '#fff' }}>{st}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Metadata Tags */}
            <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
              {selectedArticle.tags?.map((tg, i) => (
                <span
                  key={i}
                  style={{
                    fontSize: '0.7rem',
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-secondary)',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  #{tg}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            Select an article to view details
          </div>
        )}
      </div>
    </div>
  );
}

