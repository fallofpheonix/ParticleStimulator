"""Field solver — computes E and B fields at arbitrary positions.

Provides a composable ``FieldConfiguration`` that aggregates contributions
from accelerator magnets, RF cavities, and any external field sources.
Field values are queried per-position and returned as ``(E⃗, B⃗)`` pairs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

from backend.core_math.vector3 import Vector3


# ---------------------------------------------------------------------------
# Field source protocol
# ---------------------------------------------------------------------------


class FieldSource(Protocol):
    """Any object that can provide E and/or B at a given position."""

    def electric_field_at(self, position: Vector3) -> Vector3: ...
    def magnetic_field_at(self, position: Vector3) -> Vector3: ...


# ---------------------------------------------------------------------------
# Built-in uniform field sources
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class UniformElectricField:
    """Constant electric field everywhere."""

    field: Vector3 = Vector3()

    def electric_field_at(self, _position: Vector3) -> Vector3:
        return self.field

    def magnetic_field_at(self, _position: Vector3) -> Vector3:
        return Vector3()


@dataclass(frozen=True, slots=True)
class UniformMagneticField:
    """Constant magnetic field everywhere."""

    field: Vector3 = Vector3()

    def electric_field_at(self, _position: Vector3) -> Vector3:
        return Vector3()

    def magnetic_field_at(self, _position: Vector3) -> Vector3:
        return self.field


# ---------------------------------------------------------------------------
# Composite field configuration
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class FieldConfiguration:
    """Aggregates multiple field sources and provides total (E⃗, B⃗) at any point.

    Usage::

        config = FieldConfiguration()
        config.add_source(UniformMagneticField(Vector3(0, 0, 3.5)))
        config.add_source(my_rf_cavity)
        E, B = config.fields_at(particle_position)
    """

    sources: list[FieldSource] = field(default_factory=list)

    def add_source(self, source: FieldSource) -> None:
        """Register a field source."""
        self.sources.append(source)

    def fields_at(self, position: Vector3) -> tuple[Vector3, Vector3]:
        """Sum contributions from all sources at *position*.

        Returns:
            (electric_field, magnetic_field) tuple of Vector3.
        """
        total_e = Vector3()
        total_b = Vector3()
        for source in self.sources:
            total_e = total_e + source.electric_field_at(position)
            total_b = total_b + source.magnetic_field_at(position)
        return total_e, total_b

    def electric_field_at(self, position: Vector3) -> Vector3:
        """Total electric field."""
        return self.fields_at(position)[0]

    def magnetic_field_at(self, position: Vector3) -> Vector3:
        """Total magnetic field."""
        return self.fields_at(position)[1]


# ---------------------------------------------------------------------------
# Magnetic field map (grid-based interpolation stub)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class MagneticFieldMap:
    """Placeholder for a 3D grid-interpolated magnetic field map.

    Real implementations load precomputed field maps from data files.
    This version stores a single callable for flexibility.
    """

    field_func: Callable[[Vector3], Vector3] = lambda _pos: Vector3()

    def electric_field_at(self, _position: Vector3) -> Vector3:
        return Vector3()

    def magnetic_field_at(self, position: Vector3) -> Vector3:
        return self.field_func(position)
