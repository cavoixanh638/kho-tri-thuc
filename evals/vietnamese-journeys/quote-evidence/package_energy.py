"""Read the native Windows cumulative RAPL processor-package energy counter."""

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from time import perf_counter_ns


_COUNTER_PATH = r"\Energy Meter(rapl_package0_pkg)\Energy"
_PWH_PER_WH = 10**12
_VALID_COUNTER_STATUSES = {0, 1}


class _RawCounter(ctypes.Structure):
    _fields_ = [
        ("status", wintypes.DWORD),
        ("timestamp", wintypes.FILETIME),
        ("first_value", ctypes.c_longlong),
        ("second_value", ctypes.c_longlong),
        ("multi_count", wintypes.DWORD),
    ]


@dataclass(frozen=True)
class PackageEnergySample:
    energy_pwh: int
    monotonic_ns: int
    overhead_ns: int


class PackageEnergyMeter:
    """Reuse one PDH query. Return None if a reading is unavailable."""

    def __init__(self):
        self._query = wintypes.HANDLE()
        self._counter = wintypes.HANDLE()
        self._error = None
        try:
            self._pdh = ctypes.WinDLL("pdh.dll")
        except (AttributeError, OSError):
            self._error = "pdh_unavailable"
            return

        signature = {
            "PdhOpenQueryW": [
                wintypes.LPCWSTR, ctypes.c_size_t, ctypes.POINTER(wintypes.HANDLE)
            ],
            "PdhAddEnglishCounterW": [
                wintypes.HANDLE, wintypes.LPCWSTR, ctypes.c_size_t,
                ctypes.POINTER(wintypes.HANDLE)
            ],
            "PdhCollectQueryData": [wintypes.HANDLE],
            "PdhGetRawCounterValue": [
                wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD),
                ctypes.POINTER(_RawCounter)
            ],
            "PdhCloseQuery": [wintypes.HANDLE],
        }
        for name, parameter_types in signature.items():
            function = getattr(self._pdh, name)
            function.argtypes = parameter_types
            function.restype = wintypes.DWORD

        result = self._pdh.PdhOpenQueryW(None, 0, ctypes.byref(self._query))
        if result:
            self._error = f"open_query:0x{result:08x}"
            return

        result = self._pdh.PdhAddEnglishCounterW(
            self._query, _COUNTER_PATH, 0, ctypes.byref(self._counter)
        )
        if result:
            self._error = f"add_counter:0x{result:08x}"
            self.close()

    @property
    def last_error(self):
        return self._error

    def read(self):
        if not self._counter:
            return None

        start = perf_counter_ns()
        result = self._pdh.PdhCollectQueryData(self._query)
        if result:
            self._error = f"collect:0x{result:08x}"
            return None

        raw = _RawCounter()
        result = self._pdh.PdhGetRawCounterValue(
            self._counter, None, ctypes.byref(raw)
        )
        end = perf_counter_ns()
        if result:
            self._error = f"raw_value:0x{result:08x}"
            return None
        if raw.status not in _VALID_COUNTER_STATUSES or raw.first_value <= 0:
            self._error = f"counter_data:0x{raw.status:08x}"
            return None

        self._error = None
        return PackageEnergySample(
            energy_pwh=raw.first_value,
            monotonic_ns=(start + end) // 2,
            overhead_ns=end - start,
        )

    def close(self):
        if self._query:
            self._pdh.PdhCloseQuery(self._query)
        self._query = wintypes.HANDLE()
        self._counter = wintypes.HANDLE()

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        self.close()


def package_energy_delta(begin, end):
    """Calculate gross CPU-package energy for the bracket, in Wh."""
    measurement = {
        "meter_status": "unavailable",
        "package_energy_wh": None,
        "sample_overhead_ms": None,
        "elapsed_s": None,
    }
    if begin is None or end is None:
        return measurement

    measurement["sample_overhead_ms"] = (
        begin.overhead_ns + end.overhead_ns
    ) / 1_000_000
    measurement["elapsed_s"] = (end.monotonic_ns - begin.monotonic_ns) / 1e9
    if measurement["elapsed_s"] <= 0:
        measurement["meter_status"] = "invalid_interval"
        return measurement

    energy_pwh = end.energy_pwh - begin.energy_pwh
    if energy_pwh < 0:
        measurement["meter_status"] = "counter_reset"
        return measurement

    measurement["meter_status"] = "ok"
    measurement["package_energy_wh"] = energy_pwh / _PWH_PER_WH
    return measurement