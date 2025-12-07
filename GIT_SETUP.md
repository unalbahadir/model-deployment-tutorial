# Git Repository Setup Guide

## Current Issue

You're trying to push to `unalbahadir/model-deployment-tutorial.git` but authenticated as `bahadirunal7`, causing a permission denied error.

## Solutions

### Option 1: Use Personal Access Token (Recommended for unalbahadir repo)

**If you want to use your own GitHub repository:**

1. **Create a new repository on GitHub:**
   - Go to https://github.com/new
   - Repository name: `model-deployment-tutorial`
   - Make it public or private (your choice)
   - Don't initialize with README (we already have one)
   - Click "Create repository"

2. **Update the remote URL:**
```bash
# Remove current remote
git remote remove origin

# Add your repository
git remote add origin https://github.com/bahadirunal7/model-deployment-tutorial.git

# Verify
git remote -v

# Push to your repository
git push -u origin main
```

---

### Option 2: Use SSH Instead of HTTPS (Recommended if you have SSH keys)

**If you have SSH keys set up and want to use the existing repository:**

1. **Check if you have SSH keys:**
```bash
ls -la ~/.ssh/id_*.pub
```

2. **If you don't have SSH keys, generate them:**
```bash
ssh-keygen -t ed25519 -C "bahadir94@gmail.com"
# Press Enter to accept default location
# Optionally set a passphrase
```

3. **Add SSH key to GitHub:**
```bash
# Copy your public key
cat ~/.ssh/id_ed25519.pub
# Copy the output
```

   - Go to GitHub → Settings → SSH and GPG keys → New SSH key
   - Paste your public key
   - Save

4. **Change remote to SSH:**
```bash
git remote set-url origin git@github.com:unalbahadir/model-deployment-tutorial.git
```

5. **Test SSH connection:**
```bash
ssh -T git@github.com
# Should say: "Hi unalbahadir! You've successfully authenticated..."
```

6. **Try pushing:**
```bash
git push -u origin main
```

**Note**: This only works if:
- You have SSH keys configured with GitHub
- You have write access to the repository (or are a collaborator)

---

### Option 3: Get Added as Collaborator

**If you want to use the existing repository:**

1. Ask `unalbahadir` to add you as a collaborator:
   - Repository → Settings → Collaborators → Add people
   - Add `bahadirunal7` with write access

2. Then you can push:
```bash
git push -u origin main
```

---

### Option 4: Use Personal Access Token

**If you need to authenticate with HTTPS:**

1. **Create a Personal Access Token:**
   - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` scope

2. **Use token for authentication:**
```bash
# When prompted for password, use the token instead
git push -u origin main
# Username: bahadirunal7
# Password: <your-personal-access-token>
```

Or configure credential helper:
```bash
git config --global credential.helper store
git push -u origin main
# Enter token when prompted
```

---

## Recommended Solution

**For using the unalbahadir repository, I recommend:**

1. **Option 2 (SSH)** - If you have or can set up SSH keys (most secure)
2. **Option 1 (Personal Access Token)** - If you prefer HTTPS

**Quick fix with Personal Access Token:**
```bash
# 1. Create token on GitHub (Settings → Developer settings → Personal access tokens)
# 2. Use it to authenticate:
git push -u origin main
# Username: bahadirunal7
# Password: <paste-your-token-here>
```

**Or use SSH (if you have keys set up):**
```bash
git remote set-url origin git@github.com:unalbahadir/model-deployment-tutorial.git
git push -u origin main
```

---

## Verify Setup

After fixing, verify everything works:

```bash
# Check remote
git remote -v

# Check status
git status

# Test push (if you have changes)
git push origin main
```

---

## For CodePipeline

Once your repository is set up, you'll use it in CodePipeline:

- **Repository URL**: `https://github.com/unalbahadir/model-deployment-tutorial.git`
- **Branch**: `main`

**Important for CodePipeline:**
- The repository needs to be accessible to CodePipeline
- If it's private, you'll need to:
  1. Create a GitHub connection in CodePipeline
  2. Authorize AWS to access the repository
  3. Or use a Personal Access Token in CodePipeline connection settings

