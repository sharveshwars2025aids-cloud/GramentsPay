from pydantic import BaseModel


class OperationBase(BaseModel):
    operation_name: str


class OperationCreate(OperationBase):
    pass


class OperationUpdate(OperationBase):
    status: str


class OperationResponse(OperationBase):
    id: int
    status: str

    class Config:
        from_attributes = True