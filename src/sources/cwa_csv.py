"""CWA CSV source client (formal report, monthly query).

Provides a minimal async client that:
1) GETs the landing page to establish session/cookies
2) POSTs /zh-tw/earthquake/csv with form payload for a given month

The caller is responsible for decoding Big5 and parsing CSV.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Final

import aiohttp


DATA_PATH: Final[str] = "/zh-tw/earthquake/data/"
CSV_PATH: Final[str] = "/zh-tw/earthquake/csv"


def _month_search_label(year: int, month: int) -> str:
    """Return search label like '2025年12月'."""

    return f"{year}年{month:02d}月"


def build_form_payload(year: int, month: int, table_length: int = 100) -> dict[str, str]:
    """Construct form payload matching observed POST body for CSV export.

    Minimal required fields are included; unused filters stay empty.
    """

    return {
        "Search": _month_search_label(year, month),
        "SearchText": "",
        "table_length": str(table_length),
        "txtSDate": "",
        "txtEDate": "",
        "txtSscale": "",
        "txtEscale": "",
        "txtSdepth": "",
        "txtEdepth": "",
        "txtLonS": "",
        "txtLonE": "",
        "txtLatS": "",
        "txtLatE": "",
        "ddlCity": "",
        "ddlTown": "",
        "ddlCitySta": "",
        "ddlStation": "",
        "ddlStationName": "",
        "txtIntensityB": "",
        "txtIntensityE": "",
        "txtLon": "",
        "txtLat": "",
        "txtKM": "",
        "order[0][column]": "2",  # OriginTime
        "order[0][dir]": "desc",
        "columns[0][name]": "EventNo",
        "columns[1][name]": "MaxIntensity",
        "columns[2][name]": "OriginTime",
        "columns[3][name]": "MagnitudeValue",
        "columns[4][name]": "Depth",
        "columns[5][name]": "Description",
    }


@dataclass
class CwaCsvSource:
    base_url: str
    table_length: int = 100
    allow_insecure_ssl: bool = False
    _session: aiohttp.ClientSession | None = None
    _init_lock: asyncio.Lock = asyncio.Lock()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            async with self._init_lock:
                if self._session is None or self._session.closed:
                    connector = None
                    if self.allow_insecure_ssl:
                        connector = aiohttp.TCPConnector(ssl=False)
                    self._session = aiohttp.ClientSession(base_url=self.base_url, connector=connector)
                    # hit landing page to build session/cookies
                    async with self._session.get(DATA_PATH) as resp:
                        resp.raise_for_status()
                        await resp.read()
        return self._session

    async def fetch_month_csv(self, year: int, month: int) -> bytes:
        session = await self._ensure_session()
        payload = build_form_payload(year, month, table_length=self.table_length)
        async with session.post(CSV_PATH, data=payload) as resp:
            resp.raise_for_status()
            return await resp.read()

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


__all__ = ["CwaCsvSource", "build_form_payload"]