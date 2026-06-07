"""Pydantic request/response models."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---- Auth ----
class RegisterReq(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=80)


class LoginReq(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthReq(BaseModel):
    session_id: str


# ---- Visualize ----
class VisualizeReq(BaseModel):
    kitchen_image_base64: str
    stone_id: str
    mode: str = "auto"  # auto | hybrid
    instructions: Optional[str] = ""


class VisualizationUpdate(BaseModel):
    published: Optional[bool] = None


# ---- Credits ----
class PurchaseReq(BaseModel):
    pack_id: str  # starter | pro | studio
    method: str  # paypal | apple_pay | google_pay


# ---- Stones ----
class CustomStoneCreate(BaseModel):
    name: str
    type: str = "Custom"
    finish: str = "Custom"
    image_base64: str


class HouseStoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: str = Field(min_length=1, max_length=40)
    finish: str = Field(min_length=1, max_length=40)
    origin: str = ""
    description: str = ""
    image_url: str = Field(min_length=1)
    swatch_color: str = "#A1A1A1"
    featured: bool = False


class HouseStoneUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    finish: Optional[str] = None
    origin: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    swatch_color: Optional[str] = None
    active: Optional[bool] = None
    featured: Optional[bool] = None


# ---- Quotes ----
class QuoteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    phone: Optional[str] = ""
    notes: Optional[str] = ""
    visualization_id: Optional[str] = None
    stone_id: Optional[str] = None


class QuoteUpdate(BaseModel):
    status: Optional[str] = None  # new | contacted | closed
