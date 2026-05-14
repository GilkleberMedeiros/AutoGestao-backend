from datetime import date

from ninja import Schema


class DashboardPeriodFilter(Schema):
  start_date: date
  end_date: date
