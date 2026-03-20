import { useState, useEffect, useRef, useCallback } from 'react'

// Load PDF.js from CDN (injected once)
let pdfjsLib = null
function loadPdfJs() {
  if (pdfjsLib) return Promise.resolve(pdfjsLib)
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js'
    script.onload = () => {
      window.pdfjsLib.GlobalWorkerOptions.workerSrc =
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'
      pdfjsLib = window.pdfjsLib
      resolve(pdfjsLib)
    }
    script.onerror = reject
    document.head.appendChild(script)
  })
}

async function extractTextFromFile(file) {
  const ext = file.name.split('.').pop().toLowerCase()

  if (ext === 'pdf') {
    const lib = await loadPdfJs()
    const arrayBuffer = await file.arrayBuffer()
    const pdf = await lib.getDocument({ data: arrayBuffer }).promise
    let text = ''
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i)
      const content = await page.getTextContent()
      text += content.items.map(item => item.str).join(' ') + '\n'
    }
    return text.trim()
  }

  if (['doc', 'docx'].includes(ext)) {
    throw new Error('Word documents (.doc/.docx) cannot be read directly.\nPlease copy and paste the text from your document instead.')
  }

  // Plain text
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = e => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

/* ── Reusable DropZone component ── */
function DropZone({ label, fileName, dragOver, onDragOver, onDragLeave, onDrop, onClick, loading }) {
  return (
    <div
      className={`drop-zone${dragOver ? ' drag-active' : ''}${fileName ? ' has-file' : ''}`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onClick={onClick}
    >
      {loading ? (
        <>
          <span className="drop-icon" style={{ color: 'var(--teal, #00f5d4)' }}>
            <span className="loader" style={{ width: 28, height: 28 }} />
          </span>
          <span className="drop-label">Reading file…</span>
        </>
      ) : (
        <>
          <div className="drop-icon">
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          {fileName
            ? <span className="drop-filename">{fileName}</span>
            : <>
                <span className="drop-label">Drop your {label} here</span>
                <span className="drop-hint">or click to browse &nbsp;·&nbsp; .txt .pdf</span>
              </>
          }
        </>
      )}
    </div>
  )
}

function sourceIcon(source) {
  switch (source) {
    case 'freeCodeCamp':  return '🏕️'
    case 'GeeksforGeeks': return '🧠'
    case 'YouTube':       return '▶️'
    case 'Coursera':      return '🎓'
    default:              return '🔗'
  }
}

function App() {
  const [activeTab, setActiveTab] = useState('analyze')
  const [resumeText, setResumeText] = useState('')
  const [jdText, setJdText] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [stats, setStats] = useState(null)

  // Resume upload state
  const [resumeDrag, setResumeDrag] = useState(false)
  const [resumeFile, setResumeFile] = useState(null)
  const [resumeLoading, setResumeLoading] = useState(false)
  const resumeInputRef = useRef(null)
  const resourcesRef = useRef(null)

  // JD upload state
  const [jdDrag, setJdDrag] = useState(false)
  const [jdFile, setJdFile] = useState(null)
  const [jdLoading, setJdLoading] = useState(false)
  const jdInputRef = useRef(null)

  useEffect(() => { fetchHistory(); fetchStats() }, [])

  const fetchHistory = async () => {
    try {
      const r = await fetch('http://localhost:8000/api/v1/sessions')
      const d = await r.json()
      setHistory(d.sessions || [])
    } catch (e) { console.error(e) }
  }

  const fetchStats = async () => {
    try {
      const r = await fetch('http://localhost:8000/api/v1/stats')
      const d = await r.json()
      setStats(d)
    } catch (e) { console.error(e) }
  }

  const analyze = async () => {
    if (!resumeText || !jdText) {
      alert('Please provide both Resume and Job Description')
      return
    }
    setLoading(true)
    try {
      const r = await fetch('http://localhost:8000/api/v1/analyze/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resumeText, jd_text: jdText, candidate_name: 'Guest User' }),
      })
      const d = await r.json()
      setResults(d.pathway)
      fetchHistory(); fetchStats()
    } catch (err) {
      console.error(err)
      alert('Error connecting to backend. Make sure it is running on port 8000.')
    }
    setLoading(false)
  }

  /* ── Generic file handler ── */
  const handleFile = async (file, setText, setFile, setFileLoading) => {
    if (!file) return
    setFile(file.name)
    setFileLoading(true)
    try {
      const text = await extractTextFromFile(file)
      setText(text)
    } catch (err) {
      alert(err.message || 'Could not read file. Please paste the text manually.')
      setFile(null)
      setText('')
    }
    setFileLoading(false)
  }

  /* ── Resume handlers ── */
  const onResumeDragOver  = useCallback(e => { e.preventDefault(); setResumeDrag(true) }, [])
  const onResumeDragLeave = useCallback(() => setResumeDrag(false), [])
  const onResumeDrop      = useCallback(e => {
    e.preventDefault(); setResumeDrag(false)
    handleFile(e.dataTransfer.files[0], setResumeText, setResumeFile, setResumeLoading)
  }, [])
  const onResumeChange    = e => handleFile(e.target.files[0], setResumeText, setResumeFile, setResumeLoading)

  /* ── JD handlers ── */
  const onJdDragOver  = useCallback(e => { e.preventDefault(); setJdDrag(true) }, [])
  const onJdDragLeave = useCallback(() => setJdDrag(false), [])
  const onJdDrop      = useCallback(e => {
    e.preventDefault(); setJdDrag(false)
    handleFile(e.dataTransfer.files[0], setJdText, setJdFile, setJdLoading)
  }, [])
  const onJdChange    = e => handleFile(e.target.files[0], setJdText, setJdFile, setJdLoading)

  return (
    <div className="App">
      <header className="glass">
        <div className="logo">Career<span>DNA</span></div>
        <nav>
          <button className={activeTab === 'analyze' ? 'active' : ''} onClick={() => setActiveTab('analyze')}>Analyze</button>
          <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>History</button>
          <button className={activeTab === 'stats'   ? 'active' : ''} onClick={() => setActiveTab('stats')}>Stats</button>
        </nav>
      </header>

      <main>
        {activeTab === 'analyze' && (
          <section className="analyze-section">
            <h1 className="gradient-text">Decode Your Potential</h1>
            <p className="subtitle">AI-powered career pathway analysis — aligned to your DNA.</p>

            <div className="input-grid">

              {/* RESUME CARD */}
              <div className="card glass">
                <h3>Resume</h3>
                <input ref={resumeInputRef} type="file" accept=".txt,.pdf"
                  style={{ display: 'none' }} onChange={onResumeChange} />
                <DropZone
                  label="resume"
                  fileName={resumeFile}
                  dragOver={resumeDrag}
                  loading={resumeLoading}
                  onDragOver={onResumeDragOver}
                  onDragLeave={onResumeDragLeave}
                  onDrop={onResumeDrop}
                  onClick={() => resumeInputRef.current?.click()}
                />
                <div className="or-divider"><span>or paste text</span></div>
                <textarea
                  value={resumeText}
                  onChange={e => setResumeText(e.target.value)}
                  placeholder="Paste your resume text here..."
                />
              </div>

              {/* JD CARD */}
              <div className="card glass">
                <h3>Job Description</h3>
                <input ref={jdInputRef} type="file" accept=".txt,.pdf"
                  style={{ display: 'none' }} onChange={onJdChange} />
                <DropZone
                  label="job description"
                  fileName={jdFile}
                  dragOver={jdDrag}
                  loading={jdLoading}
                  onDragOver={onJdDragOver}
                  onDragLeave={onJdDragLeave}
                  onDrop={onJdDrop}
                  onClick={() => jdInputRef.current?.click()}
                />
                <div className="or-divider"><span>or paste text</span></div>
                <textarea
                  value={jdText}
                  onChange={e => setJdText(e.target.value)}
                  placeholder="Paste the job description here..."
                />
              </div>

            </div>

            <div className="actions">
              <button className="btn-primary" onClick={analyze} disabled={loading}>
                {loading ? <span className="loader"></span> : 'Decode My Career Path'}
              </button>
            </div>

            {results && (
              <div className="results-container animate-in">
                <div className="results-header glass">
                  <div className="score-circle">
                    <svg viewBox="0 0 36 36" className="circular-chart">
                      <path className="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                      <path className="circle" strokeDasharray={`${results.readiness_score}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                      <text x="18" y="20.35" className="percentage">{Math.round(results.readiness_score)}</text>
                    </svg>
                    <span className="score-label">Readiness Score</span>
                  </div>
                  <div className="summary-info">
                    <h2>Analysis for {results.target_role}</h2>
                    <div className="stats-row">
                      <div className="stat-pill">Coverage: {results.skill_coverage_percent}%</div>
                      <div className="stat-pill">Gaps: {results.skill_gaps.length}</div>
                      <div className="stat-pill">Total Time: {results.total_duration_hours}h</div>
                    </div>
                    <button
                      className="btn-resources"
                      onClick={() => resourcesRef.current?.scrollIntoView({ behavior: 'smooth' })}
                    >
                      📚 View Learning Resources
                    </button>
                  </div>
                </div>

                <div className="pathway-grid">
                  <div className="card glass">
                    <h3>Learning Pathway</h3>
                    <div className="timeline">
                      {results.modules.length > 0 ? results.modules.map((item, i) => (
                        <div key={i} className="timeline-item">
                          <div className="marker"></div>
                          <div className="content">
                            <h4>{item.title} <span>({item.difficulty})</span></h4>
                            <p>{item.description}</p>
                          </div>
                        </div>
                      )) : <p style={{color:'var(--muted, #aaa)', fontSize:'0.9rem'}}>No critical gap modules found.</p>}
                    </div>
                  </div>
                  <div className="card glass">
                    <h3>Skill Breakdown</h3>
                    <div className="skill-labels">
                      <h4 className="section-title">Strengths</h4>
                      <div className="pills">
                        {results.strengths.map((s, i) => <span key={i} className="pill strength">{s}</span>)}
                      </div>
                      <h4 className="section-title">Critical Gaps</h4>
                      <div className="pills">
                        {results.critical_gaps.map((s, i) => <span key={i} className="pill gap">{s}</span>)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* ── Resources Section ── */}
                {results.critical_gaps?.length > 0 && (
                  <div className="resources-section" ref={resourcesRef}>
                    <div className="resources-header">
                      <h2 className="gradient-text">📚 Learning Resources</h2>
                      <p className="subtitle">Curated links for your critical skill gaps</p>
                    </div>
                    <div className="resources-grid">
                      {results.skill_gaps
                        .filter(g => results.critical_gaps.includes(g.skill))
                        .map((gap, i) => (
                          <div key={i} className="resource-card glass">
                            <div className="resource-card-header">
                              <span className="pill gap" style={{fontSize:'0.75rem'}}>{gap.skill}</span>
                              <span className="priority-badge">{gap.priority.toUpperCase()}</span>
                            </div>
                            <div className="resource-links">
                              {gap.links?.map((link, j) => (
                                <a
                                  key={j}
                                  href={link.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className={`resource-link source-${link.source.toLowerCase().replace(/\s+/g,'')}`}
                                >
                                  <span className="resource-icon">{sourceIcon(link.source)}</span>
                                  <span className="resource-text">
                                    <span className="resource-platform">{link.source}</span>
                                    <span className="resource-label">Learn {gap.skill}</span>
                                  </span>
                                  <span className="resource-arrow">→</span>
                                </a>
                              ))}
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {activeTab === 'history' && (
          <section className="history-section animate-in">
            <h2>Recent Sessions</h2>
            <div className="history-list">
              {history.length > 0 ? history.map((session, i) => (
                <div key={i} className="history-card glass" onClick={() => { setResults(session); setActiveTab('analyze') }}>
                  <div className="h-info">
                    <strong>{session.target_role}</strong>
                    <span>{session.candidate_name || 'Guest'}</span>
                  </div>
                  <div className="h-score">{Math.round(session.readiness_score)}</div>
                </div>
              )) : <p>No history yet.</p>}
            </div>
          </section>
        )}

        {activeTab === 'stats' && (
          <section className="stats-section animate-in">
            <h2>System Overview</h2>
            {stats ? (
              <div className="stats-grid">
                <div className="stat-card glass">
                  <h3>{stats.total_analyses ?? 0}</h3>
                  <p>Total Analyses</p>
                </div>
                <div className="stat-card glass">
                  <h3>{stats.avg_readiness_score != null ? stats.avg_readiness_score : '—'}</h3>
                  <p>Avg Readiness Score</p>
                </div>
                <div className="stat-card glass">
                  <h3>{stats.avg_skill_coverage != null ? stats.avg_skill_coverage : '—'}%</h3>
                  <p>Avg Skill Coverage</p>
                </div>
                <div className="stat-card glass">
                  <h3>{stats.top_target_roles?.[0]?.target_role ?? '—'}</h3>
                  <p>Top Role Analysed</p>
                </div>
              </div>
            ) : <p>Loading stats...</p>}
          </section>
        )}
      </main>
    </div>
  )
}

export default App
