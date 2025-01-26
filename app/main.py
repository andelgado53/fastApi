from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://emisofia.com", "https://www.emisofia.com", "http://localhost:5173" ],  # Allow emisofia.com
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
	return { "message": "Emi is loved."}

@app.get("/healthy")
def health_check():
	return {"message": "healthy"}