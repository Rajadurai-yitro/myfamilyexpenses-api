from decimal import Decimal
from typing import Dict


class BalanceCalculator:
    @staticmethod
    def calculate_remaining(
        opening_balance: Decimal,
        total_income: Decimal,
        total_expense: Decimal,
    ) -> Dict[str, Decimal]:
        """
        Calculate remaining balance and metrics cleanly.
        """
        opening = round(Decimal(str(opening_balance)), 2)
        income = round(Decimal(str(total_income)), 2)
        expense = round(Decimal(str(total_expense)), 2)
        remaining = round(opening + income - expense, 2)

        return {
            "opening_balance": opening,
            "total_income": income,
            "total_expense": expense,
            "remaining_balance": remaining,
        }
