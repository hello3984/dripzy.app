# GitHub Secrets Setup for CI/CD

This document explains how to set up the required secrets for the dripzy.app CI/CD pipeline.

## Required Secrets

The following secrets need to be added to your GitHub repository:

### 1. SSH_PRIVATE_KEY

This is used for secure deployments. You've already generated this key:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK7WMW2FOvuEpHu0ND8M82DZ+wyr4sVGpF0rhgruWRCz dripzy-deployment
```

Add the private key to GitHub secrets:

1. Go to your repository: https://github.com/hello3984/dripzy.app
2. Click on "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Name: `SSH_PRIVATE_KEY`
5. Value: The entire content of your SSH private key including BEGIN and END lines.

### 2. HEROKU_API_KEY

This is needed for deploying the backend to Heroku:

1. Log in to Heroku (https://dashboard.heroku.com)
2. Go to "Account settings"
3. Scroll down to "API Key" section and click "Reveal"
4. Copy the key
5. Add it as a GitHub secret with name `HEROKU_API_KEY`

### 3. HEROKU_EMAIL

Add the email address associated with your Heroku account:

1. Add it as a GitHub secret with name `HEROKU_EMAIL`

## Setting Up Secrets

To add secrets:

1. Go to your GitHub repository: https://github.com/hello3984/dripzy.app
2. Click on "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add each of the required secrets above

## Verifying Setup

After adding all required secrets:

1. Go to the "Actions" tab in your repository
2. Click "CI/CD Pipeline" in the left sidebar
3. Click "Run workflow" and select the main branch
4. Wait for the workflow to complete

## Troubleshooting

If you encounter deployment issues:

1. Check that all secrets are correctly added with the exact names shown above
2. Verify that your Heroku app "dripzy-backend" exists and you have the proper permissions
3. Check the GitHub Actions logs for detailed error messages 