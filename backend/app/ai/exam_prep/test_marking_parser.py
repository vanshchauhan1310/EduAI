from pathlib import Path

from app.ai.exam_prep.marking_scheme_parser import (
    MarkingSchemeParser
)

pdf_file = next(
    Path(
        "data/marking_schemes/jesc101"
    ).glob("*.pdf")
)

parser = MarkingSchemeParser()

result = parser.parse_pdf(
    str(pdf_file)
)

print(result)
print("Total:", len(result))