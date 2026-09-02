from pydantic import BaseModel


class StyleBase(BaseModel):
    style_no: str
    style_name: str | None = None


class StyleCreate(StyleBase):
    pass


class StyleUpdate(StyleBase):
    status: str


class StyleResponse(StyleBase):
    id: str | int
    status: str

    class Config:
        from_attributes = True