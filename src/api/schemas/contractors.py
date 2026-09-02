from pydantic import BaseModel


class ContractorBase(BaseModel):
    name: str
    commission_amount: float


class ContractorCreate(ContractorBase):
    pass


class ContractorUpdate(ContractorBase):
    status: str


class ContractorResponse(ContractorBase):
    id: int
    status: str

    class Config:
        from_attributes = True