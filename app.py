import sys
import os

# Add the root directory to sys.path so that 'src' can be imported correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from group_project.web_app import Handler, run_server

# Vercel's Python runtime requires the entrypoint object to be named 'handler' or 'app'
app = Handler
handler = Handler


if __name__ == "__main__":
    run_server()
