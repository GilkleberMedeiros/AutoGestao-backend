from ninja import Schema

from datetime import date


class DashboardPeriodFilter(Schema):
  start_date: date
  end_date: date
