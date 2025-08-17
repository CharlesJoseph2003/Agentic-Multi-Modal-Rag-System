from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

class TextProcessing:
    EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
    MAX_TOKENS = 300  # set to a small number for illustrative purposes
    default_tokenizer = HuggingFaceTokenizer(tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),max_tokens=MAX_TOKENS)  # optional, by default derived from `tokenizer` for HF case
    default_chunker = HybridChunker(tokenizer=default_tokenizer, merge_peers=True)  # optional, defaults to True
        
    def __init__(self, file_path, tokenizer=None, chunker=None):
        self.file_path = file_path
        self.tokenizer = tokenizer or self.default_tokenizer
        self.chunker  = chunker or self.default_chunker
    
    def pdf_to_text(self):
        source = self.file_path
        converter = DocumentConverter()
        result = converter.convert(source)
        return result.document.export_to_text()

    def pdf_to_chunks(self):
        doc = DocumentConverter().convert(self.file_path).document
        chunk_iter = self.chunker.chunk(dl_doc=doc)
        chunks = list(chunk_iter)
        for i, chunk in enumerate(chunks):
            print(f"=== {i} ===")
            txt_tokens = self.tokenizer.count_tokens(chunk.text)
            print(f"chunk.text ({txt_tokens} tokens):\n{chunk.text!r}")
            ser_txt = self.chunker.contextualize(chunk=chunk)
            ser_tokens = self.tokenizer.count_tokens(ser_txt)
            print(f"chunker.contextualize(chunk) ({ser_tokens} tokens):\n{ser_txt!r}")
            print()


test = TextProcessing(r"C:\Users\chuck\Downloads\Charles_Joseph_Resume_Updated (5).pdf")
print(test.pdf_to_chunks())

    # def pdf_to_chunks(self):
    #     doc = DocumentConverter().convert(source=self.file_path).document
    #     chunker = HybridChunker()
    #     chunk_iter = chunker.chunk(dl_doc=doc)
    #     for i, chunk in enumerate(chunk_iter):
    #         print(f"=== {i} ===")
    #         print(f"chunk.text:\n{f'{chunk.text[:300]}…'!r}")
    #         enriched_text = chunker.contextualize(chunk=chunk)
    #         print(f"chunker.contextualize(chunk):\n{f'{enriched_text[:300]}…'!r}")


# source = r"C:\Users\chuck\Downloads\Charles_Joseph_Resume_Updated (5).pdf"  # PDF path or URL
# converter = DocumentConverter()
# result = converter.convert(source)
# print(result.document.export_to_markdown())  # output: "### Docling Technical Report[...]"