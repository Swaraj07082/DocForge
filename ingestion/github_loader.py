from langchain_community.document_loaders.git import GitLoader
from langchain_core.documents import Document

def load_repo(clone_url : str , branch : str = "master") -> list[Document]:
    # clone_url = "https://github.com/Swaraj07082/Amazon-Reviews-Sentiment-Analysis"

    repo_name = clone_url.split("/")[-1]
    
    github_loader = GitLoader(
    repo_path = f"./repos/{repo_name}",
    clone_url = clone_url,
    branch = branch
    )
    
    files = github_loader.load()
    
    return files

if __name__ == "__main__":
    files = load_repo("https://github.com/Swaraj07082/Amazon-Reviews-Sentiment-Analysis" , "master")
    print(files)