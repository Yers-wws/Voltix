"""In-memory data store with thread-safety and seed data."""

import threading
from typing import Dict, List, Optional, Any
from datetime import datetime


class InMemoryDatabase:
    def __init__(self):
        self._lock = threading.Lock()
        self.products: Dict[int, Dict[str, Any]] = {}
        self.orders: Dict[int, Dict[str, Any]] = {}
        self.reviews: Dict[int, Dict[str, Any]] = {}
        self._next_product_id: int = 1
        self._next_order_id: int = 1001
        self._next_review_id: int = 1
        self.seed_data()

    def seed_data(self):
        """Populates the in-memory store with realistic electronics data."""
        with self._lock:
            self.products.clear()
            self.orders.clear()
            self.reviews.clear()
            self._next_product_id = 1
            self._next_order_id = 1001
            self._next_review_id = 1

            initial_products = [
                {
                    "title": "iPhone 15 Pro",
                    "description": "Aerospace-grade titanium design with A17 Pro chip and customizable Action button.",
                    "category": "smartphones",
                    "price": 999.00,
                    "discount_percentage": 5.0,
                    "stock": 15,
                    "brand": "Apple",
                    "thumbnail": "https://cdn.dummyjson.com/products/images/smartphones/iPhone%2013%20Pro/thumbnail.png",
                    "images": [
                        "https://cdn.dummyjson.com/products/images/smartphones/iPhone%2013%20Pro/1.png"
                    ],
                    "reviews": [
                        {
                            "id": 1,
                            "reviewer_name": "Alex Smith",
                            "rating": 5,
                            "comment": "Incredible camera performance and battery life!",
                            "created_at": "2026-11-01T12:00:00"
                        }
                    ]
                },
                {
                    "title": "Samsung Galaxy S24 Ultra",
                    "description": "Galaxy AI features, titanium frame, built-in S Pen, and 200MP camera system.",
                    "category": "smartphones",
                    "price": 1199.00,
                    "discount_percentage": 10.0,
                    "stock": 12,
                    "brand": "Samsung",
                    "thumbnail": "https://cdn.dummyjson.com/products/images/smartphones/Realme%20C35/thumbnail.png",
                    "images": [],
                    "reviews": [
                        {
                            "id": 2,
                            "reviewer_name": "Elena Rostova",
                            "rating": 5,
                            "comment": "Screen is bright outdoors and zoom camera is unbeatable.",
                            "created_at": "2026-11-03T15:30:00"
                        }
                    ]
                },
                {
                    "title": "Google Pixel 8 Pro",
                    "description": "Google Tensor G3, best-in-class computational photography, and Android 14.",
                    "category": "smartphones",
                    "price": 899.00,
                    "discount_percentage": 8.0,
                    "stock": 8,
                    "brand": "Google",
                    "thumbnail": "https://cdn.dummyjson.com/products/images/smartphones/iPhone%20X/thumbnail.png",
                    "images": [],
                    "reviews": []
                },
                {
                    "title": 'MacBook Pro 14" M3',
                    "description": "Blazing-fast M3 chip, Liquid Retina XDR display, up to 22 hours of battery life.",
                    "category": "laptops",
                    "price": 1599.00,
                    "discount_percentage": 7.0,
                    "stock": 10,
                    "brand": "Apple",
                    "thumbnail": "https://cdn.dummyjson.com/products/images/laptops/Apple%20MacBook%20Pro%2014%20Inch%20Space%20Grey/thumbnail.png",
                    "images": [],
                    "reviews": [
                        {
                            "id": 3,
                            "reviewer_name": "Dmitry K.",
                            "rating": 5,
                            "comment": "Silent under heavy dev workload and phenomenal battery.",
                            "created_at": "2026-11-05T09:15:00"
                        }
                    ]
                },
                {
                    "title": "Dell XPS 15",
                    "description": "OLED 3.5K touch display, Intel Core i7, NVIDIA RTX 4060 graphics.",
                    "category": "laptops",
                    "price": 1899.00,
                    "discount_percentage": 12.0,
                    "stock": 5,
                    "brand": "Dell",
                    "thumbnail": "https://cdn.dummyjson.com/products/images/laptops/Asus%20Zenbook%20Pro%20Dual%20Screen%20Laptop/thumbnail.png",
                    "images": [],
                    "reviews": []
                },
                {
                    "title": "iPad Air M2 11-inch",
                    "description": "Supercharged by Apple M2 chip with Liquid Retina display and Apple Pencil Pro support.",
                    "category": "tablets",
                    "price": 599.00,
                    "discount_percentage": 5.0,
                    "stock": 20,
                    "brand": "Apple",
                    "thumbnail": "https://cdn.dummyjson.com/products/images/tablets/iPad%20Mini%202021%20Starlight/thumbnail.png",
                    "images": [],
                    "reviews": []
                },
                {
                    "title": "AirPods Pro (2nd Generation)",
                    "description": "Up to 2x more Active Noise Cancellation with USB-C MagSafe charging case.",
                    "category": "mobile-accessories",
                    "price": 249.00,
                    "discount_percentage": 10.0,
                    "stock": 30,
                    "brand": "Apple",
                    "thumbnail": "https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png",
                    "images": [],
                    "reviews": []
                },
                {
                    "title": "Anker Prime 100W GaN Wall Charger",
                    "description": "Ultra-compact 3-port fast charger with ActiveShield 2.0 temperature monitoring.",
                    "category": "mobile-accessories",
                    "price": 79.99,
                    "discount_percentage": 15.0,
                    "stock": 45,
                    "brand": "Anker",
                    "thumbnail": "https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png",
                    "images": [],
                    "reviews": []
                }
            ]

            for p in initial_products:
                pid = self._next_product_id
                self._next_product_id += 1
                p_copy = p.copy()
                p_copy["id"] = pid
                self.products[pid] = p_copy

            self._next_review_id = 4


# Global database singleton
db = InMemoryDatabase()
