# Deployment Guide for Dripzy.app

This guide explains how to deploy the Dripzy.app application using the CI/CD pipeline.

## CI/CD Pipeline

The repository has a GitHub Actions workflow that automates testing, building, and deploying the application.

### How it works

1. When you push to `main` or `master` branch, the workflow automatically:
   - Runs tests
   - Builds the frontend
   - Deploys to GitHub Pages
   - Deploys the backend to Heroku

2. Pull requests to these branches will trigger testing and building (but not deployment).

3. You can also manually trigger the workflow from the GitHub Actions tab.

## Secrets Setup

For the CI/CD pipeline to work correctly, you need to set up several GitHub secrets:

1. `SSH_PRIVATE_KEY`: Your SSH private key for secure deployments
2. `HEROKU_API_KEY`: Your Heroku API key for backend deployment
3. `HEROKU_EMAIL`: The email associated with your Heroku account

**For detailed instructions on setting up these secrets, see the [GitHub Secrets Setup Guide](GITHUB_SECRETS.md).**

## Manual Deployment

If you prefer manual deployment:

### Frontend Deployment

Run the build-deploy script:
```bash
./build-deploy.sh
```

Then push to GitHub:
```bash
git add .
git commit -m "Deploy frontend update"
git push origin main
```

### Backend Deployment

#### Option 1: Deploy to Heroku manually

```bash
cd backend
git init
heroku git:remote -a dripzy-backend
git add .
git commit -m "Deploy backend update"
git push heroku main
```

#### Option 2: SSH into your server (if using VPS)

```bash
ssh user@your-server.com
cd /path/to/backend
git pull
python -m pip install -r requirements.txt
sudo systemctl restart dripzy-backend
```

## Custom Domain Setup

The application is configured to use `dripzy.app` as its custom domain. Make sure your domain DNS settings point to GitHub Pages.

For a custom domain on GitHub Pages:
1. Set up an A record pointing to GitHub Pages IP addresses
2. Make sure the CNAME file contains your domain name
3. Configure the domain in your repository settings

## Troubleshooting

If deployments fail:
1. Check the GitHub Actions logs
2. Verify that all tests pass
3. Ensure all required secrets are configured
4. Check that your domain DNS settings are correct 