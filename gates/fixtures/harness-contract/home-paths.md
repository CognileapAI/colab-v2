# harness-contract K3 fixture — each of lines 3-6 leaks one user home path
allowed: /home/user/ is the git-guard example; /home/<u>/ and ~/ are placeholders
/home/alice/workspace/repo
/Users/alice/workspace/repo
C:\Users\alice\workspace\repo
/mnt/c/Users/alice/workspace/repo
