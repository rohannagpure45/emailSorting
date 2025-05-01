import sys
import os
import streamlit as st

# Add the parent directory to the path so we can import properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the dashboard app
from dashboard.app import main

# Run the Streamlit app
if __name__ == "__main__":
    main() 