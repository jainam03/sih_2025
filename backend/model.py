import os
import json
from typing import List, Dict, Any, Optional, Tuple
import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import joblib


class InternshipRecommendationEngine:
    """Enhanced content-based recommendation engine for internships.

    Features:
    - Multi-field weighted similarity scoring
    - Education level compatibility scoring
    - Location preference matching with fuzzy logic
    - Skills gap analysis and recommendations
    - Confidence scoring for recommendations
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self.internships_df: Optional[pd.DataFrame] = None

        # Enhanced vectorizers with better parameters
        self.vec_main: Optional[TfidfVectorizer] = None
        self.vec_industry: Optional[TfidfVectorizer] = None
        self.vec_location: Optional[TfidfVectorizer] = None

        # Internship-side feature matrices
        self.intern_main = None
        self.intern_industry = None
        self.intern_location = None

        # Enhanced weights with more granular control
        if weights is None:
            weights = {
                "main": 0.5,      # Skills and role matching
                "industry": 0.25,  # Industry/sector matching
                "location": 0.15,  # Location preference
                "education": 0.1   # Education compatibility
            }
        self.weights = weights

        # Education level hierarchy for compatibility scoring
        self.education_hierarchy = {
            '10th': 1, '12th': 2, 'Diploma': 3,
            'UG': 4, 'B.Tech': 4, 'B.Sc': 4, 'BBA': 4, 'B.Com': 4, 'BCA': 4,
            'PG': 5, 'M.Tech': 5, 'M.Sc': 5, 'MBA': 5, 'MCA': 5, 'M.Com': 5,
            'PhD': 6
        }

    def _preprocess_text(self, text: str) -> str:
        """Enhanced text preprocessing with better normalization."""
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase and remove extra whitespace
        text = re.sub(r'\s+', ' ', str(text).lower().strip())
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\+\#\-\.]', ' ', text)
        
        # Normalize common skill variations
        skill_mappings = {
            'javascript': 'js', 'python programming': 'python',
            'machine learning': 'ml', 'artificial intelligence': 'ai',
            'data science': 'data analysis', 'web development': 'web dev'
        }
        
        for original, normalized in skill_mappings.items():
            text = text.replace(original, normalized)
        
        return text

    def load_data(self, internships_csv_path: str) -> None:
        """Load and validate internship data with enhanced error handling."""
        try:
            df = pd.read_csv(internships_csv_path)
            
            # Validate required columns
            expected = {"id", "company", "role", "location", "industry", "required_skills"}
            missing = expected - set(df.columns)
            if missing:
                raise ValueError(f"internships.csv missing columns: {', '.join(sorted(missing))}")

            # Enhanced data cleaning and preprocessing
            for col in ["company", "role", "location", "industry", "required_skills"]:
                df[col] = df[col].fillna("").astype(str)
                df[col] = df[col].apply(self._preprocess_text)

            # Add derived columns for better matching
            df['role_level'] = df['role'].apply(self._extract_role_level)
            df['company_size'] = df['company'].apply(self._estimate_company_size)
            
            self.internships_df = df
            print(f"✅ Loaded {len(df)} internships successfully")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load internship data: {str(e)}")

    def _extract_role_level(self, role: str) -> str:
        """Extract role level from job title."""
        role_lower = role.lower()
        if any(word in role_lower for word in ['intern', 'trainee', 'entry', 'junior', 'associate']):
            return 'entry'
        elif any(word in role_lower for word in ['senior', 'lead', 'manager', 'head']):
            return 'senior'
        return 'mid'

    def _estimate_company_size(self, company: str) -> str:
        """Estimate company size based on name patterns."""
        company_lower = company.lower()
        if any(word in company_lower for word in ['google', 'microsoft', 'amazon', 'apple', 'meta']):
            return 'large'
        elif any(word in company_lower for word in ['startup', 'tech', 'solutions', 'systems']):
            return 'medium'
        return 'small'

    def _build_internship_corpora(self) -> Dict[str, List[str]]:
        """Build enhanced text corpora for different matching aspects."""
        assert self.internships_df is not None
        
        # Enhanced main text with role context
        main = (
            self.internships_df["required_skills"].astype(str) + " " +
            self.internships_df["role"].astype(str) + " " +
            self.internships_df["role_level"].astype(str)
        ).tolist()
        
        # Industry with company context
        industry = (
            "industry:" + self.internships_df["industry"].astype(str) + " " +
            "size:" + self.internships_df["company_size"].astype(str)
        ).tolist()
        
        # Location with regional context
        location = ("location:" + self.internships_df["location"].astype(str)).tolist()
        
        return {"main": main, "industry": industry, "location": location}

    def fit(self) -> None:
        """Fit enhanced vectorizers with optimized parameters."""
        if self.internships_df is None:
            raise RuntimeError("Load internships data before fit().")

        corpora = self._build_internship_corpora()

        # Enhanced vectorizers with better parameters
        self.vec_main = TfidfVectorizer(
            ngram_range=(1, 3), 
            min_df=1, 
            max_df=0.95,
            stop_words='english',
            sublinear_tf=True
        )
        
        self.vec_industry = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            stop_words='english'
        )
        
        self.vec_location = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1
        )

        try:
            self.intern_main = self.vec_main.fit_transform(corpora["main"])
            self.intern_industry = self.vec_industry.fit_transform(corpora["industry"])
            self.intern_location = self.vec_location.fit_transform(corpora["location"])
            print("✅ Vectorizers fitted successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to fit vectorizers: {str(e)}")

    def _calculate_education_compatibility(self, candidate_education: str, internship_idx: int) -> float:
        """Calculate education level compatibility score."""
        candidate_level = self.education_hierarchy.get(candidate_education, 3)
        
        # For internships, we assume they're suitable for UG level and above
        internship_min_level = 3  # Diploma level minimum
        internship_max_level = 5  # PG level maximum
        
        if candidate_level < internship_min_level:
            return 0.3  # Under-qualified but still possible
        elif candidate_level > internship_max_level:
            return 0.7  # Over-qualified but acceptable
        else:
            return 1.0  # Perfect match

    def _analyze_skills_gap(self, candidate_skills: str, required_skills: str) -> Dict[str, Any]:
        """Analyze skills gap and provide recommendations."""
        candidate_skills_list = [s.strip().lower() for s in candidate_skills.split(',') if s.strip()]
        required_skills_list = [s.strip().lower() for s in required_skills.split(',') if s.strip()]
        
        matching_skills = set(candidate_skills_list) & set(required_skills_list)
        missing_skills = set(required_skills_list) - set(candidate_skills_list)
        
        match_percentage = len(matching_skills) / len(required_skills_list) if required_skills_list else 0
        
        return {
            'matching_skills': list(matching_skills),
            'missing_skills': list(missing_skills),
            'match_percentage': match_percentage,
            'skills_confidence': min(match_percentage * 1.2, 1.0)
        }

    def _candidate_texts(self, candidate: Dict[str, Any]) -> Dict[str, str]:
        """Enhanced candidate text processing with better normalization."""
        # Process skills
        skills = candidate.get("skills", [])
        if isinstance(skills, str):
            skills_list = [s.strip() for s in skills.split(",") if s.strip()]
        else:
            skills_list = list(skills)

        # Process aspirations
        aspirations = candidate.get("aspirations", [])
        if isinstance(aspirations, str):
            asp_list = [s.strip() for s in aspirations.split(",") if s.strip()]
        else:
            asp_list = list(aspirations)

        # Process other fields
        sector = str(candidate.get("sector_interest", "")).strip()
        location = str(candidate.get("location_preference", "")).strip()
        experience = str(candidate.get("experience", "")).strip()

        # Build enhanced text representations
        main_text = self._preprocess_text(", ".join(skills_list + asp_list + [experience]))
        industry_text = f"industry:{self._preprocess_text(sector)}"
        location_text = f"location:{self._preprocess_text(location)}"
        
        return {"main": main_text, "industry": industry_text, "location": location_text}

    def get_recommendations(self, candidate: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """Get enhanced recommendations with detailed scoring and analysis."""
        if self.internships_df is None:
            return {"error": "Engine not initialized with internship data."}
        
        if self.vec_main is None:
            self.fit()

        try:
            cand_texts = self._candidate_texts(candidate)

            # Transform candidate into vectors
            cand_main = self.vec_main.transform([cand_texts["main"]])
            cand_industry = self.vec_industry.transform([cand_texts["industry"]])
            cand_location = self.vec_location.transform([cand_texts["location"]])

            # Calculate similarities
            sim_main = cosine_similarity(cand_main, self.intern_main).ravel()
            sim_industry = cosine_similarity(cand_industry, self.intern_industry).ravel()
            sim_location = cosine_similarity(cand_location, self.intern_location).ravel()

            # Calculate education compatibility scores
            candidate_education = candidate.get("education_level", "")
            education_scores = np.array([
                self._calculate_education_compatibility(candidate_education, i) 
                for i in range(len(self.internships_df))
            ])

            # Weighted final scores
            final_scores = (
                self.weights["main"] * sim_main +
                self.weights["industry"] * sim_industry +
                self.weights["location"] * sim_location +
                self.weights["education"] * education_scores
            )

            # Get top recommendations
            top_idx = np.argsort(final_scores)[::-1][:top_k]
            recommendations = []

            for idx in top_idx:
                internship = self.internships_df.iloc[idx].to_dict()
                
                # Enhanced scoring breakdown
                skills_analysis = self._analyze_skills_gap(
                    candidate.get("skills", ""),
                    internship["required_skills"]
                )
                
                # Calculate confidence score
                confidence = min(
                    (final_scores[idx] * 0.7 + skills_analysis['skills_confidence'] * 0.3) * 100,
                    95.0
                )
                
                # Generate match reasoning
                reasoning_parts = []
                if sim_main[idx] > 0.3:
                    reasoning_parts.append(f"Strong skills match ({sim_main[idx]:.1%})")
                if sim_industry[idx] > 0.5:
                    reasoning_parts.append(f"Industry alignment ({sim_industry[idx]:.1%})")
                if sim_location[idx] > 0.7:
                    reasoning_parts.append("Location preference match")
                if education_scores[idx] > 0.8:
                    reasoning_parts.append("Education level compatible")
                
                match_reasoning = "; ".join(reasoning_parts) if reasoning_parts else "General compatibility"

                recommendation = {
                    **internship,
                    'similarity': float(final_scores[idx]),
                    'confidence_score': round(confidence, 1),
                    'match_reasoning': match_reasoning,
                    'skills_analysis': skills_analysis,
                    'score_breakdown': {
                        'skills_match': float(sim_main[idx]),
                        'industry_match': float(sim_industry[idx]),
                        'location_match': float(sim_location[idx]),
                        'education_compatibility': float(education_scores[idx])
                    }
                }
                
                recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            return {"error": f"Failed to generate recommendations: {str(e)}"}

    # Enhanced artifact management
    def export_artifacts(self, output_dir: str) -> Dict[str, str]:
        """Export model artifacts with enhanced metadata."""
        os.makedirs(output_dir, exist_ok=True)
        paths = {}
        
        # Define all paths
        artifact_files = [
            "vec_main", "vec_industry", "vec_location",
            "intern_main", "intern_industry", "intern_location",
            "internships_df"
        ]
        
        for artifact in artifact_files:
            paths[artifact] = os.path.join(output_dir, f"{artifact}.joblib")
        
        paths["weights_json"] = os.path.join(output_dir, "weights.json")
        paths["metadata_json"] = os.path.join(output_dir, "metadata.json")

        # Ensure fitted
        if any(getattr(self, attr) is None for attr in ["vec_main", "vec_industry", "vec_location"]):
            self.fit()

        # Save artifacts
        for artifact in artifact_files:
            joblib.dump(getattr(self, artifact), paths[artifact])

        # Save configuration and metadata
        with open(paths["weights_json"], "w", encoding="utf-8") as f:
            json.dump(self.weights, f, indent=2)
        
        metadata = {
            "model_version": "2.0",
            "education_hierarchy": self.education_hierarchy,
            "total_internships": len(self.internships_df) if self.internships_df is not None else 0,
            "feature_dimensions": {
                "main": self.intern_main.shape[1] if self.intern_main is not None else 0,
                "industry": self.intern_industry.shape[1] if self.intern_industry is not None else 0,
                "location": self.intern_location.shape[1] if self.intern_location is not None else 0
            }
        }
        
        with open(paths["metadata_json"], "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return paths

    def load_artifacts(self, input_dir: str) -> None:
        """Load artifacts with validation."""
        try:
            # Load vectorizers and matrices
            self.vec_main = joblib.load(os.path.join(input_dir, "vec_main.joblib"))
            self.vec_industry = joblib.load(os.path.join(input_dir, "vec_industry.joblib"))
            self.vec_location = joblib.load(os.path.join(input_dir, "vec_location.joblib"))
            self.intern_main = joblib.load(os.path.join(input_dir, "intern_main.joblib"))
            self.intern_industry = joblib.load(os.path.join(input_dir, "intern_industry.joblib"))
            self.intern_location = joblib.load(os.path.join(input_dir, "intern_location.joblib"))
            self.internships_df = joblib.load(os.path.join(input_dir, "internships_df.joblib"))
            
            # Load weights
            weights_path = os.path.join(input_dir, "weights.json")
            if os.path.exists(weights_path):
                with open(weights_path, "r", encoding="utf-8") as f:
                    self.weights = json.load(f)
            
            print("✅ Artifacts loaded successfully")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load artifacts: {str(e)}")


if __name__ == "__main__":
    # Enhanced CLI with better error handling
    try:
        here = os.path.dirname(__file__)
        csv_path = os.path.join(here, "internships.csv")
        artifacts_dir = os.path.join(here, "artifacts")
        
        if not os.path.exists(csv_path):
            print("❌ internships.csv not found. Please ensure the data file exists.")
            exit(1)
        
        print("🚀 Initializing Enhanced Recommendation Engine...")
        engine = InternshipRecommendationEngine()
        engine.load_data(csv_path)
        engine.fit()
        paths = engine.export_artifacts(artifacts_dir)
        
        print("\n✅ Enhanced artifacts exported successfully:")
        for k, v in paths.items():
            print(f"  📁 {k}: {v}")
        
        print(f"\n📊 Model Statistics:")
        print(f"  • Total internships: {len(engine.internships_df)}")
        print(f"  • Feature dimensions: {engine.intern_main.shape[1]} (main)")
        print(f"  • Education levels: {len(engine.education_hierarchy)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)