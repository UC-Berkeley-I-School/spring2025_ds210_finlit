from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

class UserPersonalization:
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=4, random_state=42)
        
    def _encode_categorical_features(self, profile_data):
        """
        Convert profile categorical data to numerical features:
        - Time in UAE: Convert to months
        - Education: Convert to years of education
        - Job stability: Based on employment status
        - Financial access: Based on bank account status
        - Risk level: Based on debt and remittance method
        """
        features = {
            'time_in_uae_months': self._convert_time_to_months(profile_data['time_in_uae']),
            'education_years': self._convert_education_to_years(profile_data['education_level']),
            'job_stability': self._calculate_job_stability(profile_data['job_title']),
            'financial_access': self._calculate_financial_access(profile_data['bank_account']),
            'risk_level': self._calculate_risk_level(profile_data['debt_information'], 
                                                   profile_data['remittance_information'])
        }
        return features

    def _convert_time_to_months(self, time_range):
        mapping = {
            'Less than a year': 6,
            '1-3 Years': 24,
            '3-5 Years': 48,
            '5-10 Years': 84,
            '10+ Years': 120
        }
        return mapping.get(time_range, 0)

    def _convert_education_to_years(self, education):
        mapping = {
            'None': 0,
            'Primary School': 6,
            'High School': 12,
            'College': 16
        }
        return mapping.get(education, 0)

    def _calculate_job_stability(self, job_title):
        if job_title == 'Seeking Employment':
            return 0
        return 1

    def _calculate_financial_access(self, bank_account):
        return 0 if bank_account == 'No Bank Account' else 1

    def _calculate_risk_level(self, debt_info, remittance_method):
        risk_score = 0
        if debt_info != 'No Debt':
            risk_score += 1
        if remittance_method == "Don't know how to Send Money":
            risk_score += 1
        return risk_score

    def get_user_cluster(self, profile_data):
        """
        Determine user's financial literacy cluster based on profile data
        """
        features = self._encode_categorical_features(profile_data)
        feature_vector = np.array(list(features.values())).reshape(1, -1)
        scaled_features = self.scaler.fit_transform(feature_vector)
        cluster = self.kmeans.fit_predict(scaled_features)[0]
        return cluster

    def get_recommended_topics(self, profile_data):
        """
        Generate personalized learning topic recommendations based on user profile
        """
        cluster = self.get_user_cluster(profile_data)
        
        # Base topics that everyone should learn
        base_topics = ["Learn Financial Basics"]
        
        # Additional topics based on profile analysis
        recommended_topics = []
        
        # Banking recommendations
        if profile_data['bank_account'] == 'No Bank Account':
            recommended_topics.append("Banking Options")
        
        # Debt management recommendations
        if profile_data['debt_information'] != 'No Debt':
            recommended_topics.append("Debt Repayment")
        
        # Remittance recommendations
        if profile_data['remittance_information'] in ["Don't know how to Send Money", "Send Money through Informal Network"]:
            recommended_topics.append("Sending Money Home")
        
        # Budgeting recommendations (prioritized for certain clusters)
        if cluster in [0, 2]:  # Clusters that might need more financial planning help
            recommended_topics.append("Creating a Budget")
            
        # Combine and prioritize topics
        all_topics = base_topics + recommended_topics
        
        return all_topics[:5]  # Return top 5 most relevant topics 

# Personalization Strategy Notes

"""
1. User Clustering Approach
-------------------------
- Cluster users based on profile information:
  * Time in UAE (experience in the region)
  * Education level (financial literacy potential)
  * Job stability
  * Banking status
  * Risk level (debt situation)

2. Feature Engineering
---------------------
- Convert categorical variables to numerical:
  * Time ranges to months
  * Education levels to years
  * Binary indicators for employment, banking status
  * Risk scores based on debt and remittance methods

3. Recommendation Logic
----------------------
- Base recommendations on:
  * User's cluster assignment
  * Immediate needs (no bank account → banking module)
  * Risk factors (debt situation → debt management)
  * Financial behavior (remittance habits)
  * Previous module completion

4. Future Enhancements
---------------------
- Incorporate user interaction data
- A/B testing different recommendation strategies
- Collaborative filtering based on similar user profiles
- Dynamic difficulty adjustment based on user progress
- Multi-language content customization
""" 