from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text_into_chunks(
    text: str,
    product_code: str,
    source: str,
) -> list[Document]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    texts = splitter.split_text(text)

    documents = []

    for index, chunk_text in enumerate(texts):
        document = Document(
            page_content=chunk_text,
            metadata={
                "product_code": product_code,
                "source": source,
                "chunk_index": index,
                "document_type": "insurance_policy",
            },
        )

        documents.append(document)

    return documents