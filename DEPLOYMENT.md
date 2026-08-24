# Deployment Guide for NLP Pipeline

This guide provides step-by-step instructions for deploying the NLP Pipeline web application to various platforms.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Option A: Railway.app (Recommended)](#option-a-railwayapp-recommended)
3. [Option B: Render.com](#option-b-rendercom)
4. [Option C: Fly.io](#option-c-flyio)
5. [Option D: Google Cloud Run](#option-d-google-cloud-run)
6. [Environment Variables](#environment-variables)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Troubleshooting](#troubleshooting)
9. [Updating the Application](#updating-the-application)

---

## Pre-Deployment Checklist

Before deploying, ensure the following:

### Code Preparation
- [ ] Remove `venv/` from repository (already in `.gitignore`)
- [ ] Remove `orchestrator/pipeline_config.json` from repository (already in `.gitignore`)
- [ ] Remove `registry/modules.json` from repository (already in `.gitignore`)
- [ ] Ensure `requirements.txt` is up-to-date
- [ ] Test Docker build locally (optional but recommended)

### Security
- [ ] Change `app.secret_key` from hardcoded default (see Environment Variables)
- [ ] Set `FLASK_ENV=production` to disable debug mode

### Testing
- [ ] Run full test suite: `python3 run_tests.py`
- [ ] Test web UI locally: `python3 run_web.py`
- [ ] Verify all modules work correctly

---

## Option A: Railway.app (Recommended)

Railway is the easiest platform for deploying Flask applications. It offers a free tier and automatic HTTPS.

### Steps

1. **Create a GitHub Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/nlp-pipeline.git
   git push -u origin main
   ```

2. **Sign Up for Railway**
   - Go to [railway.app](https://railway.app)
   - Sign up with your GitHub account

3. **Create a New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select your `nlp-pipeline` repository

4. **Configure the Service**
   - Railway will auto-detect the Flask app
   - Set the following environment variables:
     - `FLASK_ENV`: `production`
     - `SECRET_KEY`: (generate a random string, see Environment Variables)
     - `PORT`: `5000`

5. **Deploy**
   - Railway will automatically deploy on every push to `main`
   - The deployment URL will be shown in the dashboard

6. **Verify Deployment**
   - Visit the provided URL
   - Test the analyze functionality
   - Check all pages (Analyze, Modules, Config)

### Railway Configuration File (Optional)

Create a `railway.toml` file for custom configuration:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python run_web.py"
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
```

---

## Option B: Render.com

Render offers a free tier with automatic HTTPS and easy GitHub integration.

### Steps

1. **Create a GitHub Repository** (same as Railway)

2. **Sign Up for Render**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account

3. **Create a New Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select the `nlp-pipeline` repository

4. **Configure the Service**
   - **Name:** `nlp-pipeline`
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run_web.py`
   - **Plan:** Free

5. **Set Environment Variables**
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: (generate a random string)
   - `PYTHON_VERSION`: `3.11`

6. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically

7. **Verify Deployment**
   - Visit the provided URL (e.g., `https://nlp-pipeline.onrender.com`)
   - Test the application

---

## Option C: Fly.io

Fly.io offers global edge deployment with Docker support.

### Steps

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign Up for Fly.io**
   ```bash
   fly auth signup
   ```

3. **Initialize the App**
   ```bash
   cd nlp-pipeline
   fly launch
   ```
   - This will create a `fly.toml` file
   - Choose a name for your app
   - Select a region (closest to your users)

4. **Configure Environment Variables**
   ```bash
   fly secrets set FLASK_ENV=production
   fly secrets set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

6. **Verify Deployment**
   ```bash
   fly open
   ```

### Fly.io Configuration

The `fly.toml` file will be auto-generated. Example:

```toml
app = "nlp-pipeline"
primary_region = "iad"

[build]

[http_service]
  internal_port = 5000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 1024
```

---

## Option D: Google Cloud Run

Google Cloud Run offers pay-per-use pricing and automatic scaling.

### Steps

1. **Install Google Cloud CLI**
   ```bash
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud init
   ```

2. **Enable Cloud Run API**
   ```bash
   gcloud services enable run.googleapis.com
   ```

3. **Build and Push Docker Image**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/nlp-pipeline
   ```

4. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy nlp-pipeline \
     --image gcr.io/YOUR_PROJECT_ID/nlp-pipeline \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars FLASK_ENV=production,SECRET_KEY=YOUR_SECRET_KEY
   ```

5. **Verify Deployment**
   ```bash
   gcloud run services describe nlp-pipeline --region us-central1
   ```

---

## Environment Variables

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `SECRET_KEY` | Secret key for session signing | (random 32-byte hex string) |
| `PORT` | Port to listen on | `5000` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_DEBUG` | Enable debug mode | `false` |

### Generating a Secret Key

Use Python to generate a secure secret key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Post-Deployment Verification

After deployment, verify the following:

1. **Home Page**
   - Visit the root URL
   - Verify the page loads correctly
   - Check that sample sentences are displayed

2. **Analyze Functionality**
   - Enter a sample text (e.g., "This is a great day!")
   - Click "Analyze"
   - Verify results are displayed correctly
   - Check that all pipeline stages are shown

3. **Modules Page**
   - Navigate to `/modules`
   - Verify registered modules are displayed
   - Test module functionality

4. **Config Page**
   - Navigate to `/config`
   - Verify pipeline configuration is displayed
   - Test enable/disable functionality

5. **Error Handling**
   - Test with empty input
   - Test with very long input
   - Verify error messages are displayed correctly

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Symptoms:** 500 error or application crashes on startup

**Solutions:**
- Check environment variables are set correctly
- Verify `requirements.txt` is complete
- Check application logs for error messages

#### 2. Module Loading Errors

**Symptoms:** Pipeline fails to run, module errors in logs

**Solutions:**
- Verify all required packages are installed
- Check module file paths are correct
- Review module registration in `registry/modules.json`

#### 3. Static Files Not Loading

**Symptoms:** CSS/JS not loading, page looks unstyled

**Solutions:**
- Verify static files are included in deployment
- Check Flask static file configuration
- Clear browser cache

#### 4. Memory Issues

**Symptoms:** Application crashes during HuggingFace model loading

**Solutions:**
- Increase memory allocation in platform settings
- Use smaller models (e.g., DistilBERT instead of BERT-large)
- Consider using CPU-only models

### Debugging Commands

```bash
# Check application logs
railway logs  # Railway
render logs   # Render
fly logs      # Fly.io
gcloud logging read "resource.type=cloud_run_revision"  # Cloud Run

# Test locally
python3 run_web.py

# Run tests
python3 run_tests.py
```

---

## Updating the Application

### Automatic Updates (Railway/Render)

1. Push changes to GitHub:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

2. The platform will automatically redeploy

### Manual Updates (Fly.io)

1. Push changes to GitHub
2. Deploy manually:
   ```bash
   fly deploy
   ```

### Rolling Back

If an update causes issues:

1. **Railway:** Use the dashboard to roll back to a previous deployment
2. **Render:** Use the dashboard to roll back to a previous deployment
3. **Fly.io:** Deploy a previous version:
   ```bash
   fly deploy --image-label v1
   ```

---

## Performance Optimization

### For Production

1. **Use Gunicorn** (recommended for production):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 run_web:app
   ```

2. **Enable Caching:**
   - Add cache headers for static files
   - Use Redis for session storage (optional)

3. **Optimize HuggingFace Models:**
   - Use smaller models (DistilBERT, etc.)
   - Pre-download models during build
   - Use CPU-only models for free tiers

---

## Security Considerations

1. **Secret Key:** Always use a strong, random secret key
2. **Debug Mode:** Never enable debug mode in production
3. **HTTPS:** All platforms provide automatic HTTPS
4. **Input Validation:** The application validates all user inputs
5. **Session Security:** Flask sessions are signed with the secret key

---

## Cost Estimation

### Free Tiers

| Platform | Free Tier | Limitations |
|----------|-----------|-------------|
| Railway | 500 hours/month | Sleeps after 30 min inactivity |
| Render | 750 hours/month | Sleeps after 15 min inactivity |
| Fly.io | 3 shared-cpu-1x VMs | 256MB RAM each |
| Cloud Run | 2 million requests/month | 180,000 vCPU-seconds |

### Paid Plans

For production use with high traffic:
- Railway: $5/month for Hobby plan
- Render: $7/month for Starter plan
- Fly.io: Pay-as-you-go
- Cloud Run: Pay-per-use

---

## Support

For deployment issues:
1. Check platform documentation
2. Review application logs
3. Test locally first
4. Contact platform support if needed

---

## Quick Start Commands

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Render
```bash
# No CLI required - use web dashboard
# Push to GitHub and connect in Render dashboard
```

### Fly.io
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy
fly deploy
```

### Google Cloud Run
```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Login
gcloud auth login

# Deploy
gcloud run deploy nlp-pipeline --source .
```

---

## Conclusion

The NLP Pipeline can be deployed to any of these platforms with minimal configuration. Railway.app is recommended for the easiest setup, while Fly.io offers the best performance for global users. Choose the platform that best fits your needs and budget.

For questions or issues, refer to the platform documentation or contact the development team.
