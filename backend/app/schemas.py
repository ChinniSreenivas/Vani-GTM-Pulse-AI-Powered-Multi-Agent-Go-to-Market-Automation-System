from pydantic import BaseModel, Field


class ProspectInput(BaseModel):
    company: str = Field(min_length=2, max_length=120)
    industry: str = "Consulting / Professional Services"
    location: str = "India"
    product: str = "Vani communication fitness and coaching platform"
    target_role: str = "Head of Learning & Development"
    company_size: str = "Enterprise"
    pain_points: list[str] = Field(default_factory=lambda: [
        "client-facing communication consistency",
        "stakeholder communication",
        "sales or client conversation effectiveness",
    ])
    signals: list[str] = Field(default_factory=lambda: [
        "client-facing hiring",
        "learning and development initiative",
        "sales enablement",
    ])
    notes: str = ""
