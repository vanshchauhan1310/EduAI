import re
import fitz


class PYQParser:

    @staticmethod
    def extract_text(pdf_path: str) -> str:

        doc = fitz.open(pdf_path)

        text = []

        for page in doc:
            page_text = page.get_text()

            if page_text:
                text.append(page_text)

        doc.close()

        return "\n".join(text)

    @staticmethod
    def clean_question_text(question_text: str) -> str:

        question_text = " ".join(
            question_text.split()
        )

        # Remove marks
        question_text = re.sub(
            r"\[\d+\s*Marks?\]",
            "",
            question_text,
            flags=re.IGNORECASE
        )

        # Remove source information
        question_text = re.sub(
            r"Source:\s*CBSE\s*\d{4}",
            "",
            question_text,
            flags=re.IGNORECASE
        )

        # Remove standalone tags like 1M, 2M, 3M
        question_text = re.sub(
            r"\b\d+M\b",
            "",
            question_text,
            flags=re.IGNORECASE
        )

        # Remove extra spaces
        question_text = re.sub(
            r"\s+",
            " ",
            question_text
        )

        return question_text.strip()

    @classmethod
    def extract_questions(cls, text: str):

        questions = []

        pattern = r"(Q\d+)\.\s*(.*?)(?=(?:Q\d+\.)|$)"

        matches = re.findall(
            pattern,
            text,
            flags=re.DOTALL | re.IGNORECASE
        )

        for question_number, question_text in matches:

            cleaned_text = cls.clean_question_text(
                question_text
            )

            questions.append(
                {
                    "question_number":
                    question_number.upper(),

                    "question_text":
                    cleaned_text
                }
            )

        return questions