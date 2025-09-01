import jwt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def get_auth_params(req):
    """ Estrae il token dall'header e ritorna il payload decodificato """
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise PermissionError(f"Authorization header mancante o non valido: {req.headers}")

    token = auth_header.split(" ")[1]


    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded   
    except jwt.ExpiredSignatureError:
        raise PermissionError("Token scaduto")
    except jwt.InvalidTokenError as e:
        raise PermissionError(f"Token non valido: {token}")
