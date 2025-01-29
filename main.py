import os
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List  # Import List for response
import shutil
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware

# Ensure the 'uploads' directory exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ORM model for Items
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, Sequence('item_id_seq'), primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)

# Pydantic model for Item Create Request
class ItemCreate(BaseModel):
    name: str
    description: str

# Pydantic model for Image response
class Image(BaseModel):
    id: int
    file_path: str

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# FastAPI app setup
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontserver.netlify.app/"],  # Allows all origins; you can restrict this to specific URLs (e.g., ["https://example.com"])
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods like GET, POST, etc.
    allow_headers=["*"],  # Allows all headers
)

# Mount StaticFiles to serve images from the 'uploads' directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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

# Endpoint for uploading an image
@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}

# Endpoint to get a list of images
@app.get("/images/", response_model=List[Image])
def get_images():
    image_files = []
    for filename in os.listdir("uploads"):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_files.append({"id": len(image_files) + 1, "file_path": f"uploads/{filename}"})
    return image_files
