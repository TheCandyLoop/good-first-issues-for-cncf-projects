import requests
import json
import os
import time

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

def get_live_cncf_repos():
    """Stage 1: Dynamically fetch all official CNCF projects from the Landscape API."""
    print("Fetching live CNCF project list from landscape.cncf.io...")
    try:
        response = requests.get("https://landscape.cncf.io/data.json")
        data = response.json()
    except Exception as e:
        print(f"Failed to fetch CNCF landscape data: {e}")
        return {}

    repos = {}
    for item in data:
        # Check if the item is an official CNCF project
        project_tier = item.get("project")
        if project_tier in ["graduated", "incubating", "sandbox"]:
            
            repo_url = item.get("repo_url", "")
            if repo_url and repo_url.startswith("https://github.com/"):
                # Clean the URL to get just "org/repo"
                repo_path = repo_url.replace("https://github.com/", "").strip("/")
                
                # The landscape data often includes the primary language
                github_data = item.get("github_data", {})
                lang = github_data.get("language", "Unknown")
                if not lang:
                    lang = "Unknown"

                repos[repo_path] = {
                    "tier": project_tier.capitalize(),
                    "lang": lang
                }
                
    print(f"Discovered {len(repos)} official CNCF GitHub repositories.")
    return repos


def fetch_issues(repos):
    """Stage 2: Hunt for beginner issues across all discovered repositories."""
    labels = ["good first issue", "good-first-issue", "help wanted"]
    all_issues = []

    for repo, meta in repos.items():
        print(f"Checking {repo} ({meta['tier']})...")
        
        for label in labels:
            url = f"https://api.github.com/repos/{repo}/issues"
            params = {"state": "open", "labels": label, "per_page": 30}
            
            response = requests.get(url, headers=HEADERS, params=params)
            
            if response.status_code == 200:
                issues = response.json()
                for issue in issues:
                    # Ignore PRs, we only want actual issues
                    if "pull_request" not in issue:
                        issue_data = {
                            "repo": repo,
                            "tier": meta["tier"],
                            "lang": meta["lang"],
                            "title": issue["title"],
                            "url": issue["html_url"],
                            "labels": [l["name"] for l in issue["labels"]],
                            "created_at": issue["created_at"]
                        }
                        if issue_data not in all_issues:
                            all_issues.append(issue_data)
            elif response.status_code == 403:
                print(f"Rate limited by GitHub! Pausing for 5 seconds...")
                time.sleep(5)
            else:
                print(f"Failed to fetch {repo}: {response.status_code}")
                
        # Pause for 1/2 a second between repos to respect GitHub's anti-abuse limits
        time.sleep(0.5)

    # Save the final dataset
    with open("data.json", "w") as f:
        json.dump(all_issues, f, indent=4)
    print(f"\n--- SUCCESS ---")
    print(f"Saved {len(all_issues)} total beginner issues to data.json")


if __name__ == "__main__":
    # Run Stage 1
    cncf_repos = get_live_cncf_repos()
    
    # Run Stage 2 (Only if Stage 1 found repositories)
    if cncf_repos:
        fetch_issues(cncf_repos)
    else:
        print("No repositories found. Check your internet connection or the CNCF Landscape API.")
