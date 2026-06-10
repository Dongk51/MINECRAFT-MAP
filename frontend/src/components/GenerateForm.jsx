import { useState } from 'react'

const DIMENSIONS = ['overworld', 'nether', 'end']

export default function GenerateForm({ worldPath, onResult, onLoading }) {
  const [genType, setGenType]         = useState('flat')
  const [block, setBlock]             = useState('minecraft:grass_block')
  const [height, setHeight]           = useState(64)
  const [baseHeight, setBaseHeight]   = useState(64)
  const [amplitude, setAmplitude]     = useState(20)
  const [scale, setScale]             = useState(100)
  const [dimension, setDim]           = useState('overworld')
  const [useRegion, setUseRegion]     = useState(false)
  const [x1, setX1] = useState(0)
  const [z1, setZ1] = useState(0)
  const [x2, setX2] = useState(256)
  const [z2, setZ2] = useState(256)
  const [dryRun, setDryRun]           = useState(false)
  const [busy, setBusy]               = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (!worldPath.trim()) {
      onResult({ type: 'error', message: '월드 경로를 먼저 입력하세요.' })
      return
    }
    setBusy(true)
    onLoading(true)
    onResult(null)

    const body = {
      world_path: worldPath,
      type: genType,
      block,
      dimension,
      dry_run: dryRun,
      region: useRegion
        ? { x1: Number(x1), z1: Number(z1), x2: Number(x2), z2: Number(z2) }
        : null,
      ...(genType === 'flat'
        ? { height: Number(height) }
        : { base_height: Number(baseHeight), amplitude: Number(amplitude), scale: Number(scale) }),
    }

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
      {/* Type selector */}
      <div className="field">
        <label>지형 타입</label>
        <select value={genType} onChange={e => setGenType(e.target.value)}>
          <option value="flat">🟩 평지 (Flat)</option>
          <option value="hills">⛰ 언덕 (Hills)</option>
        </select>
      </div>

      {/* Block */}
      <div className="field">
        <label>채울 블록</label>
        <input
          type="text"
          value={block}
          onChange={e => setBlock(e.target.value)}
          placeholder="minecraft:grass_block"
          required
        />
      </div>

      {/* Type-specific params */}
      {genType === 'flat' ? (
        <div className="field">
          <label>높이 (Height y)</label>
          <input
            type="number"
            value={height}
            onChange={e => setHeight(e.target.value)}
            min={-64} max={320}
          />
        </div>
      ) : (
        <div className="field-row">
          <div className="field">
            <label>기준 높이</label>
            <input type="number" value={baseHeight} onChange={e => setBaseHeight(e.target.value)} min={-64} max={320} />
          </div>
          <div className="field">
            <label>진폭</label>
            <input type="number" value={amplitude} onChange={e => setAmplitude(e.target.value)} min={1} max={200} />
          </div>
          <div className="field">
            <label>스케일</label>
            <input type="number" value={scale} onChange={e => setScale(e.target.value)} min={1} max={2000} />
          </div>
        </div>
      )}

      {/* Dimension */}
      <div className="field">
        <label>차원 (Dimension)</label>
        <select value={dimension} onChange={e => setDim(e.target.value)}>
          {DIMENSIONS.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>

      {/* Region toggle */}
      <div>
        <button
          type="button"
          className="region-toggle"
          onClick={() => setUseRegion(v => !v)}
        >
          {useRegion ? '▼ 영역 지정 ON' : '▶ 영역 지정 (선택)'}
        </button>

        {useRegion && (
          <div className="region-section" style={{ marginTop: 10 }}>
            <span className="region-label">📍 블록 좌표 (Block Coordinates)</span>
            <div className="field-row-4">
              {[['X1', x1, setX1], ['Z1', z1, setZ1], ['X2', x2, setX2], ['Z2', z2, setZ2]].map(
                ([lbl, val, set]) => (
                  <div key={lbl} className="field">
                    <label>{lbl}</label>
                    <input type="number" value={val} onChange={e => set(e.target.value)} />
                  </div>
                )
              )}
            </div>
          </div>
        )}
      </div>

      <label className="checkbox-row">
        <input type="checkbox" checked={dryRun} onChange={e => setDryRun(e.target.checked)} />
        <span>Dry-run (저장 없이 개수만 확인)</span>
      </label>

      <button type="submit" className="mc-btn full-width" disabled={busy}>
        {busy ? '⏳ 처리 중...' : '🌍 지형 생성 실행'}
      </button>
    </form>
  )
}
