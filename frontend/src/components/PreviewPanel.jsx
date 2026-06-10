import { useState, useRef, useEffect } from 'react'

const DIMENSIONS = ['overworld', 'nether', 'end']
const CELL_PX    = 8   // pixels per chunk on the canvas

const LEGEND = [
  { label: '잔디', colour: '#5D9C3C' },
  { label: '돌',   colour: '#7F7F7F' },
  { label: '물',   colour: '#3D5BDE' },
  { label: '모래', colour: '#DDD074' },
  { label: '흙',   colour: '#8B5A2B' },
  { label: '나뭇잎', colour: '#3B7A2B' },
  { label: '눈',   colour: '#FFFFFF' },
  { label: '용암', colour: '#FF6600' },
  { label: '기반암', colour: '#1A1A1A' },
  { label: '미탐색', colour: '#0A0A0A' },
]

export default function PreviewPanel({ worldPath }) {
  const canvasRef = useRef(null)

  const [y, setY]             = useState(64)
  const [dimension, setDim]   = useState('overworld')
  const [size, setSize]       = useState(64)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)
  const [gridMeta, setGridMeta] = useState(null)   // { size, y } after last fetch

  const fetchPreview = async () => {
    if (!worldPath.trim()) {
      setError('월드 경로를 먼저 입력하세요.')
      return
    }
    setLoading(true)
    setError(null)
    setGridMeta(null)

    try {
      const params = new URLSearchParams({
        world: worldPath,
        y: String(y),
        dimension,
        size: String(size),
      })
      const res  = await fetch(`/api/preview?${params}`)
      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail ?? `HTTP ${res.status}`)
      }

      // Draw immediately after receiving data
      drawGrid(data.grid, data.size)
      setGridMeta({ size: data.size, y: data.y })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function drawGrid(grid, gridSize) {
    const canvas = canvasRef.current
    if (!canvas) return
    const canvasSide = gridSize * CELL_PX
    canvas.width  = canvasSide
    canvas.height = canvasSide
    const ctx = canvas.getContext('2d')

    for (let z = 0; z < gridSize; z++) {
      for (let x = 0; x < gridSize; x++) {
        ctx.fillStyle = grid[z][x]
        ctx.fillRect(x * CELL_PX, z * CELL_PX, CELL_PX, CELL_PX)
      }
    }

    // Faint chunk grid lines every 4 chunks
    ctx.strokeStyle = 'rgba(255,255,255,0.08)'
    ctx.lineWidth   = 0.5
    for (let i = 0; i <= gridSize; i += 4) {
      ctx.beginPath()
      ctx.moveTo(i * CELL_PX, 0)
      ctx.lineTo(i * CELL_PX, canvasSide)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(0, i * CELL_PX)
      ctx.lineTo(canvasSide, i * CELL_PX)
      ctx.stroke()
    }

    // Centre cross-hair
    const mid = (gridSize / 2) * CELL_PX
    ctx.strokeStyle = 'rgba(255,80,80,0.7)'
    ctx.lineWidth   = 1
    ctx.beginPath(); ctx.moveTo(mid - 6, mid); ctx.lineTo(mid + 6, mid); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(mid, mid - 6); ctx.lineTo(mid, mid + 6); ctx.stroke()
  }

  return (
    <div className="form">
      {/* Controls */}
      <div className="field-row">
        <div className="field">
          <label>Y 높이</label>
          <input
            type="number"
            value={y}
            onChange={e => setY(Number(e.target.value))}
            min={-64} max={320}
          />
        </div>
        <div className="field">
          <label>차원</label>
          <select value={dimension} onChange={e => setDim(e.target.value)}>
            {DIMENSIONS.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <div className="field">
          <label>그리드 크기 (청크)</label>
          <select value={size} onChange={e => setSize(Number(e.target.value))}>
            <option value={16}>16 × 16</option>
            <option value={32}>32 × 32</option>
            <option value={64}>64 × 64</option>
          </select>
        </div>
      </div>

      <button
        className="mc-btn full-width"
        onClick={fetchPreview}
        disabled={loading}
      >
        {loading ? '⏳ 로딩 중…' : '🗺 맵 미리보기'}
      </button>

      {/* Error */}
      {error && (
        <div className="result-panel error">
          <span className="result-icon">❌</span>
          <div>{error}</div>
        </div>
      )}

      {/* Canvas */}
      {(gridMeta || loading) && (
        <div className="preview-canvas-wrap">
          {gridMeta && (
            <div className="preview-meta">
              Y={gridMeta.y} · {gridMeta.size}×{gridMeta.size} 청크 · 중심=(0,0)
            </div>
          )}
          <div className="preview-canvas-scroll">
            <canvas
              ref={canvasRef}
              className="preview-canvas"
              style={{ imageRendering: 'pixelated' }}
            />
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="preview-legend">
        {LEGEND.map(({ label, colour }) => (
          <div key={label} className="legend-item">
            <span className="legend-swatch" style={{ background: colour }} />
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
