import streamlit as st
import pandas as pd
from github import Github
import io

def get_github_repo():
    g = Github(st.secrets["GITHUB_TOKEN"])
    return g.get_repo(st.secrets["REPO_NAME"])

def load_data():
    """Fetches the latest CSV from GitHub."""
    try:
        repo = get_github_repo()
        file_path = st.secrets["FILE_PATH"]
        contents = repo.get_contents(file_path)
        
        # Read the file content into a Pandas DataFrame
        decoded_content = contents.decoded_content.decode('utf-8')
        df = pd.read_csv(io.StringIO(decoded_content))
        return df
    except Exception as e:
        st.error(f"⚠️ Failed to load data from GitHub: {e}")
        return pd.DataFrame() # Return empty if it fails

def save_data_to_github(df, commit_message="Update records via Streamlit"):
    """Overwrites the GitHub CSV with the new DataFrame."""
    try:
        repo = get_github_repo()
        file_path = st.secrets["FILE_PATH"]
        
        # Get the current file's SHA (required by GitHub to update a file)
        contents = repo.get_contents(file_path)
        
        # Convert DataFrame back to CSV string
        csv_string = df.to_csv(index=False)
        
        # Commit the update
        repo.update_file(
            path=file_path, 
            message=commit_message, 
            content=csv_string, 
            sha=contents.sha
        )
        return True
    except Exception as e:
        st.error(f"⚠️ Failed to save to GitHub: {e}")
        return False
