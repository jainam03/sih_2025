# 🎯 PM Internship Recommendation System

A comprehensive AI-based recommendation engine for the PM Internship Scheme that helps youth across India find the most relevant internship opportunities based on their profile, skills, and preferences.

## 🌟 Features

- **Personalized Recommendations**: Uses TF-IDF and cosine similarity to match candidates with internships
- **Mobile-First Design**: Responsive UI optimized for mobile devices and low digital literacy users
- **Intuitive Interface**: Simple form with visual cues and minimal text
- **Smart Matching**: Considers skills, education level, sector interests, and location preferences
- **Real-time Results**: Instant recommendations with match scores and reasoning
- **Accessibility**: High contrast support, keyboard navigation, and screen reader friendly

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:5173`

## 📱 Usage

1. **Open the application** in your browser
2. **Fill in your profile:**
   - Skills (e.g., "Python, Communication, Excel")
   - Education Level (select from dropdown)
   - Sector Interest (e.g., "Technology, Finance")
   - Preferred Location (select from dropdown)
   - Experience (optional)

3. **Click "Get My Recommendations"** to receive personalized internship suggestions

4. **Review the results** showing:
   - Match percentage
   - Internship details
   - Required skills
   - Match reasoning
   - Apply button

## 🏗️ Architecture

### Backend (Flask + Python)
- **Recommendation Engine**: TF-IDF vectorization with cosine similarity
- **Location Matching**: Smart location preference scoring
- **Education Scoring**: Education level compatibility
- **REST API**: Multiple endpoints for different functionalities

### Frontend (React + Vite)
- **Mobile-First Design**: Responsive grid layout
- **Component-Based**: Modular React components
- **State Management**: React hooks for form and results state
- **API Integration**: Axios for backend communication

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/recommendations` | Get personalized recommendations |
| GET | `/api/internships` | Browse all internships |
| GET | `/api/sectors` | Get all sectors |
| GET | `/api/locations` | Get all locations |
| GET | `/api/skills` | Get all skills |
| GET | `/api/education-levels` | Get education levels |

## 🎨 Design Features

- **Gradient Backgrounds**: Modern visual appeal
- **Card-Based Layout**: Easy-to-scan information
- **Icon Integration**: Lucide React icons for better UX
- **Smooth Animations**: CSS transitions and keyframes
- **Accessibility**: ARIA labels, keyboard navigation, high contrast support

## 📊 Recommendation Algorithm

1. **Text Preprocessing**: Clean and normalize input text
2. **TF-IDF Vectorization**: Convert text to numerical vectors
3. **Cosine Similarity**: Calculate similarity between candidate and internships
4. **Location Bonus**: Add extra points for location matches
5. **Education Bonus**: Consider education level compatibility
6. **Final Scoring**: Combine all factors for final recommendation score

## 🌍 Regional Language Support

The system is designed to be easily extensible for regional languages:
- Text preprocessing handles multiple languages
- UI components support RTL layouts
- Placeholder text can be localized
- Form validation messages can be translated

