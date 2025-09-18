import { useEffect, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

export default function Recommendations() {
  const locationHook = useLocation()
  const state = locationHook.state || {}
  const formData = state.formData || null
  const preloaded = state.recommendations || null

  const [recommendations, setRecommendations] = useState(preloaded || [])
  const [browseTable, setBrowseTable] = useState(state.browseTable || [])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(!preloaded)

  useEffect(() => {
    const fetchData = async () => {
      if (!formData || preloaded) return
      try {
        const res = await axios.post(`${API_BASE_URL}/recommendations`, formData)
        if (res.data?.success) {
          setRecommendations(res.data.data.recommendations)
          setBrowseTable(res.data.data.browse_table || [])
        } else {
          setError(res.data?.error || 'Failed to get recommendations')
        }
      } catch (e) {
        setError(e.response?.data?.error || 'Network error')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [formData, preloaded])

  if (loading) return <div style={{ padding: 24 }}>Loading recommendations...</div>
  if (error) return (
    <div style={{ padding: 24 }}>
      <div style={{ color: 'crimson', marginBottom: 12 }}>{error}</div>
      <Link to="/">Back</Link>
    </div>
  )

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Your Recommendations</h2>
        <Link to="/">New Search</Link>
      </div>

      <div style={{ overflowX: 'auto', marginTop: 12 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: 12 }}>
          <thead>
            <tr>
              <th style={th}>#</th>
              <th style={th}>Company</th>
              <th style={th}>Role</th>
              <th style={th}>Location</th>
              <th style={th}>Industry</th>
              <th style={th}>Required Skills</th>
              <th style={th}>Similarity</th>
            </tr>
          </thead>
          <tbody>
            {recommendations.length === 0 && (
              <tr>
                <td style={{ padding: 12 }} colSpan={7}>No recommendations found. Try broadening inputs.</td>
              </tr>
            )}
            {recommendations.map((r, i) => (
              <tr key={`${r.id}-${i}`}>
                <td style={td}>{i + 1}</td>
                <td style={td}>{r.company}</td>
                <td style={td}>{r.role}</td>
                <td style={td}>{r.location}</td>
                <td style={td}>{r.industry}</td>
                <td style={td}>{r.required_skills}</td>
                <td style={td}>{(r.similarity ?? 0).toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 style={{ marginTop: 32 }}>Other Opportunities</h3>
      <div style={{ overflowX: 'auto', marginTop: 12 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: 12 }}>
          <thead>
            <tr>
              <th style={th}>ID</th>
              <th style={th}>Company</th>
              <th style={th}>Role</th>
              <th style={th}>Location</th>
              <th style={th}>Industry</th>
              <th style={th}>Required Skills</th>
            </tr>
          </thead>
          <tbody>
            {browseTable.length === 0 && (
              <tr>
                <td style={{ padding: 12 }} colSpan={6}>No internships available.</td>
              </tr>
            )}
            {browseTable.map((r, i) => (
              <tr key={`${r.id}-${i}`}>
                <td style={td}>{r.id}</td>
                <td style={td}>{r.company}</td>
                <td style={td}>{r.role}</td>
                <td style={td}>{r.location}</td>
                <td style={td}>{r.industry}</td>
                <td style={td}>{r.required_skills}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const th = { textAlign: 'left', borderBottom: '1px solid #e5e7eb', padding: '8px' }
const td = { borderBottom: '1px solid #f1f5f9', padding: '8px' }


