from langchain_community.document_loaders.git import GitLoader

clone_url = "https://github.com/Swaraj07082/Amazon-Reviews-Sentiment-Analysis"

repo_name = clone_url.split("/")[-1]


github_loader = GitLoader(
    repo_path = f"./repos/{repo_name}",
    clone_url = clone_url,
    branch = "master"
    )

documents = github_loader.load()

print(documents)