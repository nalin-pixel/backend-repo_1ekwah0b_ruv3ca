"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Travel app schemas

class Place(BaseModel):
    """
    Saved places for a user
    Collection name: "place"
    """
    user_id: str = Field(..., description="Identifier to group places per user/session")
    name: str = Field(..., description="Place name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    category: Optional[str] = Field(None, description="Category like museum, cafe, park")
    notes: Optional[str] = Field(None, description="Optional notes")

class DayPlan(BaseModel):
    day: int
    place_ids: List[str]

class Itinerary(BaseModel):
    """
    Generated itineraries
    Collection name: "itinerary"
    """
    user_id: str = Field(..., description="User/session identifier")
    title: str = Field(..., description="Itinerary title")
    start_date: Optional[date] = Field(None, description="Start date of the trip")
    days: List[DayPlan] = Field(default_factory=list, description="Ordered places per day")
    total_distance_km: Optional[float] = Field(None, description="Estimated total travel distance in km")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
