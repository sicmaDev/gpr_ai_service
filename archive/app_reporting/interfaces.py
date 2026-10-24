from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Optional

from .schemas import (
    DashboardResponse,
    ReportingFilters,
    ReportingQueryResponse,
)


class ReportingRepository(ABC):
    @abstractmethod
    def get_dashboard(self, filters: ReportingFilters) -> DashboardResponse:
        raise NotImplementedError

    @abstractmethod
    def get_query_data(
        self,
        filters: ReportingFilters,
        metric: str,
        group_by: Optional[str],
        limit: int,
    ) -> Iterable[Dict[str, Any]]:
        raise NotImplementedError


class DashboardService(ABC):
    @abstractmethod
    def build_dashboard(self, filters: ReportingFilters) -> DashboardResponse:
        raise NotImplementedError


class ReportingQueryService(ABC):
    @abstractmethod
    def answer(
        self,
        question: str,
        filters: ReportingFilters,
    ) -> ReportingQueryResponse:
        raise NotImplementedError
