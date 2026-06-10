# ⛏ Minecraft Map Editor

> Minecraft Java Edition 월드 파일을 웹 GUI로 편집하는 풀스택 도구  
> A full-stack tool for editing Minecraft Java Edition world files via a web GUI

<!-- TODO: replace with real screenshot after deploy -->
<!-- ![screenshot](docs/screenshot.png) -->

**[🚀 Live Demo](#)** · **[📖 API Docs](http://localhost:8000/docs)**

---

## 한국어

### 소개

마인크래프트 Java Edition 월드 파일(`.minecraft/saves/…`)을 직접 파싱해  
**블록 교체**와 **지형 자동 생성**을 브라우저에서 수행할 수 있는 풀스택 웹 에디터입니다.  
기존 CLI 도구를 FastAPI 백엔드로 감싸고, React+Vite 프론트엔드로 시각화했습니다.

### 주요 기능

| 기능 | 설명 |
|------|------|
| **블록 교체** | 월드 전체 또는 특정 차원에서 A 블록 → B 블록 일괄 교체 |
| **평지 지형** | 지정 높이까지 단일 블록으로 모든 컬럼 채우기 |
| **언덕 지형** | OpenSimplex 노이즈 기반 자연스러운 언덕 지형 생성 |
| **영역 지정** | (x1,z1)~(x2,z2) 좌표로 작업 범위 제한 |
| **Dry-run** | 실제 저장 없이 처리될 블록 수 미리 확인 |
| **Web GUI** | 마인크래프트 픽셀 테마의 React 브라우저 UI |

### 기술 스택

| 레이어 | 기술 |
|--------|------|
| Backend | Python 3.11 · FastAPI · uvicorn |
| Frontend | React 18 · Vite 5 · CSS (Press Start 2P) |
| 월드 파싱 | amulet-core 1.9 |
| 노이즈 | opensimplex 0.4 |
| 배포 | Railway (단일 서버 — FastAPI가 빌드된 React 정적 파일 서빙) |

---

## English

### Overview

A full-stack web editor that parses Minecraft Java Edition world files and applies
**block replacement** and **terrain generation** directly through a browser UI.
The existing Python CLI modules are wrapped with a FastAPI backend and a React+Vite frontend.

### Features

- **Block Replace** — swap block A with block B across an entire dimension or a custom region  
- **Flat Terrain** — fill every column up to a fixed Y with any block  
- **Hills Terrain** — noise-based height map using OpenSimplex for natural-looking hills  
- **Region filter** — constrain operations to an (x1,z1)→(x2,z2) bounding box  
- **Dry-run mode** — count affected blocks without writing to disk  
- **Minecraft-themed UI** — pixel-font React interface styled like the in-game menu  

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 · FastAPI · uvicorn |
| Frontend | React 18 · Vite 5 · vanilla CSS |
| World I/O | [amulet-core](https://github.com/Amulet-Team/Amulet-Core) |
| Noise | [opensimplex](https://github.com/lmas/opensimplex) |
| Deployment | Railway — single-server (FastAPI serves built React bundle) |

---

## 로컬 실행 / Local Setup

### Prerequisites

- Python 3.11 · [uv](https://github.com/astral-sh/uv) · Node.js 18+

```bash
# 1. Clone
git clone https://github.com/<you>/minecraft-map.git
cd minecraft-map

# 2. Python environment (Python 3.11 required for amulet-core wheels)
uv venv .venv --python 3.11
uv pip install -r requirements.local.txt   # includes amulet-core + opensimplex

# 3. Frontend
cd frontend && npm install && npm run build && cd ..
```

### Dev mode (two terminals)

```bash
# Terminal 1 — API
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS / Linux
uvicorn api.main:app --reload

# Terminal 2 — Frontend hot-reload
cd frontend && npm run dev
# open http://localhost:5173
```

### Production preview (single server)

```bash
cd frontend && npm run build && cd ..
uvicorn api.main:app --host 0.0.0.0 --port 8000
# open http://localhost:8000
```

---

## 배포 / Deployment

### Railway (recommended)

[![Deploy on Railway](https://railway.app/button.svg)](#)

```bash
# 1. Push to GitHub
# 2. Connect repo on railway.app
# 3. Railway reads railway.toml automatically → build + start
```

Environment variables to set in Railway dashboard:

| Variable | Example | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Set by Railway automatically |
| `ALLOWED_ORIGINS` | `https://your-app.railway.app` | CORS allowed origins |

### Render

- **Build Command**: `pip install -r requirements.txt && cd frontend && npm ci && npm run build`
- **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

---

## CLI (기존 스크립트 유지 / Legacy CLI still works)

```bash
# Block replacement
python replace_blocks.py path/to/world minecraft:stone minecraft:diamond_block

# Flat terrain
python generate_terrain.py path/to/world flat --block minecraft:grass_block --height 64

# Hilly terrain (with region)
python generate_terrain.py path/to/world hills --block minecraft:stone \
  --base-height 60 --amplitude 25 --scale 80 \
  --x1 -200 --z1 -200 --x2 200 --z2 200

# Dry-run
python replace_blocks.py path/to/world stone air --dry-run
```

---

## 설계 포인트 / Architecture Notes

### ThreadPoolExecutor (max_workers=1)

amulet-core 의 월드 읽기/쓰기는 동기 파일 I/O입니다.  
FastAPI의 async 이벤트 루프를 블로킹하지 않도록 `loop.run_in_executor`로 스레드 풀에 위임합니다.  
**단, workers=1로 제한**해 두 요청이 동시에 같은 월드 파일을 쓰는 충돌을 방지합니다.

```
Browser → POST /api/replace
           ↓
   FastAPI (async)
           ↓ run_in_executor
   ThreadPoolExecutor(1) → amulet-core (sync file I/O)
```

### 청크 팔레트 레벨 교체

블록을 한 개씩 순회하지 않고 **청크의 block_palette를 스캔**해 교체할 인덱스를 찾은 뒤  
numpy 배열 전체에 한 번에 적용합니다.  
O(volume) → O(palette_size) per chunk, 대형 월드에서 수십 배 빠릅니다.

### opensimplex 선택 이유

`noise` 패키지는 C 확장 컴파일이 필요해 Windows 빌드 환경 없이 설치 불가.  
`opensimplex`는 순수 Python으로 플랫폼 무관 설치가 가능하며,  
OpenSimplex2 알고리즘이 Perlin 대비 방향성 아티팩트(directional artifacts)가 적습니다.

### 단일 서버 배포 구조

```
Railway
└── uvicorn api.main:app
    ├── /api/*       → FastAPI routes (Python)
    └── /*           → frontend/dist/ (pre-built React bundle)
```

---

## 프로젝트 구조 / Project Structure

```
minecraft-map/
├── api/                    FastAPI backend
│   ├── main.py             App factory, static file serving
│   ├── _executor.py        Shared ThreadPoolExecutor
│   ├── schemas.py          Pydantic request/response models
│   └── routes/
│       ├── replace.py      POST /api/replace
│       └── generate.py     POST /api/generate
├── block_replacer/
│   └── core.py             replace_blocks()
├── terrain_generator/
│   ├── __init__.py         Shared chunk utilities
│   ├── flat.py             generate_flat()
│   └── hills.py            generate_hills()
├── frontend/               React + Vite
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── ReplaceForm.jsx
│           └── GenerateForm.jsx
├── replace_blocks.py       Legacy CLI
├── generate_terrain.py     Legacy CLI
├── railway.toml
├── Procfile
└── requirements.txt
```

---

## License

MIT
