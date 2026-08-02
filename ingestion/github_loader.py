from pathlib import Path

from langchain_community.document_loaders.git import GitLoader
from langchain_core.documents import Document


def load_repo(
    clone_url: str,
    branch: str = "master",
    *,
    repos_root: str | Path = "./repos",
) -> list[Document]:
    repo_name = clone_url.split("/")[-1]
    repo_path = Path(repos_root) / repo_name
    repo_path.parent.mkdir(parents=True, exist_ok=True)

    github_loader = GitLoader(
        repo_path=str(repo_path),
        clone_url=clone_url,
        branch=branch,
    )

    return github_loader.load()

if __name__ == "__main__":
    files = load_repo("https://github.com/Swaraj07082/Amazon-Reviews-Sentiment-Analysis" , "master")
    print(files)