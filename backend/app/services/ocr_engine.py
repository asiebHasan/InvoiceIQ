import tempfile
import platform
from pathlib import Path
from dataclasses import dataclass


@dataclass
class OcrResult:
    text: str = ""
    confidence: float = 0.0
    method: str = "paddleocr"


def _convert_pdf_to_images(file_path: str, dpi: int = 300) -> list:
    try:
        from pdf2image import convert_from_path
        return convert_from_path(file_path, dpi=dpi)
    except Exception:
        pass

    # Fallback: use pdfplumber to render pages as images (works everywhere)
    try:
        import pdfplumber
        from PIL import Image
        images = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                im = page.to_image(resolution=dpi)
                images.append(im.original)
        return images
    except Exception:
        raise RuntimeError(
            "Cannot convert PDF to images. Install poppler (Linux/Mac) "
            "or run in Docker: docker-compose up backend"
        )


def _ocr_with_paddle(image_paths: list[str]) -> OcrResult:
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    all_text = []
    confidences = []

    for img_path in image_paths:
        result = ocr.ocr(img_path, cls=True)
        if result and result[0]:
            for line in result[0]:
                text, confidence = line[1]
                all_text.append(text)
                confidences.append(confidence)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return OcrResult(
        text="\n".join(all_text),
        confidence=avg_confidence,
        method="paddleocr",
    )


def _ocr_with_tesseract(image_paths: list[str]) -> OcrResult:
    import pytesseract
    from PIL import Image

    all_text = []
    confidences = []

    for img_path in image_paths:
        img = Image.open(img_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        for text, conf in zip(data["text"], data["conf"]):
            if text.strip() and int(conf) > 0:
                all_text.append(text)
                confidences.append(int(conf) / 100.0)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return OcrResult(
        text="\n".join(all_text),
        confidence=avg_confidence,
        method="tesseract",
    )


def extract_text_from_scanned_pdf(file_path: str) -> OcrResult:
    images = _convert_pdf_to_images(file_path, dpi=300)

    with tempfile.TemporaryDirectory() as tmp_dir:
        image_paths = []
        for i, img in enumerate(images):
            img_path = Path(tmp_dir) / f"page_{i}.png"
            img.save(str(img_path), "PNG")
            image_paths.append(str(img_path))

        # Try PaddleOCR first (best accuracy), fallback to Tesseract
        try:
            return _ocr_with_paddle(image_paths)
        except ImportError:
            pass

        try:
            return _ocr_with_tesseract(image_paths)
        except ImportError:
            pass

        return OcrResult(
            text="",
            confidence=0.0,
            method="none",
        )
