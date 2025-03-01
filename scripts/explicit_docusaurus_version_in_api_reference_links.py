import sys
from pathlib import Path

if __name__ == "__main__":
    version_to_update = sys.argv[1]
    folder_path = f"../docs/docusaurus/versioned_docs/version-{version_to_update}/reference/api"
    for file in Path(folder_path).rglob("*"):
        if file.is_file():
            try:
                with file.open("r", encoding="utf-8") as f:
                    file_content = f.read()

                replaced_content = file_content.replace(
                    "/docs/reference/api", f"/docs/{version_to_update}/reference/api"
                )

                with file.open("w", encoding="utf-8") as f:
                    f.write(replaced_content)

            except Exception as e:
                print(f"Error processing file {file}: {e}")
