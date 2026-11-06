"""Pure paper-trading risk check. No broker integration, orders or financial advice."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

def money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid money amount") from exc
    if not amount.is_finite():
        raise ValueError("Nonfinite money amount")
    return amount

@dataclass
class PaperLimits:
    initial_equity: Decimal
    daily_loss_limit: Decimal
    total_loss_limit: Decimal

    def __post_init__(self):
        self.initial_equity = money(self.initial_equity)
        self.daily_loss_limit = money(self.daily_loss_limit)
        self.total_loss_limit = money(self.total_loss_limit)
        if self.initial_equity <= 0 or self.daily_loss_limit <= 0 or self.total_loss_limit <= 0:
            raise ValueError("Positive equity and positive loss budgets required")

    def check(self, *, equity, daily_open_equity, proposed_risk):
        current = money(equity)
        opening = money(daily_open_equity)
        risk = money(proposed_risk)
        if opening <= 0 or current < 0 or risk < 0:
            raise ValueError("Invalid paper-account state")
        projected = current - risk
        daily_floor = opening - self.daily_loss_limit
        total_floor = self.initial_equity - self.total_loss_limit
        reasons = []
        if current <= daily_floor or projected < daily_floor:
            reasons.append("DAILY_DRAWDOWN")
        if current <= total_floor or projected < total_floor:
            reasons.append("MAX_DRAWDOWN")
        if projected < 0:
            reasons.append("INSUFFICIENT_EQUITY")
        return {"permitted": not reasons, "reasons": reasons, "projected_equity": str(projected),
                "daily_floor": str(daily_floor), "total_floor": str(total_floor),
                "mode": "PAPER_ONLY", "executed": False}
