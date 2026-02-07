# --- 1. THE BASE LAYER ---
# We start with a standard Python 3.9 image. 
# "slim" means it's a stripped-down version (smaller, faster, more secure).
# This is like buying a computer with Windows pre-installed.
FROM python:3.9-slim

# --- 2. THE WORKING DIRECTORY ---
# We create a folder named "/app" inside the container.
# This acts as our "home base" inside the Linux system.
WORKDIR /app

# --- 3. CACHING DEPENDENCIES ---
# We copy ONLY the requirements.txt file first.
# Why? Docker caches layers. If you change your code (chaos_service.py) but NOT your requirements,
# Docker skips this step next time. This makes re-building 10x faster.
COPY requirements.txt .

# --- 4. INSTALLATION ---
# We run pip install inside the container.
# "--no-cache-dir" keeps the image small by not saving temporary download files.
RUN pip install --no-cache-dir -r requirements.txt

# --- 5. COPY SOURCE CODE ---
# Now we copy everything else (chaos_service.py, etc.) from your laptop into the container's /app folder.
COPY . .

# --- 6. NETWORK EXPOSURE ---
# This tells Docker "Hey, this container listens on port 8000."
# It's mostly for documentation, but good practice.
EXPOSE 8000

# --- 7. THE START COMMAND ---
# This is the command that runs when the container starts.
# CRITICAL CHANGE: We use "0.0.0.0" instead of "127.0.0.1".
# Why? "127.0.0.1" inside a container means "inside this box only."
# "0.0.0.0" means "accept connections from the outside world (your laptop)."
CMD ["uvicorn", "chaos_service:app", "--host", "0.0.0.0", "--port", "8000"]