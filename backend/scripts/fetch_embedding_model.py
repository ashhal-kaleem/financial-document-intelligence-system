"""Download public, revision-pinned MiniLM weights at build time, with integrity checks.
No API key or user document is used. Runtime remains network-free for embeddings.
"""
import os
from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.infrastructure.embedding_assets import ARTIFACTS, MODEL_DIR, MODEL_ID, MODEL_REVISION, verify_artifact


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name, (remote, size, digest) in ARTIFACTS.items():
        target = MODEL_DIR / name
        try:
            verify_artifact(target, size, digest)
            print(f"Verified cached embedding asset: {name}")
            continue
        except RuntimeError:
            pass
        temp = target.with_suffix(target.suffix + ".part")
        try:
            url = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/{remote}"
            request = urllib.request.Request(url, headers={"User-Agent": "FDIS-model-build/1"})
            with urllib.request.urlopen(request, timeout=60) as response, temp.open("wb") as output:
                downloaded = 0
                while chunk := response.read(1024 * 1024):
                    downloaded += len(chunk)
                    if downloaded > size:
                        raise RuntimeError("Embedding artifact exceeded pinned size")
                    output.write(chunk)
            verify_artifact(temp, size, digest)
            os.replace(temp, target)
            print(f"Verified downloaded embedding asset: {name} ({size} bytes)")
        finally:
            temp.unlink(missing_ok=True)
    print(f"Pinned model ready: {MODEL_ID}@{MODEL_REVISION}")


if __name__ == "__main__":
    main()
