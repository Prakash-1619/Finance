import streamlit as st
import pandas as pd
from github import Github
import io
from pathlib import Path

LOCAL_DATA_PATH = Path("data.csv")


def get_github_repo():
    g = Github(st.secrets["GITHUB_TOKEN"])
    return g.get_repo(st.secrets["REPO_NAME"])


def has_github_secrets():
    return all(key in st.secrets for key in ("GITHUB_TOKEN", "REPO_NAME", "FILE_PATH"))


def load_local_data():
    if not LOCAL_DATA_PATH.exists():
        df = pd.DataFrame(columns=[
            "Date", "Transaction Type", "Payment Status", "Amount", "Frequency",
            "Payment App", "Phone Number", "Bank Name", "Person/Org Name",
            "Org Name", "Domain", "Sub-Category", "Description", "Extra Details"
        ])
        df.to_csv(LOCAL_DATA_PATH, index=False)
        return df
    try:
        return pd.read_csv(LOCAL_DATA_PATH)
    except Exception as e:
        st.error(f"⚠️ Failed to read local data file: {e}")
        return pd.DataFrame()


def load_data():
    """Fetches the latest CSV from GitHub or falls back to local storage."""
    if has_github_secrets():
        try:
            repo = get_github_repo()
            file_path = st.secrets["FILE_PATH"]
            contents = repo.get_contents(file_path)
            decoded_content = contents.decoded_content.decode('utf-8')
            return pd.read_csv(io.StringIO(decoded_content))
        except Exception as e:
            st.warning(f"⚠️ GitHub load failed. Falling back to local data.csv: {e}")
            return load_local_data()
    return load_local_data()


def save_local_data(df):
    try:
        LOCAL_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(LOCAL_DATA_PATH, index=False)
        return True
    except Exception as e:
        st.error(f"⚠️ Failed to save local data: {e}")
        return False


def save_data_to_github(df, commit_message="Update records via Streamlit"):
    """Overwrites the GitHub CSV with the new DataFrame or saves locally if GitHub is not configured."""
    if has_github_secrets():
        try:
            repo = get_github_repo()
            file_path = st.secrets["FILE_PATH"]
            contents = repo.get_contents(file_path)
            csv_string = df.to_csv(index=False)
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=csv_string,
                sha=contents.sha
            )
            return True
        except Exception as e:
            st.warning(f"⚠️ GitHub save failed. Saving locally to data.csv instead: {e}")
            return save_local_data(df)
    return save_local_data(df)
