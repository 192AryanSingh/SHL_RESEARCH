import json

class SHLRecommender:
    def __init__(self, catalog_path="data/assessments.json"):
        with open(catalog_path, "r", encoding="utf-8") as file:
            self.assessments = json.load(file)
    
    def recommend(self, job_role=None, job_level=None, required_skills=None):
        recommendations = []
        
        for assessment in self.assessments:
            
            role_match = (
                job_role is None or
                any(job_role.lower() in role.lower() 
                    for role in assessment.get("job_roles", []))
            )
            
            
            level_match = (
                job_level is None or
                job_level in assessment.get("job_level", [])
            )
            
            
            skills_match = (
                required_skills is None or
                any(skill.lower() in [t.lower() for t in assessment["traits_measured"]]
                    for skill in required_skills)
            )
            
            if role_match and level_match and skills_match:
                recommendations.append(assessment["name"])
        
        return recommendations if recommendations else ["No matching assessments found."]
