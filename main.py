from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List
import os

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ORM models
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, Sequence('item_id_seq'), primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, Sequence('image_id_seq'), primary_key=True, index=True)
    file_path = Column(String, index=True)

# Pydantic models for response
class ItemCreate(BaseModel):
    name: str
    description: str

class ImageResponse(BaseModel):
    id: int
    file_path: str

    class Config:
        orm_mode = True

# Create tables in the database
Base.metadata.create_all(bind=engine)

# FastAPI app setup
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://amosnudel.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.post("/items/", response_model=ItemCreate)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/{item_id}", response_model=ItemCreate)
def get_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.get("/items/", response_model=List[ItemCreate])
def get_items(db: Session = Depends(get_db)):
    db_items = db.query(Item).all()
    return db_items

@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save the image to a folder
    os.makedirs("uploads", exist_ok=True)
    upload_path = f"uploads/{file.filename}"
    with open(upload_path, "wb") as buffer:
        buffer.write(file.file.read())

    # Save the image path to the database
    db_image = Image(file_path=upload_path)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    return {"filename": file.filename, "file_path": upload_path}

@app.get("/images/", response_model=List[ImageResponse])
def get_images(db: Session = Depends(get_db)):
    db_images = db.query(Image).all()
    return db_images
