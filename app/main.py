from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
import requests

from fastapi.middleware.cors import CORSMiddleware

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://emisofia.com", "https://www.emisofia.com", "http://localhost:5173" ],  # Allow emisofia.com
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Replace with your User Pool ID and Client ID
USER_POOL_ID = "us-west-2_eh0GmvqRD"
CLIENT_ID = "7lq155jn8debntq7mieosmeish"

COGNITO_PUBLIC_KEYS_URL = f"https://cognito-idp.us-west-2.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
keys = requests.get(COGNITO_PUBLIC_KEYS_URL).json()

def decode_token(token: str):
    try:
        payload = jwt.decode(token, options={"verify_signature": False})  # Replace with signature verification
        return payload
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/")
def root(token: str = Depends(oauth2_scheme)):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = auth_header.split(" ")[1]  # Extract Bearer token
    try:
        claims = decode_token(token)
        return { "message": "Emi is loved.", "context": claims}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
	

@app.get("/healthy")
def health_check():
	return {"message": "healthy"}