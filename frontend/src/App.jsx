import { useState, useEffect, useRef, useCallback } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, CartesianGrid, PieChart, Pie, Cell, Legend } from 'recharts'


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
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  
  const [activeTab, setActiveTab] = useState('analyze')
  const [resumeText, setResumeText] = useState('')
  const [jdText, setJdText] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [stats, setStats] = useState(null)
  const [candidateNameInput, setCandidateNameInput] = useState('')
  const [expandedHistory, setExpandedHistory] = useState(null)
  const [historySearch, setHistorySearch] = useState('')
  const [historySort, setHistorySort] = useState('newest')

  const filteredHistory = history.filter(h => {
     if(!historySearch) return true;
     const lower = historySearch.toLowerCase();
     const name = h.candidate_name || 'Guest User';
     const role = h.target_role || '';
     return name.toLowerCase().includes(lower) || role.toLowerCase().includes(lower);
  }).sort((a,b) => {
     if(historySort === 'score_desc') return b.readiness_score - a.readiness_score;
     if(historySort === 'score_asc') return a.readiness_score - b.readiness_score;
     if(historySort === 'oldest') return new Date(a.created_at || 0) - new Date(b.created_at || 0);
     if(historySort === 'shortlisted') return shortlisted.includes(b.session_id) - shortlisted.includes(a.session_id);
     return new Date(b.created_at || 0) - new Date(a.created_at || 0);
  })
  .filter(h => historySort === 'shortlisted' ? shortlisted.includes(h.session_id) : true)
  const [assessmentMode, setAssessmentMode] = useState(false)
  const [assessmentData, setAssessmentData] = useState(null)
  const [assAnswers, setAssAnswers] = useState({})
  const [assScore, setAssScore] = useState(null)

  // Advanced features
  const [shortlisted, setShortlisted] = useState(() => {
    try { return JSON.parse(localStorage.getItem('shortlisted') || '[]') } catch { return [] }
  })
  const [notesMap, setNotesMap] = useState(() => {
    try { return JSON.parse(localStorage.getItem('notesMap') || '{}') } catch { return {} }
  })
  const [noteTarget, setNoteTarget] = useState(null)
  const [noteText, setNoteText] = useState('')
  const [compareA, setCompareA] = useState(null)
  const [compareB, setCompareB] = useState(null)
  const [compareMode, setCompareMode] = useState(false)

  const toggleShortlist = (id) => {
    setShortlisted(prev => {
      const next = prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
      localStorage.setItem('shortlisted', JSON.stringify(next))
      return next
    })
  }

  const saveNote = () => {
    if (!noteTarget) return
    setNotesMap(prev => {
      const next = { ...prev, [noteTarget]: noteText }
      localStorage.setItem('notesMap', JSON.stringify(next))
      return next
    })
    setNoteTarget(null)
    setNoteText('')
  }

  const openNote = (sessionId, existing) => {
    setNoteTarget(sessionId)
    setNoteText(existing || '')
  }

  const startComparePick = (session) => {
    if (!compareA) { setCompareA(session); return }
    if (!compareB && session.session_id !== compareA.session_id) {
      setCompareB(session)
      setActiveTab('compare')
    }
  }

  const clearCompare = () => { setCompareA(null); setCompareB(null); setActiveTab('history') }

  // Deep Profile Sheet
  const [profileSheet, setProfileSheet] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)

  const openProfile = async (sessionId) => {
    setProfileLoading(true)
    setProfileSheet('loading')
    try {
      const r = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`)
      const d = await r.json()
      if (d.success) setProfileSheet(d.pathway)
      else setProfileSheet(null)
    } catch(e) { setProfileSheet(null) }
    setProfileLoading(false)
  }

  const closeProfile = () => setProfileSheet(null)

  // Pipeline
  const [pipeline, setPipeline] = useState(() => {
    try { return JSON.parse(localStorage.getItem('pipeline') || '{"Applied":[],"Screening":[],"Technical":[],"Offer":[]}') }
    catch { return { Applied:[], Screening:[], Technical:[], Offer:[] } }
  })

  const savePipeline = (next) => {
    setPipeline(next)
    localStorage.setItem('pipeline', JSON.stringify(next))
  }

  const addToPipeline = (session, stage='Applied') => {
    const id = session.session_id
    const card = { id, name: session.candidate_name || 'Guest', role: session.target_role, score: Math.round(session.readiness_score) }
    setPipeline(prev => {
      // Remove from any existing stage first
      const cleaned = {}
      Object.keys(prev).forEach(k => { cleaned[k] = prev[k].filter(c => c.id !== id) })
      const next = { ...cleaned, [stage]: [...cleaned[stage], card] }
      localStorage.setItem('pipeline', JSON.stringify(next))
      return next
    })
  }

  const movePipelineCard = (id, fromStage, toStage) => {
    setPipeline(prev => {
      const card = prev[fromStage]?.find(c => c.id === id)
      if (!card) return prev
      const next = {
        ...prev,
        [fromStage]: prev[fromStage].filter(c => c.id !== id),
        [toStage]: [...(prev[toStage] || []), card]
      }
      localStorage.setItem('pipeline', JSON.stringify(next))
      return next
    })
  }

  const removeFromPipeline = (id) => {
    setPipeline(prev => {
      const next = {}
      Object.keys(prev).forEach(k => { next[k] = prev[k].filter(c => c.id !== id) })
      localStorage.setItem('pipeline', JSON.stringify(next))
      return next
    })
  }

  const isInPipeline = (id) => Object.values(pipeline).flat().some(c => c.id === id)

  // Skills Intelligence derived data
  const getSkillsIntelligence = () => {
    const freq = {}
    history.forEach(h => {
      const role = h.target_role || 'Other'
      if (!freq[role]) freq[role] = 0
      freq[role]++
    })
    const scoreByRole = {}
    history.forEach(h => {
      const role = h.target_role || 'Other'
      if (!scoreByRole[role]) scoreByRole[role] = []
      scoreByRole[role].push(h.readiness_score)
    })
    const hireData = Object.keys(scoreByRole).map(role => ({
      role: role.length > 18 ? role.slice(0,16)+'…' : role,
      avgScore: Math.round(scoreByRole[role].reduce((a,b)=>a+b,0)/scoreByRole[role].length),
      count: scoreByRole[role].length
    })).sort((a,b) => b.count - a.count).slice(0,8)

    const scoreDistribution = [
      { range:'90-100', count: history.filter(h=>h.readiness_score>=90).length },
      { range:'80-89',  count: history.filter(h=>h.readiness_score>=80&&h.readiness_score<90).length },
      { range:'70-79',  count: history.filter(h=>h.readiness_score>=70&&h.readiness_score<80).length },
      { range:'60-69',  count: history.filter(h=>h.readiness_score>=60&&h.readiness_score<70).length },
      { range:'50-59',  count: history.filter(h=>h.readiness_score>=50&&h.readiness_score<60).length },
      { range:'<50',    count: history.filter(h=>h.readiness_score<50).length },
    ]
    return { hireData, scoreDistribution }
  }



  // Hackathon features
  const [hireRec, setHireRec] = useState(null)
  const [interviewQs, setInterviewQs] = useState(null)
  const [showInterviewQs, setShowInterviewQs] = useState(false)
  const [recLoading, setRecLoading] = useState(false)

  const getTierBadge = (score) => {
    if (score >= 85) return { label: 'Platinum', color: '#e2e8f0', bg: 'rgba(226,232,240,0.1)', border: '#a0aec0'}
    if (score >= 70) return { label: 'Gold', color: '#f6ad55', bg: 'rgba(246,173,85,0.1)', border: '#ed8936'}
    if (score >= 55) return { label: 'Silver', color: '#90cdf4', bg: 'rgba(144,205,244,0.1)', border: '#63b3ed'}
    if (score >= 40) return { label: 'Bronze', color: '#fc8181', bg: 'rgba(252,129,129,0.1)', border: '#f56565'}
    return { label: 'Needs Work', color: '#718096', bg: 'rgba(113,128,150,0.1)', border: '#718096'}
  }

  const exportJSON = (data, filename) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  }

  const exportHistoryCSV = () => {
    const headers = ['Candidate Name', 'Target Role', 'Readiness Score', 'Skill Coverage %', 'Critical Gaps', 'Training Hours', 'Date']
    const rows = history.map(h => [
      h.candidate_name || 'Guest User',
      h.target_role || '',
      Math.round(h.readiness_score),
      h.skill_coverage_percent,
      h.critical_gap_count,
      h.total_duration_hours,
      new Date(h.created_at || Date.now()).toLocaleDateString()
    ])
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'candidate_pipeline.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  const fetchHireRecommendation = async (pathway) => {
    setRecLoading(true)
    try {
      const r = await fetch(`${API_BASE}/api/v1/assessment/hire-recommendation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          readiness_score: pathway.readiness_score,
          skill_coverage_percent: pathway.skill_coverage_percent,
          critical_gap_count: pathway.critical_gaps?.length || 0,
          total_duration_hours: pathway.total_duration_hours
        })
      })
      const d = await r.json()
      setHireRec(d)
    } catch(e) { console.error(e) }
    setRecLoading(false)
  }

  const fetchInterviewQuestions = async (pathway) => {
    setShowInterviewQs(true)
    if (interviewQs) return
    try {
      const r = await fetch(`${API_BASE}/api/v1/assessment/interview-questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gaps: pathway.critical_gaps || [],
          strengths: pathway.strengths || [],
          readiness_score: pathway.readiness_score
        })
      })
      const d = await r.json()
      setInterviewQs(d.interview_questions)
    } catch(e) { console.error(e) }
  }

  const [assLoading, setAssLoading] = useState(false)

  const loadFullAnalysis = async (sessionId) => {
    try {
        const r = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`)
        const d = await r.json()
        if (d.success) {
            setResults(d.pathway)
            setAssessmentMode(false)
            setAssessmentData(null)
            setActiveTab('analyze')
            window.scrollTo({ top: 0, behavior: 'instant' })
        }
    } catch (e) { alert("Failed to load deep analysis: " + e.message) }
  }

  const COLORS = ['#2b6cb0', '#4a5568', '#718096', '#a0aec0', '#e2e8f0'];
  const getQualityData = () => {
     let bins = {'Excellent (>85)': 0, 'Good (70-85)': 0, 'Average (50-70)': 0, 'Needs Work (<50)': 0}
     history.forEach(h => {
        if(h.readiness_score >= 85) bins['Excellent (>85)']++;
        else if(h.readiness_score >= 70) bins['Good (70-85)']++;
        else if(h.readiness_score >= 50) bins['Average (50-70)']++;
        else bins['Needs Work (<50)']++;
     })
     return Object.keys(bins).map(k => ({name: k, count: bins[k]}))
  }


  const startAssessment = async () => {
    setAssessmentMode(true)
    setAssLoading(true)
    setAssScore(null)
    setAssAnswers({})
    try {
      const r = await fetch(`${API_BASE}/api/v1/assessment/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jd_text: jdText, level: "intermediate" })
      })
      const d = await r.json()
      setAssessmentData(d)
    } catch(e) { alert(e) }
    setAssLoading(false)
  }

  const submitAssessment = async () => {
    setAssLoading(true)
    try {
      const r = await fetch(`${API_BASE}/api/v1/assessment/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modules: assessmentData.modules, candidate_answers: assAnswers })
      })
      const d = await r.json()
      setAssScore(d)
    } catch(e) { alert(e) }
    setAssLoading(false)
  }

  const handleOptionChange = (questionId, option) => {
    setAssAnswers(prev => ({ ...prev, [questionId]: option }))
  }


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
  useEffect(() => {
    if (results) {
      setHireRec(null)
      setInterviewQs(null)
      setShowInterviewQs(false)
      fetchHireRecommendation(results)
    }
  }, [results])

  const fetchHistory = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/v1/sessions`)
      const d = await r.json()
      setHistory(d.sessions || [])
    } catch (e) { console.error(e) }
  }

  const fetchStats = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/v1/stats`)
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
      const r = await fetch(`${API_BASE}/api/v1/analyze/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resumeText, jd_text: jdText, candidate_name: candidateNameInput || 'Guest User' }),
      })
      if (!r.ok) {
        throw new Error(`HTTP error! status: ${r.status}`);
      }
      const d = await r.json()
      setResults(d.pathway)
      fetchHistory(); fetchStats()
    } catch (err) {
      console.error("Backend Error:", err)
      alert(`Error connecting to backend (${API_BASE}). Make sure it is running. Detail: ` + err.message)
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
          <button className={activeTab === 'compare' ? 'active' : ''} onClick={() => setActiveTab('compare')}>Compare</button>
          <button className={activeTab === 'leaderboard' ? 'active' : ''} onClick={() => setActiveTab('leaderboard')}>Leaderboard</button>
          <button className={activeTab === 'pipeline' ? 'active' : ''} onClick={() => setActiveTab('pipeline')}>Pipeline</button>
          <button className={activeTab === 'skills' ? 'active' : ''} onClick={() => setActiveTab('skills')}>Skills</button>
        </nav>
      </header>

      <main>
        {activeTab === 'analyze' && (
          <section className="analyze-section">
            <h1 className="gradient-text">Decode Your Potential</h1>
            <p className="subtitle">AI-powered career pathway analysis — aligned to your DNA.</p>

            <div className="input-grid">
              
              <div className="card glass" style={{gridColumn: '1 / -1'}}>
                 <h3 style={{marginBottom:'10px'}}>Candidate Name</h3>
                 <input type="text" placeholder="Enter candidate name (e.g. David)" value={candidateNameInput} onChange={e => setCandidateNameInput(e.target.value)} style={{width: '100%', padding: '12px', background: 'rgba(255,255,255,0.05)', color: 'var(--white)', border: '1px solid rgba(0,245,212,0.3)', borderRadius: '6px', fontSize: '1rem'}} />
              </div>

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
                    <button
                      className="btn-resources" style={{marginLeft: "10px", background: "rgba(245, 166, 35, 0.15)", borderColor: "var(--amber)", color: "var(--amber)"}}
                      onClick={startAssessment}
                    >
                      ⚡ Take Technical Assessment
                    </button>
                    <button
                      className="btn-resources" style={{marginLeft: "10px", background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.15)", color: "var(--white-dim)"}}
                      onClick={() => fetchInterviewQuestions(results)}
                    >
                      🎤 Interview Questions
                    </button>
                    <button
                      className="btn-resources" style={{marginLeft: "10px", background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.15)", color: "var(--white-dim)"}}
                      onClick={() => exportJSON(results, `${results.candidate_name || 'candidate'}_analysis.json`)}
                    >
                      ⬇ Export Report
                    </button>
                  </div>
                </div>

                {/* ── Hire Recommendation + Tier Badge ── */}
                {hireRec && (
                  <div className="card glass" style={{marginTop: '20px', padding: '20px', borderLeft: `3px solid ${hireRec.color === 'green' ? '#48bb78' : hireRec.color === 'teal' ? '#38b2ac' : hireRec.color === 'amber' ? '#ed8936' : hireRec.color === 'orange' ? '#dd6b20' : '#fc8181'}`}}>
                    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px'}}>
                      <div>
                        <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px'}}>
                          <span style={{fontSize: '1.5rem'}}>{hireRec.badge}</span>
                          <strong style={{fontSize: '1.1rem', letterSpacing: '0.05em'}}>{hireRec.tier}</strong>
                          {(() => { const t = getTierBadge(hireRec.readiness_score); return (
                            <span style={{fontSize: '0.75rem', padding: '2px 10px', borderRadius: '20px', border: `1px solid ${t.border}`, color: t.color, background: t.bg}}>{t.label} Tier</span>
                          )})()}
                        </div>
                        <p style={{color: 'var(--white-dim)', fontSize: '0.9rem', margin: '0 0 6px'}}>{hireRec.summary}</p>
                        <p style={{color: 'rgba(255,255,255,0.45)', fontSize: '0.82rem', fontStyle: 'italic'}}>Recommended Action: {hireRec.action}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* ── Training Timeline BarChart ── */}
                {results.skill_gaps?.length > 0 && (
                  <div className="card glass" style={{marginTop: '20px', padding: '20px'}}>
                    <h3 style={{color: 'var(--white-dim)', fontWeight: 500, marginBottom: '15px'}}>Skill Gap Training Timeline</h3>
                    <div style={{height: '220px', width: '100%'}}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={results.skill_gaps.map(g => ({name: g.skill, hours: g.estimated_hours || Math.round(Math.random()*20+5), priority: g.priority}))} margin={{top: 5, right: 20, left: 0, bottom: 30}}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                          <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" tick={{fontSize: 11, fill: 'rgba(255,255,255,0.5)'}} angle={-20} textAnchor="end" />
                          <YAxis stroke="rgba(255,255,255,0.3)" tick={{fontSize: 11, fill: 'rgba(255,255,255,0.4)'}} label={{value: 'Hours', angle: -90, position: 'insideLeft', style: {fill: 'rgba(255,255,255,0.3)', fontSize: 10}}} />
                          <Tooltip contentStyle={{background: '#0d1b2a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px'}} />
                          <Bar dataKey="hours" name="Training Hours" radius={[3,3,0,0]}>
                            {results.skill_gaps.map((entry, index) => (
                              <Cell key={index} fill={entry.priority === 'critical' ? '#4a5568' : '#2d3748'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

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

            {/* ── Interview Questions Panel ── */}
            {showInterviewQs && results && (
              <div className="results-container animate-in" style={{marginTop: '2rem'}}>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
                  <h2 style={{margin: 0}}>🎤 Suggested Interview Questions</h2>
                  <button onClick={() => setShowInterviewQs(false)} style={{background: 'none', border: '1px solid rgba(255,255,255,0.15)', color: 'var(--white-dim)', padding: '6px 14px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem'}}>✕ Close</button>
                </div>
                {!interviewQs ? (
                  <p style={{color: 'var(--white-dim)'}}>Generating targeted questions...</p>
                ) : (
                  <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
                    {interviewQs.map((q, i) => (
                      <div key={i} className="card glass" style={{padding: '16px 20px', borderLeft: `3px solid ${q.type === 'gap' ? '#4a5568' : q.type === 'behavioral' ? '#38b2ac' : '#2d3748'}`}}>
                        <div style={{display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '8px'}}>
                          <span style={{fontSize: '0.72rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.08em'}}>{q.skill}</span>
                          <span style={{fontSize: '0.72rem', color: 'rgba(255,255,255,0.3)'}}>{q.type}</span>
                        </div>
                        <p style={{margin: 0, lineHeight: 1.6, color: 'var(--white)'}}>{q.question}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {assessmentMode && (
              <div className="results-container animate-in" style={{marginTop: '2rem'}}>
                <div className="resources-header">
                  <h2 className="gradient-text">⚡ Technical Assessment</h2>
                  <p className="subtitle">Procedurally generated to match the Job Description in real-time.</p>
                </div>
                
                {assLoading && <p>Loading...</p>}
                
                {!assLoading && !assScore && assessmentData && (
                  <div className="pathway-grid" style={{gridTemplateColumns: '1fr'}}>
                    {assessmentData.modules.map((mod, i) => (
                      <div key={i} className="card glass" style={{marginBottom: '1rem'}}>
                        <h3 style={{color: 'var(--teal)', marginBottom: '1rem'}}>{mod.skill_name}</h3>
                        {mod.questions.map((q, j) => (
                          <div key={q.id} style={{marginBottom: '1.5rem', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px'}}>
                            <p style={{marginBottom: '1rem', fontSize: '1.05rem', lineHeight: '1.5'}}><strong style={{color: 'var(--white)'}}>Q:</strong> {q.question}</p>
                            <div style={{display: 'flex', flexDirection: 'column', gap: '8px'}}>
                              {q.options.map((opt, k) => (
                                <label key={k} style={{display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px'}}>
                                  <input 
                                    type="radio" 
                                    name={q.id} 
                                    value={opt} 
                                    checked={assAnswers[q.id] === opt}
                                    onChange={() => handleOptionChange(q.id, opt)}
                                  />
                                  <span>{opt}</span>
                                </label>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    ))}
                    <button className="btn-primary" onClick={submitAssessment} style={{marginTop: '1rem', width: '200px'}}>Submit Assessment</button>
                  </div>
                )}

                {assScore && (
                  <div className="results-header glass">
                    <div className="score-circle">
                      <svg viewBox="0 0 36 36" className="circular-chart" style={{stroke: 'var(--amber)'}}>
                        <path className="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                        <path className="circle" strokeDasharray={`${assScore.score_percentage}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                        <text x="18" y="20.35" className="percentage" fill="var(--amber)">{Math.round(assScore.score_percentage)}</text>
                      </svg>
                      <span className="score-label" style={{color: 'var(--amber)'}}>Assessment Score</span>
                    </div>
                    <div className="summary-info">
                      <h2 style={{color: 'var(--amber)'}}>Evaluation Complete</h2>
                      <div className="stats-row">
                        <div className="stat-pill" style={{borderColor: 'var(--amber)', color: 'var(--amber)'}}>Correct: {assScore.correct_answers} / {assScore.total_questions}</div>
                      </div>
                      <div style={{marginTop: '1rem'}}>
                        {Object.entries(assScore.breakdown).map(([skill, data]) => (
                          <div key={skill} style={{display: 'flex', justifyContent: 'space-between', marginBottom: '4px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '4px'}}>
                            <span>{skill}</span>
                            <span style={{color: data.correct === data.total ? 'var(--teal)' : 'var(--amber)'}}>{data.correct}/{data.total}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

          </section>
        )}

        {activeTab === 'history' && (
          <section className="history-section animate-in">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
              <h2 style={{margin: 0}}>Candidate History</h2>
              <button onClick={exportHistoryCSV} style={{background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.15)', color: 'var(--white-dim)', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px'}}>⬇ Export CSV</button>
            </div>
            <div style={{display: 'flex', gap: '15px', marginBottom: '20px'}}>
               <input type="text" placeholder="Search by candidate name or role..." value={historySearch} onChange={e => setHistorySearch(e.target.value)} style={{flex: 1, padding: '10px 15px', background: 'rgba(255,255,255,0.03)', color: 'var(--white)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', fontSize: '0.95rem'}} />
               <select value={historySort} onChange={e => setHistorySort(e.target.value)} style={{padding: '10px 20px', background: 'rgba(255,255,255,0.03)', color: 'var(--white)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', cursor: 'pointer', outline: 'none'}}>
                  <option value="newest" style={{background: '#0a192f'}}>Newest First</option>
                  <option value="oldest" style={{background: '#0a192f'}}>Oldest First</option>
                  <option value="score_desc" style={{background: '#0a192f'}}>Score: High to Low</option>
                  <option value="score_asc" style={{background: '#0a192f'}}>Score: Low to High</option>
                  <option value="shortlisted" style={{background: '#0a192f'}}>⭐ Shortlisted Only</option>
               </select>
            </div>

            {compareA && !compareB && (
              <div style={{background:'rgba(56,178,172,0.08)',border:'1px solid #38b2ac',borderRadius:'8px',padding:'12px 16px',marginBottom:'16px',display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                <span style={{color:'#38b2ac',fontSize:'0.9rem'}}>⚖ Selected <strong>{compareA.candidate_name || 'Guest'}</strong> for comparison. Click another candidate's ⚖ to compare.</span>
                <button onClick={() => setCompareA(null)} style={{background:'none',border:'none',color:'rgba(255,255,255,0.4)',cursor:'pointer',fontSize:'1.2rem'}}>✕</button>
              </div>
            )}
            <div className="history-list">
              {filteredHistory.length > 0 ? filteredHistory.map((session, i) => {
                const isExpanded = expandedHistory === session.session_id;
                // create chart data from gaps/coverage mock
                const chartData = [
                   { subject: 'Skills Match', A: session.skill_coverage_percent, fullMark: 100 },
                   { subject: 'Readiness', A: session.readiness_score, fullMark: 100 },
                   { subject: 'Gaps Avoided', A: Math.max(0, 100 - (session.skill_gaps?.length || 0) * 10), fullMark: 100 }
                ];
                return (
                <div key={i} className="history-card glass" style={{cursor: 'pointer', display: 'flex', flexDirection: 'column'}} onClick={() => { setExpandedHistory(isExpanded ? null : session.session_id) }}>
                  <div style={{display: 'flex', justifyContent: 'space-between', width: '100%', gap: '10px'}}>
                    <div className="h-info" style={{flex:1}}>
                      <strong>{session.target_role}</strong>
                      <span>{session.candidate_name || 'Guest User'} · {new Date(session.created_at || Date.now()).toLocaleDateString()}</span>
                      {notesMap[session.session_id] && <span style={{fontSize:'0.78rem',color:'rgba(255,255,255,0.4)',display:'block',marginTop:'3px',fontStyle:'italic'}}>📝 {notesMap[session.session_id].substring(0,60)}{notesMap[session.session_id].length > 60 ? '…' : ''}</span>}
                    </div>
                    <div style={{display:'flex',alignItems:'center',gap:'8px',flexShrink:0}}>
                      <button onClick={e => { e.stopPropagation(); toggleShortlist(session.session_id) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'1.1rem',opacity: shortlisted.includes(session.session_id) ? 1 : 0.3}} title={shortlisted.includes(session.session_id) ? 'Remove from shortlist' : 'Shortlist'}>
                        {shortlisted.includes(session.session_id) ? '⭐' : '☆'}
                      </button>
                      <button onClick={e => { e.stopPropagation(); openNote(session.session_id, notesMap[session.session_id]) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'0.9rem',color:'rgba(255,255,255,0.35)',padding:'4px 8px'}} title="Add recruiter note">📝</button>
                      <button onClick={e => { e.stopPropagation(); startComparePick(session) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'0.85rem',color: compareA?.session_id === session.session_id ? '#38b2ac' : 'rgba(255,255,255,0.3)',padding:'4px 8px'}} title="Pick for comparison">⚖</button>
                      <button onClick={e => { e.stopPropagation(); isInPipeline(session.session_id) ? removeFromPipeline(session.session_id) : addToPipeline(session) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'0.85rem',color: isInPipeline(session.session_id) ? '#68d391' : 'rgba(255,255,255,0.3)',padding:'4px 8px'}} title="Add to pipeline">⟳</button>
                      <button onClick={e => { e.stopPropagation(); openProfile(session.session_id) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'0.85rem',color:'rgba(255,255,255,0.35)',padding:'4px 8px'}} title="Deep profile view">👤</button>
                      <div className="h-score">{Math.round(session.readiness_score)}</div>
                    </div>
                  </div>
                  
                  {isExpanded && (
                    <div style={{marginTop: '20px', width: '100%', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '20px'}}>
                      <h4 style={{marginBottom:'10px', color: 'var(--teal)'}}>Candidate Profile Visualization</h4>
                      <div style={{height: '250px', width: '100%'}}>
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                            <PolarGrid stroke="rgba(255,255,255,0.2)" />
                            <PolarAngleAxis dataKey="subject" tick={{fill: 'var(--white-dim)'}} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                            <Radar name={session.candidate_name} dataKey="A" stroke="#2b6cb0" fill="#2b6cb0" fillOpacity={0.4} />
                            <Tooltip contentStyle={{background: 'var(--navy)', border: '1px solid #718096', borderRadius: '4px'}} />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                      <div style={{marginTop: '15px'}}>
                         <button className="btn-primary" onClick={(e) => { e.stopPropagation(); loadFullAnalysis(session.session_id) }} style={{fontSize: '0.85rem', padding: '8px 16px', display: 'inline-block'}}>Load Full Analysis</button>
                      </div>
                    </div>
                  )}
                </div>
              )}) : <p>No history yet.</p>}
            </div>
          </section>
        )}

        {activeTab === 'stats' && (
          <section className="stats-section animate-in">
            <h2>Analytics & Recruitment Dashboard</h2>
            {stats ? (
              <>
                <div className="stats-grid" style={{marginBottom: '30px'}}>
                  <div className="stat-card glass">
                    <h3>{stats.total_analyses ?? 0}</h3>
                    <p>Total Candidates Evaluated</p>
                  </div>
                  <div className="stat-card glass">
                    <h3>{stats.avg_readiness_score != null ? stats.avg_readiness_score : '—'}</h3>
                    <p>Average Readiness Score</p>
                  </div>
                  <div className="stat-card glass">
                    <h3>{stats.avg_skill_coverage != null ? stats.avg_skill_coverage : '—'}%</h3>
                    <p>Average Skills Match</p>
                  </div>
                  <div className="stat-card glass">
                    <h3 style={{fontSize: '1.2rem'}}>{stats.top_target_roles?.[0]?.target_role ?? '—'}</h3>
                    <p>Most Demanded Role (Top)</p>
                  </div>
                </div>

                <div className="card glass" style={{padding: '20px'}}>
                  <h3 style={{color: 'var(--white-dim)', marginBottom: '15px', fontWeight: 500}}>Candidate Timeline (Readiness Trend)</h3>
                  <div style={{height: '250px', width: '100%'}}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={history.slice(0, 20).reverse()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="candidate_name" stroke="var(--white-dim)" tick={{fontSize: 10}} />
                        <YAxis domain={[0, 100]} stroke="var(--white-dim)" />
                        <Tooltip contentStyle={{background: 'var(--navy)', border: '1px solid #718096', borderRadius: '4px'}} />
                        <Line type="monotone" dataKey="readiness_score" name="Readiness Score" stroke="#2b6cb0" strokeWidth={3} dot={{r: 4, fill: '#2b6cb0'}} activeDot={{r: 7}} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '30px'}}>
                    <div className="card glass" style={{padding: '20px'}}>
                      <h3 style={{color: 'var(--white-dim)', marginBottom: '15px', fontWeight: 500}}>Target Roles Evaluated</h3>
                      <div style={{height: '300px', width: '100%'}}>
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie data={stats.top_target_roles} dataKey="count" nameKey="target_role" cx="50%" cy="50%" outerRadius={90}>
                              {stats.top_target_roles.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip contentStyle={{background: 'var(--navy)', border: 'none', borderRadius: '8px'}} />
                            <Legend wrapperStyle={{fontSize: '12px'}} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    <div className="card glass" style={{padding: '20px'}}>
                      <h3 style={{color: 'var(--white-dim)', marginBottom: '15px', fontWeight: 500}}>Candidate Quality Tiers</h3>
                      <div style={{height: '300px', width: '100%'}}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={getQualityData()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" stroke="var(--white-dim)" tick={{fontSize: 11}} />
                            <YAxis stroke="var(--white-dim)" />
                            <Tooltip contentStyle={{background: 'var(--navy)', border: 'none', borderRadius: '8px'}} />
                            <Bar dataKey="count" name="Total Candidates" fill="var(--teal)" radius={[4, 4, 0, 0]}>
                               {getQualityData().map((entry, index) => (
                                 <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                               ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                </div>
                
              </>
            ) : <p>Loading advanced analytics...</p>}
          </section>
        )}

        {/* ── Notes Modal ── */}
        {noteTarget && (
          <div style={{position:'fixed',inset:0,background:'rgba(0,0,0,0.7)',zIndex:1000,display:'flex',alignItems:'center',justifyContent:'center'}} onClick={() => setNoteTarget(null)}>
            <div className="card glass" style={{width:'480px',padding:'28px',borderRadius:'12px'}} onClick={e=>e.stopPropagation()}>
              <h3 style={{marginBottom:'14px'}}>📝 Recruiter Notes</h3>
              <textarea value={noteText} onChange={e=>setNoteText(e.target.value)} placeholder="Add your recruiter notes for this candidate..." style={{width:'100%',minHeight:'120px',padding:'12px',background:'rgba(255,255,255,0.04)',color:'var(--white)',border:'1px solid rgba(255,255,255,0.12)',borderRadius:'6px',fontSize:'0.95rem',resize:'vertical'}} />
              <div style={{display:'flex',gap:'10px',marginTop:'14px',justifyContent:'flex-end'}}>
                <button onClick={() => setNoteTarget(null)} style={{padding:'8px 18px',background:'none',border:'1px solid rgba(255,255,255,0.15)',color:'var(--white-dim)',borderRadius:'6px',cursor:'pointer'}}>Cancel</button>
                <button onClick={saveNote} style={{padding:'8px 18px',background:'rgba(56,178,172,0.15)',border:'1px solid #38b2ac',color:'#38b2ac',borderRadius:'6px',cursor:'pointer'}}>Save Note</button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'compare' && (
          <section className="stats-section animate-in">
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'24px'}}>
              <h2 style={{margin:0}}>⚖ Candidate Comparison</h2>
              {(compareA || compareB) && <button onClick={clearCompare} style={{background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.15)',color:'var(--white-dim)',padding:'8px 16px',borderRadius:'6px',cursor:'pointer',fontSize:'0.85rem'}}>Clear & Return</button>}
            </div>

            {(!compareA || !compareB) ? (
              <div className="card glass" style={{padding:'40px',textAlign:'center'}}>
                <p style={{color:'var(--white-dim)',marginBottom:'12px',fontSize:'1.1rem'}}>No candidates selected for comparison.</p>
                <p style={{color:'rgba(255,255,255,0.35)',fontSize:'0.9rem'}}>Go to the <strong>History</strong> tab and click the <strong>⚖</strong> icon on two different candidates to compare them here.</p>
              </div>
            ) : (
              <>
                <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'20px',marginBottom:'24px'}}>
                  {[compareA, compareB].map((c, idx) => {
                    const tier = getTierBadge(c.readiness_score)
                    return (
                    <div key={idx} className="card glass" style={{padding:'20px'}}>
                      <h3 style={{marginBottom:'6px'}}>{c.candidate_name || 'Guest User'}</h3>
                      <p style={{color:'var(--white-dim)',fontSize:'0.85rem',marginBottom:'14px'}}>{c.target_role}</p>
                      <div style={{display:'flex',gap:'10px',flexWrap:'wrap',marginBottom:'14px'}}>
                        <span style={{fontSize:'0.78rem',padding:'3px 10px',borderRadius:'12px',border:`1px solid ${tier.border}`,color:tier.color,background:tier.bg}}>{tier.label}</span>
                      </div>
                      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'10px'}}>
                        {[
                          ['Readiness', Math.round(c.readiness_score) + '%'],
                          ['Coverage', c.skill_coverage_percent + '%'],
                          ['Gaps', c.critical_gap_count],
                          ['Hours', c.total_duration_hours + 'h'],
                        ].map(([label, val]) => (
                          <div key={label} style={{background:'rgba(255,255,255,0.04)',borderRadius:'8px',padding:'10px 12px'}}>
                            <div style={{fontSize:'0.75rem',color:'rgba(255,255,255,0.4)',marginBottom:'3px'}}>{label}</div>
                            <div style={{fontWeight:600,fontSize:'1.15rem'}}>{val}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )})}
                </div>

                <div className="card glass" style={{padding:'20px'}}>
                  <h3 style={{color:'var(--white-dim)',fontWeight:500,marginBottom:'15px'}}>Readiness Comparison</h3>
                  <div style={{height:'260px'}}>
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={[
                        {metric:'Readiness', A: compareA.readiness_score, B: compareB.readiness_score, fullMark:100},
                        {metric:'Coverage', A: compareA.skill_coverage_percent, B: compareB.skill_coverage_percent, fullMark:100},
                        {metric:'Low Gaps', A: Math.max(0,100-(compareA.critical_gap_count||0)*15), B: Math.max(0,100-(compareB.critical_gap_count||0)*15), fullMark:100},
                        {metric:'Low Hours', A: Math.max(0,100-compareA.total_duration_hours*2), B: Math.max(0,100-compareB.total_duration_hours*2), fullMark:100},
                      ]}>
                        <PolarGrid stroke="rgba(255,255,255,0.1)" />
                        <PolarAngleAxis dataKey="metric" tick={{fill:'rgba(255,255,255,0.5)',fontSize:12}} />
                        <PolarRadiusAxis angle={30} domain={[0,100]} tick={false} axisLine={false} />
                        <Radar name={compareA.candidate_name || 'A'} dataKey="A" stroke="#2b6cb0" fill="#2b6cb0" fillOpacity={0.3} />
                        <Radar name={compareB.candidate_name || 'B'} dataKey="B" stroke="#38b2ac" fill="#38b2ac" fillOpacity={0.3} />
                        <Legend wrapperStyle={{fontSize:'12px'}} />
                        <Tooltip contentStyle={{background:'#0d1b2a',border:'1px solid rgba(255,255,255,0.1)',borderRadius:'6px'}} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="card glass" style={{marginTop:'20px',padding:'20px'}}>
                  <h3 style={{color:'var(--white-dim)',fontWeight:500,marginBottom:'12px'}}>Head-to-Head Metrics</h3>
                  <table style={{width:'100%',borderCollapse:'collapse',fontSize:'0.9rem'}}>
                    <thead>
                      <tr style={{borderBottom:'1px solid rgba(255,255,255,0.08)'}}>
                        <th style={{padding:'10px 0',color:'rgba(255,255,255,0.4)',textAlign:'left',fontWeight:400}}>Metric</th>
                        <th style={{padding:'10px 0',color:'#7eb8d4',textAlign:'center',fontWeight:500}}>{compareA.candidate_name || 'Candidate A'}</th>
                        <th style={{padding:'10px 0',color:'#38b2ac',textAlign:'center',fontWeight:500}}>{compareB.candidate_name || 'Candidate B'}</th>
                        <th style={{padding:'10px 0',color:'rgba(255,255,255,0.4)',textAlign:'center',fontWeight:400}}>Winner</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ['Readiness Score', compareA.readiness_score, compareB.readiness_score, true],
                        ['Skill Coverage %', compareA.skill_coverage_percent, compareB.skill_coverage_percent, true],
                        ['Critical Gaps', compareA.critical_gap_count, compareB.critical_gap_count, false],
                        ['Training Hours', compareA.total_duration_hours, compareB.total_duration_hours, false],
                      ].map(([label, a, b, higherBetter]) => {
                        const aWins = higherBetter ? a > b : a < b
                        const tie = a === b
                        return (
                          <tr key={label} style={{borderBottom:'1px solid rgba(255,255,255,0.04)'}}>
                            <td style={{padding:'10px 0',color:'rgba(255,255,255,0.6)'}}>{label}</td>
                            <td style={{padding:'10px 0',textAlign:'center',color: aWins && !tie ? '#7eb8d4' : 'rgba(255,255,255,0.5)'}}>{typeof a === 'number' ? a.toFixed ? a.toFixed(1) : a : a}</td>
                            <td style={{padding:'10px 0',textAlign:'center',color: !aWins && !tie ? '#38b2ac' : 'rgba(255,255,255,0.5)'}}>{typeof b === 'number' ? b.toFixed ? b.toFixed(1) : b : b}</td>
                            <td style={{padding:'10px 0',textAlign:'center',color:'rgba(255,255,255,0.4)'}}>{tie ? '—' : aWins ? (compareA.candidate_name || 'A') : (compareB.candidate_name || 'B')}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>
        )}

        {activeTab === 'leaderboard' && (
          <section className="stats-section animate-in">
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'24px'}}>
              <h2 style={{margin:0}}>🏆 Candidate Leaderboard</h2>
              <span style={{color:'rgba(255,255,255,0.35)',fontSize:'0.85rem'}}>Top {Math.min(history.length, 20)} candidates by readiness score</span>
            </div>
            <div className="card glass" style={{overflow:'hidden'}}>
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:'0.9rem'}}>
                <thead>
                  <tr style={{background:'rgba(255,255,255,0.035)',borderBottom:'1px solid rgba(255,255,255,0.08)'}}>
                    <th style={{padding:'12px 16px',color:'rgba(255,255,255,0.4)',textAlign:'left',fontWeight:400,width:'50px'}}>#</th>
                    <th style={{padding:'12px 16px',color:'rgba(255,255,255,0.4)',textAlign:'left',fontWeight:400}}>Candidate</th>
                    <th style={{padding:'12px 16px',color:'rgba(255,255,255,0.4)',textAlign:'left',fontWeight:400}}>Role</th>
                    <th style={{padding:'12px 16px',color:'rgba(255,255,255,0.4)',textAlign:'center',fontWeight:400}}>Tier</th>
                    <th style={{padding:'12px 16px',color:'rgba(255,255,255,0.4)',textAlign:'center',fontWeight:400}}>Score</th>
                    <th style={{padding:'12px 16px',color:'rgba(255,255,255,0.4)',textAlign:'center',fontWeight:400}}>Coverage</th>
                    <th style={{padding:'12px 16px',color:'rgba(255,255,255,0.4)',textAlign:'center',fontWeight:400}}>Gaps</th>
                    <th style={{padding:'12px 16px',color:'rgba(255,255,255,0.4)',textAlign:'center',fontWeight:400}}>⭐</th>
                  </tr>
                </thead>
                <tbody>
                  {[...history].sort((a,b) => b.readiness_score - a.readiness_score).slice(0,20).map((h, i) => {
                    const tier = getTierBadge(h.readiness_score)
                    const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i+1}`
                    return (
                      <tr key={h.session_id} style={{borderBottom:'1px solid rgba(255,255,255,0.04)',cursor:'pointer',transition:'background 0.15s'}} onClick={() => openProfile(h.session_id)} onMouseEnter={e=>e.currentTarget.style.background='rgba(255,255,255,0.03)'} onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
                        <td style={{padding:'12px 16px',textAlign:'center',fontSize:'1rem'}}>{medal}</td>
                        <td style={{padding:'12px 16px',fontWeight:500}}>{h.candidate_name || 'Guest User'}</td>
                        <td style={{padding:'12px 16px',color:'rgba(255,255,255,0.5)',fontSize:'0.85rem'}}>{h.target_role}</td>
                        <td style={{padding:'12px 16px',textAlign:'center'}}><span style={{fontSize:'0.72rem',padding:'2px 8px',borderRadius:'12px',border:`1px solid ${tier.border}`,color:tier.color,background:tier.bg}}>{tier.label}</span></td>
                        <td style={{padding:'12px 16px',textAlign:'center',fontWeight:600,color:'rgba(255,255,255,0.9)'}}>{Math.round(h.readiness_score)}</td>
                        <td style={{padding:'12px 16px',textAlign:'center',color:'rgba(255,255,255,0.6)'}}>{h.skill_coverage_percent}%</td>
                        <td style={{padding:'12px 16px',textAlign:'center',color: (h.critical_gap_count||0) > 3 ? '#fc8181' : '#68d391'}}>{h.critical_gap_count || 0}</td>
                        <td style={{padding:'12px 16px',textAlign:'center'}}><button onClick={e=>{e.stopPropagation();toggleShortlist(h.session_id)}} style={{background:'none',border:'none',cursor:'pointer',fontSize:'1rem',opacity:shortlisted.includes(h.session_id)?1:0.3}}>{shortlisted.includes(h.session_id)?'⭐':'☆'}</button></td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              {history.length === 0 && <p style={{textAlign:'center',padding:'40px',color:'rgba(255,255,255,0.3)'}}>No candidates evaluated yet.</p>}
            </div>
          </section>
        )}

        {activeTab === 'pipeline' && (
          <section className="stats-section animate-in">
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'24px'}}>
              <div>
                <h2 style={{margin:'0 0 4px'}}>📋 Talent Pipeline</h2>
                <p style={{margin:0,color:'rgba(255,255,255,0.35)',fontSize:'0.85rem'}}>Track candidates through your hiring stages. Add them from the History tab using the ⟳ button.</p>
              </div>
              <span style={{color:'rgba(255,255,255,0.3)',fontSize:'0.85rem'}}>{Object.values(pipeline).flat().length} candidates tracked</span>
            </div>

            <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'16px',alignItems:'start'}}>
              {[
                { key:'Applied', label:'Applied', icon:'📥', color:'#718096', light:'rgba(113,128,150,0.1)' },
                { key:'Screening', label:'Screening', icon:'🔍', color:'#4299e1', light:'rgba(66,153,225,0.1)' },
                { key:'Technical', label:'Technical', icon:'⚙', color:'#9f7aea', light:'rgba(159,122,234,0.1)' },
                { key:'Offer', label:'Offer', icon:'✅', color:'#48bb78', light:'rgba(72,187,120,0.1)' },
              ].map(stage => (
                <div key={stage.key} style={{background:'rgba(255,255,255,0.025)',borderRadius:'12px',border:'1px solid rgba(255,255,255,0.06)',overflow:'hidden'}}>
                  {/* Stage header */}
                  <div style={{padding:'14px 16px',borderBottom:'1px solid rgba(255,255,255,0.06)',display:'flex',alignItems:'center',justifyContent:'space-between',background:stage.light}}>
                    <div style={{display:'flex',alignItems:'center',gap:'8px'}}>
                      <span>{stage.icon}</span>
                      <span style={{fontWeight:500,fontSize:'0.9rem',color:stage.color}}>{stage.label}</span>
                    </div>
                    <span style={{fontSize:'0.8rem',color:'rgba(255,255,255,0.3)',background:'rgba(255,255,255,0.06)',padding:'2px 8px',borderRadius:'12px'}}>{(pipeline[stage.key]||[]).length}</span>
                  </div>

                  {/* Cards */}
                  <div style={{padding:'10px',minHeight:'120px',display:'flex',flexDirection:'column',gap:'8px'}}>
                    {(pipeline[stage.key]||[]).length === 0 && (
                      <p style={{textAlign:'center',color:'rgba(255,255,255,0.15)',fontSize:'0.8rem',padding:'20px 0',margin:0}}>Empty</p>
                    )}
                    {(pipeline[stage.key]||[]).map(card => {
                      const tier = getTierBadge(card.score)
                      const stages = ['Applied','Screening','Technical','Offer']
                      const curIdx = stages.indexOf(stage.key)
                      return (
                        <div key={card.id} style={{background:'rgba(255,255,255,0.04)',borderRadius:'8px',padding:'12px',border:'1px solid rgba(255,255,255,0.06)'}}>
                          <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:'6px'}}>
                            <span style={{fontWeight:500,fontSize:'0.88rem',lineHeight:1.3}}>{card.name}</span>
                            <span style={{fontSize:'0.72rem',padding:'1px 6px',borderRadius:'10px',border:`1px solid ${tier.border}`,color:tier.color,background:tier.bg,flexShrink:0,marginLeft:'6px'}}>{card.score}</span>
                          </div>
                          <p style={{margin:'0 0 8px',fontSize:'0.75rem',color:'rgba(255,255,255,0.35)',lineHeight:1.3}}>{card.role}</p>
                          <div style={{display:'flex',gap:'4px',flexWrap:'wrap'}}>
                            {curIdx > 0 && <button onClick={() => movePipelineCard(card.id,stage.key,stages[curIdx-1])} style={{fontSize:'0.7rem',padding:'2px 7px',background:'rgba(255,255,255,0.05)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:'4px',color:'rgba(255,255,255,0.4)',cursor:'pointer'}}>← Back</button>}
                            {curIdx < stages.length-1 && <button onClick={() => movePipelineCard(card.id,stage.key,stages[curIdx+1])} style={{fontSize:'0.7rem',padding:'2px 7px',background:`rgba(${stage.color.replace('#','').match(/../g).map(h=>parseInt(h,16)).join(',')},0.15)`,border:`1px solid ${stage.color}`,borderRadius:'4px',color:stage.color,cursor:'pointer'}}>Next →</button>}
                            <button onClick={() => removeFromPipeline(card.id)} style={{fontSize:'0.7rem',padding:'2px 6px',background:'none',border:'none',color:'rgba(255,255,255,0.2)',cursor:'pointer',marginLeft:'auto'}}>✕</button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {activeTab === 'skills' && (
          <section className="stats-section animate-in">
            <div style={{marginBottom:'24px'}}>
              <h2 style={{margin:'0 0 4px'}}>🔬 Skills Intelligence</h2>
              <p style={{margin:0,color:'rgba(255,255,255,0.35)',fontSize:'0.85rem'}}>Demand analytics derived from your candidate evaluation history.</p>
            </div>

            {history.length === 0 ? (
              <div className="card glass" style={{padding:'60px',textAlign:'center'}}>
                <p style={{color:'rgba(255,255,255,0.3)'}}>No evaluations yet. Run some analyses to populate this dashboard.</p>
              </div>
            ) : (() => {
              const { hireData, scoreDistribution } = getSkillsIntelligence()
              return (
                <>
                  {/* Summary KPIs */}
                  <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'12px',marginBottom:'24px'}}>
                    {[
                      ['Total Evaluations', history.length, '#90cdf4'],
                      ['Avg Readiness', Math.round(history.reduce((s,h)=>s+h.readiness_score,0)/history.length)+'%', '#68d391'],
                      ['Shortlisted', shortlisted.length, '#f6ad55'],
                      ['In Pipeline', Object.values(pipeline).flat().length, '#a0aec0'],
                    ].map(([lbl,val,col])=>(
                      <div key={lbl} style={{background:'rgba(255,255,255,0.04)',borderRadius:'10px',padding:'16px',textAlign:'center',border:'1px solid rgba(255,255,255,0.06)'}}>
                        <div style={{fontSize:'0.72rem',color:'rgba(255,255,255,0.35)',marginBottom:'6px',textTransform:'uppercase',letterSpacing:'0.08em'}}>{lbl}</div>
                        <div style={{fontSize:'1.6rem',fontWeight:700,color:col}}>{val}</div>
                      </div>
                    ))}
                  </div>

                  <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'20px',marginBottom:'20px'}}>
                    {/* Score distribution */}
                    <div className="card glass" style={{padding:'20px'}}>
                      <h3 style={{color:'rgba(255,255,255,0.5)',fontWeight:400,marginBottom:'16px',fontSize:'0.85rem',textTransform:'uppercase',letterSpacing:'0.08em'}}>Score Distribution</h3>
                      <div style={{height:'220px'}}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={scoreDistribution} margin={{top:0,right:10,left:-20,bottom:0}}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                            <XAxis dataKey="range" stroke="rgba(255,255,255,0.2)" tick={{fontSize:11,fill:'rgba(255,255,255,0.4)'}} />
                            <YAxis stroke="rgba(255,255,255,0.2)" tick={{fontSize:11,fill:'rgba(255,255,255,0.35)'}} />
                            <Tooltip contentStyle={{background:'#0d1b2a',border:'1px solid rgba(255,255,255,0.1)',borderRadius:'6px'}} />
                            <Bar dataKey="count" name="Candidates" radius={[3,3,0,0]}>
                              {scoreDistribution.map((e,i)=><Cell key={i} fill={['#2f855a','#276749','#2c7a7b','#2b6cb0','#4a5568','#742a2a'][i]} />)}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Avg score by role */}
                    <div className="card glass" style={{padding:'20px'}}>
                      <h3 style={{color:'rgba(255,255,255,0.5)',fontWeight:400,marginBottom:'16px',fontSize:'0.85rem',textTransform:'uppercase',letterSpacing:'0.08em'}}>Avg. Readiness by Role</h3>
                      <div style={{height:'220px'}}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={hireData} layout="vertical" margin={{top:0,right:10,left:0,bottom:0}}>
                            <XAxis type="number" domain={[0,100]} stroke="rgba(255,255,255,0.2)" tick={{fontSize:10,fill:'rgba(255,255,255,0.35)'}} />
                            <YAxis dataKey="role" type="category" width={100} stroke="rgba(255,255,255,0.2)" tick={{fontSize:10,fill:'rgba(255,255,255,0.5)'}} />
                            <Tooltip contentStyle={{background:'#0d1b2a',border:'1px solid rgba(255,255,255,0.1)',borderRadius:'6px'}} formatter={(v,n,p)=>[v+'%','Avg Readiness']} />
                            <Bar dataKey="avgScore" name="Avg Score" radius={[0,3,3,0]}>
                              {hireData.map((e,i)=><Cell key={i} fill={e.avgScore>=70?'#2b6cb0':'#4a5568'} />)}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  {/* Hiring Funnel */}
                  <div className="card glass" style={{padding:'20px'}}>
                    <h3 style={{color:'rgba(255,255,255,0.5)',fontWeight:400,marginBottom:'16px',fontSize:'0.85rem',textTransform:'uppercase',letterSpacing:'0.08em'}}>Hiring Funnel Depth</h3>
                    <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'1px',background:'rgba(255,255,255,0.06)',borderRadius:'10px',overflow:'hidden'}}>
                      {[
                        {stage:'Applied',val:history.length,pct:100},
                        {stage:'Screening',val:pipeline['Screening']?.length||0,pct:Math.round((pipeline['Screening']?.length||0)/Math.max(history.length,1)*100)},
                        {stage:'Technical',val:pipeline['Technical']?.length||0,pct:Math.round((pipeline['Technical']?.length||0)/Math.max(history.length,1)*100)},
                        {stage:'Offer',val:pipeline['Offer']?.length||0,pct:Math.round((pipeline['Offer']?.length||0)/Math.max(history.length,1)*100)},
                      ].map((f,i)=>(
                        <div key={f.stage} style={{background:'rgba(255,255,255,0.03)',padding:'20px',textAlign:'center'}}>
                          <div style={{fontSize:'0.72rem',color:'rgba(255,255,255,0.35)',marginBottom:'8px',textTransform:'uppercase',letterSpacing:'0.08em'}}>{f.stage}</div>
                          <div style={{fontSize:'1.8rem',fontWeight:700,marginBottom:'4px'}}>{f.val}</div>
                          <div style={{fontSize:'0.78rem',color:'rgba(255,255,255,0.3)'}}>{f.pct}% of total</div>
                          <div style={{marginTop:'10px',height:'4px',background:'rgba(255,255,255,0.06)',borderRadius:'2px'}}>
                            <div style={{height:'100%',width:`${f.pct}%`,background:['#4a5568','#2b6cb0','#6b46c1','#276749'][i],borderRadius:'2px',transition:'width 0.5s ease'}} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )
            })()}
          </section>
        )}

        {/* ── Deep Candidate Profile Sheet ── */}
        {profileSheet && profileSheet !== 'loading' && (
          <div style={{position:'fixed',inset:0,background:'rgba(4,10,20,0.95)',zIndex:2000,overflowY:'auto'}} onClick={closeProfile}>
            <div style={{maxWidth:'900px',margin:'40px auto',padding:'32px',background:'rgba(255,255,255,0.03)',borderRadius:'16px',border:'1px solid rgba(255,255,255,0.07)'}} onClick={e=>e.stopPropagation()}>
              {/* Header */}
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:'28px'}}>
                <div>
                  <div style={{display:'flex',alignItems:'center',gap:'12px',marginBottom:'6px'}}>
                    <h2 style={{margin:0,fontSize:'1.5rem'}}>{profileSheet.candidate_name || 'Guest User'}</h2>
                    {(() => { const t = getTierBadge(profileSheet.readiness_score); return <span style={{fontSize:'0.78rem',padding:'3px 12px',borderRadius:'20px',border:`1px solid ${t.border}`,color:t.color,background:t.bg}}>{t.label}</span> })()}
                  </div>
                  <p style={{margin:0,color:'rgba(255,255,255,0.45)',fontSize:'0.95rem'}}>{profileSheet.target_role} · {profileSheet.domain}</p>
                </div>
                <button onClick={closeProfile} style={{background:'none',border:'1px solid rgba(255,255,255,0.15)',color:'rgba(255,255,255,0.5)',padding:'8px 16px',borderRadius:'8px',cursor:'pointer',fontSize:'0.9rem'}}>✕ Close</button>
              </div>

              {/* KPIs Row */}
              <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'12px',marginBottom:'28px'}}>
                {[
                  ['Readiness', Math.round(profileSheet.readiness_score) + '%', profileSheet.readiness_score >= 70 ? '#68d391' : '#fc8181'],
                  ['Coverage', profileSheet.skill_coverage_percent + '%', '#90cdf4'],
                  ['Skill Gaps', profileSheet.skill_gaps?.length || 0, '#f6ad55'],
                  ['Training', (profileSheet.total_duration_hours || 0) + 'h', '#a0aec0'],
                ].map(([lbl, val, col]) => (
                  <div key={lbl} style={{background:'rgba(255,255,255,0.04)',borderRadius:'10px',padding:'16px',textAlign:'center'}}>
                    <div style={{fontSize:'0.72rem',color:'rgba(255,255,255,0.35)',marginBottom:'6px',textTransform:'uppercase',letterSpacing:'0.08em'}}>{lbl}</div>
                    <div style={{fontSize:'1.6rem',fontWeight:700,color:col}}>{val}</div>
                  </div>
                ))}
              </div>

              {/* Skills row */}
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'16px',marginBottom:'24px'}}>
                <div style={{background:'rgba(255,255,255,0.03)',borderRadius:'10px',padding:'18px'}}>
                  <h4 style={{margin:'0 0 12px',color:'rgba(255,255,255,0.5)',fontWeight:400,fontSize:'0.8rem',textTransform:'uppercase',letterSpacing:'0.1em'}}>Strengths</h4>
                  <div style={{display:'flex',flexWrap:'wrap',gap:'8px'}}>
                    {(profileSheet.strengths||[]).map((s,i)=><span key={i} style={{fontSize:'0.8rem',padding:'4px 10px',borderRadius:'20px',background:'rgba(104,211,145,0.1)',border:'1px solid rgba(104,211,145,0.3)',color:'#68d391'}}>{s}</span>)}
                    {(profileSheet.strengths||[]).length === 0 && <span style={{color:'rgba(255,255,255,0.25)',fontSize:'0.85rem'}}>None detected</span>}
                  </div>
                </div>
                <div style={{background:'rgba(255,255,255,0.03)',borderRadius:'10px',padding:'18px'}}>
                  <h4 style={{margin:'0 0 12px',color:'rgba(255,255,255,0.5)',fontWeight:400,fontSize:'0.8rem',textTransform:'uppercase',letterSpacing:'0.1em'}}>Critical Gaps</h4>
                  <div style={{display:'flex',flexWrap:'wrap',gap:'8px'}}>
                    {(profileSheet.critical_gaps||[]).map((s,i)=><span key={i} style={{fontSize:'0.8rem',padding:'4px 10px',borderRadius:'20px',background:'rgba(252,129,129,0.1)',border:'1px solid rgba(252,129,129,0.3)',color:'#fc8181'}}>{s}</span>)}
                    {(profileSheet.critical_gaps||[]).length === 0 && <span style={{color:'rgba(255,255,255,0.25)',fontSize:'0.85rem'}}>None — strong match!</span>}
                  </div>
                </div>
              </div>

              {/* Radar + Training Timeline */}
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'16px',marginBottom:'24px'}}>
                <div style={{background:'rgba(255,255,255,0.03)',borderRadius:'10px',padding:'18px'}}>
                  <h4 style={{margin:'0 0 14px',color:'rgba(255,255,255,0.5)',fontWeight:400,fontSize:'0.8rem',textTransform:'uppercase',letterSpacing:'0.1em'}}>Profile Radar</h4>
                  <div style={{height:'200px'}}>
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={[
                        {m:'Readiness', v: profileSheet.readiness_score, fullMark:100},
                        {m:'Coverage', v: profileSheet.skill_coverage_percent, fullMark:100},
                        {m:'Low Gaps', v: Math.max(0,100-(profileSheet.skill_gaps?.length||0)*15), fullMark:100},
                        {m:'Time Eff.', v: Math.max(0,100-(profileSheet.total_duration_hours||0)*2), fullMark:100},
                      ]}>
                        <PolarGrid stroke="rgba(255,255,255,0.07)" />
                        <PolarAngleAxis dataKey="m" tick={{fill:'rgba(255,255,255,0.4)',fontSize:11}} />
                        <PolarRadiusAxis angle={30} domain={[0,100]} tick={false} axisLine={false} />
                        <Radar dataKey="v" stroke="#4299e1" fill="#4299e1" fillOpacity={0.25} />
                        <Tooltip contentStyle={{background:'#0d1b2a',border:'1px solid rgba(255,255,255,0.1)',borderRadius:'6px'}} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div style={{background:'rgba(255,255,255,0.03)',borderRadius:'10px',padding:'18px'}}>
                  <h4 style={{margin:'0 0 14px',color:'rgba(255,255,255,0.5)',fontWeight:400,fontSize:'0.8rem',textTransform:'uppercase',letterSpacing:'0.1em'}}>Gap Training Load</h4>
                  <div style={{height:'200px'}}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={(profileSheet.skill_gaps||[]).slice(0,6).map(g=>({name:g.skill,h:g.estimated_hours||Math.round(Math.random()*20+5)}))} layout="vertical" margin={{top:0,right:10,left:0,bottom:0}}>
                        <XAxis type="number" stroke="rgba(255,255,255,0.2)" tick={{fontSize:10,fill:'rgba(255,255,255,0.35)'}} />
                        <YAxis dataKey="name" type="category" width={80} stroke="rgba(255,255,255,0.2)" tick={{fontSize:10,fill:'rgba(255,255,255,0.5)'}} />
                        <Tooltip contentStyle={{background:'#0d1b2a',border:'1px solid rgba(255,255,255,0.1)',borderRadius:'6px'}} />
                        <Bar dataKey="h" name="Hours" fill="#2b6cb0" radius={[0,3,3,0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Recruiter Notes */}
              <div style={{background:'rgba(255,255,255,0.03)',borderRadius:'10px',padding:'18px',marginBottom:'16px'}}>
                <h4 style={{margin:'0 0 10px',color:'rgba(255,255,255,0.5)',fontWeight:400,fontSize:'0.8rem',textTransform:'uppercase',letterSpacing:'0.1em'}}>Recruiter Notes</h4>
                {notesMap[profileSheet.session_id]
                  ? <p style={{margin:0,color:'rgba(255,255,255,0.7)',lineHeight:1.6,fontSize:'0.9rem'}}>{notesMap[profileSheet.session_id]}</p>
                  : <p style={{margin:0,color:'rgba(255,255,255,0.25)',fontSize:'0.85rem',fontStyle:'italic'}}>No notes added yet.</p>
                }
              </div>

              {/* Actions */}
              <div style={{display:'flex',gap:'10px',flexWrap:'wrap'}}>
                <button onClick={() => { loadFullAnalysis(profileSheet.session_id); closeProfile() }} style={{padding:'10px 20px',background:'rgba(43,108,176,0.15)',border:'1px solid #2b6cb0',color:'#90cdf4',borderRadius:'8px',cursor:'pointer',fontSize:'0.9rem'}}>Load Full Analysis</button>
                <button onClick={() => openNote(profileSheet.session_id, notesMap[profileSheet.session_id])} style={{padding:'10px 20px',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.15)',color:'var(--white-dim)',borderRadius:'8px',cursor:'pointer',fontSize:'0.9rem'}}>📝 Edit Notes</button>
                <button onClick={() => exportJSON(profileSheet, `${profileSheet.candidate_name||'candidate'}_profile.json`)} style={{padding:'10px 20px',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.15)',color:'var(--white-dim)',borderRadius:'8px',cursor:'pointer',fontSize:'0.9rem'}}>⬇ Export JSON</button>
                <button onClick={() => toggleShortlist(profileSheet.session_id)} style={{padding:'10px 20px',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.15)',color: shortlisted.includes(profileSheet.session_id) ? '#f6ad55' : 'var(--white-dim)',borderRadius:'8px',cursor:'pointer',fontSize:'0.9rem'}}>{shortlisted.includes(profileSheet.session_id) ? '⭐ Shortlisted' : '☆ Shortlist'}</button>
              </div>
            </div>
          </div>
        )}
        {profileSheet === 'loading' && (
          <div style={{position:'fixed',inset:0,background:'rgba(4,10,20,0.9)',zIndex:2000,display:'flex',alignItems:'center',justifyContent:'center'}}>
            <div style={{textAlign:'center'}}>
              <div style={{width:'40px',height:'40px',border:'3px solid rgba(255,255,255,0.1)',borderTopColor:'#4299e1',borderRadius:'50%',animation:'spin 0.8s linear infinite',margin:'0 auto 12px'}} />
              <p style={{color:'rgba(255,255,255,0.4)'}}>Loading profile…</p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
