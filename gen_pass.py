from werkzeug.security import generate_password_hash

# Generate the hash
hashed = generate_password_hash('123456')
print(hashed)  # Copy this value