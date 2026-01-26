# Deployment Guide 🚀

## Option 1: Streamlit Community Cloud (Easiest & Free)
Best for quick demos.

1.  **Push to GitHub**:
    Ensure this project is in a GitHub repository.
    ```bash
    git add .
    git commit -m "Ready for deploy"
    git push origin main
    ```

2.  **Connect to Streamlit**:
    *   Go to [share.streamlit.io](https://share.streamlit.io/).
    *   Login with GitHub.
    *   Click **"New App"**.
    *   Select your repository, branch (`main`), and file path (`src/ui/app.py`).

3.  **Add Secrets (Critical!)**:
    *   In the Streamlit Dashboard, click "Advanced Settings" -> "Secrets".
    *   Add your API key:
        ```
        GEMINI_API_KEY = "AIzaSy..."
        ```
    *   *Note: Our code reads `os.getenv`, but Streamlit secrets are also injected as env vars, so this works.*

4.  **Deploy!**
    *   **Warning:** Streamlit Cloud filesystem is *ephemeral*. If the app restarts, **newly ingested topics or sessions might be reset**. To fix this for production, you would need to switch the `KnowledgeBase` to save to a database (like Firestore) instead of JSON files.

---

## Option 2: Docker / Any Cloud (Robust)
Best for persistence (if using Volumes) and control.

1.  **Build Image**:
    ```bash
    docker build -t smart-practice .
    ```

2.  **Run Container**:
    ```bash
    docker run -p 8501:8501 \
      -e GEMINI_API_KEY="your_key_here" \
      -v $(pwd)/data:/app/data \
      smart-practice
    ```
    *   The `-v` flag maps your local `data` folder to the container. This ensures **your sessions and topics are saved** even if you stop the container.
