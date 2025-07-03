import os
from github import Github
from datetime import datetime, timedelta

# 从环境变量中获取 GitHub Token (这将是您在 Actions 中配置的 ORG_PAT)
token = os.environ["GITHUB_TOKEN"]
org_name = os.environ["ORG_NAME"]

# 使用 Token 初始化 PyGithub 客户端
# 确保此 Token 具有访问私有仓库的 'repo' 权限
g = Github(token)
org = g.get_organization(org_name)

# 用于存储每个成员的贡献数据，以 login 为键
member_contributions = {}

print(f"Fetching members for organization: {org_name}")
# 获取组织所有成员的 login，并初始化他们的贡献数据
members_in_org = {member.login for member in org.get_members()}
for member_login in members_in_org:
    member_contributions[member_login] = {'commits': 0, 'prs': 0, 'issues': 0}

print(f"Starting to process repositories for comprehensive stats...")

# 定义统计的时间范围（可选，用于减少 API 调用和聚焦近期活动）
# 例如，只统计最近 365 天的贡献
# end_date = datetime.utcnow()
# start_date = end_date - timedelta(days=365)

# 遍历组织下的所有仓库
# 如果 PAT 具有 'repo' 权限，org.get_repos() 将返回公共和私有仓库
for repo in org.get_repos():
    # 可以根据需要跳过某些仓库，例如归档的、Fork 的、或不相关的
    if repo.archived or repo.fork:
        print(f"  Skipping archived or forked repo: {repo.name}")
        continue

    print(f"  Processing repo: {repo.name}")

    try:
        # --- 获取 Commits ---
        # 遍历仓库的提交。可以添加 since 参数来限制时间范围。
        # 例如: for commit in repo.get_commits(since=start_date):
        for commit in repo.get_commits():
            if commit.author and commit.author.login in members_in_org:
                member_contributions[commit.author.login]['commits'] += 1
            # 注意: 大量提交的仓库可能会导致速率限制，考虑时间过滤

        # --- 获取 Issues 和 Pull Requests ---
        # 遍历仓库的所有 issues (Pull Request 也是一种特殊的 Issue)
        # 可以添加 since 参数来限制时间范围。
        # 例如: for issue in repo.get_issues(state='all', since=start_date):
        for issue in repo.get_issues(state='all'): # 'all' 状态包括 open 和 closed
            if issue.user and issue.user.login in members_in_org:
                if issue.pull_request: # 如果 issue.pull_request 不为 None，则这是一个 Pull Request
                    member_contributions[issue.user.login]['prs'] += 1
                else: # 否则，这是一个普通的 Issue
                    member_contributions[issue.user.login]['issues'] += 1

    except Exception as e:
        # 捕获 API 错误，例如 403 Forbidden（权限不足），404 Not Found（仓库不存在），或速率限制
        print(f"  Error processing repo {repo.name}: {e}")
        if "API rate limit exceeded" in str(e):
            print("    API rate limit exceeded. Stopping further API calls for this run.")
            # 在达到速率限制时，可以选择退出脚本，让 Action 失败以提示问题
            # 或者实现一个等待机制（但会延长 Action 运行时间）
            break # 退出仓库遍历循环

# 将字典转换为列表，以便排序和表格格式化
stats = []
for login, data in member_contributions.items():
    stats.append((login, data['commits'], data['prs'], data['issues']))

# 按 Commit 数量降序排序
stats.sort(key=lambda x: x[1], reverse=True)

# --- 更新 README.md 文件 ---
# README.md 位于仓库根目录下的 profile 文件夹中
readme_path = "profile/README.md"
try:
    with open(readme_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 查找贡献排名表格的开始标记
    start_marker = "| 👤 成员 | 📝 Commits | 🔧 PRs | 🗳️ Issues |\n"
    start_index = -1
    for i, line in enumerate(lines):
        if line == start_marker:
            start_index = i + 2 # 表格头两行（标题和分隔符）之后
            break

    if start_index == -1:
        print("Error: Could not find the start marker for the contribution table in README.md.")
        exit(1) # 退出脚本，让 Action 失败

    # 查找表格结束的位置
    end_index = start_index
    while end_index < len(lines) and lines[end_index].strip().startswith("|"):
        end_index += 1

    # 生成新的表格内容
    table_rows = [
        f"| @{login} | {c} | {p} | {i} |\n"
        for login, c, p, i in stats
    ]

    # 替换旧的表格内容
    lines[start_index:end_index] = table_rows

    # 将更新后的内容写回 README.md
    with open(readme_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"README.md updated successfully for organization {org_name}.")

except FileNotFoundError:
    print(f"Error: README.md file not found at {readme_path}. Please ensure the path is correct.")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred while updating README.md: {e}")
    exit(1)

