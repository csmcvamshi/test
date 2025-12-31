from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, String, Integer, Text, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List

URL = "sqlite:///./todos.db"

engine = create_engine(
    URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

class createTable(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    desc = Column(Text)
    status = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

class Input(BaseModel):
    title: str
    desc: str
    status: bool = False

class Output(BaseModel):
    id: int
    title: str
    desc: str
    status: bool

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=["*"],
)

@app.get("/")
def welcome():
    return {"message": "Hello and welcome to server"}

@app.get("/items", response_model=List[Output])
def get_items(db: Session = Depends(get_db)):
    return db.query(createTable).all()   # empty → []

@app.post("/items/insert", response_model=Output)
def create_task(tasks: Input, db: Session = Depends(get_db)):
    obj = createTable(
        title=tasks.title,
        desc=tasks.desc,
        status=tasks.status
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.put("/items/{item_id}", response_model=Output)
def update_table(item_id: int, tasks: Input, db: Session = Depends(get_db)):
    obj = db.query(createTable).filter(createTable.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")

    obj.title = tasks.title
    obj.desc = tasks.desc
    obj.status = tasks.status

    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/items/delete/{item_id}")
def delete_record(item_id: int, db: Session = Depends(get_db)):
    obj = db.query(createTable).filter(createTable.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(obj)
    db.commit()
    return {"message": "Task deleted successfully"}
