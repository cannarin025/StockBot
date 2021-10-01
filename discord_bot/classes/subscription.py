from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import json

from data.monitor import ProductCategory


@dataclass
class SubscriptionData:
    max_price: Optional[float]


@dataclass
class Subscription:
    products: Dict[str, SubscriptionData]
