import { useEffect, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import axios from 'axios'
import { 
  ArrowLeft, 
  Star, 
  MapPin, 
  Building, 
  Users, 
  Clock, 
  TrendingUp,
  Award,
  Target,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Filter,
  Search,
  BarChart3,
  Lightbulb,
  Zap
} from 'lucide-react'
import './Recommendations.css'

const API_BASE_URL = 'http://localhost:5000/api'

export default function Recommendations() {
  const locationHook = useLocation()
  const state = locationHook.state || {}
  const formData = state.formData || null
  const preloaded = state.recommendations || null
  const analytics = state.analytics || null

  const [recommendations, setRecommendations] = useState(preloaded || [])
  const [browseTable, setBrowseTable] = useState(state.browseTable || [])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(!preloaded)
  const [activeTab, setActiveTab] = useState('recommendations')
  const [filterSector, setFilterSector] = useState('')
  const [filterLocation, setFilterLocation] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

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

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'var(--success-500)'
    if (confidence >= 60) return 'var(--warning-500)'
    return 'var(--error-500)'
  }

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 80) return 'Excellent Match'
    if (confidence >= 60) return 'Good Match'
    return 'Potential Match'
  }

  const renderSkillsAnalysis = (skillsAnalysis) => {
    if (!skillsAnalysis) return null

    const { matching_skills, missing_skills, match_percentage } = skillsAnalysis

    return (
      <div className="skills-analysis">
        <h4>Skills Analysis</h4>
        <div className="skills-match-bar">
          <div 
            className="skills-match-fill" 
            style={{ width: `${match_percentage * 100}%` }}
          ></div>
          <span className="skills-match-text">
            {Math.round(match_percentage * 100)}% Skills Match
          </span>
        </div>
        
        {matching_skills.length > 0 && (
          <div className="skills-section">
            <h5>
              <CheckCircle className="icon-sm success" />
              Matching Skills ({matching_skills.length})
            </h5>
            <div className="skills-tags">
              {matching_skills.map((skill, idx) => (
                <span key={idx} className="skill-tag matching">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {missing_skills.length > 0 && (
          <div className="skills-section">
            <h5>
              <Lightbulb className="icon-sm warning" />
              Skills to Develop ({missing_skills.length})
            </h5>
            <div className="skills-tags">
              {missing_skills.slice(0, 5).map((skill, idx) => (
                <span key={idx} className="skill-tag missing">
                  {skill}
                </span>
              ))}
              {missing_skills.length > 5 && (
                <span className="skill-tag more">
                  +{missing_skills.length - 5} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderScoreBreakdown = (scoreBreakdown) => {
    if (!scoreBreakdown) return null

    const scores = [
      { label: 'Skills Match', value: scoreBreakdown.skills_match, icon: Target },
      { label: 'Industry Fit', value: scoreBreakdown.industry_match, icon: Building },
      { label: 'Location', value: scoreBreakdown.location_match, icon: MapPin },
      { label: 'Education', value: scoreBreakdown.education_compatibility, icon: Award }
    ]

    return (
      <div className="score-breakdown">
        <h4>Match Breakdown</h4>
        <div className="score-items">
          {scores.map((score, idx) => {
            const IconComponent = score.icon
            return (
              <div key={idx} className="score-item">
                <div className="score-label">
                  <IconComponent className="icon-sm" />
                  {score.label}
                </div>
                <div className="score-bar">
                  <div 
                    className="score-fill" 
                    style={{ width: `${score.value * 100}%` }}
                  ></div>
                </div>
                <div className="score-value">
                  {Math.round(score.value * 100)}%
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const renderRecommendationCard = (rec, index) => (
    <div key={`${rec.id}-${index}`} className="recommendation-card">
      <div className="card-header">
        <div className="card-number">#{index + 1}</div>
        <div className="confidence-badge" style={{ backgroundColor: getConfidenceColor(rec.confidence_score) }}>
          <Star className="icon-sm" />
          {rec.confidence_score}% {getConfidenceLabel(rec.confidence_score)}
        </div>
      </div>

      <div className="card-content">
        <h3 className="internship-title">{rec.role}</h3>
        <p className="company-name">
          <Building className="icon-sm" />
          {rec.company}
        </p>

        <div className="card-details">
          <div className="detail-item">
            <MapPin className="icon-sm" />
            {rec.location}
          </div>
          <div className="detail-item">
            <Filter className="icon-sm" />
            {rec.industry}
          </div>
        </div>

        <div className="required-skills">
          <h4>Required Skills</h4>
          <div className="skills-tags">
            {rec.required_skills.split(',').slice(0, 4).map((skill, idx) => (
              <span key={idx} className="skill-tag">
                {skill.trim()}
              </span>
            ))}
            {rec.required_skills.split(',').length > 4 && (
              <span className="skill-tag more">
                +{rec.required_skills.split(',').length - 4} more
              </span>
            )}
          </div>
        </div>

        {rec.match_reasoning && (
          <div className="match-reasoning">
            <h4>Why This Matches</h4>
            <p>{rec.match_reasoning}</p>
          </div>
        )}

        {renderSkillsAnalysis(rec.skills_analysis)}
        {renderScoreBreakdown(rec.score_breakdown)}

        <div className="card-actions">
          <button className="apply-btn primary">
            <ExternalLink className="icon-sm" />
            Apply Now
          </button>
          <button className="apply-btn secondary">
            <Star className="icon-sm" />
            Save
          </button>
        </div>
      </div>
    </div>
  )

  const filteredBrowseTable = browseTable.filter(internship => {
    const matchesSector = !filterSector || internship.industry?.toLowerCase().includes(filterSector.toLowerCase())
    const matchesLocation = !filterLocation || internship.location?.toLowerCase().includes(filterLocation.toLowerCase())
    const matchesSearch = !searchTerm || 
      internship.role?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      internship.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      internship.required_skills?.toLowerCase().includes(searchTerm.toLowerCase())
    
    return matchesSector && matchesLocation && matchesSearch
  })

  const renderAnalytics = () => {
    if (!analytics) return null

    return (
      <div className="analytics-section">
        <h3>
          <BarChart3 className="icon" />
          Your Profile Analytics
        </h3>
        <div className="analytics-grid">
          <div className="analytics-card">
            <div className="analytics-value">{analytics.total_recommendations}</div>
            <div className="analytics-label">Recommendations Found</div>
          </div>
          <div className="analytics-card">
            <div className="analytics-value">{analytics.avg_confidence}%</div>
            <div className="analytics-label">Average Confidence</div>
          </div>
          <div className="analytics-card">
            <div className="analytics-value">{analytics.top_match_score}%</div>
            <div className="analytics-label">Best Match Score</div>
          </div>
          <div className="analytics-card">
            <div className="analytics-value">{analytics.candidate_profile?.skills_count || 0}</div>
            <div className="analytics-label">Skills Listed</div>
          </div>
        </div>
      </div>
    )
  }

  const renderBrowseTable = () => (
    <div className="browse-section">
      <div className="browse-header">
        <h3>Explore More Opportunities</h3>
        <div className="browse-filters">
          <div className="filter-group">
            <Search className="icon-sm" />
            <input
              type="text"
              placeholder="Search internships..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          <select
            value={filterSector}
            onChange={(e) => setFilterSector(e.target.value)}
            className="filter-select"
          >
            <option value="">All Industries</option>
            {[...new Set(browseTable.map(i => i.industry))].map(industry => (
              <option key={industry} value={industry}>{industry}</option>
            ))}
          </select>
          <select
            value={filterLocation}
            onChange={(e) => setFilterLocation(e.target.value)}
            className="filter-select"
          >
            <option value="">All Locations</option>
            {[...new Set(browseTable.map(i => i.location))].map(location => (
              <option key={location} value={location}>{location}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="browse-grid">
        {filteredBrowseTable.length === 0 ? (
          <div className="no-results">
            <AlertCircle className="icon" />
            <p>No internships match your current filters.</p>
          </div>
        ) : (
          filteredBrowseTable.slice(0, 12).map((internship, index) => (
            <div key={`browse-${internship.id}-${index}`} className="browse-card">
              <h4>{internship.role}</h4>
              <p className="browse-company">
                <Building className="icon-sm" />
                {internship.company}
              </p>
              <div className="browse-details">
                <span className="browse-location">
                  <MapPin className="icon-sm" />
                  {internship.location}
                </span>
                <span className="browse-industry">
                  <Filter className="icon-sm" />
                  {internship.industry}
                </span>
              </div>
              <div className="browse-skills">
                {internship.required_skills?.split(',').slice(0, 3).map((skill, idx) => (
                  <span key={idx} className="skill-tag small">
                    {skill.trim()}
                  </span>
                ))}
              </div>
              <button className="browse-apply-btn">
                <ExternalLink className="icon-sm" />
                View Details
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="loading-page">
        <div className="loading-spinner"></div>
        <p>Loading your recommendations...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-page">
        <AlertCircle className="icon" />
        <h2>Something went wrong</h2>
        <p>{error}</p>
        <Link to="/" className="back-btn">
          <ArrowLeft className="icon" />
          Try Again
        </Link>
      </div>
    )
  }

  return (
    <div className="recommendations-page">
      <div className="page-header">
        <div className="header-content">
          <Link to="/" className="back-btn">
            <ArrowLeft className="icon" />
            New Search
          </Link>
          <div className="header-text">
            <h1>
              <Zap className="icon" />
              Your Personalized Recommendations
            </h1>
            <p>
              Found {recommendations.length} internships tailored to your profile
              {analytics?.avg_confidence && ` with ${analytics.avg_confidence}% average match confidence`}
            </p>
          </div>
        </div>
        
        {renderAnalytics()}
      </div>

      <div className="tabs-container">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'recommendations' ? 'active' : ''}`}
            onClick={() => setActiveTab('recommendations')}
          >
            <TrendingUp className="icon-sm" />
            Top Matches ({recommendations.length})
          </button>
          <button 
            className={`tab ${activeTab === 'browse' ? 'active' : ''}`}
            onClick={() => setActiveTab('browse')}
          >
            <Search className="icon-sm" />
            Explore More ({browseTable.length})
          </button>
        </div>
      </div>

      <div className="tab-content">
        {activeTab === 'recommendations' ? (
          <div className="recommendations-section">
            {recommendations.length === 0 ? (
              <div className="no-recommendations">
                <AlertCircle className="icon" />
                <h3>No recommendations found</h3>
                <p>Try adjusting your preferences or skills to get better matches.</p>
                <Link to="/" className="retry-btn">
                  <ArrowLeft className="icon" />
                  Update Profile
                </Link>
              </div>
            ) : (
              <div className="recommendations-grid">
                {recommendations.map((rec, index) => renderRecommendationCard(rec, index))}
              </div>
            )}
          </div>
        ) : (
          renderBrowseTable()
        )}
      </div>
    </div>
  )
}