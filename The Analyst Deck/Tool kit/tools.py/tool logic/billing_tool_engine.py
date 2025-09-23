# Billing Compliance Tool - Python Engine

class BillingTool:
    def __init__(self, contract_total, prep_cost, subcontractor_rate=None, subcontractor_hours=0):
        self.contract_total = contract_total
        self.prep_cost = prep_cost
        self.subcontractor_rate = subcontractor_rate
        self.subcontractor_hours = subcontractor_hours
        self.hourly_rate = 100.00
        self.recon_rate = 0.00
        self.pre_surveil_time = 0.5  # hours
        self.post_surveil_time = 0.5
        self.retainer_offset = 500.00
        self.field_ops_budget = 0
        self.notes = []

    def calculate(self):
        if self.prep_cost <= self.retainer_offset:
            self.field_ops_budget = self.contract_total - self.retainer_offset
            self.notes.append("No overage. Standard $500 applied clean.")
        else:
            overage = self.prep_cost - self.retainer_offset
            self.field_ops_budget = self.contract_total - self.prep_cost
            self.notes.append(f"Overage of ${overage} applied to field ops.")

        sub_cost = 0
        if self.subcontractor_rate and self.subcontractor_hours:
            sub_cost = self.subcontractor_rate * self.subcontractor_hours

        self.subcontractor_total = sub_cost
        self.company_margin = self.hourly_rate * self.subcontractor_hours - sub_cost

    def summary(self):
        return {
            "Contract Total": f"${self.contract_total:.2f}",
            "Prep Cost": f"${self.prep_cost:.2f}",
            "Subcontractor Cost": f"${self.subcontractor_total:.2f}",
            "Remaining Ops Budget": f"${self.field_ops_budget:.2f}",
            "Internal Margin": f"${self.company_margin:.2f}",
            "Notes": self.notes
        }

# Example usage:
example = BillingTool(contract_total=3000, prep_cost=500, subcontractor_rate=85, subcontractor_hours=15)
example.calculate()
results = example.summary()
for k, v in results.items():
    print(f"{k}: {v}")
