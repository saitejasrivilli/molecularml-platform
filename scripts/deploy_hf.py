"""Deploy backend to Hugging Face Spaces."""
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ["HF_TOKEN"])
username = os.environ["HF_USERNAME"]
repo_id = f"{username}/molecularml-platform"

api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="docker", exist_ok=True)

import os
for root, dirs, files in os.walk("backend"):
    for f in files:
        local_path = os.path.join(root, f)
        path_in_repo = local_path.replace("backend/", "")
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=path_in_repo,
            repo_id=repo_id,
            repo_type="space",
        )

print(f"Deployed to https://huggingface.co/spaces/{repo_id}")
