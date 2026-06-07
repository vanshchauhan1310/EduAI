import fitz  # PyMuPDF
import re
from pathlib import Path


def clean_text(text: str) -> str:
    """
    Clean extracted PDF text.
    """

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = text.replace("\x00", "")

    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF.

    Args:
        pdf_path: Full PDF path

    Returns:
        Cleaned text string
    """

    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    try:
        doc = fitz.open(pdf_file)

        if len(doc) == 0:
            raise ValueError(
                f"PDF contains no pages: {pdf_path}"
            )

        pages = []

        for page_num in range(len(doc)):

            page = doc.load_page(page_num)

            page_text = page.get_text()

            if page_text.strip():

                pages.append(
                    f"\n--- PAGE {page_num + 1} ---\n"
                    f"{page_text}"
                )

        doc.close()

        full_text = "\n".join(pages)

        full_text = clean_text(full_text)

        if len(full_text) < 100:
            raise ValueError(
                f"Very little text extracted from "
                f"{pdf_path}. PDF may be scanned."
            )

        return full_text

    except Exception as e:
        raise RuntimeError(
            f"Failed to extract text from "
            f"{pdf_path}: {e}"
        )


def get_pdf_info(pdf_path: str) -> dict:
    """
    Get PDF metadata.
    """

    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    doc = fitz.open(pdf_file)

    info = {
        "filename": pdf_file.name,
        "page_count": len(doc),
        "file_size_kb": round(
            pdf_file.stat().st_size / 1024,
            2
        ),
        "metadata": doc.metadata
    }

    doc.close()

    return info


def get_chapter_name_from_pdf(pdf_path: str) -> str:
    """
    Generate chapter name from PDF filename.

    Example:
        jesc101.pdf
        ->
        jesc101
    """

    return Path(pdf_path).stem


def scan_pdf_directory(directory_path: str) -> list[Path]:
    """
    Returns all PDFs in directory.
    """

    directory = Path(directory_path)

    if not directory.exists():
        raise FileNotFoundError(
            f"Directory not found: {directory_path}"
        )

    pdfs = sorted(
        directory.rglob("*.pdf")
    )

    return pdfs


def extract_all_pdfs(directory_path: str) -> dict:
    """
    Extract text from all PDFs.

    Returns:
        {
            "chapter_name": "text..."
        }
    """

    results = {}

    pdf_files = scan_pdf_directory(
        directory_path
    )

    print(
        f"[PDF Parser] Found "
        f"{len(pdf_files)} PDFs"
    )

    for pdf_file in pdf_files:

        try:

            chapter_name = (
                get_chapter_name_from_pdf(
                    str(pdf_file)
                )
            )

            print(
                f"[PDF Parser] Processing "
                f"{pdf_file.name}"
            )

            text = extract_text_from_pdf(
                str(pdf_file)
            )

            results[chapter_name] = text

            print(
                f"[PDF Parser] Success "
                f"({len(text)} chars)"
            )

        except Exception as e:

            print(
                f"[PDF Parser] Failed "
                f"{pdf_file.name}: {e}"
            )

    return results


if __name__ == "__main__":

    PDF_DIRECTORY = (
        r"C:\Users\Intern01600"
        r"\PycharmProjects\EduAI"
        r"\backend\data\chapters"
    )

    pdf_files = scan_pdf_directory(
        PDF_DIRECTORY
    )

    print(
        f"\nFound {len(pdf_files)} PDFs\n"
    )

    for pdf in pdf_files:

        try:

            info = get_pdf_info(str(pdf))

            text = extract_text_from_pdf(
                str(pdf)
            )

            print(
                f"\n{'=' * 50}"
            )

            print(
                f"File: {pdf.name}"
            )

            print(
                f"Pages: "
                f"{info['page_count']}"
            )

            print(
                f"Characters: "
                f"{len(text)}"
            )

            print(
                text[:500]
            )

        except Exception as e:

            print(
                f"Failed: {pdf.name}"
            )

            print(e)