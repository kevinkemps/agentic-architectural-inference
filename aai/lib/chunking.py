"""Chunking helpers for repository source files."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from langchain_text_splitters import RecursiveCharacterTextSplitter

FilePayload = dict[str, str]


class LangChainChunker:
    """Split source files into semantically friendlier batches for summarization."""

    def __init__(
        self,
        max_chunk_chars: int,
        chunk_overlap_chars: int = 500,
        separators: Sequence[str] | None = None,
    ) -> None:
        if max_chunk_chars <= 0:
            raise ValueError("max_chunk_chars must be positive")

        bounded_overlap = max(0, min(chunk_overlap_chars, max_chunk_chars - 1))
        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap_chars = bounded_overlap
        self.separators = list(separators) if separators is not None else None

    def chunk_files(self, files: list[FilePayload]) -> list[list[FilePayload]]:
        """Split large files, then pack the resulting segments into LLM-sized batches."""
        segments: list[FilePayload] = []
        for file_data in files:
            segments.extend(self._split_file(file_data))
        return self._pack_segments(segments)

    def _split_file(self, file_data: FilePayload) -> list[FilePayload]:
        path = file_data["path"]
        content = file_data["content"]
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chunk_chars,
            chunk_overlap=self.chunk_overlap_chars,
            separators=self.separators or self._default_separators(path),
        )
        documents = splitter.create_documents([content], metadatas=[{"path": path}])
        if len(documents) == 1:
            return [{"path": path, "content": documents[0].page_content}]

        total_parts = len(documents)
        return [
            {
                "path": f"{path} (chunk {index}/{total_parts})",
                "content": document.page_content,
            }
            for index, document in enumerate(documents, start=1)
        ]

    def _pack_segments(self, segments: list[FilePayload]) -> list[list[FilePayload]]:
        batches: list[list[FilePayload]] = []
        current_batch: list[FilePayload] = []
        current_size = 0

        for segment in segments:
            segment_size = len(segment["content"])
            if current_batch and current_size + segment_size > self.max_chunk_chars:
                batches.append(current_batch)
                current_batch = []
                current_size = 0
            current_batch.append(segment)
            current_size += segment_size

        if current_batch:
            batches.append(current_batch)
        return batches

    def _default_separators(self, path: str) -> list[str]:
        suffix = Path(path).suffix.lower()
        if suffix == ".py":
            return ["\nclass ", "\ndef ", "\n\n", "\n", " ", ""]
        if suffix in {".js", ".ts", ".tsx", ".jsx"}:
            return ["\nexport ", "\nfunction ", "\nclass ", "\n\n", "\n", " ", ""]
        if suffix in {".md", ".rst"}:
            return ["\n# ", "\n## ", "\n### ", "\n\n", "\n", " ", ""]
        return ["\n\n", "\n", " ", ""]
