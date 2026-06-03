import requests
import json
import os
from datetime import datetime

# You can add more CNCF projects here (e.g., kubernetes/kubernetes, prometheus/prometheus)
REPOS = [
    "argoproj/argo-cd",
    "kubernetes-sigs/kustomize",
    "helm/helm",
    "fluent/fluentd"
]

LABELS = ["good first issue", "good-first-issue", "help wanted"]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def fetch_issues():
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    all_issues = []

    for repo in REPOS:
        print(f"Fetching issues for {repo}...")
        for label in LABELS:
            url = f"https://api.github.com/repos/{repo}/issues"
            params = {"state": "open", "labels": label, "per_page": 30}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                issues = response.json()
                for issue in issues:
                    # Ignore pull requests, we only want issues
                    if "pull_request" not in issue:
                        issue_data = {
                            "repo": repo,
                            "title": issue["title"],
                            "url": issue["html_url"],
                            "labels": [l["name"] for l in issue["labels"]],
                            "created_at": issue["created_at"]
                        }
                        # Prevent duplicates if an issue has multiple matching labels
                        if issue_data not in all_issues:
                            all_issues.append(issue_data)
            else:
                print(f"Failed to fetch {repo}: {response.status_code}")

    # Save to data.json
    with open("data.json", "w") as f:
        json.dump(all_issues, f, indent=4)
    print(f"Successfully saved {len(all_issues)} issues to data.json")

if __name__ == "__main__":
    fetch_issues()
