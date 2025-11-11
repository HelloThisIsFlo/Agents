import os

from chonkie import SemanticChunker

from chonkie import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()


def init_chunker() -> SemanticChunker:
    return SemanticChunker(
        mode="window",
        threshold="auto",
        chunk_size=512,
        similarity_window=1,
        min_sentences=1,
        min_characters_per_sentence=12,
        min_chunk_size=2,
        threshold_step=0.01,
        delim=[".", "!", "?", "\n"],
        return_type="chunks",
    )


RESEARCH_DIR = os.path.expanduser(
    "~/Work/Private/Dev/Finance/pf-simulations/DeepResearch/"
)


def load_text(filename) -> str:
    file_path = os.path.join(RESEARCH_DIR, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading file: {e}")


text = load_text("EfficientTransfer.md")


chunker = init_chunker()
chunks = chunker.chunk(text)
print("hello")
