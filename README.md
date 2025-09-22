# ML-Powered Restaurant Recommender

A restaurant discovery tool that allows users to input a few of their favorite restaurants (anywhere) and receive similar recommendations in a selected city based on cuisine, price, description, and reviews.

## Running the Project

### Backend
```bash
cd backend/app
pip install -r ../requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The backend will run on `http://localhost:8000` and the frontend on `http://localhost:3000`.

