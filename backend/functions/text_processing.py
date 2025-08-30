from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

class TextProcessing:
    EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
    MAX_TOKENS = 300  # Further reduced to 300 to ensure we stay well under 512 limit
    default_tokenizer = HuggingFaceTokenizer(tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),max_tokens=MAX_TOKENS) 
    default_chunker = HybridChunker(tokenizer=default_tokenizer, merge_peers=False)  # Changed to False to prevent merging  
    converter = DocumentConverter()
        
    def __init__(self, file_path, tokenizer=None, chunker=None):
        self.file_path = file_path
        self.tokenizer = tokenizer or self.default_tokenizer
        self.chunker  = chunker or self.default_chunker
    
    def pdf_to_text(self):
        source = self.file_path
        converter = self.converter
        result = converter.convert(source)
        return result.document.export_to_text()

    def pdf_to_chunks(self):
        doc = self.converter.convert(self.file_path).document
        chunk_iter = self.chunker.chunk(dl_doc=doc)
        chunks = list(chunk_iter)
        return [c.text for c in chunks]
