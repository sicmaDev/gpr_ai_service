import logging
from typing import Any


def trace_info(
    logger: logging.Logger,
    trace_id: str | None,
    event: str,
    **fields: Any,
) -> None:
    lines = [
        f"[trace_id={trace_id or '-'}] {event}",
        *[
            f"  {key}={value!r}"
            for key, value in fields.items()
        ],
    ]
    logger.info("\n" + "\n".join(lines))


def trace_warning(
    logger: logging.Logger,
    trace_id: str | None,
    event: str,
    **fields: Any,
) -> None:
    lines = [
        f"[trace_id={trace_id or '-'}] {event}",
        *[
            f"  {key}={value!r}"
            for key, value in fields.items()
        ],
    ]
    logger.warning("\n" + "\n".join(lines))
