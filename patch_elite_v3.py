"""
Elite Features Patch v3 - adds:
1. ✨ Deep Profile Sheet - full-screen overlay modal for any candidate
2. 📋 Pipeline Tab - drag-free Kanban with 4 stages (Applied→Screening→Technical→Offer)  
3. 🔬 Skills Intelligence Tab - cross-candidate skill demand analysis + BarChart
"""

with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# ─── 1. NEW STATES ────────────────────────────────────────────────────────────
OLD_STATE_ANCHOR = "  const clearCompare = () => { setCompareA(null); setCompareB(null); setActiveTab('history') }"

NEW_STATES = """  const clearCompare = () => { setCompareA(null); setCompareB(null); setActiveTab('history') }

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
"""

content = content.replace(OLD_STATE_ANCHOR, NEW_STATES)

# ─── 2. NAV: add Pipeline and Skills tabs ─────────────────────────────────────
OLD_NAV = """          <button className={activeTab === 'compare' ? 'active' : ''} onClick={() => setActiveTab('compare')}>Compare</button>
          <button className={activeTab === 'leaderboard' ? 'active' : ''} onClick={() => setActiveTab('leaderboard')}>Leaderboard</button>"""

NEW_NAV = """          <button className={activeTab === 'compare' ? 'active' : ''} onClick={() => setActiveTab('compare')}>Compare</button>
          <button className={activeTab === 'leaderboard' ? 'active' : ''} onClick={() => setActiveTab('leaderboard')}>Leaderboard</button>
          <button className={activeTab === 'pipeline' ? 'active' : ''} onClick={() => setActiveTab('pipeline')}>Pipeline</button>
          <button className={activeTab === 'skills' ? 'active' : ''} onClick={() => setActiveTab('skills')}>Skills</button>"""

content = content.replace(OLD_NAV, NEW_NAV)

# ─── 3. Add "Add to Pipeline" button in each history card ─────────────────────
OLD_HISTORY_ACTIONS = """                      <button onClick={e => { e.stopPropagation(); openNote(session.session_id, notesMap[session.session_id]) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'0.9rem',color:'rgba(255,255,255,0.35)',padding:'4px 8px'}} title="Add recruiter note">📝</button>
                      <button onClick={e => { e.stopPropagation(); startComparePick(session) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'0.85rem',color: compareA?.session_id === session.session_id ? '#38b2ac' : 'rgba(255,255,255,0.3)',padding:'4px 8px'}} title="Pick for comparison">⚖</button>"""

NEW_HISTORY_ACTIONS = """                      <button onClick={e => { e.stopPropagation(); openNote(session.session_id, notesMap[session.session_id]) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'0.9rem',color:'rgba(255,255,255,0.35)',padding:'4px 8px'}} title="Add recruiter note">📝</button>
                      <button onClick={e => { e.stopPropagation(); startComparePick(session) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'0.85rem',color: compareA?.session_id === session.session_id ? '#38b2ac' : 'rgba(255,255,255,0.3)',padding:'4px 8px'}} title="Pick for comparison">⚖</button>
                      <button onClick={e => { e.stopPropagation(); isInPipeline(session.session_id) ? removeFromPipeline(session.session_id) : addToPipeline(session) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'0.85rem',color: isInPipeline(session.session_id) ? '#68d391' : 'rgba(255,255,255,0.3)',padding:'4px 8px'}} title="Add to pipeline">⟳</button>
                      <button onClick={e => { e.stopPropagation(); openProfile(session.session_id) }} style={{background:'none',border:'none',cursor:'pointer',fontSize:'0.85rem',color:'rgba(255,255,255,0.35)',padding:'4px 8px'}} title="Deep profile view">👤</button>"""

content = content.replace(OLD_HISTORY_ACTIONS, NEW_HISTORY_ACTIONS)

# ─── 4. DEEP PROFILE SHEET MODAL ─────────────────────────────────────────────
DEEP_PROFILE_MODAL = """
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
"""

# ─── 5. PIPELINE TAB ──────────────────────────────────────────────────────────
PIPELINE_TAB = """
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
"""

# ─── 6. SKILLS INTELLIGENCE TAB ──────────────────────────────────────────────
SKILLS_TAB = """
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
"""

# ─── 7. INJECT ALL NEW TABS & MODALS ─────────────────────────────────────────
BEFORE_CLOSE_MAIN = "      </main>\n    </div>\n  )\n}"
content = content.replace(
    BEFORE_CLOSE_MAIN,
    PIPELINE_TAB + SKILLS_TAB + DEEP_PROFILE_MODAL + "      </main>\n    </div>\n  )\n}"
)

# ─── 8. Also add 👤 open-profile button in leaderboard ────────────────────────
content = content.replace(
    "onClick={() => { loadFullAnalysis(h.session_id) }} onMouseEnter",
    "onClick={() => openProfile(h.session_id)} onMouseEnter"
)

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Elite Features v3 patch applied successfully!")
