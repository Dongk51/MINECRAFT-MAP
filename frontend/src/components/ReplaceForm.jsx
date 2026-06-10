import { useState } from 'react'

const DIMENSIONS = ['overworld', 'nether', 'end']

export default function ReplaceForm({ worldPath, onResult, onLoading }) {
  const [source, setSource]     = useState('minecraft:stone')
  const [target, setTarget]     = useState('minecraft:diamond_block')
  const [dimension, setDim]     = useState('overworld')
  const [dryRun, setDryRun]     = useState(false)
  const [busy, setBusy]         = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (!worldPath.trim()) {
      onResult({ type: 'error', message: '월드 경로를 먼저 입력하세요.' })
      return
    }
    setBusy(true)
    onLoading(true)
    onResult(null)
    try {
      const res = await fetch('/api/replace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          world_path: worldPath,
          source,
          target,
          dimension,
          dry_run: dryRun,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Unknown error')
      onResult({ type: dryRun ? 'dry' : 'success', message: data.message, count: data.count })
    } catch (err) {
      onResult({ type: 'error', message: err.message })
    } finally {
      setBusy(false)
      onLoading(false)
    }
  }

  return (
    <form className="form" onSubmit={submit}>
      <div className="field">
        <label>교체할 블록 (Source)</label>
        <input
          type="text"
          value={source}
          onChange={e => setSource(e.target.value)}
          placeholder="minecraft:stone"
          required
        />
      </div>

      <div className="field">
        <label>대체 블록 (Target)</label>
        <input
          type="text"
          value={target}
          onChange={e => setTarget(e.target.value)}
          placeholder="minecraft:diamond_block"
          required
        />
      </div>

      <div className="field">
        <label>차원 (Dimension)</label>
        <select value={dimension} onChange={e => setDim(e.target.value)}>
          {DIMENSIONS.map(d => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      <label className="checkbox-row">
        <input type="checkbox" checked={dryRun} onChange={e => setDryRun(e.target.checked)} />
        <span>Dry-run (저장 없이 개수만 확인)</span>
      </label>

      <button type="submit" className="mc-btn full-width" disabled={busy}>
        {busy ? '⏳ 처리 중...' : '⛏ 블록 교체 실행'}
      </button>
    </form>
  )
}
