from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score

CATEGORIES = ["ai_ml", "biotech", "fintech", "cleantech", "edtech", "general"]
CONFIDENCE_THRESHOLD = 0.25

SEED = {
    "ai_ml": [
        "An AI mobile app that identifies crop diseases from a photo of the leaf",
        "Machine learning model that predicts customer churn for telecom companies",
        "A chatbot using natural language processing to answer customer questions in Amharic",
        "Computer vision system that inspects products on a factory line for defects",
        "Deep learning platform that translates between Amharic, Oromo and English",
        "Predictive analytics tool that forecasts demand for retail shops using neural networks",
        "Speech recognition software that transcribes meetings automatically",
        "Recommendation engine that suggests products using user behaviour data",
        "AI assistant that reads legal contracts and highlights risky clauses",
        "Algorithm that detects fraud patterns in large datasets using machine learning",
        "Image recognition app that grades coffee beans by quality",
        "Generative AI tool that writes marketing content for small businesses",
        "Autonomous drone with computer vision for monitoring farmland",
        "Data science platform that automates reports with artificial intelligence",
        "Natural language processing system that summarizes news and documents",
    ],
    "biotech": [
        "Rapid diagnostic test kit that detects malaria from a blood sample",
        "Biofertilizer made from microorganisms to improve soil health",
        "Gene sequencing service for identifying hereditary diseases",
        "Vaccine cold storage solution using biological stabilizers",
        "Laboratory developed enzyme that increases yield in food fermentation",
        "Medical device that monitors blood glucose for diabetic patients",
        "Biopharmaceutical production of low cost insulin",
        "Cell culture technology to produce lab grown meat",
        "Herbal medicine research that isolates active compounds for drug development",
        "Genetic testing to select drought resistant crop varieties",
        "Probiotic supplements developed from local fermented foods",
        "Portable DNA test to detect livestock diseases in the field",
        "Antibiotic resistance research and new antimicrobial compounds",
        "Biosensor that detects toxins and pathogens in drinking water",
        "Clinical trial platform for testing new therapies",
    ],
    "fintech": [
        "Mobile money wallet that lets people send and receive payments without a bank account",
        "Micro loan platform that scores borrowers using mobile phone data",
        "Digital savings group app for rural cooperatives",
        "Payment gateway that lets online shops accept card and mobile payments",
        "Insurance platform that pays farmers automatically when rainfall is low",
        "Peer to peer lending marketplace connecting investors and small businesses",
        "Remittance service for sending money from the diaspora to families at low fees",
        "Point of sale system with built in credit for street vendors",
        "Blockchain based platform for secure transactions and digital identity",
        "Accounting and invoicing software for small businesses with tax reporting",
        "Crowdfunding platform that helps startups raise capital from investors",
        "Buy now pay later service for electronics and household goods",
        "Banking app that offers budgeting tools and instant transfers",
        "Credit scoring service for people without a bank history",
        "Mobile platform that lets traders pay suppliers and manage cash flow",
    ],
    "cleantech": [
        "Solar powered irrigation pumps for smallholder farmers",
        "Biogas digesters that turn animal waste into cooking fuel",
        "Recycling plant that converts plastic waste into building materials",
        "Clean cookstoves that reduce smoke and firewood use",
        "Solar home systems that bring electricity to off grid villages",
        "Wind and solar microgrid for rural health centres",
        "Water purification system powered by renewable energy",
        "Electric motorbikes that replace petrol taxis and cut emissions",
        "Waste to energy technology that burns municipal garbage cleanly",
        "Carbon credit platform that rewards tree planting and forest protection",
        "Energy efficient LED lighting and smart meters to reduce electricity use",
        "Rainwater harvesting and drip systems for water conservation",
        "Compost and organic waste processing to reduce landfill",
        "Hydropower and green hydrogen project for clean energy",
        "Solar dryers that preserve fruit and vegetables and cut post harvest loss",
    ],
    "edtech": [
        "Online learning platform with video lessons for secondary school students",
        "Mobile app that teaches reading and math to children in local languages",
        "Digital library and e-books for universities and schools",
        "Virtual classroom software for teachers to run live lessons",
        "Exam preparation app with practice questions and quizzes for national exams",
        "Coding bootcamp that trains young people in software development",
        "Skills training platform that connects graduates with internships and jobs",
        "Interactive science lab simulations for students without equipment",
        "Tutoring marketplace that matches students with qualified teachers",
        "Learning management system for schools to track attendance and grades",
        "Adult literacy course delivered by SMS and radio",
        "Educational games that make learning fun for primary school pupils",
        "Teacher training programme with online certification",
        "Scholarship and university admission guidance platform for students",
        "Vocational training courses in tailoring, welding and hospitality",
    ],
    "general": [
        "A coffee shop and roastery serving local customers",
        "Delivery service for restaurants and grocery shops in the city",
        "Tourism company offering guided cultural tours and hotel booking",
        "Furniture workshop making handmade wooden chairs and tables",
        "Clothing brand selling traditional textiles and fashion",
        "Event planning and wedding services company",
        "Real estate agency that rents apartments and offices",
        "Poultry and dairy farm selling eggs and milk to supermarkets",
        "Printing and packaging business for small manufacturers",
        "Car wash and vehicle repair garage",
        "Beauty salon and cosmetics retail store",
        "Logistics company transporting goods between towns",
        "Bakery producing bread and pastries for hotels and cafes",
        "Cleaning and security services for office buildings",
        "Photography and video production studio for businesses",
    ],
}


def _build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, stop_words="english",
                                  ngram_range=(1, 2), sublinear_tf=True)),
        ("nb", MultinomialNB(alpha=0.3)),
    ])


def _training_data():
    texts, labels = [], []
    for cat, items in SEED.items():
        for t in items:
            texts.append(t)
            labels.append(cat)
    return texts, labels


_model = None
_info = None


def get_model():
    global _model, _info
    if _model is None:
        texts, labels = _training_data()
        _model = _build_pipeline().fit(texts, labels)
        cv = cross_val_score(_build_pipeline(), texts, labels,
                             cv=StratifiedKFold(5, shuffle=True, random_state=42))
        _info = {
            "algorithm": "TF-IDF + Multinomial Naive Bayes",
            "categories": CATEGORIES,
            "training_examples": len(texts),
            "cv_accuracy": round(float(cv.mean()), 3),
            "note": "Small, hand-written dataset. Prototype quality. Advisory only.",
        }
    return _model


def model_info():
    get_model()
    return dict(_info)


def classify_idea(text):
    text = (text or "").strip()
    if len(text) < 10:
        return {"category": "general", "confidence": 0.0, "top3": [],
                "low_confidence": True, "reason": "Text too short"}
    m = get_model()
    probs = m.predict_proba([text])[0]
    classes = [str(c) for c in m.classes_]
    ranked = sorted(zip(classes, probs), key=lambda p: p[1], reverse=True)
    best, conf = ranked[0]
    low = bool(conf < CONFIDENCE_THRESHOLD)
    return {
        "category": "general" if low else str(best),
        "raw_prediction": str(best),
        "confidence": round(float(conf), 3),
        "low_confidence": low,
        "top3": [{"category": c, "probability": round(float(p), 3)} for c, p in ranked[:3]],
    }
