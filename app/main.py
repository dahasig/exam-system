from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from random import sample, shuffle
import secrets
import json
from pathlib import Path

from .database import create_db_and_tables, get_session
from .models import User, Question, Exam, ExamQuestion, Answer, ProctorEvent, Snapshot

app = FastAPI(title="RC Exam System")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.middleware("http")
async def no_cache(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def get_allowed_emails():
    path = Path("allowed_emails.txt")
    if not path.exists():
        return set()

    emails = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip().lower()
        if line and not line.startswith("#"):
            emails.add(line)

    return emails


def is_email_allowed(email: str):
    return email.strip().lower() in get_allowed_emails()


@app.on_event("startup")
def startup():
    create_db_and_tables()


def public_question(q):
    return {
        "id": q.id,
        "qtype": q.qtype,
        "type": "سؤال مقالي" if q.qtype == "essay" else "سؤال اختياري",
        "question": q.question,
        "option_a": q.option_a,
        "option_b": q.option_b,
        "option_c": q.option_c,
        "option_d": q.option_d,
        "seconds": 120 if q.qtype == "essay" else 40
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/start")
def start(request: Request, name: str = Form(...), email: str = Form(...), session: Session = Depends(get_session)):
    email = email.strip().lower()

    if not is_email_allowed(email):
        return templates.TemplateResponse("home.html", {
            "request": request,
            "error": "البريد الالكتروني غير مصرح له بالدخول"
        })

    existing_exam = session.exec(
        select(Exam).where(
            Exam.email == email
        )
    ).first()

    if existing_exam:
        return templates.TemplateResponse("home.html", {
            "request": request,
            "error": "تم استخدام هذا البريد مسبقا ولا يمكن الدخول للاختبار مرة أخرى"
        })

    mcq_medium = session.exec(
        select(Question).where(Question.qtype != "essay", Question.level == "medium")
    ).all()

    mcq_hard = session.exec(
        select(Question).where(Question.qtype != "essay", Question.level == "hard")
    ).all()

    essay_medium = session.exec(
        select(Question).where(Question.qtype == "essay", Question.level == "medium")
    ).all()

    essay_hard = session.exec(
        select(Question).where(Question.qtype == "essay", Question.level == "hard")
    ).all()

    if len(mcq_medium) < 12 or len(mcq_hard) < 16 or len(essay_medium) < 1 or len(essay_hard) < 1:
        raise HTTPException(500, "بنك الاسئلة غير كاف للتوزيع المطلوب")
        
    mcq_medium = list({q.question: q for q in mcq_medium}.values())
    mcq_hard = list({q.question: q for q in mcq_hard}.values())
    essay_medium = list({q.question: q for q in essay_medium}.values())
    essay_hard = list({q.question: q for q in essay_hard}.values())
    
    selected = (
        sample(mcq_medium, 12) +
        sample(mcq_hard, 16) +
        sample(essay_medium, 1) +
        sample(essay_hard, 1)
    )

    shuffle(selected)

    token = secrets.token_urlsafe(16)

    exam = Exam(name=name, email=email, token=token, status="instructions")
    session.add(exam)
    session.commit()
    session.refresh(exam)

    for order_no, q in enumerate(selected, 1):
        session.add(ExamQuestion(exam_id=exam.id, question_id=q.id, order_no=order_no))

    session.commit()

    return RedirectResponse(f"/instructions/{token}", status_code=303)


@app.get("/instructions/{token}", response_class=HTMLResponse)
def instructions(token: str, request: Request, session: Session = Depends(get_session)):
    exam = session.exec(select(Exam).where(Exam.token == token)).first()
    if not exam:
        raise HTTPException(404)

    return templates.TemplateResponse("instructions.html", {
        "request": request,
        "exam": exam
    })


@app.post("/begin/{token}")
def begin(token: str, session: Session = Depends(get_session)):
    exam = session.exec(select(Exam).where(Exam.token == token)).first()
    if not exam:
        raise HTTPException(404)

    if exam.status == "submitted":
        return RedirectResponse(f"/result/{token}", status_code=303)

    exam.status = "started"
    session.add(exam)
    session.commit()

    return RedirectResponse(f"/exam/{token}", status_code=303)


@app.get("/exam/{token}", response_class=HTMLResponse)
def exam_page(token: str, request: Request, session: Session = Depends(get_session)):
    exam = session.exec(select(Exam).where(Exam.token == token)).first()
    if not exam:
        raise HTTPException(404)

    if exam.status == "submitted":
        return RedirectResponse(f"/result/{token}", status_code=303)

    links = session.exec(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam.id).order_by(ExamQuestion.order_no)
    ).all()

    questions = [public_question(session.get(Question, link.question_id)) for link in links]

    return templates.TemplateResponse("exam.html", {
        "request": request,
        "exam": exam,
        "questions": json.dumps(questions, ensure_ascii=False)
    })


@app.post("/submit/{token}")
async def submit(token: str, request: Request, session: Session = Depends(get_session)):
    exam = session.exec(select(Exam).where(Exam.token == token)).first()
    if not exam:
        raise HTTPException(404)

    if exam.status == "submitted":
        return {"redirect": f"/result/{token}"}

    data = await request.json()

    score = 0
    total = 0
    essay_count = 0

    for qid, ans in data.get("answers", {}).items():
        q = session.get(Question, int(qid))

        selected = ""
        essay = ""
        correct = False

        if q.qtype == "essay":
            essay_count += 1
            essay = str(ans or "")
        else:
            total += 1
            selected = str(ans or "")
            correct = selected == q.correct_option
            if correct:
                score += 1

        session.add(
            Answer(
                exam_id=exam.id,
                question_id=q.id,
                answer=selected,
                essay=essay,
                correct=correct,
                seconds=int(data.get("times", {}).get(str(qid), 0))
            )
        )

    events = session.exec(select(ProctorEvent).where(ProctorEvent.exam_id == exam.id)).all()

    exam.score = score
    exam.total = total
    exam.essay_count = essay_count
    exam.suspicion = len([
        event for event in events
        if event.event not in ["exam_started", "camera_started", "snapshot"]
    ])
    exam.status = "submitted"

    session.add(exam)
    session.commit()

    return {"redirect": f"/result/{token}"}


@app.get("/result/{token}", response_class=HTMLResponse)
def result(token: str, request: Request, session: Session = Depends(get_session)):
    exam = session.exec(select(Exam).where(Exam.token == token)).first()
    if not exam:
        raise HTTPException(404)

    return templates.TemplateResponse("result.html", {
        "request": request,
        "exam": exam
    })


@app.post("/event/{token}")
async def event(token: str, request: Request, session: Session = Depends(get_session)):
    exam = session.exec(select(Exam).where(Exam.token == token)).first()
    data = await request.json()

    if exam:
        session.add(ProctorEvent(
            exam_id=exam.id,
            event=data.get("event", "unknown"),
            details=json.dumps(data, ensure_ascii=False)
        ))
        session.commit()

    return {"ok": True}


@app.post("/snapshot/{token}")
async def snapshot(token: str, request: Request, session: Session = Depends(get_session)):
    exam = session.exec(select(Exam).where(Exam.token == token)).first()
    data = await request.json()

    if exam and data.get("image"):
        session.add(Snapshot(exam_id=exam.id, image=data["image"]))
        session.add(ProctorEvent(exam_id=exam.id, event="snapshot", details="saved"))
        session.commit()

    return {"ok": True}


@app.get("/admin", response_class=HTMLResponse)
def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "error": None
    })


