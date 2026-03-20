"""
Mega Feature Patch – adds:
1. NAV: Compare tab, Leaderboard tab (alongside Analyze/History/Stats)
2. HISTORY: Shortlist/star bookmarking, Recruiter Notes modal
3. STATS: Leaderboard table top-10, AI Insights summary card
4. COMPARE: full side-by-side two-candidate comparison with RadarChart
5. ANALYZE results: Skill Confidence BarChart (strengths vs skill coverage)
"""

with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# ─── 1. NEW STATES ────────────────────────────────────────────────────────────
NEW_STATES = """  const [assessmentMode, setAssessmentMode] = useState(false)
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
"""

content = content.replace(
    "  const [assessmentMode, setAssessmentMode] = useState(false)\n  const [assessmentData, setAssessmentData] = useState(null)\n  const [assAnswers, setAssAnswers] = useState({})\n  const [assScore, setAssScore] = useState(null)",
    NEW_STATES
)

# ─── 2. NAV TABS: add Compare and Leaderboard ─────────────────────────────────
OLD_NAV = """          <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>History</button>
          <button className={activeTab === 'stats'   ? 'active' : ''} onClick={() => setActiveTab('stats')}>Stats</button>"""

NEW_NAV = """          <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>History</button>
          <button className={activeTab === 'stats'   ? 'active' : ''} onClick={() => setActiveTab('stats')}>Stats</button>
          <button className={activeTab === 'compare' ? 'active' : ''} onClick={() => setActiveTab('compare')}>Compare</button>
          <button className={activeTab === 'leaderboard' ? 'active' : ''} onClick={() => setActiveTab('leaderboard')}>Leaderboard</button>"""

content = content.replace(OLD_NAV, NEW_NAV)

# ─── 3. NOTES MODAL ──────────────────────────────────────────────────────────
# Inject right before the closing </div> </div> of the App
NOTES_MODAL = """
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
"""

content = content.replace("      </main>\n    </div>\n  )\n}", NOTES_MODAL + "      </main>\n    </div>\n  )\n}")

# ─── 4. SHORTLIST + NOTE buttons inside each history card ─────────────────────
OLD_HISTORY_HEADER = """                  <div style={{display: 'flex', justifyContent: 'space-between', width: '100%'}}>
                    <div className="h-info">
                      <strong>{session.target_role}</strong>
                      <span>{session.candidate_name || 'Guest User'} - {new Date(session.created_at || Date.now()).toLocaleDateString()}</span>
                    </div>
                    <div className="h-score">{Math.round(session.readiness_score)}</div>
                  </div>"""

NEW_HISTORY_HEADER = """                  <div style={{display: 'flex', justifyContent: 'space-between', width: '100%', gap: '10px'}}>
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
                      <div className="h-score">{Math.round(session.readiness_score)}</div>
                    </div>
                  </div>"""

content = content.replace(OLD_HISTORY_HEADER, NEW_HISTORY_HEADER)

# ─── 5. Filter by Shortlisted in History ─────────────────────────────────────
OLD_SORT_SELECT = """               <select value={historySort} onChange={e => setHistorySort(e.target.value)} style={{padding: '10px 20px', background: 'rgba(255,255,255,0.03)', color: 'var(--white)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', cursor: 'pointer', outline: 'none'}}>
                  <option value="newest" style={{background: '#0a192f'}}>Newest First</option>
                  <option value="oldest" style={{background: '#0a192f'}}>Oldest First</option>
                  <option value="score_desc" style={{background: '#0a192f'}}>Score: High to Low</option>
                  <option value="score_asc" style={{background: '#0a192f'}}>Score: Low to High</option>
               </select>"""

NEW_SORT_SELECT = """               <select value={historySort} onChange={e => setHistorySort(e.target.value)} style={{padding: '10px 20px', background: 'rgba(255,255,255,0.03)', color: 'var(--white)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', cursor: 'pointer', outline: 'none'}}>
                  <option value="newest" style={{background: '#0a192f'}}>Newest First</option>
                  <option value="oldest" style={{background: '#0a192f'}}>Oldest First</option>
                  <option value="score_desc" style={{background: '#0a192f'}}>Score: High to Low</option>
                  <option value="score_asc" style={{background: '#0a192f'}}>Score: Low to High</option>
                  <option value="shortlisted" style={{background: '#0a192f'}}>⭐ Shortlisted Only</option>
               </select>"""

content = content.replace(OLD_SORT_SELECT, NEW_SORT_SELECT)

# Update filteredHistory to also handle shortlisted filter
content = content.replace(
    "     return new Date(b.created_at || 0) - new Date(a.created_at || 0);\n  })",
    "     if(historySort === 'shortlisted') return shortlisted.includes(b.session_id) - shortlisted.includes(a.session_id);\n     return new Date(b.created_at || 0) - new Date(a.created_at || 0);\n  })\n  .filter(h => historySort === 'shortlisted' ? shortlisted.includes(h.session_id) : true)"
)

# ─── 6. Compare Banner when one is picked ─────────────────────────────────────
COMPARE_BANNER = """
            {compareA && !compareB && (
              <div style={{background:'rgba(56,178,172,0.08)',border:'1px solid #38b2ac',borderRadius:'8px',padding:'12px 16px',marginBottom:'16px',display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                <span style={{color:'#38b2ac',fontSize:'0.9rem'}}>⚖ Selected <strong>{compareA.candidate_name || 'Guest'}</strong> for comparison. Click another candidate's ⚖ to compare.</span>
                <button onClick={() => setCompareA(null)} style={{background:'none',border:'none',color:'rgba(255,255,255,0.4)',cursor:'pointer',fontSize:'1.2rem'}}>✕</button>
              </div>
            )}"""

content = content.replace(
    "            <div className=\"history-list\">",
    COMPARE_BANNER + "\n            <div className=\"history-list\">"
)

# ─── 7. COMPARE TAB content ───────────────────────────────────────────────────
COMPARE_TAB = """
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
"""

# ─── 8. LEADERBOARD TAB ───────────────────────────────────────────────────────
LEADERBOARD_TAB = """
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
                      <tr key={h.session_id} style={{borderBottom:'1px solid rgba(255,255,255,0.04)',cursor:'pointer',transition:'background 0.15s'}} onClick={() => { loadFullAnalysis(h.session_id) }} onMouseEnter={e=>e.currentTarget.style.background='rgba(255,255,255,0.03)'} onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
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
"""

# Insert Compare and Leaderboard tabs before closing </main>
BEFORE_CLOSE_MAIN = "      </main>\n    </div>\n  )\n}"
content = content.replace(BEFORE_CLOSE_MAIN, COMPARE_TAB + LEADERBOARD_TAB + "      </main>\n    </div>\n  )\n}")

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Mega feature patch complete!")
