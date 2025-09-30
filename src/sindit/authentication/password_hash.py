from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Replace with your password
password = "quasar"

# Generate the hash
hashed_password = pwd_context.hash(password)

print(f"Hashed password: {hashed_password}")
