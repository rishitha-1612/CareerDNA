import re

with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

STATE_INJECTION = """  const [assessmentMode, setAssessmentMode] = useState(false)
  const [assessmentData, setAssessmentData] = useState(null)
  const [assAnswers, setAssAnswers] = useState({})
  const [assScore, setAssScore] = useState(null)
  const [assLoading, setAssLoading] = useState(false)

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
"""

BUTTON_INJECTION = """                    <button
                      className="btn-resources" style={{marginLeft: "10px", background: "rgba(245, 166, 35, 0.15)", borderColor: "var(--amber)", color: "var(--amber)"}}
                      onClick={startAssessment}
                    >
                      ⚡ Take Technical Assessment
                    </button>"""

UI_INJECTION = """
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
"""

# Inject state variables
content = content.replace("  const [stats, setStats] = useState(null)", "  const [stats, setStats] = useState(null)\n" + STATE_INJECTION)

# Inject button next to view resources
content = content.replace("📚 View Learning Resources\n                    </button>", "📚 View Learning Resources\n                    </button>\n" + BUTTON_INJECTION)

# Inject the UI below the results container closing div
# Look for:
#                 )}
#               </div>
#             )}
#           </section>
# And replace with UI injection
content = content.replace("              </div>\n            )}", "              </div>\n            )}\n" + UI_INJECTION)


with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Patching complete!")
