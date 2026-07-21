# Finance Management Streamlit App

A Streamlit application for personal and farm financial management with profile-based dashboard layouts.

## Local development

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Run locally

```bash
python -m streamlit run main.py
```

If port `8501` is already in use, run:

```bash
python -m streamlit run main.py --server.port 8502
```

Or use the Windows launcher:

```cmd
run_app.bat
```

## Local data fallback

This app supports local development without GitHub secrets.

- If `GITHUB_TOKEN`, `REPO_NAME`, and `FILE_PATH` are not set in Streamlit secrets, the app uses a local `data.csv` file.
- The local file is created automatically when needed.
- This means the dashboard works locally even without GitHub sync enabled.

## GitHub sync

To enable GitHub-backed storage, add these Streamlit secrets in your deployment settings:

- `GITHUB_TOKEN`
- `REPO_NAME`
- `FILE_PATH`

If GitHub sync fails, the app will fall back to local storage and continue working.

## Deployment

### Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to https://share.streamlit.io.
3. Connect your GitHub repository.
4. Set `main.py` as the main file.
5. Add the GitHub secrets above under App Settings > Secrets.

### Heroku / other hosts

1. Push this repository to your chosen host.
2. Configure `Procfile` and `requirements.txt`.
3. Add GitHub secrets as environment variables if using sync.

## Notes

- The app is designed to work locally and on Streamlit-compatible hosts.
- If you want a public URL, deploy to Streamlit Community Cloud or another hosting provider.
