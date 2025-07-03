from github import Github
import os
from datetime import datetime, timedelta

token = os.environ["GITHUB_TOKEN"]
org_name = os.environ["ORG_NAME"]
g = Github(token)
org = g.get_organization(org_name)

members = org.get_members()
stats = []

# 定义一个时间范围，例如只统计过去90天的贡献，以减少API调用和提高相关性
# end_date = datetime.now()
# start_date = end_date - timedelta(days=90) # 统计最近90天的贡献

print(f"Fetching stats for organization: {org_name}")

for member in members:
    # 注意：get_events() 只能获取到用户最近的公开活动，可能不完整
    # 对于更精确的组织范围贡献，可能需要遍历组织内的所有仓库，然后获取每个仓库的贡献者统计
    # 或者使用 GitHub GraphQL API 进行更聚合的查询

    commits_count = 0
    issues_count = 0
    prs_count = 0

    try:
        # 获取用户在组织内的所有公开仓库事件
        # 这依然受限于get_events()的限制，但可以作为初步实现
        for event in member.get_events():
            # 考虑事件的时间范围，如果需要
            # if event.created_at < start_date:
            #     break # 如果事件超出了时间范围，就停止
            
            if event.type == "PushEvent":
                # 统计实际的 commit 数量
                commits_count += sum(len(c['commits']) for c in event.payload.get('commits', []))
            elif event.type == "IssuesEvent":
                # 只统计用户创建的 issue
                if event.payload.get('action') == "opened":
                    issues_count += 1
            elif event.type == "PullRequestEvent":
                # 只统计用户创建的 PR
                if event.payload.get('action') == "opened":
                    prs_count += 1
    except Exception as e:
        print(f"Error fetching events for {member.login}: {e}")
    
    stats.append((member.login, commits_count, prs_count, issues_count))

stats.sort(key=lambda x: x[1], reverse=True)

readme_path = "profile/README.md" # 修正路径
with open(readme_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_marker = "| 👤 成员 | 📝 Commits | 🔧 PRs | 🗳️ Issues |\n"
start = -1
for i, line in enumerate(lines):
    if line == start_marker:
        start = i + 2 # 表格头两行（标题和分隔符）之后
        break

if start == -1:
    print("Error: Could not find the start marker for the contribution table.")
    exit(1)

end = start
# 找到表格结束的位置
while end < len(lines) and lines[end].strip().startswith("|"):
    end += 1

table = [
    f"| @{login} | {c} | {p} | {i} |\n"
    for login, c, p, i in stats
]

# 替换旧的表格内容
lines[start:end] = table

with open(readme_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"README.md updated for organization {org_name}.")
