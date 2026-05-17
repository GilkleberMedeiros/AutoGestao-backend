from datetime import date

from ninja import Schema


from pydantic import model_validator


class DashboardPeriodFilter(Schema):
  start_date: date
  end_date: date

  @model_validator(mode="after")
  def validate_date_range(self):
    if self.start_date > self.end_date:
      raise ValueError("start_date cannot be greater than end_date")
    return self


class DashboardFilter(DashboardPeriodFilter):
  includes_open_projects: bool
