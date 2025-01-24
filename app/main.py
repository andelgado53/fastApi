from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
	return { "message": "Emi is loved."}

@app.get("/healthy")
def health_check():
	return {"message": "healthy"}