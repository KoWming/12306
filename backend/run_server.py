import uvicorn
import os
import sys

# Ensure the current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

if __name__ == "__main__":
    # When running as an executable, we use the app object directly
    # and disable reload.
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
