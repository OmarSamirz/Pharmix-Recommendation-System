import uvicorn
from fastapi import FastAPI, Request
from models import RecommendationScheme, Product
from pharmix_recommender import PharmixRecommender

app = FastAPI()

@app.post('/recommend')
async def recommend(value: RecommendationScheme):
    recommender = PharmixRecommender(value)
    recommendations: Product = recommender()
    return {'recommendations': recommendations}

@app.get('/')
async def main(request: Request):
    return {'status': True}

if __name__ == '__main__':
    uvicorn.run(app)