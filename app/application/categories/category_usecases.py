from typing import List
from app.domain.entities.category import Category
from app.domain.repositories.category_repository import CategoryRepository

DEFAULT_CATEGORIES = [
    {"name_key": "food", "icon_key": "restaurant", "sort_order": 1, "kind": "debit"},
    {"name_key": "grocery", "icon_key": "shopping_cart", "sort_order": 2, "kind": "debit"},
    {"name_key": "snacks", "icon_key": "fastfood", "sort_order": 3, "kind": "debit"},
    {"name_key": "rent", "icon_key": "home", "sort_order": 3, "kind": "debit"},
    {"name_key": "electricity", "icon_key": "bolt", "sort_order": 4, "kind": "debit"},
    {"name_key": "gas", "icon_key": "local_gas_station", "sort_order": 5, "kind": "debit"},
    {"name_key": "recharge", "icon_key": "phone_android", "sort_order": 6, "kind": "debit"},
    {"name_key": "travel", "icon_key": "directions_car", "sort_order": 7, "kind": "debit"},
    {"name_key": "shopping", "icon_key": "shopping_bag", "sort_order": 8, "kind": "debit"},
    {"name_key": "medical", "icon_key": "medical_services", "sort_order": 9, "kind": "debit"},
    {"name_key": "education", "icon_key": "school", "sort_order": 10, "kind": "debit"},
    {"name_key": "shared", "icon_key": "group", "sort_order": 11, "kind": "debit"},
    {"name_key": "insurance", "icon_key": "security", "sort_order": 12, "kind": "debit"},
    {"name_key": "maintenance", "icon_key": "handyman", "sort_order": 13, "kind": "debit"},
    {"name_key": "vegetables", "icon_key": "eco", "sort_order": 14, "kind": "debit"},
    {"name_key": "fruits", "icon_key": "nutrition", "sort_order": 15, "kind": "debit"},
    {"name_key": "entertainment", "icon_key": "movie", "sort_order": 16, "kind": "debit"},
    {"name_key": "other", "icon_key": "category", "sort_order": 17, "kind": "debit"},
    {"name_key": "salary", "icon_key": "payments", "sort_order": 101, "kind": "credit"},
    {"name_key": "interest", "icon_key": "percent", "sort_order": 102, "kind": "credit"},
    {"name_key": "rewards", "icon_key": "emoji_events", "sort_order": 103, "kind": "credit"},
    {"name_key": "gift", "icon_key": "card_giftcard", "sort_order": 104, "kind": "credit"},
    {"name_key": "bonus", "icon_key": "workspace_premium", "sort_order": 105, "kind": "credit"},
    {"name_key": "other_income", "icon_key": "savings", "sort_order": 106, "kind": "credit"},
]


class SeedCategoriesUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self) -> List[Category]:
        seeded = []
        for cat_data in DEFAULT_CATEGORIES:
            existing = self.category_repo.get_by_name_key(cat_data["name_key"])
            if not existing:
                new_cat = Category.create(
                    name_key=cat_data["name_key"],
                    icon_key=cat_data["icon_key"],
                    sort_order=cat_data["sort_order"],
                    kind=cat_data["kind"],
                )
                seeded.append(self.category_repo.create(new_cat))
            elif (
                existing.kind != cat_data["kind"]
                or existing.sort_order != cat_data["sort_order"]
                or existing.icon_key != cat_data["icon_key"]
            ):
                existing.kind = cat_data["kind"]
                existing.sort_order = cat_data["sort_order"]
                existing.icon_key = cat_data["icon_key"]
                seeded.append(self.category_repo.update(existing))
            else:
                seeded.append(existing)
        return seeded


class ListCategoriesUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, active_only: bool = True) -> List[Category]:
        return self.category_repo.list_all(active_only=active_only)
