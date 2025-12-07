# Push with Personal Access Token

## Quick Method: Embed Token in URL

Replace `YOUR_TOKEN` with your actual token:

```bash
git remote set-url origin https://unalbahadir:YOUR_TOKEN@github.com/unalbahadir/model-deployment-tutorial.git
git push -u origin main
```

**Note**: This stores the token in the URL. After pushing, you can remove it:
```bash
git remote set-url origin https://github.com/unalbahadir/model-deployment-tutorial.git
```

---

## Alternative: Use Credential Helper

1. **Store token using credential helper:**
```bash
git config --global credential.helper store
```

2. **Push (it will prompt):**
```bash
git push -u origin main
# Username: unalbahadir
# Password: <paste-your-token-here>
```

The token will be saved in `~/.git-credentials` for future use.

---

## Alternative: Use GIT_ASKPASS

Create a simple script to provide the token:

```bash
# Create token file (one-time)
echo '#!/bin/sh
echo "YOUR_TOKEN_HERE"' > ~/git-token-helper.sh
chmod +x ~/git-token-helper.sh

# Use it for this push
GIT_ASKPASS=~/git-token-helper.sh git push -u origin main
```

---

## Recommended: Use SSH Instead

If you have SSH keys set up for unalbahadir:

```bash
git remote set-url origin git@github.com:unalbahadir/model-deployment-tutorial.git
git push -u origin main
```

