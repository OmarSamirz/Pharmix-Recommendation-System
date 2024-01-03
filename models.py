from pydantic import BaseModel
from dataclasses import dataclass

class RecommendationScheme(BaseModel):
    user_id: int
    n_recommend: int


@dataclass
class Product:
    id: int
    image_url: str
    name: str
    price: float
    old_price: float
    discountAmount: float
    company_name: str
    category: str
    amount: str
    is_prescription: bool
    is_discount: bool
    description: str
