# Git Authentication as unalbahadir

To push to the `unalbahadir/model-deployment-tutorial` repository, you need to authenticate as `unalbahadir`.

## Option 1: Use unalbahadir's Personal Access Token (Recommended)

1. **Log in to GitHub as `unalbahadir`**
   - Go to https://github.com/login
   - Sign in with unalbahadir account

2. **Create a Personal Access Token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Name: `Local-Development-Access`
   - Expiration: 90 days (or your preference)
   - Scopes: Check `repo` (full control)
   - Click "Generate token"
   - **Copy the token immediately**

3. **Configure git credentials:**
```bash
# Set git user for this repository
git config --local user.name "unalbahadir"
git config --local user.email "your-email@example.com"  # Use unalbahadir's email

# Push using the token
git push -u origin main
# Username: unalbahadir
# Password: <paste-unalbahadir's-personal-access-token>
```

4. **Store credentials (optional):**
```bash
git config --global credential.helper store
git push -u origin main
# Enter token once, it will be saved for future pushes
```

---

## Option 2: Use SSH Key for unalbahadir

1. **Generate SSH key (if not exists):**
```bash
ssh-keygen -t ed25519 -C "unalbahadir-email@example.com"
# Save as: ~/.ssh/id_ed25519_unalbahadir
```

2. **Add SSH key to unalbahadir's GitHub account:**
   - Log in as unalbahadir
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste the public key: `cat ~/.ssh/id_ed25519_unalbahadir.pub`
   - Save

3. **Configure SSH for this repository:**
```bash
# Add SSH config
cat >> ~/.ssh/config << EOF
Host github.com-unalbahadir
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_unalbahadir
EOF

# Change remote to use SSH
git remote set-url origin git@github.com-unalbahadir:unalbahadir/model-deployment-tutorial.git

# Test connection
ssh -T git@github.com-unalbahadir

# Push
git push -u origin main
```

---

## Option 3: Use GitHub CLI (gh)

If you have GitHub CLI installed:

```bash
# Authenticate as unalbahadir
gh auth login
# Follow prompts, select unalbahadir account

# Then push normally
git push -u origin main
```

---

## Current Configuration

Your git is now configured for this repository:
- **User**: `unalbahadir`
- **Email**: Set to unalbahadir's email (update if needed)

To push, you still need to authenticate with unalbahadir's credentials (token or SSH key).

---

## Quick Test

After setting up authentication:

```bash
# Verify git config
git config --local user.name
git config --local user.email

# Try pushing
git push -u origin main
```

---

## For CodePipeline

When setting up CodePipeline, you'll need:
- A GitHub connection authenticated as `unalbahadir`
- Or use unalbahadir's Personal Access Token in the connection

The repository URL remains: `https://github.com/unalbahadir/model-deployment-tutorial.git`

