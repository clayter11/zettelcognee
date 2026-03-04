"""Custom Cognee DataPoints for domain-specific document types.

These define the structured entities that Cognee extracts during cognify().
Each document type gets its own DataPoint with domain-specific fields,
so the knowledge graph captures precise structured information.
"""

from pydantic import BaseModel, Field


class CommercialProposal(BaseModel):
    """Коммерческое предложение."""

    client: str = Field(description="Клиент / заказчик")
    project_name: str = Field(description="Название проекта")
    items: list[str] = Field(default_factory=list, description="Позиции спецификации")
    total_price: float | None = Field(default=None, description="Общая сумма")
    currency: str = Field(default="RUB", description="Валюта")
    validity_date: str | None = Field(default=None, description="Срок действия")
    payment_terms: str | None = Field(default=None, description="Условия оплаты")
    delivery_terms: str | None = Field(default=None, description="Условия поставки")


class Contract(BaseModel):
    """Договор."""

    parties: list[str] = Field(default_factory=list, description="Стороны договора")
    contract_number: str | None = Field(default=None, description="Номер договора")
    subject: str = Field(description="Предмет договора")
    value: float | None = Field(default=None, description="Сумма договора")
    currency: str = Field(default="RUB", description="Валюта")
    start_date: str | None = Field(default=None, description="Дата начала")
    end_date: str | None = Field(default=None, description="Дата окончания")
    payment_schedule: str | None = Field(default=None, description="График оплаты")
    penalties: str | None = Field(default=None, description="Штрафные санкции")


class Calculation(BaseModel):
    """Расчёт / смета / калькуляция."""

    project: str = Field(description="Проект")
    calculation_type: str = Field(description="Тип: смета, ТЭО, калькуляция")
    total: float | None = Field(default=None, description="Итого")
    currency: str = Field(default="RUB", description="Валюта")
    sections: list[str] = Field(default_factory=list, description="Разделы расчёта")
    assumptions: list[str] = Field(default_factory=list, description="Допущения")


class Drawing(BaseModel):
    """Чертёж / схема."""

    title: str = Field(description="Название чертежа")
    drawing_number: str | None = Field(default=None, description="Номер чертежа")
    scale: str | None = Field(default=None, description="Масштаб")
    description: str = Field(description="Текстовое описание")
    related_project: str | None = Field(default=None, description="Проект")
    revision: str | None = Field(default=None, description="Ревизия")
    author: str | None = Field(default=None, description="Автор")


class MeetingNote(BaseModel):
    """Протокол / запись встречи."""

    title: str = Field(description="Название встречи")
    date: str | None = Field(default=None, description="Дата")
    participants: list[str] = Field(default_factory=list, description="Участники")
    decisions: list[str] = Field(default_factory=list, description="Решения")
    action_items: list[str] = Field(default_factory=list, description="Задачи / действия")
    project: str | None = Field(default=None, description="Проект")


# Map document types to their DataPoint models
DATAPOINT_MAP = {
    "proposal": CommercialProposal,
    "contract": Contract,
    "calculation": Calculation,
    "drawing": Drawing,
    "meeting": MeetingNote,
}
