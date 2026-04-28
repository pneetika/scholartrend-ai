from __future__ import annotations

from dataclasses import dataclass
from itertools import count


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    document_name: str
    text: str


class TextChunker:
    def __init__(self, chunk_size: int = 180, overlap: int = 30) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, document_id: str, document_name: str, text: str) -> list[Chunk]:
        words = text.split()
        if not words:
            return []

        chunks: list[Chunk] = []
        cursor = 0

        for index in count():
            slice_words = words[cursor : cursor + self.chunk_size]
            if not slice_words:
                break
            chunks.append(
                Chunk(
                    chunk_id=f"{document_id}-chunk-{index}",
                    document_id=document_id,
                    document_name=document_name,
                    text=" ".join(slice_words),
                )
            )
            if cursor + self.chunk_size >= len(words):
                break
            cursor += max(1, self.chunk_size - self.overlap)

        return chunks

