import { useState } from 'react'
import ReplaceForm   from './components/ReplaceForm'
import GenerateForm  from './components/GenerateForm'
import PreviewPanel  from './components/PreviewPanel'

const TABS = [
  { id: 'replace',  label: '⛏ 블록 교체' },
  { id: 'generate', label: '🌍 지형 생성' },
  { id: 'preview',  label: '🗺 맵 미리보기' },
]

function ResultPanel({ result, loading }) {
  if (loading && !result) {
    return (
      <div className="result-panel loading">
        <span className="result-icon">⏳</span>
        <div>
          <div>처리 중입니다…</div>
          <div style={{ fontSize: '7px', marginTop: 6, color: '#666' }}>
            월드 크기에 따라 수 분이 걸릴 수 있습니다.
          </div>
        </div>
      </div>
    )
  }
  if (!result) return null

  const cls   = result.type === 'error' ? 'error' : result.type === 'dry' ? 'dry' : 'success'
  const icons = { success: '✅', dry: '🔍', error: '❌' }
  const icon  = icons[result.type] ?? '❓'

  return (
    <div className={`result-panel ${cls}`}>
      <span className="result-icon">{icon}</span>
      <div>
        {result.count != null && (
          <div className="result-count">{result.count.toLocaleString()} 블록</div>
        )}
        <div>{result.message}</div>
        {result.type === 'dry' && (
          <div style={{ fontSize: '7px', marginTop: 6, opacity: 0.7 }}>
            Dry-run 결과 — 저장은 되지 않았습니다.
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [worldPath, setWorldPath] = useState('')
  const [activeTab, setActiveTab] = useState('replace')
  const [result, setResult]       = useState(null)
  const [loading, setLoading]     = useState(false)

  const handleTabChange = (id) => {
    setActiveTab(id)
    setResult(null)
  }

  return (
    <div className="app">
      {/* ── Header ───────────────────────────────────────────── */}
      <header className="app-header">
        <h1>⛏ MINECRAFT MAP EDITOR</h1>
        <p>Java Edition · amulet-core powered</p>
      </header>

      {/* ── World path ───────────────────────────────────────── */}
      <div className="panel">
        <div className="world-path-bar">
          <label>🗂 월드 경로 (World Path)</label>
          <input
            type="text"
            value={worldPath}
            onChange={e => setWorldPath(e.target.value)}
            placeholder="C:\Users\...\AppData\Roaming\.minecraft\saves\MyWorld"
          />
        </div>
      </div>

      {/* ── Tabs ─────────────────────────────────────────────── */}
      <div className="tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn${activeTab === t.id ? ' active' : ''}`}
            onClick={() => handleTabChange(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Form panel ───────────────────────────────────────── */}
      <div className="panel">
        {activeTab === 'replace' && (
          <ReplaceForm
            worldPath={worldPath}
            onResult={setResult}
            onLoading={setLoading}
          />
        )}
        {activeTab === 'generate' && (
          <GenerateForm
            worldPath={worldPath}
            onResult={setResult}
            onLoading={setLoading}
          />
        )}
        {activeTab === 'preview' && (
          <PreviewPanel worldPath={worldPath} />
        )}
      </div>

      {/* ── Result (replace / generate only) ─────────────────── */}
      {activeTab !== 'preview' && (
        <ResultPanel result={result} loading={loading} />
      )}
    </div>
  )
}
