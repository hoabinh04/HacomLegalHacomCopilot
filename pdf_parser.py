import re
from pathlib import Path
from typing import List, Dict, Any

# Nhập an toàn các thư viện xử lý PDF để không báo lỗi linter trong IDE
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


class LegalPDFParser:
    """
    Parser chuyên dụng bóc tách & làm sạch Văn bản Quy phạm Pháp luật Việt Nam.
    Tự động hỗ trợ đa bộ giải mã (PyMuPDF, pdfplumber, pypdf) để bóc tách mọi loại văn bản PDF (ký số, scan text, digital).
    """
    
    def __init__(self):
        pass

    def extract_document_dates(self, filename: str, text: str) -> tuple[str, str]:
        """Tự động trích xuất Ngày ban hành và Ngày có hiệu lực từ tên file hoặc nội dung văn bản."""
        issue_date = "01/08/2024"
        effective_date = "01/08/2024"

        # 1. Trích xuất từ tiền tố tên file dạng YYMMDD (VD: 240715_88-2024-ND-CP... -> 15/07/2024)
        m_file = re.match(r'^(\d{2})(\d{2})(\d{2})_', filename)
        if m_file:
            yy, mm, dd = m_file.groups()
            year = f"20{yy}" if int(yy) < 50 else f"19{yy}"
            issue_date = f"{dd}/{mm}/{year}"
            effective_date = issue_date

        # 2. Trích xuất từ nội dung đầu văn bản (VD: Hà Nội, ngày 18 tháng 01 năm 2024)
        m_text_issue = re.search(r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})', text[:2000], re.IGNORECASE)
        if m_text_issue:
            d, m, y = m_text_issue.groups()
            issue_date = f"{int(d):02d}/{int(m):02d}/{y}"
            if not m_file:
                effective_date = issue_date

        # 3. Trích xuất ngày có hiệu lực từ phần Điều khoản thi hành ở cuối văn bản
        m_text_eff = re.search(r'có\s+hiệu\s+lực\s+(?:thi\s+hành\s+)?(?:từ\s+)?ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})', text[-3000:], re.IGNORECASE)
        if m_text_eff:
            d, m, y = m_text_eff.groups()
            effective_date = f"{int(d):02d}/{int(m):02d}/{y}"

        return issue_date, effective_date

    def clean_legal_text(self, text: str) -> str:
        """Làm sạch văn bản pháp luật, xóa số trang rác và nối dòng đứt đoạn."""
        if not text:
            return ""
        
        # 1. Xóa số trang nằm riêng 1 dòng (VD: \n10\n, \n19\n)
        text = re.sub(r'(?m)^\s*\d+\s*$', '', text)
        
        # 2. Xóa các dòng rác Header / Footer (VD: Trang 10, CÔNG BÁO...)
        text = re.sub(r'(?m)^\s*Trang\s+\d+.*$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?m)^\s*CÔNG BÁO.*$', '', text, flags=re.IGNORECASE)

        # 3. Nối các dòng bị ngắt câu giữa chừng do sang trang PDF
        raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_lines = []
        
        for line in raw_lines:
            if cleaned_lines and not re.match(r'^(Điều\s+\d+|\d+\.|[a-zđ]\)|[\*\-\•]|Chương\s+[IVXLCDM]+)', line, re.IGNORECASE):
                prev = cleaned_lines[-1]
                if not prev.endswith(('.', ':', ';', '?', '!', '"', '”')):
                    cleaned_lines[-1] = f"{prev} {line}"
                    continue
            cleaned_lines.append(line)
            
        return "\n\n".join(cleaned_lines)

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Trích xuất toàn bộ văn bản từ PDF sử dụng đa bộ parser."""
        extracted_text = ""
        
        # 1. Thử PyMuPDF (fitz)
        if fitz is not None:
            try:
                doc = fitz.open(str(pdf_path))
                full_text = []
                for page in doc:
                    t = page.get_text()
                    if t:
                        full_text.append(t)
                extracted_text = "\n".join(full_text)
                if len(extracted_text.strip()) > 100:
                    return extracted_text
            except Exception:
                pass

        # 2. Fallback pdfplumber
        if pdfplumber is not None:
            try:
                with pdfplumber.open(str(pdf_path)) as pdf:
                    pages_text = [p.extract_text() for p in pdf.pages if p.extract_text()]
                    extracted_text = "\n".join(pages_text)
                    if len(extracted_text.strip()) > 100:
                        return extracted_text
            except Exception:
                pass

        # 3. Fallback pypdf
        if PdfReader is not None:
            try:
                reader = PdfReader(str(pdf_path))
                pages_text = [page.extract_text() for page in reader.pages if page.extract_text()]
                extracted_text = "\n".join(pages_text)
                if len(extracted_text.strip()) > 50:
                    return extracted_text
            except Exception:
                pass

        return extracted_text

    def parse_legal_chunks(self, pdf_path: Path) -> List[Dict[str, Any]]:
        filename = pdf_path.name
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text or len(text.strip()) < 30:
            return []
        
        # Identify Document Number & Title from header
        doc_num_match = re.search(r'(Số:\s*[\d]+(?:/[\d\w-]+)?)', text[:1500], re.IGNORECASE)
        doc_number = doc_num_match.group(1).replace("Số:", "").strip() if doc_num_match else filename.split('_')[1] if '_' in filename else filename
        
        # Regex split by "Điều X." hoặc "Điều X "
        article_pattern = re.compile(r'(^|\n)(Điều\s+\d+[\.\:\s][^\n]+)', re.MULTILINE)
        splits = article_pattern.split(text)
        
        chunks = []
        doc_title = filename.replace('.pdf', '')
        issue_date, effective_date = self.extract_document_dates(filename, text)
        
        if len(splits) <= 1:
            # Fallback chunking theo từng đoạn văn bản nếu không tìm thấy "Điều X"
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
            if not paragraphs:
                paragraphs = [line.strip() for line in text.splitlines() if len(line.strip()) > 30]
            
            for idx, p in enumerate(paragraphs, 1):
                chunk_text = self.clean_legal_text(p)
                chunks.append({
                    "doc_name": doc_title,
                    "doc_number": doc_number,
                    "article": f"Phần {idx}",
                    "article_title": f"Nội dung quy định mục {idx}",
                    "content": chunk_text,
                    "source_file": filename
                })
            return chunks

        # Parse articles
        for i in range(1, len(splits), 3):
            article_header = splits[i+1].strip()
            article_body = splits[i+2].strip() if (i+2) < len(splits) else ""
            
            # Extract Article Number and Title
            art_match = re.match(r'Điều\s+(\d+)[\.\:\s]*(.*)', article_header)
            art_num = f"Điều {art_match.group(1)}" if art_match else article_header
            art_title = art_match.group(2).strip() if (art_match and art_match.group(2)) else "Nội dung quy định"
            
            full_chunk_raw = f"{article_header}\n{article_body}"
            full_chunk_cleaned = self.clean_legal_text(full_chunk_raw)
            
            chunks.append({
                "doc_name": doc_title,
                "doc_number": doc_number,
                "article": art_num,
                "article_title": art_title,
                "content": full_chunk_cleaned,
                "source_file": filename,
                "issue_date": issue_date,
                "effective_date": effective_date
            })
            
        return chunks


if __name__ == "__main__":
    parser = LegalPDFParser()
    sample_pdf = Path(r"C:\KHMT\HacomHoldings\HacomLegalCopilot\sample_test_laws\240730_103-2024-ND-CP_Tien_su_dung_dat_va_tien_thue_dat.pdf")
    if sample_pdf.exists():
        res = parser.parse_legal_chunks(sample_pdf)
        print(f"Parsed {len(res)} chunks from test PDF.")
