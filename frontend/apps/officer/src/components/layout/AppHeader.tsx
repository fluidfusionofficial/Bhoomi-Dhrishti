'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Search, X, MapPin } from 'lucide-react';
import { useRole } from '@/context/RoleContext';

export interface AppHeaderProps {
  onSearch?: (parcelId: string) => void;
  onGoHome?: () => void;
}

interface Suggestion {
  id: string;
  type: string;
  name: string;
  sub: string;
}

const DEMO_SUGGESTIONS: Suggestion[] = [
  {
    id: 'TN-607-001-042',
    type: 'PARCEL',
    name: 'Ag. Land — Kilpennathur Village',
    sub: 'Survey No. 42/1B · 0.82 ha',
  },
  {
    id: 'TN607001002422C',
    type: 'ULPIN',
    name: 'ULPIN Reference',
    sub: 'Linked to TN-607-001-043',
  },
  {
    id: 'TN-607-001-044',
    type: 'PARCEL',
    name: 'Residential Plot — Chengalpattu',
    sub: 'Survey No. 44/2 · 0.12 ha',
  },
];

export default function AppHeader({ onSearch, onGoHome }: AppHeaderProps) {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const { config } = useRole();

  const searchWrapperRef = useRef<HTMLDivElement>(null);

  const showSuggestions = isFocused && query.length >= 2;

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        searchWrapperRef.current &&
        !searchWrapperRef.current.contains(event.target as Node)
      ) {
        setIsFocused(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  function handleSuggestionClick(suggestion: Suggestion) {
    if (onSearch) onSearch(suggestion.id);
    setQuery('');
    setIsFocused(false);
  }

  function handleDemoClick() {
    alert('SIH Live Demo — 8 scripted scenarios available');
  }

  const filteredSuggestions = DEMO_SUGGESTIONS.filter(
    (s) =>
      s.id.toLowerCase().includes(query.toLowerCase()) ||
      s.name.toLowerCase().includes(query.toLowerCase()) ||
      s.sub.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <header
      style={{
        height: '64px',
        background: 'linear-gradient(180deg, #0b2447, #12315e)',
        zIndex: 1200,
        display: 'flex',
        alignItems: 'center',
        paddingLeft: '20px',
        paddingRight: '20px',
        gap: '16px',
        position: 'sticky',
        top: 0,
        width: '100%',
        boxSizing: 'border-box',
      }}
    >
      {/* LEFT: Brand — clickable to go home */}
      <div
        style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0, cursor: 'pointer' }}
        onClick={onGoHome}
        title="Go to Dashboard"
      >
        <div
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '9px',
            background: 'linear-gradient(135deg, #14a89a, #0f766e)',
            display: 'grid',
            placeItems: 'center',
            flexShrink: 0,
          }}
        >
          <MapPin size={24} color="white" />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
          <span
            style={{
              fontSize: '16.5px',
              fontWeight: 800,
              letterSpacing: '0.02em',
              color: 'white',
              lineHeight: 1.1,
              whiteSpace: 'nowrap',
            }}
          >
            BHOOMI DHRISHTI
          </span>
          <span
            style={{
              fontSize: '10.5px',
              color: '#aac4e8',
              lineHeight: 1.2,
              whiteSpace: 'nowrap',
            }}
          >
            Integrated GIS Land Governance · DoLR
          </span>
        </div>
      </div>

      {/* CENTER: Search */}
      <div
        style={{
          flex: 1,
          maxWidth: '520px',
          margin: '0 auto',
          position: 'relative',
        }}
        ref={searchWrapperRef}
      >
        <div style={{ position: 'relative', height: '40px' }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '13px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: isFocused ? '#9aa4b3' : '#b9cbe6',
              pointerEvents: 'none',
              zIndex: 1,
            }}
          />

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            placeholder="Search parcel ID, ULPIN, or village…"
            style={{
              width: '100%',
              height: '40px',
              borderRadius: '10px',
              border: `1.5px solid ${isFocused ? '#14a89a' : 'rgba(255,255,255,.18)'}`,
              background: isFocused ? 'white' : 'rgba(255,255,255,.10)',
              color: isFocused ? '#1f2733' : 'white',
              paddingLeft: '38px',
              paddingRight: query.length > 0 ? '36px' : '14px',
              fontSize: '13.5px',
              outline: 'none',
              boxSizing: 'border-box',
              transition: 'background 0.15s, border-color 0.15s, color 0.15s',
            }}
          />

          {query.length > 0 && (
            <button
              onClick={() => {
                setQuery('');
                setIsFocused(false);
              }}
              style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '2px',
                color: isFocused ? '#6b7280' : '#b9cbe6',
              }}
              tabIndex={-1}
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
        </div>

        {showSuggestions && (
          <div
            style={{
              position: 'absolute',
              top: '46px',
              left: 0,
              right: 0,
              background: 'white',
              borderRadius: '10px',
              boxShadow: '0 10px 40px rgba(0,0,0,0.18)',
              border: '1px solid #e3e8ef',
              zIndex: 1300,
              overflow: 'hidden',
            }}
          >
            {filteredSuggestions.length === 0 ? (
              <div
                style={{
                  padding: '12px 16px',
                  fontSize: '13px',
                  color: '#6b7280',
                }}
              >
                No results found
              </div>
            ) : (
              filteredSuggestions.map((suggestion, index) => (
                <button
                  key={suggestion.id}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    handleSuggestionClick(suggestion);
                  }}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '2px',
                    width: '100%',
                    padding: '10px 14px',
                    background: 'none',
                    border: 'none',
                    borderTop: index > 0 ? '1px solid #f1f5f9' : 'none',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.background = '#f8fafc';
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.background = 'none';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        fontFamily: 'monospace',
                        background: '#eef3fb',
                        color: '#1b4079',
                        fontSize: '11px',
                        padding: '1px 6px',
                        borderRadius: '4px',
                        fontWeight: 600,
                        letterSpacing: '0.04em',
                        flexShrink: 0,
                      }}
                    >
                      {suggestion.type}
                    </span>
                    <span
                      style={{
                        fontSize: '13px',
                        fontWeight: 600,
                        color: '#1f2733',
                      }}
                    >
                      {suggestion.name}
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: '11.5px',
                      color: '#6b7280',
                      paddingLeft: '2px',
                    }}
                  >
                    {suggestion.sub}
                  </span>
                </button>
              ))
            )}
          </div>
        )}
      </div>

      {/* RIGHT: Role Badge + Demo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        {/* Active Role Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(255,255,255,.10)',
            borderRadius: '10px',
            padding: '6px 14px',
            border: '1px solid rgba(255,255,255,.14)',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: config.color,
              flexShrink: 0,
              boxShadow: `0 0 6px ${config.color}80`,
            }}
          />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span
              style={{
                fontSize: '12px',
                fontWeight: 700,
                color: 'white',
                lineHeight: 1.2,
              }}
            >
              {config.title}
            </span>
            <span
              style={{
                fontSize: '10px',
                color: '#aac4e8',
                lineHeight: 1.2,
              }}
            >
              {config.subtitle}
            </span>
          </div>
        </div>

        {/* SIH Live Demo button */}
        <button
          onClick={handleDemoClick}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'linear-gradient(135deg, #14a89a, #0f766e)',
            color: 'white',
            fontWeight: 700,
            fontSize: '12.5px',
            border: 'none',
            borderRadius: '10px',
            padding: '9px 15px',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          <span
            className="bd-pulse"
            style={{
              display: 'inline-block',
              width: '6px',
              height: '6px',
              borderRadius: '9999px',
              background: '#baffef',
              flexShrink: 0,
            }}
          />
          SIH Live Demo
        </button>
      </div>
    </header>
  );
}
