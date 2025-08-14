from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.datastructures import URL as StarletteURL
from sqlmodel import select, Session
from .db import init_db, get_session
from .models import URL
from .utils import unique_code
import validators

app = FastAPI(title="Shorty · URL Shortener")

# Static & Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, session: Session = Depends(get_session)):
    recent = session.exec(select(URL).order_by(URL.id.desc()).limit(10)).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "recent": recent}
    )

@app.post("/shorten")
def shorten(
    request: Request,
    target_url: str = Form(...),
    custom_code: str | None = Form(None),
    session: Session = Depends(get_session),
):
    # Basic validation
    if not validators.url(target_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    if custom_code:
        code = custom_code.strip()
        if not code.isalnum() or len(code) > 16:
            raise HTTPException(status_code=400, detail="Custom code must be alphanumeric and <= 16 chars")
    else:
        code = unique_code(session)

    # Ensure uniqueness for custom code too
    exists = session.exec(select(URL).where(URL.short_code == code)).first()
    if exists:
        raise HTTPException(status_code=409, detail="Short code already exists. Try another.")

    record = URL(short_code=code, target_url=target_url)
    session.add(record)
    session.commit()
    session.refresh(record)

    # Build absolute short URL
    base = str(request.base_url).rstrip("/")
    short_url = f"{base}/{record.short_code}"

    return {"short_url": short_url, "code": record.short_code}

@app.get("/{code}")
def redirect(code: str, session: Session = Depends(get_session)):
    record = session.exec(select(URL).where(URL.short_code == code)).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    record.clicks += 1
    session.add(record)
    session.commit()
    return RedirectResponse(record.target_url, status_code=307)

# Simple JSON endpoint for recent URLs (useful for demo/testing)
@app.get("/api/recent")
def api_recent(session: Session = Depends(get_session)):
    items = session.exec(select(URL).order_by(URL.id.desc()).limit(20)).all()
    return [
        {
            "code": item.short_code,
            "target": item.target_url,
            "clicks": item.clicks,
            "created_at": item.created_at,
        }
        for item in items
    ]