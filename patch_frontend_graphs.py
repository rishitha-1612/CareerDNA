import re

with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Imports
content = content.replace(
    "import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, CartesianGrid } from 'recharts'",
    "import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, CartesianGrid, PieChart, Pie, Cell, Legend } from 'recharts'"
)

# 2. Add loadFullAnalysis logic and helpers
STATE_ADDITION = """  const [assLoading, setAssLoading] = useState(false)

  const loadFullAnalysis = async (sessionId) => {
    try {
        const r = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`)
        const d = await r.json()
        if (d.success) {
            setResults(d.pathway)
            setActiveTab('analyze')
        }
    } catch (e) { alert("Failed to load deep analysis: " + e.message) }
  }

  const COLORS = ['#00f5d4', '#fee440', '#9b5de5', '#f15bb5', '#00bbf9'];
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
"""

content = content.replace("  const [assLoading, setAssLoading] = useState(false)", STATE_ADDITION)

# 3. Update the onClick for the Load Full Analysis Button inside History Tab
content = content.replace(
    "onClick={(e) => { e.stopPropagation(); setResults(session); setActiveTab('analyze') }}",
    "onClick={(e) => { e.stopPropagation(); loadFullAnalysis(session.session_id) }}"
)

# 4. Overhaul the Stats section completely
import re
# We'll use a regex to grab everything between:
#         {activeTab === 'stats' && (
#           <section className="stats-section animate-in"> ... </section>
#         )}
# and replace it.

STATS_START = "        {activeTab === 'stats' && ("
STATS_END_TAG = "          </section>\n        )}"
new_stats = """        {activeTab === 'stats' && (
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
                  <h3 style={{color: 'var(--amber)', marginBottom: '15px'}}>Candidate Timeline (Readiness Trend)</h3>
                  <div style={{height: '250px', width: '100%'}}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={history.slice(0, 20).reverse()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="candidate_name" stroke="var(--white-dim)" tick={{fontSize: 10}} />
                        <YAxis domain={[0, 100]} stroke="var(--white-dim)" />
                        <Tooltip contentStyle={{background: 'var(--navy)', border: '1px solid var(--amber)'}} />
                        <Line type="monotone" dataKey="readiness_score" name="Readiness Score" stroke="var(--amber)" strokeWidth={3} dot={{r: 4, fill: 'var(--amber)'}} activeDot={{r: 7}} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '30px'}}>
                    <div className="card glass" style={{padding: '20px'}}>
                      <h3 style={{color: 'var(--teal)', marginBottom: '15px'}}>Target Roles Evaluated</h3>
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
                      <h3 style={{color: 'var(--teal)', marginBottom: '15px'}}>Candidate Quality Tiers</h3>
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
        )}"""

start_idx = content.find(STATS_START)
end_idx = content.find(STATS_END_TAG, start_idx) + len(STATS_END_TAG)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_stats + content[end_idx:]
else:
    print("Could not find Stats block to replace")

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied for graphs and bugfixes!")
