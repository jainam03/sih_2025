from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json
import os
import logging
from datetime import datetime
from model import InternshipRecommendationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

# Initialize the enhanced recommendation engine
engine = InternshipRecommendationEngine()

# Load internship data on startup with better error handling
DATA_PATH = os.path.join(os.path.dirname(__file__), 'internships.csv')
ARTIFACTS_PATH = os.path.join(os.path.dirname(__file__), 'artifacts')

def initialize_engine():
    """Initialize the recommendation engine with proper error handling."""
    try:
        if os.path.exists(ARTIFACTS_PATH) and os.listdir(ARTIFACTS_PATH):
            logger.info("Loading pre-trained model artifacts...")
            engine.load_artifacts(ARTIFACTS_PATH)
            logger.info("✅ Model artifacts loaded successfully")
        elif os.path.exists(DATA_PATH):
            logger.info("Training new model from CSV data...")
            engine.load_data(DATA_PATH)
            engine.fit()
            # Export artifacts for future use
            engine.export_artifacts(ARTIFACTS_PATH)
            logger.info("✅ Model trained and artifacts saved")
        else:
            logger.error("❌ No data found. Please ensure internships.csv exists.")
            return False
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize engine: {str(e)}")
        return False

# Initialize on startup
engine_initialized = initialize_engine()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check with detailed system status."""
    try:
        system_status = {
            'status': 'healthy' if engine_initialized else 'degraded',
            'message': 'PM Internship Recommendation API is running',
            'timestamp': datetime.now().isoformat(),
            'engine_status': {
                'initialized': engine_initialized,
                'internships_loaded': engine.internships_df is not None,
                'model_fitted': engine.vec_main is not None,
                'total_internships': len(engine.internships_df) if engine.internships_df is not None else 0
            },
            'version': '2.0',
            'features': [
                'Enhanced similarity scoring',
                'Skills gap analysis',
                'Education compatibility',
                'Confidence scoring',
                'Detailed match reasoning'
            ]
        }
        
        return jsonify(system_status), 200 if engine_initialized else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get enhanced internship recommendations with detailed analysis."""
    if not engine_initialized:
        return jsonify({
            'error': 'Recommendation engine not initialized. Please check server logs.',
            'suggestion': 'Ensure internships.csv exists and restart the server.'
        }), 503

    try:
        # Get and validate candidate data
        candidate_data = request.get_json()
        
        if not candidate_data:
            return jsonify({'error': 'No data provided in request body'}), 400
        
        # Enhanced validation with detailed error messages
        required_fields = ['skills', 'education_level', 'sector_interest', 'location_preference']
        validation_errors = []
        
        for field in required_fields:
            if not candidate_data.get(field):
                validation_errors.append(f'{field.replace("_", " ").title()} is required')
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_errors,
                'received_fields': list(candidate_data.keys())
            }), 400
        
        # Log the request for monitoring
        logger.info(f"Processing recommendation request for candidate with skills: {candidate_data.get('skills', 'N/A')}")
        
        # Get enhanced recommendations
        recommendations = engine.get_recommendations(candidate_data, top_k=6)
        
        if isinstance(recommendations, dict) and 'error' in recommendations:
            logger.error(f"Recommendation generation failed: {recommendations['error']}")
            return jsonify(recommendations), 400

        # Get browse table with filtering
        browse_df = engine.internships_df.head(25) if engine.internships_df is not None else pd.DataFrame([])
        browse_list = browse_df.to_dict('records')

        # Enhanced response with analytics
        response_data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'recommendations': recommendations,
                'browse_table': browse_list,
                'analytics': {
                    'total_recommendations': len(recommendations),
                    'avg_confidence': round(sum(r.get('confidence_score', 0) for r in recommendations) / len(recommendations), 1) if recommendations else 0,
                    'top_match_score': round(recommendations[0].get('similarity', 0) * 100, 1) if recommendations else 0,
                    'candidate_profile': {
                        'skills_count': len([s.strip() for s in candidate_data.get('skills', '').split(',') if s.strip()]),
                        'education_level': candidate_data.get('education_level'),
                        'sector_interest': candidate_data.get('sector_interest'),
                        'location_preference': candidate_data.get('location_preference')
                    }
                }
            }
        }
        
        logger.info(f"Successfully generated {len(recommendations)} recommendations")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Recommendation request failed: {str(e)}")
        return jsonify({
            'error': 'Internal server error occurred while processing recommendations',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/internships', methods=['GET'])
def get_all_internships():
    """Get filtered internships with enhanced search capabilities."""
    if not engine_initialized:
        return jsonify({'error': 'Engine not initialized'}), 503

    try:
        if engine.internships_df is None:
            return jsonify({'error': 'No internship data available'}), 404
        
        # Enhanced query parameters
        sector = request.args.get('sector', '').strip()
        location = request.args.get('location', '').strip()
        skills = request.args.get('skills', '').strip()
        company = request.args.get('company', '').strip()
        limit = min(int(request.args.get('limit', 50)), 100)  # Cap at 100
        offset = int(request.args.get('offset', 0))
        
        # Start with all internships
        filtered_internships = engine.internships_df.copy()
        
        # Apply filters with case-insensitive matching
        if sector:
            filtered_internships = filtered_internships[
                filtered_internships['industry'].str.contains(sector, case=False, na=False)
            ]
        
        if location:
            filtered_internships = filtered_internships[
                filtered_internships['location'].str.contains(location, case=False, na=False)
            ]
            
        if skills:
            filtered_internships = filtered_internships[
                filtered_internships['required_skills'].str.contains(skills, case=False, na=False)
            ]
            
        if company:
            filtered_internships = filtered_internships[
                filtered_internships['company'].str.contains(company, case=False, na=False)
            ]
        
        # Apply pagination
        total_filtered = len(filtered_internships)
        filtered_internships = filtered_internships.iloc[offset:offset + limit]
        
        # Convert to list of dictionaries
        internships_list = filtered_internships.to_dict('records')
        
        return jsonify({
            'success': True,
            'data': {
                'internships': internships_list,
                'pagination': {
                    'total_count': len(engine.internships_df),
                    'filtered_count': total_filtered,
                    'returned_count': len(internships_list),
                    'offset': offset,
                    'limit': limit,
                    'has_more': offset + limit < total_filtered
                },
                'filters_applied': {
                    'sector': sector or None,
                    'location': location or None,
                    'skills': skills or None,
                    'company': company or None
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Browse internships failed: {str(e)}")
        return jsonify({
            'error': f'Failed to retrieve internships: {str(e)}'
        }), 500

@app.route('/api/sectors', methods=['GET'])
def get_sectors():
    """Get all available sectors with counts."""
    if not engine_initialized:
        return jsonify({'error': 'Engine not initialized'}), 503

    try:
        if engine.internships_df is None:
            return jsonify({'error': 'No internship data available'}), 404
        
        # Get sectors with counts
        sector_counts = engine.internships_df['industry'].value_counts().to_dict()
        sectors_with_counts = [
            {'name': sector, 'count': count} 
            for sector, count in sorted(sector_counts.items())
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'sectors': [item['name'] for item in sectors_with_counts],
                'sectors_with_counts': sectors_with_counts,
                'total_sectors': len(sectors_with_counts)
            }
        })
        
    except Exception as e:
        logger.error(f"Get sectors failed: {str(e)}")
        return jsonify({'error': f'Failed to retrieve sectors: {str(e)}'}), 500

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all available locations with counts."""
    if not engine_initialized:
        return jsonify({'error': 'Engine not initialized'}), 503

    try:
        if engine.internships_df is None:
            return jsonify({'error': 'No internship data available'}), 404
        
        # Get locations with counts
        location_counts = engine.internships_df['location'].value_counts().to_dict()
        locations_with_counts = [
            {'name': location, 'count': count} 
            for location, count in sorted(location_counts.items())
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'locations': [item['name'] for item in locations_with_counts],
                'locations_with_counts': locations_with_counts,
                'total_locations': len(locations_with_counts)
            }
        })
        
    except Exception as e:
        logger.error(f"Get locations failed: {str(e)}")
        return jsonify({'error': f'Failed to retrieve locations: {str(e)}'}), 500

@app.route('/api/skills', methods=['GET'])
def get_skills():
    """Get all available skills with enhanced processing."""
    if not engine_initialized:
        return jsonify({'error': 'Engine not initialized'}), 503

    try:
        all_skills = set()
        skill_counts = {}

        # Process internship skills
        if engine.internships_df is not None and 'required_skills' in engine.internships_df.columns:
            for skills_str in engine.internships_df['required_skills'].dropna():
                skills = [skill.strip().title() for skill in str(skills_str).split(',') if skill.strip()]
                for skill in skills:
                    all_skills.add(skill)
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Also process student skills if available
        students_path = os.path.join(os.path.dirname(__file__), 'students.csv')
        if os.path.exists(students_path):
            try:
                sdf = pd.read_csv(students_path)
                if 'skills' in sdf.columns:
                    for skills_str in sdf['skills'].dropna():
                        skills = [skill.strip().title() for skill in str(skills_str).split(',') if skill.strip()]
                        for skill in skills:
                            all_skills.add(skill)
                            skill_counts[skill] = skill_counts.get(skill, 0) + 1
            except Exception as e:
                logger.warning(f"Could not process students.csv: {str(e)}")

        # Sort skills by popularity and alphabetically
        skills_with_counts = [
            {'name': skill, 'count': skill_counts.get(skill, 0)}
            for skill in sorted(all_skills)
        ]
        
        # Sort by count (descending) then by name
        skills_with_counts.sort(key=lambda x: (-x['count'], x['name']))
        
        return jsonify({
            'success': True,
            'data': {
                'skills': [item['name'] for item in skills_with_counts],
                'skills_with_counts': skills_with_counts,
                'total_skills': len(skills_with_counts),
                'popular_skills': [item['name'] for item in skills_with_counts[:20]]
            }
        })
        
    except Exception as e:
        logger.error(f"Get skills failed: {str(e)}")
        return jsonify({'error': f'Failed to retrieve skills: {str(e)}'}), 500

@app.route('/api/education-levels', methods=['GET'])
def get_education_levels():
    """Get all available education levels with hierarchy information."""
    try:
        # Get from students.csv if available
        students_path = os.path.join(os.path.dirname(__file__), 'students.csv')
        dynamic_levels = []
        
        if os.path.exists(students_path):
            try:
                sdf = pd.read_csv(students_path)
                if 'education' in sdf.columns:
                    level_counts = sdf['education'].value_counts().to_dict()
                    dynamic_levels = [
                        {'name': str(level), 'count': count}
                        for level, count in level_counts.items()
                        if pd.notna(level)
                    ]
            except Exception as e:
                logger.warning(f"Could not process students.csv for education levels: {str(e)}")
        
        # Fallback to static list with hierarchy
        static_levels = [
            '10th', '12th', 'Diploma', 'UG', 'B.Tech', 'B.Sc', 'BBA', 'B.Com', 'BCA',
            'PG', 'M.Tech', 'M.Sc', 'MBA', 'MCA', 'M.Com', 'PhD'
        ]
        
        # Use dynamic if available, otherwise static
        if dynamic_levels:
            # Sort by hierarchy if engine is available
            if engine_initialized and hasattr(engine, 'education_hierarchy'):
                dynamic_levels.sort(key=lambda x: engine.education_hierarchy.get(x['name'], 999))
            levels_data = [item['name'] for item in dynamic_levels]
            levels_with_counts = dynamic_levels
        else:
            levels_data = static_levels
            levels_with_counts = [{'name': level, 'count': 0} for level in static_levels]
        
        return jsonify({
            'success': True,
            'data': {
                'education_levels': levels_data,
                'education_levels_with_counts': levels_with_counts,
                'hierarchy': engine.education_hierarchy if engine_initialized else {},
                'total_levels': len(levels_data)
            }
        })
        
    except Exception as e:
        logger.error(f"Get education levels failed: {str(e)}")
        return jsonify({'error': f'Failed to retrieve education levels: {str(e)}'}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get system analytics and statistics."""
    if not engine_initialized:
        return jsonify({'error': 'Engine not initialized'}), 503

    try:
        if engine.internships_df is None:
            return jsonify({'error': 'No data available for analytics'}), 404

        df = engine.internships_df
        
        analytics = {
            'overview': {
                'total_internships': len(df),
                'total_companies': df['company'].nunique(),
                'total_locations': df['location'].nunique(),
                'total_industries': df['industry'].nunique()
            },
            'top_companies': df['company'].value_counts().head(10).to_dict(),
            'top_locations': df['location'].value_counts().head(10).to_dict(),
            'top_industries': df['industry'].value_counts().head(10).to_dict(),
            'role_distribution': df.get('role_level', pd.Series()).value_counts().to_dict(),
            'company_size_distribution': df.get('company_size', pd.Series()).value_counts().to_dict()
        }
        
        return jsonify({
            'success': True,
            'data': analytics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Analytics request failed: {str(e)}")
        return jsonify({'error': f'Failed to generate analytics: {str(e)}'}), 500

# Enhanced error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /api/health',
            'POST /api/recommendations',
            'GET /api/internships',
            'GET /api/sectors',
            'GET /api/locations',
            'GET /api/skills',
            'GET /api/education-levels',
            'GET /api/analytics'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred. Please try again later.',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The requested HTTP method is not allowed for this endpoint'
    }), 405

if __name__ == '__main__':
    print("🚀 Starting Enhanced PM Internship Recommendation API...")
    print("📊 Available endpoints:")
    print("  GET  /api/health - System health and status")
    print("  POST /api/recommendations - Get personalized recommendations")
    print("  GET  /api/internships - Browse and search internships")
    print("  GET  /api/sectors - Get all sectors with counts")
    print("  GET  /api/locations - Get all locations with counts")
    print("  GET  /api/skills - Get all skills with popularity")
    print("  GET  /api/education-levels - Get education levels with hierarchy")
    print("  GET  /api/analytics - Get system analytics")
    print("\n🔧 Enhanced Features:")
    print("  • Advanced similarity scoring with confidence metrics")
    print("  • Skills gap analysis and recommendations")
    print("  • Education level compatibility scoring")
    print("  • Detailed match reasoning and analytics")
    print("  • Enhanced error handling and logging")
    print("  • Comprehensive API documentation")
    
    app.run(debug=True, host='0.0.0.0', port=5000)