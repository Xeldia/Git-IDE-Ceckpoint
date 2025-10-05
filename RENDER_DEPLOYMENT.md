# Render Deployment Guide

This guide explains how to deploy the combined Django and Java Executor application to Render.

## Overview

This deployment uses a single Render service to run:
1. Django application (port 8000)
2. Java Executor WebSocket server (port 8080)
3. Nginx as a reverse proxy to route traffic

## Deployment Steps

1. **Push your code to GitHub**
   - Make sure all files are committed and pushed to your repository

2. **Create a new Web Service on Render**
   - Log in to your Render dashboard
   - Click "New" and select "Web Service"
   - Connect your GitHub repository

3. **Configure the service**
   - Name: Choose a name (e.g., "git-ide")
   - Root Directory: Leave blank (use repository root)
   - Environment: Docker
   - Region: Choose a region close to your users
   - Branch: main (or your default branch)
   - Plan: Select an appropriate plan (at least 512MB RAM recommended)

4. **Set environment variables** (optional)
   - PORT: 80 (for nginx)
   - MAX_EXECUTION_TIME: 30000 (or your preferred timeout in milliseconds)

5. **Deploy the service**
   - Click "Create Web Service"
   - Wait for the build and deployment to complete

## Testing Your Deployment

1. Access your application at the URL provided by Render
2. Navigate to the Java IDE page
3. Try running some Java code to verify the WebSocket connection works

## Troubleshooting

If you encounter issues:

1. **WebSocket Connection Failures**
   - Check Render logs for any errors in the Java executor server
   - Verify nginx is running and properly configured

2. **Java Compilation/Execution Issues**
   - Check if the Java environment is properly set up
   - Verify the temp directory has proper permissions

3. **Django Application Issues**
   - Check Django logs for any errors
   - Verify database migrations have run successfully