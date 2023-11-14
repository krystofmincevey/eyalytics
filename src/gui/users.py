import hashlib


# TODO: Dramatically improve if ever released in production
# Dummy user data for demonstration
# In a real application, use a secure database
ADMIN_USER = 'admin'
GUEST_USER = 'guest'
RAG_USER = 'rag'
USER_DATA = {
    ADMIN_USER: hashlib.sha256("password".encode()).hexdigest(),
    GUEST_USER: hashlib.sha256("password".encode()).hexdigest(),
    RAG_USER: hashlib.sha256("password".encode()).hexdigest(),
}


def verify_user(username: str, password: str):
    if username in USER_DATA:
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
        return USER_DATA[username] == hashed_pwd
    return False
