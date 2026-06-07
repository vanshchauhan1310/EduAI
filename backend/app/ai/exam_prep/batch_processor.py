from pathlib import Path
from datetime import datetime

from app.ai.exam_prep.pdf_parser import (
    extract_text_from_pdf,
    scan_pdf_directory
)

from app.ai.exam_prep.knowledge_extractor import (
    extract_chapter_knowledge,
    KNOWLEDGE_BASE_DIR
)


PDF_DIRECTORY = Path("data/chapters")


def chapter_already_processed(
        chapter_name: str
) -> bool:

    chapter_id = (
        chapter_name
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    output_file = (
        KNOWLEDGE_BASE_DIR /
        f"{chapter_id}.json"
    )

    return output_file.exists()


def get_subject_from_filename(
        filename: str
) -> str:
    """
    Optional subject mapping.

    Example:
    jesc101.pdf -> Chemistry

    Customize later if needed.
    """

    filename = filename.lower()

    if filename.startswith("jesc"):
        return "Chemistry"

    if filename.startswith("jesp"):
        return "Physics"

    if filename.startswith("jesm"):
        return "Mathematics"

    if filename.startswith("jess"):
        return "Biology"

    return "General"


def generate_chapter_name(
        pdf_path: Path
) -> str:
    """
    Temporary chapter naming.

    Later you can extract actual
    chapter titles from PDF content.
    """

    return pdf_path.stem


def process_single_pdf(
        pdf_path: Path
):

    print(
        f"\n{'=' * 70}"
    )

    print(
        f"[Batch] Processing "
        f"{pdf_path.name}"
    )

    chapter_name = (
        generate_chapter_name(
            pdf_path
        )
    )

    subject = (
        get_subject_from_filename(
            pdf_path.name
        )
    )

    if chapter_already_processed(
            chapter_name
    ):

        print(
            f"[Batch] Skipped "
            f"(already processed)"
        )

        return

    text = extract_text_from_pdf(
        str(pdf_path)
    )

    print(
        f"[Batch] Extracted "
        f"{len(text)} characters"
    )

    extract_chapter_knowledge(
        chapter_text=text,
        chapter_name=chapter_name,
        subject=subject,
        source_pdf=pdf_path.name
    )

    print(
        f"[Batch] Finished "
        f"{chapter_name}"
    )


def process_all_pdfs():

    start_time = datetime.now()

    print(
        "\n========================================"
    )

    print(
        "NCERT KNOWLEDGE BASE GENERATION"
    )

    print(
        "========================================\n"
    )

    pdf_files = scan_pdf_directory(
        str(PDF_DIRECTORY)
    )

    print(
        f"[Batch] Found "
        f"{len(pdf_files)} PDF(s)"
    )

    success_count = 0

    failed_count = 0

    for pdf_file in pdf_files:

        try:

            process_single_pdf(
                pdf_file
            )

            success_count += 1

        except Exception as e:

            failed_count += 1

            print(
                f"\n[Batch] FAILED "
                f"{pdf_file.name}"
            )

            print(
                f"Reason: {e}"
            )

    end_time = datetime.now()

    print(
        "\n========================================"
    )

    print(
        "PROCESSING COMPLETE"
    )

    print(
        "========================================"
    )

    print(
        f"Successful: {success_count}"
    )

    print(
        f"Failed: {failed_count}"
    )

    print(
        f"Duration: "
        f"{end_time - start_time}"
    )

    print(
        "========================================\n"
    )


if __name__ == "__main__":

    process_all_pdfs()