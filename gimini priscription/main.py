from fastapi import FastAPI, UploadFile, File, HTTPException
from prescription_authorization.models.ocr_engine import (
    extract_text_from_bytes,
    extract_prescription_info_from_bytes,
)

app = FastAPI(title="Gemini Prescription Agent", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "gemini-prescription-agent"}


@app.post("/ocr/text")
async def ocr_text(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    raw_text = extract_text_from_bytes(image_bytes)
    return {"status": "success", "filename": file.filename, "raw_text": raw_text}


@app.post("/ocr/info")
async def ocr_info(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    result = extract_prescription_info_from_bytes(image_bytes)
    return {"status": "success", "filename": file.filename, **result}