@app.post("/admin", response_class=HTMLResponse)
def admin(request: Request, username: str = Form(...), password: str = Form(...), session: Session = Depends(get_session)):
    user = session.exec(
        select(User).where(User.username == username, User.password == password)
    ).first()

    if not user:
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "بيانات الدخول غير صحيحة"
        })

    exams = session.exec(select(Exam).order_by(Exam.id.desc())).all()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "exams": exams
    })


@app.get("/admin/exam/{exam_id}", response_class=HTMLResponse)
def admin_exam(exam_id: int, request: Request, session: Session = Depends(get_session)):
    exam = session.get(Exam, exam_id)
    answers = session.exec(select(Answer).where(Answer.exam_id == exam_id)).all()
    events = session.exec(select(ProctorEvent).where(ProctorEvent.exam_id == exam_id)).all()
    snaps = session.exec(select(Snapshot).where(Snapshot.exam_id == exam_id)).all()
    qmap = {q.id: q for q in session.exec(select(Question)).all()}

    return templates.TemplateResponse("admin_exam.html", {
        "request": request,
        "exam": exam,
        "answers": answers,
        "events": events,
        "snaps": snaps,
        "qmap": qmap
    })
@app.get("/seed")
def seed_now():
    import seed
    seed.run()
    return {"status": "done"}
