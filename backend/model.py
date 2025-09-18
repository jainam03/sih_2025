import os
import json
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib


class InternshipRecommendationEngine:
    """Lightweight content-based recommendation engine for internships.

    Uses weighted cosine similarity across three fields:
    - main: candidate skills + aspirations vs required_skills + role (ngram TF-IDF)
    - industry: candidate sector interest vs internship industry (unigram TF-IDF)
    - location: candidate location preference vs internship location (unigram TF-IDF)
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self.internships_df: Optional[pd.DataFrame] = None

        # Vectorizers
        self.vec_main: Optional[TfidfVectorizer] = None
        self.vec_industry: Optional[TfidfVectorizer] = None
        self.vec_location: Optional[TfidfVectorizer] = None

        # Internship-side feature matrices
        self.intern_main = None
        self.intern_industry = None
        self.intern_location = None

        # Weights
        if weights is None:
            weights = {"main": 0.6, "industry": 0.2, "location": 0.2}
        self.weights = weights

    def load_data(self, internships_csv_path: str) -> None:
        df = pd.read_csv(internships_csv_path)
        # Normalize expected columns
        expected = {"id", "company", "role", "location", "industry", "required_skills"}
        missing = expected - set(df.columns)
        if missing:
            raise ValueError(f"internships.csv missing columns: {', '.join(sorted(missing))}")

        # Ensure strings
        for col in ["company", "role", "location", "industry", "required_skills"]:
            df[col] = df[col].fillna("").astype(str)

        self.internships_df = df

    def _build_internship_corpora(self) -> Dict[str, List[str]]:
        assert self.internships_df is not None
        # Main text: skills + role
        main = (self.internships_df["required_skills"].astype(str) + " " +
                self.internships_df["role"].astype(str)).tolist()
        # Industry text
        industry = ("industry:" + self.internships_df["industry"].astype(str)).tolist()
        # Location text
        location = ("location:" + self.internships_df["location"].astype(str)).tolist()
        return {"main": main, "industry": industry, "location": location}

    def fit(self) -> None:
        """Fit vectorizers on internship data and cache internship matrices."""
        if self.internships_df is None:
            raise RuntimeError("Load internships data before fit().")

        corpora = self._build_internship_corpora()

        self.vec_main = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
        self.vec_industry = TfidfVectorizer()
        self.vec_location = TfidfVectorizer()

        self.intern_main = self.vec_main.fit_transform(corpora["main"])  # (n_intern, f)
        self.intern_industry = self.vec_industry.fit_transform(corpora["industry"])  # (n_intern, f)
        self.intern_location = self.vec_location.fit_transform(corpora["location"])  # (n_intern, f)

    def _candidate_texts(self, candidate: Dict[str, Any]) -> Dict[str, str]:
        # Normalize candidate fields
        skills = candidate.get("skills", [])
        if isinstance(skills, str):
            skills_list = [s.strip() for s in skills.split(",") if s.strip()]
        else:
            skills_list = list(skills)

        aspirations = candidate.get("aspirations", [])
        if isinstance(aspirations, str):
            asp_list = [s.strip() for s in aspirations.split(",") if s.strip()]
        else:
            asp_list = list(aspirations)

        sector = str(candidate.get("sector_interest", "")).strip()
        location = str(candidate.get("location_preference", "")).strip()

        main_text = ", ".join(skills_list + asp_list)
        industry_text = f"industry:{sector}" if sector else ""
        location_text = f"location:{location}" if location else ""
        return {"main": main_text, "industry": industry_text, "location": location_text}

    def get_recommendations(self, candidate: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        if self.internships_df is None:
            return {"error": "Engine not initialized with internship data."}
        if self.vec_main is None:
            # Fit lazily if not fitted
            self.fit()

        cand_texts = self._candidate_texts(candidate)

        # Transform candidate into vectors aligned to internship feature spaces
        cand_main = self.vec_main.transform([cand_texts["main"]])
        cand_industry = self.vec_industry.transform([cand_texts["industry"]])
        cand_location = self.vec_location.transform([cand_texts["location"]])

        # Cosine similarities
        sim_main = cosine_similarity(cand_main, self.intern_main)  # (1, n)
        sim_industry = cosine_similarity(cand_industry, self.intern_industry)
        sim_location = cosine_similarity(cand_location, self.intern_location)

        scores = (self.weights["main"] * sim_main +
                  self.weights["industry"] * sim_industry +
                  self.weights["location"] * sim_location).ravel()

        # Top-k
        top_idx = np.argsort(scores)[::-1][:top_k]
        recs_df = self.internships_df.iloc[top_idx].copy()
        recs_df["similarity"] = scores[top_idx]
        return recs_df.to_dict("records")

    # --------- Artifact IO ---------
    def export_artifacts(self, output_dir: str) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        paths = {}
        paths["vec_main"] = os.path.join(output_dir, "vec_main.joblib")
        paths["vec_industry"] = os.path.join(output_dir, "vec_industry.joblib")
        paths["vec_location"] = os.path.join(output_dir, "vec_location.joblib")
        paths["intern_main"] = os.path.join(output_dir, "intern_main.joblib")
        paths["intern_industry"] = os.path.join(output_dir, "intern_industry.joblib")
        paths["intern_location"] = os.path.join(output_dir, "intern_location.joblib")
        paths["internships_df"] = os.path.join(output_dir, "internships_df.joblib")
        paths["weights_json"] = os.path.join(output_dir, "weights.json")

        if any(v is None for v in [self.vec_main, self.vec_industry, self.vec_location, self.intern_main, self.intern_industry, self.intern_location]):
            # Ensure fitted
            self.fit()

        joblib.dump(self.vec_main, paths["vec_main"])  # type: ignore[arg-type]
        joblib.dump(self.vec_industry, paths["vec_industry"])  # type: ignore[arg-type]
        joblib.dump(self.vec_location, paths["vec_location"])  # type: ignore[arg-type]
        joblib.dump(self.intern_main, paths["intern_main"])  # type: ignore[arg-type]
        joblib.dump(self.intern_industry, paths["intern_industry"])  # type: ignore[arg-type]
        joblib.dump(self.intern_location, paths["intern_location"])  # type: ignore[arg-type]
        joblib.dump(self.internships_df, paths["internships_df"])  # type: ignore[arg-type]
        with open(paths["weights_json"], "w", encoding="utf-8") as f:
            json.dump(self.weights, f)

        return paths

    def load_artifacts(self, input_dir: str) -> None:
        self.vec_main = joblib.load(os.path.join(input_dir, "vec_main.joblib"))
        self.vec_industry = joblib.load(os.path.join(input_dir, "vec_industry.joblib"))
        self.vec_location = joblib.load(os.path.join(input_dir, "vec_location.joblib"))
        self.intern_main = joblib.load(os.path.join(input_dir, "intern_main.joblib"))
        self.intern_industry = joblib.load(os.path.join(input_dir, "intern_industry.joblib"))
        self.intern_location = joblib.load(os.path.join(input_dir, "intern_location.joblib"))
        self.internships_df = joblib.load(os.path.join(input_dir, "internships_df.joblib"))
        weights_path = os.path.join(input_dir, "weights.json")
        if os.path.exists(weights_path):
            with open(weights_path, "r", encoding="utf-8") as f:
                self.weights = json.load(f)


if __name__ == "__main__":
    # Helper CLI: fit on internships.csv and export artifacts
    here = os.path.dirname(__file__)
    csv_path = os.path.join(here, "internships.csv")
    artifacts_dir = os.path.join(here, "artifacts")
    engine = InternshipRecommendationEngine()
    engine.load_data(csv_path)
    engine.fit()
    paths = engine.export_artifacts(artifacts_dir)
    print("Artifacts exported:")
    for k, v in paths.items():
        print(f"  {k}: {v}")


