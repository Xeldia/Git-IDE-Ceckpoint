# Global Deployment Guide: Making Your Java IDE Accessible Worldwide

This guide will walk you through the process of making your Java IDE globally accessible, where anyone online can write Java code, click "Run," and your PC executes it behind the scenes.

## System Architecture

```
(1) User's browser (worldwide)
      ↓
(2) Render-hosted Django website
      ↓  HTTP POST /run_java
(3) Your PC (FastAPI Java executor)
      ↓  Compiles + runs Java
(4) Sends back output → Django → Browser
```

## Step 1: Set Up ngrok for Exposing Your Local FastAPI Server

1. **Install ngrok**
   - Download from [ngrok.com/download](https://ngrok.com/download)
   - Sign up for a free account to get your auth token

2. **Configure ngrok**
   ```bash
   # Authenticate with your token
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   
   # Start ngrok to expose your FastAPI server
   ngrok http 8081
   ```

3. **Note your public URL**
   - ngrok will display a URL like `https://random-id.ngrok.io`
   - This is your public Java API endpoint that forwards requests to your PC

## Step 2: Configure Environment Variables

Create a `.env` file in your Django project root:

```
# Django settings
DJANGO_SECRET_KEY=your-django-secret-key
DEBUG=False

# Java API settings
JAVA_API_URL=https://your-ngrok-url.ngrok.io
JAVA_API_SECRET=your-secret-key
```

## Step 3: Update Django to Use the ngrok URL

The Django integration is already set up in:
- `ide/services/java_executor.py` - Service for communicating with Java API
- `ide/views/java_execution.py` - Views for handling Java execution requests
- `ide/urls.py` - URL routing for Java execution endpoints

Just make sure to set the environment variables:
```bash
# On Windows
set JAVA_API_URL=https://your-ngrok-url.ngrok.io
set JAVA_API_SECRET=your-secret-key

# On Linux/Mac
export JAVA_API_URL=https://your-ngrok-url.ngrok.io
export JAVA_API_SECRET=your-secret-key
```

## Step 4: Deploy Django to Render

1. **Push your Django project to GitHub**

2. **Create a new Web Service on Render**
   - Go to [render.com](https://render.com)
   - Click "New" and select "Web Service"
   - Connect your GitHub repository

3. **Configure the Web Service**
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn config.wsgi:application`
   
4. **Add Environment Variables**
   - `DJANGO_SECRET_KEY`: Your Django secret key
   - `JAVA_API_URL`: Your ngrok URL (e.g., `https://random-id.ngrok.io`)
   - `JAVA_API_SECRET`: The secret key for API authentication

5. **Deploy**
   - Render will build and deploy your application
   - You'll get a URL like `https://your-django-app.onrender.com`

## Step 5: Keep Your Local FastAPI Server Running

1. **Start your FastAPI server**
   ```bash
   cd java-executor-api
   uvicorn server:app --host 0.0.0.0 --port 8081
   ```

2. **Keep ngrok running**
   ```bash
   ngrok http 8081
   ```

3. **Update the ngrok URL in Render**
   - Each time you restart ngrok, you'll get a new URL
   - Update the `JAVA_API_URL` environment variable in your Render dashboard

## Step 6: Test the Complete Workflow

1. Visit your Render-hosted Django site
2. Enter Java code in the editor
3. Click "Run"
4. The code should be sent to your PC via ngrok, executed, and the results displayed

## Security Considerations

- The system already includes token-based authentication and HMAC signatures
- Consider implementing rate limiting to prevent abuse
- Monitor your PC's resource usage
- Regularly update all dependencies

## Troubleshooting

1. **Connection Issues**
   - Ensure ngrok is running and the URL is correct
   - Check that your FastAPI server is running on port 8081
   - Verify environment variables are set correctly

2. **Execution Problems**
   - Check Java installation on your PC
   - Verify Docker is running (if using Docker-based execution)
   - Check logs for error messages

3. **Deployment Issues**
   - Review Render logs for any deployment errors
   - Ensure all dependencies are in requirements.txt