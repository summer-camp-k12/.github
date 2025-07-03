from github import Github
import os

token = os.environ["GITHUB_TOKEN"]
org_name = os.environ["ORG_NAME"]
g = Github(token)
org = g.get_organization(org_name)

members = org.get_members()
stats = []

print(f"Fetching stats for organization: {org_name}")

for member in members:
    events = member.get_events()
    commits = issues = prs = 0
    try:
        for event in events:
            if event.type == "PushEvent":
                commits += sum(len(c['commits']) for c in event.payload.get('commits', []))
            elif event.type == "IssuesEvent":
                issues += 1
            elif event.type == "PullRequestEvent":
                prs += 1
    except Exception as e:
        print(f"Error fetching events for {member.login}: {e}")
    stats.append((member.login, commits, prs, issues))

stats.sort(key=lambda x: x[1], reverse=True)

with open("README.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

start = lines.index("| 👤 成员 | 📝 Commits | 🔧 PRs | 🗳️ Issues |\n") + 2
end = start
while end < len(lines) and lines[end].startswith("|"):
    end += 1

table = [
    f"| @{login} | {c} | {p} | {i} |\n"
    for login, c, p, i in stats
]

lines[start:end] = table

with open("README.md", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("README.md updated.")
