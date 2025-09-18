from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json
import os
from model import InternshipRecommendationEngine

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize the recommendation engine
engine = InternshipRecommendationEngine()

# Load internship data on startup
DATA_PATH = os.path.join(os.path.dirname(__file__), 'internships.csv')
if os.path.exists(DATA_PATH):
    engine.load_data(DATA_PATH)
else:
    print("⚠️ No internship data found. Please run the model notebook first to generate data.")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'PM Internship Recommendation API is running',
        'internships_loaded': engine.internships_df is not None
    })

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get internship recommendations for a candidate and return a dummy internships table too"""
    try:
        # Get candidate data from request
        candidate_data = request.get_json()
        
        # Validate required fields
        required_fields = ['skills', 'education_level', 'sector_interest', 'location_preference']
        missing_fields = [field for field in required_fields if not candidate_data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Get recommendations
        recommendations = engine.get_recommendations(candidate_data, top_k=5)
        
        if 'error' in recommendations:
            return jsonify(recommendations), 400

        # Also provide a small dummy/browse table from the internships CSV for the second table on UI
        browse_df = engine.internships_df.head(20) if engine.internships_df is not None else pd.DataFrame([])
        browse_list = browse_df.to_dict('records')

        return jsonify({
            'success': True,
            'data': {
                'recommendations': recommendations,
                'browse_table': browse_list
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/internships', methods=['GET'])
def get_all_internships():
    """Get all available internships (for browsing)"""
    try:
        if engine.internships_df is None:
            return jsonify({'error': 'No internship data available'}), 404
        
        # Get query parameters for filtering
        sector = request.args.get('sector')
        location = request.args.get('location')
        limit = int(request.args.get('limit', 20))
        
        # Filter internships
        filtered_internships = engine.internships_df.copy()
        
        if sector:
            filtered_internships = filtered_internships[
                filtered_internships['industry'].str.contains(sector, case=False, na=False)
            ]
        
        if location:
            filtered_internships = filtered_internships[
                filtered_internships['location'].str.contains(location, case=False, na=False)
            ]
        
        # Limit results
        filtered_internships = filtered_internships.head(limit)
        
        # Convert to list of dictionaries
        internships_list = filtered_internships.to_dict('records')
        
        return jsonify({
            'success': True,
            'data': {
                'internships': internships_list,
                'total_count': len(engine.internships_df),
                'filtered_count': len(filtered_internships)
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/sectors', methods=['GET'])
def get_sectors():
    """Get all available sectors"""
    try:
        if engine.internships_df is None:
            return jsonify({'error': 'No internship data available'}), 404
        
        sectors = engine.internships_df['industry'].unique().tolist()
        sectors.sort()
        
        return jsonify({
            'success': True,
            'data': sectors
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all available locations"""
    try:
        if engine.internships_df is None:
            return jsonify({'error': 'No internship data available'}), 404
        
        locations = engine.internships_df['location'].unique().tolist()
        locations.sort()
        
        return jsonify({
            'success': True,
            'data': locations
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/skills', methods=['GET'])
def get_skills():
    """Get all available skills"""
    try:
        all_skills = set()

        # Prefer internships skills
        if engine.internships_df is not None and 'required_skills' in engine.internships_df.columns:
            for skills_str in engine.internships_df['required_skills'].dropna():
                skills = [skill.strip() for skill in str(skills_str).split(',') if skill.strip()]
                all_skills.update(skills)

        # Also merge student skills if available
        students_path = os.path.join(os.path.dirname(__file__), 'students.csv')
        if os.path.exists(students_path):
            sdf = pd.read_csv(students_path)
            if 'skills' in sdf.columns:
                for skills_str in sdf['skills'].dropna():
                    skills = [skill.strip() for skill in str(skills_str).split(',') if skill.strip()]
                    all_skills.update(skills)

        skills_list = sorted(list(all_skills))
        return jsonify({'success': True, 'data': skills_list})
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/education-levels', methods=['GET'])
def get_education_levels():
    """Get all available education levels"""
    try:
        # Prefer deriving from students.csv if available
        students_path = os.path.join(os.path.dirname(__file__), 'students.csv')
        if os.path.exists(students_path):
            sdf = pd.read_csv(students_path)
            if 'education' in sdf.columns:
                levels = sorted([str(x) for x in sdf['education'].dropna().unique().tolist()])
                return jsonify({'success': True, 'data': levels})
        # Fallback static list
        education_levels = [
            '10th', '12th', 'Diploma', 'UG', 'B.Tech', 'B.Sc', 'BBA', 'B.Com', 'BCA',
            'PG', 'M.Tech', 'M.Sc', 'MBA', 'MCA', 'M.Com', 'PhD'
        ]
        return jsonify({'success': True, 'data': education_levels})
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 Starting PM Internship Recommendation API...")
    print("📊 Available endpoints:")
    print("  GET  /api/health - Health check")
    print("  POST /api/recommendations - Get personalized recommendations")
    print("  GET  /api/internships - Browse all internships")
    print("  GET  /api/sectors - Get all sectors")
    print("  GET  /api/locations - Get all locations")
    print("  GET  /api/skills - Get all skills")
    print("  GET  /api/education-levels - Get education levels")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
