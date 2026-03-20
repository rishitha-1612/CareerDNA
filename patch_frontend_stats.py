import re

with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Inject Recharts Import
IMPORT_STR = "import { useState, useEffect, useRef, useCallback } from 'react'\nimport { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, CartesianGrid } from 'recharts'\n"
content = content.replace("import { useState, useEffect, useRef, useCallback } from 'react'", IMPORT_STR)

# 2. Add custom candidate name state & modified analyze call
STATE_REPLACE = """  const [stats, setStats] = useState(null)
  const [candidateNameInput, setCandidateNameInput] = useState('')
  const [expandedHistory, setExpandedHistory] = useState(null)"""
content = content.replace("  const [stats, setStats] = useState(null)", STATE_REPLACE)

ANALYZE_BODY = "body: JSON.stringify({ resume_text: resumeText, jd_text: jdText, candidate_name: candidateNameInput || 'Guest User' }),"
content = re.sub(r'body: JSON.stringify\(\{ resume_text: resumeText, jd_text: jdText, candidate_name: \'Guest User\' \}\),', ANALYZE_BODY, content)

# 3. Add Candidate Input to the UI
INPUT_UI = """            <div className="input-grid">
              
              <div className="card glass" style={{gridColumn: '1 / -1'}}>
                 <h3 style={{marginBottom:'10px'}}>Candidate Name</h3>
                 <input type="text" placeholder="Enter candidate name (e.g. David)" value={candidateNameInput} onChange={e => setCandidateNameInput(e.target.value)} style={{width: '100%', padding: '12px', background: 'rgba(255,255,255,0.05)', color: 'var(--white)', border: '1px solid rgba(0,245,212,0.3)', borderRadius: '6px', fontSize: '1rem'}} />
              </div>

              {/* RESUME CARD */}"""
content = content.replace('            <div className="input-grid">\n\n              {/* RESUME CARD */}', INPUT_UI)

# 4. Modify History to show plots inline if expanded
HISTORY_UI = """        {activeTab === 'history' && (
          <section className="history-section animate-in">
            <h2>Recent Candidate Evaluations</h2>
            <div className="history-list">
              {history.length > 0 ? history.map((session, i) => {
                const isExpanded = expandedHistory === session.session_id;
                // create chart data from gaps/coverage mock
                const chartData = [
                   { subject: 'Skills Match', A: session.skill_coverage_percent, fullMark: 100 },
                   { subject: 'Readiness', A: session.readiness_score, fullMark: 100 },
                   { subject: 'Gaps Avoided', A: Math.max(0, 100 - (session.skill_gaps?.length || 0) * 10), fullMark: 100 }
                ];
                return (
                <div key={i} className="history-card glass" style={{cursor: 'pointer', display: 'flex', flexDirection: 'column'}} onClick={() => { setExpandedHistory(isExpanded ? null : session.session_id) }}>
                  <div style={{display: 'flex', justifyContent: 'space-between', width: '100%'}}>
                    <div className="h-info">
                      <strong>{session.target_role}</strong>
                      <span>{session.candidate_name || 'Guest User'} - {new Date(session.created_at || Date.now()).toLocaleDateString()}</span>
                    </div>
                    <div className="h-score">{Math.round(session.readiness_score)}</div>
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
                            <Radar name={session.candidate_name} dataKey="A" stroke="var(--teal)" fill="var(--teal-glow)" fillOpacity={0.6} />
                            <Tooltip contentStyle={{background: 'var(--navy)', border: '1px solid var(--teal)'}} />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                      <div style={{marginTop: '15px'}}>
                         <button className="btn-primary" onClick={(e) => { e.stopPropagation(); setResults(session); setActiveTab('analyze') }} style={{fontSize: '0.85rem', padding: '8px 16px', display: 'inline-block'}}>Load Full Analysis</button>
                      </div>
                    </div>
                  )}
                </div>
              )}) : <p>No history yet.</p>}
            </div>
          </section>
        )}"""

# Replace the entire history section
old_history = """        {activeTab === 'history' && (
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
        )}"""
if old_history in content:
    content = content.replace(old_history, HISTORY_UI)
else:
    print("History section not found for exact replacement!")


# 5. Modify Stats section to show a Bar Chart
# Generate chart data from the history payload itself for the stats tab!
STATS_UI = """        {activeTab === 'stats' && (
          <section className="stats-section animate-in">
            <h2>System Overview & Analytics</h2>
            {stats ? (
              <>
                <div className="stats-grid" style={{marginBottom: '30px'}}>
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
                
                <div className="card glass" style={{padding: '20px'}}>
                  <h3 style={{color: 'var(--amber)', marginBottom: '15px'}}>Historical Candidate Readiness Trend</h3>
                  <div style={{height: '300px', width: '100%'}}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={history.slice(0, 15).reverse()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="candidate_name" stroke="var(--white-dim)" tick={{fontSize: 12}} />
                        <YAxis domain={[0, 100]} stroke="var(--white-dim)" />
                        <Tooltip contentStyle={{background: 'var(--navy)', border: '1px solid var(--amber)'}} />
                        <Line type="monotone" dataKey="readiness_score" name="Readiness Score" stroke="var(--amber)" strokeWidth={3} dot={{r: 4, fill: 'var(--amber)'}} activeDot={{r: 7}} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </>
            ) : <p>Loading stats...</p>}
          </section>
        )}"""

old_stats = """        {activeTab === 'stats' && (
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
        )}"""
if old_stats in content:
    content = content.replace(old_stats, STATS_UI)
else:
    print("Stats section not found for exact replacement!")


with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Recharts UX Patch Applied Successfully!")
