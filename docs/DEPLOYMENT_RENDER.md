# Deploying Text Detective on Render

This guide provides step-by-step instructions for hosting **Text Detective** on [Render](https://render.com) using your GitHub repository:
👉 `https://github.com/punithsai2006/TEXT-DETECTIVE`

---

## Method 1: Unified Docker Deployment (Recommended — Fits Free Tier in 1 Service)

This method packages the FastAPI backend and React frontend into a single container. FastAPI serves both the REST API at `/api` and the React frontend SPA at `/`.

### Step 1: Sign Up & Connect GitHub
1. Go to [https://dashboard.render.com](https://dashboard.render.com).
2. Log in or create an account (free).
3. If not already connected, connect your GitHub account.

### Step 2: Create a New Web Service
1. In the Render Dashboard, click **New +** (top right) $\rightarrow$ **Web Service**.
2. Select **Build and deploy from a Git repository** $\rightarrow$ click **Next**.
3. Under **Connect a repository**, find or enter:
   ```
   punithsai2006/TEXT-DETECTIVE
   ```
   (or paste `https://github.com/punithsai2006/TEXT-DETECTIVE`).
4. Click **Connect**.

### Step 3: Configure the Web Service
Configure the settings as follows:
- **Name:** `text-detective` (or your choice)
- **Region:** Choose the region closest to you (e.g. *Oregon (US West)* or *Frankfurt (EU)*)
- **Branch:** `main`
- **Root Directory:** *(leave blank)*
- **Runtime / Environment:** **Docker**
  *(Render will automatically detect the `Dockerfile` in the root repository)*
- **Instance Type:** **Free** ($0/month)

### Step 4: Environment Variables (Optional)
Under the **Environment Variables** section, you can add:
| Key | Value | Description |
|---|---|---|
| `LLM_PROVIDER` | `mock` *(default)* | Set to `openai` or `anthropic` if you have API keys |
| `OPENAI_API_KEY` | *(optional)* | Your OpenAI API key if using `openai` |
| `ANTHROPIC_API_KEY`| *(optional)* | Your Anthropic key if using `anthropic` |
| `DEMO_MODE` | `true` | Enables sample benchmark cases out of the box |

### Step 5: Deploy
1. Click **Create Web Service** at the bottom.
2. Render will trigger the Docker multi-stage build:
   - Builds React frontend (`npm run build`)
   - Installs Python dependencies
   - Seeds the 4 demo benchmark cases
   - Starts the server with `uvicorn app.main:app`
3. Once the build finishes (usually ~3-4 minutes), you will see:
   ```
   Your service is live 🎉
   ```
4. Click the generated URL at the top (e.g., `https://text-detective.onrender.com`) to open your live investigation assistant!

---

## Method 2: Render Blueprint (1-Click Infrastructure as Code)

The repository includes a `render.yaml` blueprint.

1. Go to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Blueprint**.
3. Connect `punithsai2006/TEXT-DETECTIVE`.
4. Render reads `render.yaml` and sets up the service automatically.
5. Click **Apply**.

---

## Method 3: Two-Service Deployment (Native Python API + Static Site CDN)

If you prefer to separate the backend and frontend into independent services:

### Part A: Deploy the Backend API
1. Render Dashboard $\rightarrow$ **New +** $\rightarrow$ **Web Service**.
2. Connect `punithsai2006/TEXT-DETECTIVE`.
3. Settings:
   - **Name:** `text-detective-api`
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt && python scripts/seed_demo_cases.py`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
   - **Environment Variables:**
     - `PYTHON_VERSION`: `3.11.9`
     - `LLM_PROVIDER`: `mock`
     - `DEMO_MODE`: `true`
4. Deploy and copy your backend URL (e.g. `https://text-detective-api.onrender.com`).

### Part B: Deploy the Frontend Static Site
1. Render Dashboard $\rightarrow$ **New +** $\rightarrow$ **Static Site**.
2. Connect `punithsai2006/TEXT-DETECTIVE`.
3. Settings:
   - **Name:** `text-detective-ui`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
4. **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://text-detective-api.onrender.com` *(your backend URL from Part A)*
5. **Redirects/Rewrites**:
   - Under Settings $\rightarrow$ Redirects/Rewrites, add:
     - **Source:** `/*`
     - **Destination:** `/index.html`
     - **Action:** `Rewrite`
6. Click **Create Static Site**.

---

## Verification & Health Check

Once deployed, you can verify your service:
- **API Health:** `https://your-service.onrender.com/api/health` $\rightarrow$ returns status `ok`.
- **API Docs:** `https://your-service.onrender.com/docs` $\rightarrow$ interactive Swagger UI.
- **Frontend App:** `https://your-service.onrender.com/` $\rightarrow$ full interactive UI with pre-seeded benchmark investigations.

> [!NOTE]
> On Render's Free tier, services spin down after 15 minutes of inactivity. When you visit the URL after dormancy, the first request may take 30-50 seconds to wake up the service. Subsequent requests are fast.
