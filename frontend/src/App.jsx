import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { 
  Search, 
  MapPin, 
  GraduationCap, 
  Briefcase, 
  Users, 
  Filter, 
  Sparkles,
  AlertCircle,
  CheckCircle,
  Loader2,
  TrendingUp
} from 'lucide-react'
import './App.css'

const API_BASE_URL = 'http://localhost:5000/api'

function App() {
  const navigate = useNavigate()
  const [step, setStep] = useState('form') // 'form', 'loading', 'results'
  const [formData, setFormData] = useState({
    skills: '',
    education_level: '',
    sector_interest: '',
    location_preference: '',
    experience: '',
    aspirations: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [options, setOptions] = useState({
    education_levels: [],
    sectors: [],
    locations: [],
    skills: []
  })
  const [systemHealth, setSystemHealth] = useState(null)
  const [formValidation, setFormValidation] = useState({})

  // Load options and check system health on component mount
  useEffect(() => {
    checkSystemHealth()
    loadOptions()
  }, [])

  const checkSystemHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`)
      setSystemHealth(response.data)
      
      if (!response.data.engine_status?.initialized) {
        setError('System is initializing. Please wait a moment and try again.')
      }
    } catch (err) {
      console.error('Health check failed:', err)
      setError('Unable to connect to recommendation service. Please check if the backend is running.')
    }
  }

  const loadOptions = async () => {
    try {
      const [educationRes, sectorsRes, locationsRes, skillsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/education-levels`).catch(() => ({ data: { data: [] } })),
        axios.get(`${API_BASE_URL}/sectors`).catch(() => ({ data: { data: [] } })),
        axios.get(`${API_BASE_URL}/locations`).catch(() => ({ data: { data: [] } })),
        axios.get(`${API_BASE_URL}/skills`).catch(() => ({ data: { data: [] } }))
      ])

      setOptions({
        education_levels: educationRes.data.data || [],
        sectors: sectorsRes.data.data || [],
        locations: locationsRes.data.data || [],
        skills: skillsRes.data.data || []
      })

      console.log('✅ Dropdown options loaded successfully')
    } catch (err) {
      console.error('Error loading options:', err)
      setError('Failed to load form options. Some features may be limited.')
    }
  }

  const validateForm = () => {
    const validation = {}
    const requiredFields = ['skills', 'education_level', 'sector_interest', 'location_preference']
    
    requiredFields.forEach(field => {
      if (!formData[field] || formData[field].trim() === '') {
        validation[field] = `${field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} is required`
      }
    })

    // Additional validation
    if (formData.skills && formData.skills.length < 2) {
      validation.skills = 'Please enter at least one meaningful skill'
    }

    setFormValidation(validation)
    return Object.keys(validation).length === 0
  }

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))

    // Clear validation error for this field
    if (formValidation[field]) {
      setFormValidation(prev => ({
        ...prev,
        [field]: undefined
      }))
    }

    // Clear general error
    if (error) {
      setError('')
    }
  }

  const simulateLoadingProgress = () => {
    setLoadingProgress(0)
    const interval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval)
          return 90
        }
        return prev + Math.random() * 15
      })
    }, 200)
    return interval
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validate form
    if (!validateForm()) {
      setError('Please fill in all required fields correctly.')
      return
    }

    setError('')
    setLoading(true)
    setStep('loading')

    // Start loading progress simulation
    const progressInterval = simulateLoadingProgress()

    try {
      const payload = { ...formData }
      console.log('🚀 Sending recommendation request:', payload)
      
      const response = await axios.post(`${API_BASE_URL}/recommendations`, payload, {
        timeout: 30000 // 30 second timeout
      })

      // Complete the progress
      setLoadingProgress(100)
      clearInterval(progressInterval)

      if (response.data.success) {
        const { recommendations, browse_table, analytics } = response.data.data
        
        console.log('✅ Recommendations received:', {
          count: recommendations.length,
          avgConfidence: analytics?.avg_confidence,
          topMatch: analytics?.top_match_score
        })

        // Navigate to recommendations page with enhanced data
        navigate('/recommendations', { 
          state: { 
            formData, 
            recommendations, 
            browseTable: browse_table,
            analytics,
            timestamp: response.data.timestamp
          } 
        })
      } else {
        throw new Error(response.data.error || 'Failed to get recommendations')
      }
    } catch (err) {
      clearInterval(progressInterval)
      console.error('❌ Recommendation request failed:', err)
      
      let errorMessage = 'An unexpected error occurred. Please try again.'
      
      if (err.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. The server might be busy. Please try again.'
      } else if (err.response?.status === 503) {
        errorMessage = 'Service temporarily unavailable. Please wait a moment and try again.'
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error
      } else if (err.message.includes('Network Error')) {
        errorMessage = 'Unable to connect to the server. Please check your connection and ensure the backend is running.'
      }
      
      setError(errorMessage)
      setStep('form')
    } finally {
      setLoading(false)
    }
  }

  const renderSystemStatus = () => {
    if (!systemHealth) return null

    const isHealthy = systemHealth.status === 'healthy'
    const StatusIcon = isHealthy ? CheckCircle : AlertCircle

    return (
      <div className={`system-status ${isHealthy ? 'healthy' : 'degraded'}`}>
        <StatusIcon className="icon" />
        <span>
          {isHealthy ? 'System Ready' : 'System Initializing'}
          {systemHealth.engine_status?.total_internships && 
            ` • ${systemHealth.engine_status.total_internships} internships available`
          }
        </span>
      </div>
    )
  }

  const renderFormField = (field, label, icon, type = 'select', options = [], placeholder = '') => {
    const hasError = formValidation[field]
    
    return (
      <div className="form-group">
        <label htmlFor={field}>
          {icon}
          {label}
        </label>
        {type === 'select' ? (
          <select
            id={field}
            value={formData[field]}
            onChange={(e) => handleInputChange(field, e.target.value)}
            className={hasError ? 'error' : ''}
            required
          >
            <option value="">Select {label.toLowerCase()}</option>
            {options.length === 0 && (
              <option disabled>Loading options...</option>
            )}
            {options.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        ) : (
          <input
            type={type}
            id={field}
            value={formData[field]}
            onChange={(e) => handleInputChange(field, e.target.value)}
            placeholder={placeholder}
            className={hasError ? 'error' : ''}
          />
        )}
        {hasError && (
          <small className="error-text">
            <AlertCircle className="icon-sm" />
            {hasError}
          </small>
        )}
      </div>
    )
  }

  const renderForm = () => (
    <div className="form-container">
      {renderSystemStatus()}
      
      <div className="header">
        <h1>🎯 PM Internship Finder</h1>
        <p>Get personalized internship recommendations powered by advanced AI matching</p>
      </div>

      <form onSubmit={handleSubmit} className="candidate-form">
        {renderFormField(
          'skills',
          'Your Primary Skill',
          <Briefcase className="icon" />,
          'select',
          options.skills,
          'Select your strongest skill'
        )}

        {renderFormField(
          'aspirations',
          'Career Aspirations',
          <Sparkles className="icon" />,
          'text',
          [],
          'e.g., Data Analyst, Marketing Associate, Software Developer'
        )}

        {renderFormField(
          'education_level',
          'Education Level',
          <GraduationCap className="icon" />,
          'select',
          options.education_levels
        )}

        {renderFormField(
          'sector_interest',
          'Preferred Industry',
          <Filter className="icon" />,
          'select',
          options.sectors
        )}

        {renderFormField(
          'location_preference',
          'Preferred Location',
          <MapPin className="icon" />,
          'select',
          options.locations
        )}

        {renderFormField(
          'experience',
          'Experience Level (Optional)',
          <Users className="icon" />,
          'text',
          [],
          'e.g., Fresher, 6 months, 1 year'
        )}

        {error && (
          <div className="error-message">
            <AlertCircle className="icon" />
            {error}
          </div>
        )}

        <button 
          type="submit" 
          className="submit-btn"
          disabled={loading || !systemHealth?.engine_status?.initialized}
        >
          {loading ? (
            <>
              <Loader2 className="icon animate-spin" />
              Finding Matches...
            </>
          ) : (
            <>
              <Search className="icon" />
              Get My Recommendations
            </>
          )}
        </button>

        <div className="form-footer">
          <small>
            <TrendingUp className="icon-sm" />
            Enhanced with AI-powered matching • Skills gap analysis • Confidence scoring
          </small>
        </div>
      </form>
    </div>
  )

  const renderLoading = () => (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <h2>Finding Your Perfect Internships</h2>
      <p>Our AI is analyzing your profile and matching you with the best opportunities</p>
      
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${loadingProgress}%` }}
        ></div>
      </div>
      
      <div className="loading-steps">
        <div className={`step ${loadingProgress > 20 ? 'completed' : 'active'}`}>
          <CheckCircle className="icon" />
          Analyzing your skills
        </div>
        <div className={`step ${loadingProgress > 50 ? 'completed' : loadingProgress > 20 ? 'active' : ''}`}>
          <CheckCircle className="icon" />
          Matching with internships
        </div>
        <div className={`step ${loadingProgress > 80 ? 'completed' : loadingProgress > 50 ? 'active' : ''}`}>
          <CheckCircle className="icon" />
          Calculating compatibility
        </div>
        <div className={`step ${loadingProgress > 90 ? 'completed' : loadingProgress > 80 ? 'active' : ''}`}>
          <CheckCircle className="icon" />
          Preparing recommendations
        </div>
      </div>
    </div>
  )

  return (
    <div className="app">
      {step === 'form' && renderForm()}
      {step === 'loading' && renderLoading()}
    </div>
  )
}

export default App