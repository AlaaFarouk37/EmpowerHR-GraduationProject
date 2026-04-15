import os
import numpy as np
import xgboost as xgb
from django.conf import settings

# Global model cache
_model = None
MODEL_PATH = os.path.join(settings.BASE_DIR, 'attrition', 'xgboost_model.json')

# Categorical Mappings to convert Profile strings to Model numbers
EDUCATION_MAP = {
    'High School': 1, 
    'Associate Degree': 2, 
    'Bachelor’s Degree': 3, 
    'Master’s Degree': 4, 
    'PhD': 5
}

JOB_LEVEL_MAP = {
    'Entry': 1, 
    'Mid': 2, 
    'Senior': 3
}

COMPANY_SIZE_MAP = {
    'Small': 1, 
    'Medium': 2, 
    'Large': 3
}

def load_model():
    """Loads and caches the XGBoost model."""
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        _model = xgb.XGBClassifier()
        _model.load_model(MODEL_PATH)
    return _model

def get_answer_value(answers_qs, keyword):
    """Retrieves a numerical value from the feedback answers based on a keyword."""
    for answer in answers_qs:
        q_text = answer.questionID.questionText.lower()
        if keyword.lower() in q_text:
            if answer.scoreValue is not None: return answer.scoreValue
            if answer.booleanValue is not None: return int(answer.booleanValue)
            if answer.decimalValue is not None: return float(answer.decimalValue)
    return None

def build_feature_vector(profile, answers_qs):
    """
    Constructs the feature vector from the PredictionUsersProfile instance.
    """
    missing = []

    def get(value, name):
        if value is None or value == "":
            missing.append(name)
            return 0
        return value

    # 1. Direct Model Attributes (from PredictionUsersProfile)
    # Binary encoding
    gender_val = 1 if profile.gender == 'Male' else 0
    marital_married = 1 if profile.maritalStatus == 'Married' else 0
    marital_single = 1 if profile.maritalStatus == 'Single' else 0
    
    # Map categorical strings to numbers
    edu_val = EDUCATION_MAP.get(profile.educationLevel, get(None, 'Education Level'))
    job_val = JOB_LEVEL_MAP.get(profile.jobLevel, get(None, 'Job Level'))
    size_val = COMPANY_SIZE_MAP.get(profile.companySize, get(None, 'Company Size'))

    # 2. Feedback/Survey Data
    # Note: Ensure these keywords match your Question model's text
    wlb = get(get_answer_value(answers_qs, 'Work-Life Balance'), 'Work-Life Balance')
    job_sat = get(get_answer_value(answers_qs, 'Job Satisfaction'), 'Job Satisfaction')
    reputation = get(get_answer_value(answers_qs, 'Company Reputation'), 'Company Reputation')
    recognition = get(get_answer_value(answers_qs, 'Employee Recognition'), 'Employee Recognition')

    # 3. Construct Vector in the exact order the model was trained
    vector = [
        get(profile.age, 'Age'),
        gender_val,
        get(profile.yearsAtCompany, 'Years at Company'),
        get(profile.monthlyIncome, 'Monthly Income'),
        wlb,
        job_sat,
        get(profile.numberOfPromotions, 'Number of Promotions'),
        int(profile.overtime),
        get(profile.distanceFromHome, 'Distance from Home'),
        edu_val,
        get(profile.numberOfDependents, 'Number of Dependents'),
        job_val,
        size_val,
        get(profile.companyTenure, 'Company Tenure'),
        int(profile.remoteWork),
        reputation,
        recognition,
        marital_married,
        marital_single,
    ]

    return np.array(vector, dtype=float), missing

def predict_risk(profile, answers_qs):
    """
    Main entry point for calculating attrition risk.
    Receives a PredictionUsersProfile instance.
    """
    model = load_model()
    vector, missing = build_feature_vector(profile, answers_qs)

    # Reshape for a single prediction
    proba = model.predict_proba(vector.reshape(1, -1))[0][1]
    risk_score = round(float(proba), 4)

    if risk_score >= 0.70:
        risk_level = 'High'
    elif risk_score >= 0.40:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'

    return {
        'employeeID': profile.employee_id, 
        'fullName': profile.full_name,
        'riskScore': risk_score,
        'riskLevel': risk_level,
        'missingFields': missing,
    }