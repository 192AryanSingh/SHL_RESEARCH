from engine.recommender import SHLRecommender

def main():
    recommender = SHLRecommender()
    
    
    print("Recommendations for Account Manager (Mid-Level, Sales Skills):")
    print(recommender.recommend(
        job_role="Account Manager",
        job_level="Mid-Professional",
        required_skills=["Sales Potential", "Customer Focus"]
    ))
    
    
    print("\nRecommendations for Analytical Role (Entry-Level, Problem-Solving):")
    print(recommender.recommend(
        job_role="Analyst",
        job_level="Entry",
        required_skills=["Numeracy", "Problem-Solving"]
    ))

if __name__ == "__main__":
    main()
