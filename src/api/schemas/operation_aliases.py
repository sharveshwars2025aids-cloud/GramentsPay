from pydantic import BaseModel


class OperationAliasBase(BaseModel):

    operation_id: int
    alias: str


class OperationAliasCreate(OperationAliasBase):
    pass


class OperationAliasUpdate(OperationAliasBase):

    status: str


class OperationAliasResponse(OperationAliasBase):

    id: int
    status: str

    class Config:
        from_attributes = True