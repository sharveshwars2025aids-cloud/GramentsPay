from pydantic import BaseModel


class DepartmentBase(BaseModel):
    name: str


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(DepartmentBase):
    status: str


class DepartmentResponse(DepartmentBase):
    id: int
    status: str

    class Config:
        from_attributes = True