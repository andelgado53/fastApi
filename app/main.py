from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/", response_class= HTMLResponse)
def root():
	response = """
	<!DOCTYPE html>
	<html lang="en">
	<head>
  	<meta charset="UTF-8">
  	<meta name="viewport" content="width=device-width, initial-scale=1.0">
  	<title>Emi is a bug</title>
  	<style>
    body {
      font-family: Arial, sans-serif;
      text-align: center;
      margin: 20px;
    }
    img {
      max-width: 60%;
      height: 10%;
      border: 2px solid #ccc;
      box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
    }
  	</style>
	</head>
	<body>
  	<h1>Emi is a bug</h1>
  	<img src="https://emisofia.s3.us-west-2.amazonaws.com/emi_love_bug.jpg" alt="Image from S3">
  	<p>Emi</p>
	</body>
	</html>
	"""
	return response

@app.get("/healthy")
def health_check():
	return "healthy"