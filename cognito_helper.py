import boto3
import requests
from jose import jwt

# Initialize the Cognito client
client = boto3.client('cognito-idp', region_name="us-west-2")

# Replace with your User Pool ID and Client ID
USER_POOL_ID = "us-west-2_TCKuweOar"
CLIENT_ID = "5qr3335bem5aoqls1qvr7ee16r"

COGNITO_PUBLIC_KEYS_URL = f"https://cognito-idp.us-west-2.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
keys = requests.get(COGNITO_PUBLIC_KEYS_URL).json()

def decode_token(token: str):
    header = jwt.get_unverified_header(token)
    key = next(
        (key for key in keys['keys'] if key['kid'] == header['kid']), 
        None
    )
    if not key:
        raise HTTPException(status_code=401, detail="Invalid token header")
    
    # Decode and validate token
    return jwt.decode(
        token,
        key=key,
        algorithms=["RS256"],
        audience=CLIENT_ID,  # Replace with your app client ID
        issuer=f"https://cognito-idp.us-west-2.amazonaws.com/{USER_POOL_ID}"
    )

def sign_up_user(username, password, email, role, org):
    try:
        response = client.sign_up(
            ClientId=CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'custom:role', 'Value': role},
                {'Name': 'custom:org', 'Value': org},
            ]
        )
        print("Sign-up successful:", response)
    except Exception as e:
        print("Error during sign-up:", e)

# Example usage
# sign_up_user("andelgado53", "XXXXXXXXXX", "andelgado53@hotmail.com", 'admin', 'company name')

def confirm_user(username, confirmation_code):
    try:
        response = client.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=username,
            ConfirmationCode=confirmation_code
        )
        print("User confirmed successfully:", response)
    except Exception as e:
        print("Error during confirmation:", e)

# Example usage (replace with actual confirmation code sent to email)
# confirm_user("andelgado53", "407202")


def authenticate_user(username, password):
    try:
        response = client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        print("Authentication successful!")
        access_token = response['AuthenticationResult']['AccessToken']
        id_token = response['AuthenticationResult']['IdToken']
        refresh_token = response['AuthenticationResult']['RefreshToken']
        # print("Access Token:", access_token)
        print(decode_token(access_token))
        # print("ID Token:", id_token)
        # print("Refresh Token:", refresh_token)
        return access_token
    except Exception as e:
        print("Error during authentication:", e)

# Example usage
access_token = authenticate_user("andelgado53", "LoLaBunny6@")
# print(acc)

def refresh_access_token(refresh_token):
    try:
        response = client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token
            }
        )
        print("Token refreshed successfully!")
        new_access_token = response['AuthenticationResult']['AccessToken']
        return new_access_token
    except Exception as e:
        print("Error refreshing token:", e)

# Example usage
# new_access_token = refresh_access_token(refresh_token)
# access_token = authenticate_user("andelgado53", "LoLaBunny6@")

API_URL = "https://api.emisofia.com"

def call_api(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(API_URL, headers=headers)
        print("API Response:", response.status_code, response.json())
    except Exception as e:
        print("Error calling API:", e)

# Example usage
print(access_token)
call_api(access_token)

# print(decode_token(access_token))
