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
  	<title>Emi Sofia</title>
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
	<h1>Emi is turning 5!!!</h1>
	<video controls>
  	<source src="https://emisofia.s3.us-west-2.amazonaws.com/Bluey-Emi-3550868620v2.mp4" type="video/mp4">
	</video>
	</body>
	</html>
	"""
	return response

@app.get("/healthy")
def health_check():
	return "healthy"