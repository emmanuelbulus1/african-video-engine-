import { useState, useRef } from 'react'
import './index.css'

const MODES = [
  { id: 'guru',        label: '🧙 GURU',        desc: 'African wisdom & proverbs' },
  { id: 'documentary', label: '🎬 Documentary',  desc: 'Powerful & factual' },
  { id: 'story',       label: '📖 Story',        desc: 'Oral storytelling' },
  { id: 'news',        label: '📰 News',         desc: 'Urgent & authoritative' },
]

const PIPELINE_STEPS = [
  { pct: 5,  label: 'Fetch' },
  { pct: 10, label: 'Download' },
  { pct: 20, label: 'AssemblyAI' },
  { pct: 35, label: 'Transcript' },
  { pct: 55, label: 'Script' },
  { pct: 75, label: 'Voice' },
  { pct: 95, label: 'Merge' },
  { pct: 100, label: 'Done 🎉' },
]

interface JobResult {
  title: string
  transcript: string
  rewritten_script: string
  download_url: string
}

interface JobState {
  status: string
  progress: number
  message: string
  result?: JobResult
}

function App() {
  const [url, setUrl]       = useState('')
  const [mode, setMode]     = useState('guru')
  const [loading, setLoading] = useState(false)
  const [job, setJob]       = useState<JobState | null>(null)
  const [error, setError]   = useState('')
  const pollRef             = useRef<ReturnType<typeof setInterval> | null>(null)

  const handleTransform = async () => {
    if (!url.trim()) { setError('Please enter a YouTube URL'); return }
    setError('')
    setJob({ status: 'pending', progress: 0, message: 'Starting pipeline…' })
    setLoading(true)

    try {
      const res = await fetch('/api/transform', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtube_url: url, mode }),
      })
      if (!res.ok) throw new Error(await res.text())
      const { job_id } = await res.json()

      // Poll every 2 seconds
      pollRef.current = setInterval(async () => {
        const poll = await fetch(`/api/job/${job_id}`)
        const data: JobState = await poll.json()
        setJob(data)
        if (data.status === 'done' || data.status === 'error') {
          clearInterval(pollRef.current!)
          setLoading(false)
          if (data.status === 'error') setError(data.message)
        }
      }, 2000)

    } catch (e: any) {
      setError(e.message || 'Something went wrong')
      setLoading(false)
    }
  }

  const pct      = job?.progress ?? 0
  const stepDone = (threshold: number) => pct >= threshold
  const stepActive = (s: typeof PIPELINE_STEPS[0], i: number) =>
    pct >= s.pct && (i === PIPELINE_STEPS.length - 1 || pct < PIPELINE_STEPS[i + 1].pct)

  return (
    <div className="app">
      {/* Header */}
      <div className="header">
        <h1>🌍 African Video Engine</h1>
        <p>Transform any YouTube video with African GURU storytelling</p>
      </div>

      {/* Input card */}
      <div className="card">
        <div className="form-group">
          <label>YouTube URL</label>
          <input
            type="text"
            placeholder="https://youtube.com/watch?v=…"
            value={url}
            onChange={e => setUrl(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label>Transformation Mode</label>
          <div className="mode-grid">
            {MODES.map(m => (
              <button
                key={m.id}
                className={`mode-btn ${mode === m.id ? 'active' : ''}`}
                onClick={() => setMode(m.id)}
                disabled={loading}
                title={m.desc}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={handleTransform}
          disabled={loading || !url.trim()}
        >
          {loading ? '⏳ Transforming…' : '🚀 Transform Video'}
        </button>

        {/* Error */}
        {error && <div className="error-box">❌ {error}</div>}

        {/* Progress */}
        {job && (
          <div className="progress-section">
            <div className="progress-label">
              <span>{job.message}</span>
              <span>{pct}%</span>
            </div>
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <div className="steps">
              {PIPELINE_STEPS.map((s, i) => (
                <span
                  key={s.label}
                  className={`step ${stepDone(s.pct) ? 'done' : ''} ${stepActive(s, i) ? 'active' : ''}`}
                >
                  {s.label}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Result */}
      {job?.status === 'done' && job.result && (
        <div className="result-card">
          <h3>✅ {job.result.title}</h3>

          <label style={{ color: '#6ee7a0', textTransform: 'none', marginBottom: '0.4rem' }}>
            🎙 African Script:
          </label>
          <div className="script-box">{job.result.rewritten_script}</div>

          <a
            className="download-btn"
            href={job.result.download_url}
            download
          >
            ⬇️ Download Video
          </a>
        </div>
      )}
    </div>
  )
}

export default App
