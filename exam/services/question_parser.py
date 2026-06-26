"""
services/question_parser.py
─────────────────────────────────────────────────────────────────────────────
AI-Ready Question Parser – Modular Service Layer
─────────────────────────────────────────────────────────────────────────────
Currently supports:
  • Structured manual import (JSON / CSV)
  • PDF text extraction placeholder (requires pdfplumber – optional)
  • DOCX text extraction placeholder (requires python-docx)

Future AI Integration Points are marked with # AI_HOOK comments.
"""

import json
import csv
import io
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ParsedQuestion:
    question: str
    option1: str
    option2: str
    option3: str
    option4: str
    answer: str          # 'Option1' | 'Option2' | 'Option3' | 'Option4'
    marks: int = 1
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self):
        return (
            self.question and self.option1 and self.option2 and
            self.option3 and self.option4 and
            self.answer in ('Option1', 'Option2', 'Option3', 'Option4')
        )


class BaseParser:
    """Base class for all question parsers."""
    def parse(self, source) -> List[ParsedQuestion]:
        raise NotImplementedError


class JSONQuestionParser(BaseParser):
    """
    Parses a JSON array of question objects.
    Expected format:
    [
      {
        "question": "...",
        "option1": "...",
        "option2": "...",
        "option3": "...",
        "option4": "...",
        "answer": "Option1",
        "marks": 2
      },
      ...
    ]
    """
    def parse(self, source) -> List[ParsedQuestion]:
        try:
            if hasattr(source, 'read'):
                data = json.load(source)
            else:
                data = json.loads(source)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []

        results = []
        for i, item in enumerate(data):
            pq = ParsedQuestion(
                question=item.get('question', ''),
                option1=item.get('option1', ''),
                option2=item.get('option2', ''),
                option3=item.get('option3', ''),
                option4=item.get('option4', ''),
                answer=item.get('answer', ''),
                marks=int(item.get('marks', 1)),
            )
            if not pq.is_valid:
                pq.errors.append(f"Row {i+1}: Missing or invalid fields.")
            results.append(pq)
        return results


class CSVQuestionParser(BaseParser):
    """
    Parses a CSV file.
    Expected headers: question,option1,option2,option3,option4,answer,marks
    """
    def parse(self, source) -> List[ParsedQuestion]:
        if hasattr(source, 'read'):
            content = source.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
        else:
            reader = csv.DictReader(io.StringIO(source))

        results = []
        for i, row in enumerate(reader):
            pq = ParsedQuestion(
                question=row.get('question', '').strip(),
                option1=row.get('option1', '').strip(),
                option2=row.get('option2', '').strip(),
                option3=row.get('option3', '').strip(),
                option4=row.get('option4', '').strip(),
                answer=row.get('answer', '').strip(),
                marks=int(row.get('marks', 1) or 1),
            )
            if not pq.is_valid:
                pq.errors.append(f"Row {i+2}: Missing or invalid fields.")
            results.append(pq)
        return results


class PDFQuestionParser(BaseParser):
    """
    PDF text extraction placeholder.
    # AI_HOOK: Replace extract_text_from_pdf() with OCR+NLP pipeline.
    """
    def parse(self, source) -> List[ParsedQuestion]:
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(source) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            # AI_HOOK: Pass `text` to an NLP question extraction model here.
            logger.info("PDF text extracted. AI parsing not yet implemented.")
            return []
        except ImportError:
            logger.warning("pdfplumber not installed. PDF parsing unavailable.")
            return []
        except Exception as e:
            logger.error(f"PDF parse error: {e}")
            return []


class DOCXQuestionParser(BaseParser):
    """
    DOCX text extraction placeholder.
    # AI_HOOK: Replace with structured DOCX MCQ extractor.
    """
    def parse(self, source) -> List[ParsedQuestion]:
        try:
            from docx import Document
            doc = Document(source)
            text = "\n".join([para.text for para in doc.paragraphs])
            # AI_HOOK: Pass `text` to an NLP question extraction model here.
            logger.info("DOCX text extracted. AI parsing not yet implemented.")
            return []
        except ImportError:
            logger.warning("python-docx not installed. DOCX parsing unavailable.")
            return []
        except Exception as e:
            logger.error(f"DOCX parse error: {e}")
            return []


class QuestionParserFactory:
    """Factory that selects the right parser based on file extension."""
    _parsers = {
        '.json': JSONQuestionParser,
        '.csv': CSVQuestionParser,
        '.pdf': PDFQuestionParser,
        '.docx': DOCXQuestionParser,
    }

    @classmethod
    def get_parser(cls, extension: str) -> BaseParser:
        ext = extension.lower()
        parser_class = cls._parsers.get(ext)
        if not parser_class:
            raise ValueError(f"No parser available for extension '{ext}'.")
        return parser_class()

    @classmethod
    def parse_file(cls, uploaded_file) -> List[ParsedQuestion]:
        import os
        _, ext = os.path.splitext(uploaded_file.name)
        parser = cls.get_parser(ext)
        return parser.parse(uploaded_file)


def save_parsed_questions(parsed_questions: List[ParsedQuestion], course) -> dict:
    """
    Bulk-saves valid parsed questions to the database.
    Returns a summary dict.
    """
    from exam.models import Question
    saved, skipped, errors = 0, 0, []

    objs = []
    for pq in parsed_questions:
        if pq.is_valid:
            objs.append(Question(
                course=course,
                question=pq.question,
                option1=pq.option1,
                option2=pq.option2,
                option3=pq.option3,
                option4=pq.option4,
                answer=pq.answer,
                marks=pq.marks,
            ))
        else:
            skipped += 1
            errors.extend(pq.errors)

    Question.objects.bulk_create(objs)
    saved = len(objs)
    return {'saved': saved, 'skipped': skipped, 'errors': errors}
