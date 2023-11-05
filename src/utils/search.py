import re
import logging
import tiktoken

from typing import Dict, Any, List, Union
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS  # facebook AI similarity search


# Create a logger object
logger = logging.getLogger(__name__)
# Configure the logger object
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s'))
logger.addHandler(handler)

TABLE_PATTERN = r"<<T(\d+)>>:"  # must include \d+ in the pattern - important for search.
FIGURE_PATTERN = r"<<F(\d+)>>:"


class DocumentVectorizer(object):
    """
       A class for vectorizing documents. It splits the input text into smaller chunks,
       tokenizes them using a specified tokenizer, and then converts the chunks into
       vectors using a specified embedding model.
    """
    CHUNK_KEY = 'Chunk Number'
    SUPPORTED_MODELS = ['gpt-3.5-turbo', 'gtp-4']
    METADATA_CORE = {
        CHUNK_KEY: 0
    }

    def __init__(
            self,
            text: Union[str, List[str]],
            metadata: Dict[str, Any] = None,
            size: int = 240,
            overlap: int = 24,
            separators=["\n\n", "\n", " ", ""],
            model: str = 'gpt-3.5-turbo',
    ):
        """
        Initializes the DocumentVectorizer object.

        :param text: The input text to be vectorized. Can be a single string or a list of strings.
        :param metadata: A dictionary containing metadata for the document.
        :param size: The size of the chunks after splitting the text.
        :param overlap: The number of tokens that adjacent chunks will overlap.
        :param separators: The separators used for splitting the text.
        :param model: The name of the tokenizer model to be used.
        """
        self._size = size
        self._overlap = overlap
        self._separators = separators

        self.text = text
        self.metadata = metadata
        self.tokenizer = model

    @property
    def text(self) -> List[str]:
        """Returns the list of text chunks."""
        return self._text

    @text.setter
    def text(self, text: Union[str, List[str]]):
        """
        Sets the text property. If text is a list, it joins the list items into a single string.
        Then it splits the text into chunks.

        :param text: The input text to be set and processed.
        """
        if isinstance(text, list):
            text = "\n".join(text)

        self._text = self.split(text)

    @property
    def metadata(self) -> List[Dict[str, Any]]:
        """Returns the list of metadata dictionaries for each text chunk."""
        return self._metadata

    @metadata.setter
    def metadata(self, metadata: Dict[str, Any]):
        """
        Sets the metadata property. It creates a list of metadata dictionaries for each text chunk.

        :param metadata: A dictionary containing metadata for the document.
        """
        if metadata is None:
            metadata = {}
        metadata = {**self.METADATA_CORE, **metadata}

        self._metadata = []
        for i in range(1, len(self._text) + 1):
            _metadata = metadata.copy()
            _metadata[self.CHUNK_KEY] = i
            self._metadata.append(_metadata)

    @property
    def tokenizer(self):
        """Returns the tokenizer."""
        return self._tokenizer

    @tokenizer.setter
    def tokenizer(self, model: str):
        """
        Sets the tokenizer property. It checks if the model is supported and sets the tokenizer.

        :param model: The name of the tokenizer model to be used.
        :raises ValueError: If the model is not supported.
        """
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"{model} not among supported models: {self.SUPPORTED_MODELS}"
            )
        enc_code = tiktoken.encoding_for_model(model).name
        self._tokenizer = tiktoken.get_encoding(enc_code)

    def tiktoken_len(self, text: str) -> int:
        """
        Determines the length of input text after tokenization.

        :param text: The text to be tokenized.
        :return: The number of tokens.
        """
        tokens = self.tokenizer.encode(
            text,
            disallowed_special=()
        )
        return len(tokens)

    def split(self, text: str) -> List[str]:
        """
        Splits the input text into chunks based on the specified chunk size, overlap, and separators.

        :param text: The text to be split.
        :return: A list of text chunks.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._size,
            chunk_overlap=self._overlap,
            length_function=self.tiktoken_len,
            separators=self._separators
        )
        chunks = text_splitter.split_text(text)
        logger.info(
            f'The input text of length {len(text)} was split into {len(chunks)} chunks.'
        )
        return chunks

    def vectorize(
            self,
            embedding_model: str = 'text-embedding-ada-002',
            extra_text: List[str] = None,
            extra_metadata: List[Any] = None
    ) -> FAISS:
        """
        Converts text chunks into vectors and stores them in a FAISS vector store.

        Allows for the insertion of extra text and metadata. Use case might be
        when you have text/tables/figures which you do not want to be split
        by the cls recursive splitter, and instead want to vectorize it as
        is.

        :param embedding_model: The name of the embedding model to be used.
        :param extra_text: Additional text chunks to be vectorized.
        :param extra_metadata: Additional metadata for the extra text chunks.
        :return: A FAISS vector store containing vectors of all text chunks.
        :raises ValueError: If the lengths of extra_text and extra_metadata do not match.
        """
        if extra_text is not None:
            text = self.text.copy()
            metadata = self.metadata.copy()

            text.extend(extra_text)

            if extra_metadata is not None:
                if len(extra_text) != len(extra_metadata):
                    raise ValueError(
                        f"Length of extra text: {len(extra_text)} does not match "
                        f"length of extra metadata: {len(extra_metadata)}"
                    )
                metadata.extend(extra_metadata)
            else:
                last_metadata = metadata[-1]
                start_chunk_num = last_metadata[self.CHUNK_KEY] + 1
                for i in range(start_chunk_num, start_chunk_num + len(extra_text)):
                    new_metadata = last_metadata.copy()
                    new_metadata[self.CHUNK_KEY] = i
                    metadata.append(new_metadata)
        else:
            text = self._text
            metadata = self._metadata

        embed = OpenAIEmbeddings(
            model=embedding_model,
        )
        vector_store = FAISS.from_texts(
            text, embedding=embed,
            metadatas=metadata,
        )
        return vector_store


class ContextRetrieval(object):
    """
        Class to handle the retrieval of context from a vector store, potentially
        replacing summary tables with actual raw tables from documents.
    """

    def __init__(
            self,
            vector_store: FAISS,
            tables: List[str] = None,
            is_summary: bool = False
    ):
        """
          Initialize the ContextRetrieval instance.

          Parameters:
              vector_store (FAISS): The vector store from which to retrieve similar documents.
              tables (List[str], optional): A list of raw tables corresponding to summarized tables in the documents.
              is_summary (bool, optional): Flag to determine whether to include summaries in the context
                                           alongside the raw tables.

          Raises:
              ValueError: If `tables` is not None and the `TABLE_PATTERN` does not match the expected format.
        """
        self._vector_store = vector_store
        self._tables = tables
        self._is_summary = is_summary

        self._table_pattern_compiled = re.compile(TABLE_PATTERN)

        if self._tables is not None and not self._table_pattern_compiled.search('<<T1>>'):
            raise ValueError(
                "Table pattern must contain an index placeholder ('<<T\\d+>>') to match summarized tables."
            )

    def _find_index(self, docs: List[Any]) -> int:
        """
        Find the index of the first document containing a table placeholder.

        Parameters:
            docs (List[Any]): A list of document objects to search through.

        Returns:
            int: The index of the first document containing a table placeholder,
                 or -1 if no such document is found.
        """
        for i, doc in enumerate(docs):
            if self._table_pattern_compiled.search(doc.page_content):
                return i
        return -1

    def _get_table_index_from_string(self, string: str) -> List[int]:
        """
        Extract table indices from a string containing table placeholders.

        Parameters:
            string (str): The string to search for table placeholders.

        Returns:
            List[int]: A list of table indices found within the string.
        """
        matches = self._table_pattern_compiled.findall(string)
        return [int(match) for match in matches]

    def search_vector_store(self, query: str, n: int, max_n: int = 30) -> List[Any]:
        """
        Search the vector store for documents similar to a query and return a context window of documents.

        Parameters:
            query (str): The query string to search for.
            n (int): The number of documents to return.
            max_n (int, optional): The maximum number of documents to search through to find tables.

        Returns:
            List[Any]: A list of document objects similar to the query, with at least one containing a table if
            available.
        """

        if self._tables is not None:
            docs = self._vector_store.similarity_search(query, max_n)
            table_index = self._find_index(docs)
            if (table_index < n) or (table_index == -1):
                # no need to process as table either in context
                # window or not similar enough to input query
                return docs[:n]
            else:
                # inject table into context.
                return docs[:n - 1] + [docs[table_index]]
        else:
            return self._vector_store.similarity_search(query, n)

    def process_content(
        self,
        chunk: str,
    ) -> str:
        """
        Process a chunk of text to replace table placeholders with actual raw tables, if applicable.

        Parameters:
            chunk (str): The text chunk to process.

        Returns:
            str: The processed text chunk with raw tables included if found and applicable.
        """
        table_indexes = self._get_table_index_from_string(chunk)
        if not table_indexes or self._tables is None:
            return chunk

        table_idx = table_indexes[0]
        if table_idx - 1 < len(self._tables):
            table = self._tables[table_idx - 1]  # Adjust index since list is 0-indexed
            match = self._table_pattern_compiled.search(chunk)
            if match and self._is_summary:
                chunk = f"{chunk[:match.start()]}RAW TABLE: {table} \n TABLE SUMMARY:{chunk[match.end():]}"
            elif match:
                chunk = f"{chunk[:match.start()]}RAW TABLE: {table}"
        return chunk

    def get_context(self, query: str, n: int = 4) -> str:
        """
        Retrieve a contextual summary based on a query, consisting of a specified number
        of document chunks ranked by relevance.

        Parameters:
            query (str): The search query to find relevant context.
            n (int, optional): The number of contextual chunks to retrieve.

        Returns:
            str: A formatted string of contextual chunks with their rank and metadata,
                 sorted from most to least relevant.
        """
        contexts = [
            f"Rank: {rank} | {self.process_content(doc.page_content)} | Metadata: {doc.metadata}"
            for rank, doc in enumerate(self.search_vector_store(query, n=n), start=1)
        ]
        message = "Contextual information sorted from most relevant to least relevant."

        full_context = '\n\n'.join(contexts)
        return full_context + f"\n\n{message}"
