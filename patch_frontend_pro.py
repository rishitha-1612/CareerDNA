import re

with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Inject Filter States into React component
FILTER_STATES = """  const [expandedHistory, setExpandedHistory] = useState(null)
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
     return new Date(b.created_at || 0) - new Date(a.created_at || 0);
  })"""

content = content.replace("  const [expandedHistory, setExpandedHistory] = useState(null)", FILTER_STATES)

# 2. Inject Filter UI into History Tab
HISTORY_TAB_START = """        {activeTab === 'history' && (
          <section className="history-section animate-in">
            <h2>Recent Candidate Evaluations</h2>"""

HISTORY_FILTER_UI = """        {activeTab === 'history' && (
          <section className="history-section animate-in">
            <h2>Candidate History</h2>
            <div style={{display: 'flex', gap: '15px', marginBottom: '20px'}}>
               <input type="text" placeholder="Search by candidate name or role..." value={historySearch} onChange={e => setHistorySearch(e.target.value)} style={{flex: 1, padding: '10px 15px', background: 'rgba(255,255,255,0.03)', color: 'var(--white)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', fontSize: '0.95rem'}} />
               <select value={historySort} onChange={e => setHistorySort(e.target.value)} style={{padding: '10px 20px', background: 'rgba(255,255,255,0.03)', color: 'var(--white)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', cursor: 'pointer', outline: 'none'}}>
                  <option value="newest" style={{background: '#0a192f'}}>Newest First</option>
                  <option value="oldest" style={{background: '#0a192f'}}>Oldest First</option>
                  <option value="score_desc" style={{background: '#0a192f'}}>Score: High to Low</option>
                  <option value="score_asc" style={{background: '#0a192f'}}>Score: Low to High</option>
               </select>
            </div>"""

content = content.replace(HISTORY_TAB_START, HISTORY_FILTER_UI)

# Replace the history mapping loop
content = content.replace("{history.length > 0 ? history.map((session, i) => {", "{filteredHistory.length > 0 ? filteredHistory.map((session, i) => {")

# 3. Professionalize the Colors & Graph Titles
# Replace the COLORS array
content = content.replace(
    "const COLORS = ['#00f5d4', '#fee440', '#9b5de5', '#f15bb5', '#00bbf9'];",
    "const COLORS = ['#2b6cb0', '#4a5568', '#718096', '#a0aec0', '#e2e8f0'];" # Slate/Steel Blue professional
)

# Replace the LineChart neon stroke
content = content.replace(
    """<Line type="monotone" dataKey="readiness_score" name="Readiness Score" stroke="var(--amber)" strokeWidth={3} dot={{r: 4, fill: 'var(--amber)'}} activeDot={{r: 7}} />""",
    """<Line type="monotone" dataKey="readiness_score" name="Readiness Score" stroke="#2b6cb0" strokeWidth={3} dot={{r: 4, fill: '#2b6cb0'}} activeDot={{r: 7}} />"""
)

# And its Tooltip border
content = content.replace(
    """<Tooltip contentStyle={{background: 'var(--navy)', border: '1px solid var(--amber)'}} />""",
    """<Tooltip contentStyle={{background: 'var(--navy)', border: '1px solid #718096', borderRadius: '4px'}} />"""
)

# Replace the RadarChart neon stroke
content = content.replace(
    """<Radar name={session.candidate_name} dataKey="A" stroke="var(--teal)" fill="var(--teal-glow)" fillOpacity={0.6} />""",
    """<Radar name={session.candidate_name} dataKey="A" stroke="#2b6cb0" fill="#2b6cb0" fillOpacity={0.4} />"""
)
content = content.replace(
    """<Tooltip contentStyle={{background: 'var(--navy)', border: '1px solid var(--teal)'}} />""",
    """<Tooltip contentStyle={{background: 'var(--navy)', border: '1px solid #718096', borderRadius: '4px'}} />"""
)

# Tone down the Headers in the Stats tab
content = content.replace(
    """<h3 style={{color: 'var(--amber)', marginBottom: '15px'}}>Candidate Timeline (Readiness Trend)</h3>""",
    """<h3 style={{color: 'var(--white-dim)', marginBottom: '15px', fontWeight: 500}}>Candidate Timeline (Readiness Trend)</h3>"""
)
content = content.replace(
    """<h3 style={{color: 'var(--teal)', marginBottom: '15px'}}>Target Roles Evaluated</h3>""",
    """<h3 style={{color: 'var(--white-dim)', marginBottom: '15px', fontWeight: 500}}>Target Roles Evaluated</h3>"""
)
content = content.replace(
    """<h3 style={{color: 'var(--teal)', marginBottom: '15px'}}>Candidate Quality Tiers</h3>""",
    """<h3 style={{color: 'var(--white-dim)', marginBottom: '15px', fontWeight: 500}}>Candidate Quality Tiers</h3>"""
)

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Professional UI and History Search UX Applied Successfully.")
