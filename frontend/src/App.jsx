import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { Search, MapPin, GraduationCap, Briefcase, Users, Filter, Sparkles } from 'lucide-react'
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
  const [recommendations, setRecommendations] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [options, setOptions] = useState({
    education_levels: [],
    sectors: [],
    locations: [],
    skills: []
  })

  // Load options on component mount
  useEffect(() => {
    loadOptions()
  }, [])

  const loadOptions = async () => {
    try {
      const [educationRes, sectorsRes, locationsRes, skillsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/education-levels`),
        axios.get(`${API_BASE_URL}/sectors`),
        axios.get(`${API_BASE_URL}/locations`),
        axios.get(`${API_BASE_URL}/skills`)
      ])

      setOptions({
        education_levels: educationRes.data.data,
        sectors: sectorsRes.data.data,
        locations: locationsRes.data.data,
        skills: skillsRes.data.data
      })
        // Debug output for dropdown options
        console.log('Dropdown options loaded:', {
          education_levels: educationRes.data.data,
          sectors: sectorsRes.data.data,
          locations: locationsRes.data.data,
          skills: skillsRes.data.data
        })
    } catch (err) {
      console.error('Error loading options:', err)
        setError('Failed to load dropdown options. Please check backend API.')
    }
  }

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    setStep('loading')

    try {
      const payload = { ...formData }
      const response = await axios.post(`${API_BASE_URL}/recommendations`, payload)

      if (response.data.success) {
        const recs = response.data.data.recommendations
        const browse = response.data.data.browse_table || []
        // navigate to recommendations page with state
        navigate('/recommendations', { state: { formData, recommendations: recs, browseTable: browse } })
      } else {
        setError(response.data.error || 'Failed to get recommendations')
        setStep('form')
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Network error. Please try again.')
      setStep('form')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setFormData({
      skills: '',
      education_level: '',
      sector_interest: '',
      location_preference: '',
      experience: '',
      aspirations: ''
    })
    setRecommendations([])
    setError('')
    setStep('form')
  }

  const renderForm = () => (
    <div className="form-container">
      <div className="header">
        <h1>🎯 PM Internship Recommendation</h1>
        <p>Get 3–5 personalized suggestions based on your profile</p>
      </div>

      <form onSubmit={handleSubmit} className="candidate-form">
        <div className="form-group">
          <label htmlFor="skills">
            <Briefcase className="icon" />
            Your Skills
          </label>
          <select
            id="skills"
            value={formData.skills}
            onChange={(e) => handleInputChange('skills', e.target.value)}
            required
          >
            <option value="">Select a skill</option>
            {options.skills.length === 0 && (
              <option disabled>Loading skills or none available</option>
            )}
            {options.skills.map((sk) => (
              <option key={sk} value={sk}>{sk}</option>
            ))}
          </select>
          <small>You can start with your strongest skill</small>
        </div>

        <div className="form-group">
          <label htmlFor="aspirations">
            <Sparkles className="icon" />
            Aspirations (roles you aim for)
          </label>
          <input
            type="text"
            id="aspirations"
            value={formData.aspirations}
            onChange={(e) => handleInputChange('aspirations', e.target.value)}
            placeholder="e.g., Data Analyst, Marketing Associate"
          />
          <small>Optional. Helps refine matches.</small>
        </div>

        <div className="form-group">
          <label htmlFor="education_level">
            <GraduationCap className="icon" />
            Education Level
          </label>
          <select
            id="education_level"
            value={formData.education_level}
            onChange={(e) => handleInputChange('education_level', e.target.value)}
            required
          >
            <option value="">Select your education level</option>
            {options.education_levels.length === 0 && (
              <option disabled>Loading education levels or none available</option>
            )}
            {options.education_levels.map(level => (
              <option key={level} value={level}>{level}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="sector_interest">
            <Filter className="icon" />
            Sector Interest
          </label>
          <select
            id="sector_interest"
            value={formData.sector_interest}
            onChange={(e) => handleInputChange('sector_interest', e.target.value)}
            required
          >
            <option value="">Select a sector</option>
            {options.sectors.length === 0 && (
              <option disabled>Loading sectors or none available</option>
            )}
            {options.sectors.map((sector) => (
              <option key={sector} value={sector}>{sector}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="location_preference">
            <MapPin className="icon" />
            Preferred Location
          </label>
          <select
            id="location_preference"
            value={formData.location_preference}
            onChange={(e) => handleInputChange('location_preference', e.target.value)}
            required
          >
            <option value="">Select preferred location</option>
            {options.locations.length === 0 && (
              <option disabled>Loading locations or none available</option>
            )}
            {options.locations.map(location => (
              <option key={location} value={location}>{location}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="experience">
            <Users className="icon" />
            Experience (Optional)
          </label>
          <input
            type="text"
            id="experience"
            value={formData.experience}
            onChange={(e) => handleInputChange('experience', e.target.value)}
            placeholder="e.g., Fresher, 6 months, 1 year"
          />
        </div>

        {error && <div className="error-message">{error}</div>}

        <button type="submit" className="submit-btn">
          <Search className="icon" />
          Get My Recommendations
        </button>
      </form>
    </div>
  )

  const renderLoading = () => (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <h2>Finding the best internships for you...</h2>
      <p>Analyzing your profile and matching with available opportunities</p>
    </div>
  )

  const renderResults = () => null

  return (
    <div className="app">
      {step === 'form' && renderForm()}
      {step === 'loading' && renderLoading()}
      {step === 'results' && renderResults()}
    </div>
  )
}

export default App
