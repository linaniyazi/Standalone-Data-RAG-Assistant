import os

def chunk_text(text, chunk_size=300, overlap=50):
    """
    Split text into overlapping word-based chunks.
    chunk_size: approximate number of words per chunk.
    overlap: number of words repeated between consecutive chunks.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start += chunk_size - overlap

    return chunks


def build_document_chunks(folder_path, doc_type_map):
    """
    Read all .txt files in folder_path, chunk them, and attach metadata.
    """
    all_chunks = []

    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(folder_path, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        doc_type = doc_type_map.get(filename, "unknown")

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk_id": f"{filename}_chunk{i}",
                "source_document": filename,
                "document_type": doc_type,
                "chunk_index": i,
                "text": chunk
            })

    return all_chunks