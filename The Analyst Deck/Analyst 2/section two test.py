import pytesseract
import easyocr
from PIL import Image
from unstructured.partition.auto import partition

class Section2Framework(SectionFramework):
    SECTION_ID = "section_2_planning"
    MAX_RERUNS = 2
    def __init__(self, gateway: Any, ecc: Optional[Any] = None) -> None:
        super().__init__(gateway=gateway, ecc=ecc)
        self._last_context: Dict[str, Any] = {}
        self._ocr_reader = easyocr.Reader(['en'], gpu=False)

    def _ocr_tesseract(self, image_path: str) -> str:
        try:
            image = Image.open(image_path)
            return pytesseract.image_to_string(image)
        except Exception as e:
            return f"Tesseract OCR error: {str(e)}"

    def _ocr_easyocr(self, image_path: str) -> str:
        try:
            results = self._ocr_reader.readtext(image_path, detail=0)
            return "\n".join(results)
        except Exception as e:
            return f"EasyOCR error: {str(e)}"

    def _unstructured_parse(self, file_path: str) -> str:
        try:
            elements = partition(filename=file_path)
            return "\n".join(str(el) for el in elements)
        except Exception as e:
            return f"Unstructured parsing error: {str(e)}"

    # ... rest of your methods stay unchanged ...
