"""
analysis — Physics analysis pipeline.

Subsystem responsibilities:
  • histogram_engine: flexible 1D/2D binned accumulation
  • invariant_mass: di-object mass spectrum computation
  • likelihood_analysis: binned extended ML fit, profile likelihood ratio
  • signal_background_model: Gaussian signal + polynomial background
  • significance_test: Asimov formula, p-value → σ conversion

Output: AnalysisResult objects describing measurements and discoveries.
"""

from __future__ import annotations

import math
from statistics import NormalDist
import uuid
from typing import Callable

import numpy as np

try:  # pragma: no cover - optional dependency in local environments
    from scipy import optimize, stats
except ModuleNotFoundError:  # pragma: no cover - exercised through fallback execution
    optimize = None
    stats = None

from simulation_core.core_models.models import (
    ReconstructedEvent,
    AnalysisResult,
)



class Histogram1D:
    """
    1D histogram with fixed-width bins.
    Supports fill(), overflow/underflow tracking, and basic statistics.
    """

    def __init__(self, name: str, n_bins: int, x_min: float, x_max: float):
        self.name = name
        self.n_bins = n_bins
        self.x_min = x_min
        self.x_max = x_max
        self.bin_width = (x_max - x_min) / n_bins
        self.counts = np.zeros(n_bins, dtype=np.float64)
        self.sumw2  = np.zeros(n_bins, dtype=np.float64)  # sum of weight²
        self.overflow = 0.0
        self.underflow = 0.0
        self.n_entries = 0

    def fill(self, value: float, weight: float = 1.0) -> None:
        self.n_entries += 1
        if value < self.x_min:
            self.underflow += weight
            return
        if value >= self.x_max:
            self.overflow += weight
            return
        idx = int((value - self.x_min) / self.bin_width)
        idx = min(idx, self.n_bins - 1)
        self.counts[idx] += weight
        self.sumw2[idx]  += weight * weight

    def fill_many(self, values: list[float], weights: list[float] = None) -> None:
        if weights is None:
            weights = [1.0] * len(values)
        for v, w in zip(values, weights):
            self.fill(v, w)

    def bin_centers(self) -> np.ndarray:
        return np.linspace(self.x_min + self.bin_width/2,
                           self.x_max - self.bin_width/2, self.n_bins)

    def bin_errors(self) -> np.ndarray:
        return np.sqrt(self.sumw2)

    def integral(self) -> float:
        return float(np.sum(self.counts))

    def mean(self) -> float:
        centers = self.bin_centers()
        total = float(np.sum(self.counts))
        if total == 0:
            return 0.0
        return float(np.sum(centers * self.counts) / total)

    def rms(self) -> float:
        centers = self.bin_centers()
        total = float(np.sum(self.counts))
        if total == 0:
            return 0.0
        mean = self.mean()
        return float(math.sqrt(np.sum(self.counts * (centers - mean)**2) / total))

    def peak_bin(self) -> tuple[int, float]:
        """Return (bin_index, peak_value) of the maximum bin."""
        idx = int(np.argmax(self.counts))
        return idx, self.bin_centers()[idx]

    def normalize(self) -> "Histogram1D":
        """Return a new normalised histogram (area = 1)."""
        h = Histogram1D(self.name + "_norm", self.n_bins, self.x_min, self.x_max)
        total = self.integral()
        if total > 0:
            h.counts = self.counts / (total * self.bin_width)
        return h

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "bin_centers": self.bin_centers().tolist(),
            "counts": self.counts.tolist(),
            "errors": self.bin_errors().tolist(),
            "x_min": self.x_min,
            "x_max": self.x_max,
            "n_entries": self.n_entries,
            "mean": self.mean(),
            "rms": self.rms(),
        }


class Histogram2D:
    """2D histogram: η vs φ, pT vs mass, etc."""

    def __init__(self, name: str, nx: int, x_min: float, x_max: float,
                 ny: int, y_min: float, y_max: float):
        self.name = name
        self.nx, self.x_min, self.x_max = nx, x_min, x_max
        self.ny, self.y_min, self.y_max = ny, y_min, y_max
        self.dx = (x_max - x_min) / nx
        self.dy = (y_max - y_min) / ny
        self.counts = np.zeros((nx, ny), dtype=np.float64)

    def fill(self, x: float, y: float, weight: float = 1.0) -> None:
        if x < self.x_min or x >= self.x_max: return
        if y < self.y_min or y >= self.y_max: return
        xi = min(int((x - self.x_min) / self.dx), self.nx - 1)
        yi = min(int((y - self.y_min) / self.dy), self.ny - 1)
        self.counts[xi, yi] += weight


class HistogramEngine:
    """Registry of named histograms for a run."""

    def __init__(self):
        self._histograms: dict[str, Histogram1D] = {}

    def book(self, name: str, n_bins: int, x_min: float, x_max: float) -> Histogram1D:
        h = Histogram1D(name, n_bins, x_min, x_max)
        self._histograms[name] = h
        return h

    def fill(self, name: str, value: float, weight: float = 1.0) -> None:
        if name in self._histograms:
            self._histograms[name].fill(value, weight)

    def get(self, name: str) -> Histogram1D | None:
        return self._histograms.get(name)

    def all_histograms(self) -> dict[str, Histogram1D]:
        return dict(self._histograms)



def di_object_invariant_mass(
    e1: float, p1: tuple[float, float, float],
    e2: float, p2: tuple[float, float, float],
) -> float:
    """Compute invariant mass m_inv = √((E1+E2)² − (p1+p2)²) in GeV."""
    e_sum = e1 + e2
    px = p1[0] + p2[0]
    py = p1[1] + p2[1]
    pz = p1[2] + p2[2]
    m2 = e_sum**2 - px**2 - py**2 - pz**2
    return math.sqrt(max(0.0, m2))


def all_pair_masses(
    objects: list[tuple[float, tuple[float, float, float]]],
) -> list[float]:
    """
    Compute invariant masses for all unique pairs.

    Args:
        objects: list of (energy_gev, (px, py, pz)) tuples

    Returns:
        List of invariant masses in GeV.
    """
    masses = []
    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            e1, p1 = objects[i]
            e2, p2 = objects[j]
            masses.append(di_object_invariant_mass(e1, p1, e2, p2))
    return masses


def compute_invariant_mass_spectrum(
    events: list[ReconstructedEvent],
    histogram: Histogram1D,
    min_jets: int = 2,
) -> Histogram1D:
    """
    Fill a histogram with di-jet invariant mass from all reconstructed events.

    Args:
        events: list of ReconstructedEvent objects
        histogram: pre-booked Histogram1D to fill
        min_jets: minimum number of jets required per event

    Returns:
        The filled histogram.
    """
    for event in events:
        if len(event.jets) < min_jets:
            continue

        # Leading two jets
        j1 = event.jets[0]
        j2 = event.jets[1]

        m = di_object_invariant_mass(
            j1.energy_gev, j1.momentum,
            j2.energy_gev, j2.momentum,
        )
        histogram.fill(m)

    return histogram



def gaussian_signal(x: float, mu: float, sigma: float, amplitude: float) -> float:
    """Gaussian signal: A × exp(−(x−μ)² / (2σ²))."""
    if sigma <= 0:
        return 0.0
    return amplitude * math.exp(-0.5 * ((x - mu) / sigma)**2)


def exponential_background(x: float, norm: float, slope: float) -> float:
    """Exponential background: N × exp(−slope × x)."""
    return norm * math.exp(-slope * x)


def polynomial_background(x: float, coefficients: list[float]) -> float:
    """Polynomial background: Σ c_i × x^i."""
    return sum(c * x**i for i, c in enumerate(coefficients))


def signal_plus_background(
    x: float,
    mu: float,
    sigma: float,
    n_signal: float,
    n_background: float,
    bg_slope: float,
) -> float:
    """
    Combined signal + exponential background model.
    Normalised so that integral ≈ n_signal + n_background.
    """
    sig = gaussian_signal(x, mu, sigma, n_signal)
    bg  = exponential_background(x, n_background, bg_slope)
    return sig + bg



def poisson_log_likelihood(
    observed: np.ndarray,
    expected: np.ndarray,
) -> float:
    """
    Binned Poisson log-likelihood:
        ln L = Σ [n_i × ln(μ_i) − μ_i]

    (Constant terms omitted as they cancel in ratios.)
    """
    safe_exp = np.clip(expected, 1e-10, None)
    ll = np.sum(observed * np.log(safe_exp) - safe_exp)
    return float(ll)


def chi_squared(observed: np.ndarray, expected: np.ndarray) -> float:
    """χ² = Σ (obs − exp)² / exp."""
    mask = expected > 0
    return float(np.sum((observed[mask] - expected[mask])**2 / expected[mask]))


class LikelihoodFitter:
    """
    Binned extended maximum-likelihood fitter for signal + background.

    Fits the model μ(x | μ_sig, σ_sig, n_sig, n_bg, λ) to observed histogram counts.
    Uses scipy.optimize.minimize with the BFGS method.
    """

    def __init__(self, histogram: Histogram1D):
        self.histogram = histogram
        self.result: Dict | None = None

    def fit(
        self,
        mu_init: float,
        sigma_init: float,
        n_sig_init: float = None,
        n_bg_init: float = None,
        bg_slope_init: float = 0.01,
    ) -> Dict:
        """
        Run the maximum-likelihood fit.

        Returns:
            dict with keys: mu, sigma, n_signal, n_background, bg_slope,
                            log_likelihood, chi2_ndf, success
        """
        obs = self.histogram.counts
        centers = self.histogram.bin_centers()
        bw = self.histogram.bin_width
        total = float(np.sum(obs))

        if n_sig_init is None:
            n_sig_init = total * 0.1
        if n_bg_init is None:
            n_bg_init = total * 0.9

        def neg_ll(params):
            mu, sigma, n_sig, n_bg, slope = params
            if sigma <= 0 or n_sig < 0 or n_bg < 0:
                return 1e18
            expected = np.array([
                signal_plus_background(x, mu, sigma, n_sig, n_bg, slope) * bw
                for x in centers
            ])
            return -poisson_log_likelihood(obs, expected)

        x0 = [mu_init, sigma_init, n_sig_init, n_bg_init, bg_slope_init]
        bounds = [
            (self.histogram.x_min, self.histogram.x_max),
            (0.001, self.histogram.x_max - self.histogram.x_min),
            (0, None),
            (0, None),
            (1e-6, 10.0),
        ]

        try:
            if optimize is not None:
                res = optimize.minimize(
                    neg_ll,
                    x0,
                    method="L-BFGS-B",
                    bounds=bounds,
                    options={"maxiter": 1000, "ftol": 1e-10},
                )
            else:
                res = _fallback_minimize(neg_ll, x0, bounds)
        except Exception as e:
            return {"success": False, "error": str(e)}

        mu, sigma, n_sig, n_bg, slope = res.x
        expected = np.array([
            signal_plus_background(x, mu, sigma, n_sig, n_bg, slope) * bw
            for x in centers
        ])
        chi2 = chi_squared(obs, expected)
        ndf = max(1, self.histogram.n_bins - 5)

        self.result = {
            "success": res.success,
            "mu_gev": float(mu),
            "sigma_gev": float(sigma),
            "n_signal": float(n_sig),
            "n_background": float(n_bg),
            "bg_slope": float(slope),
            "log_likelihood": float(-res.fun),
            "chi2_ndf": float(chi2 / ndf),
        }
        return self.result



def profile_likelihood_significance(n_signal: float, n_background: float) -> float:
    """
    Asimov formula for discovery significance:
        Z = √[ 2 × ((s+b) × ln(1 + s/b) − s) ]

    Valid when s/b is not too large.
    """
    if n_background <= 0 or n_signal <= 0:
        return 0.0
    sb = n_signal + n_background
    z2 = 2.0 * (sb * math.log(1.0 + n_signal / n_background) - n_signal)
    return math.sqrt(max(0.0, z2))


def simple_significance(n_signal: float, n_background: float) -> float:
    """Simple S/√B significance estimate."""
    if n_background <= 0:
        return 0.0
    return n_signal / math.sqrt(n_background)


def sigma_to_pvalue(sigma: float) -> float:
    """Convert significance σ to one-sided p-value using the normal distribution."""
    if stats is not None:
        return float(stats.norm.sf(sigma))
    return 1.0 - NormalDist().cdf(sigma)


def pvalue_to_sigma(p_value: float) -> float:
    """Convert one-sided p-value to significance σ."""
    if p_value <= 0:
        return float("inf")
    if stats is not None:
        return float(stats.norm.isf(p_value))
    return float(NormalDist().inv_cdf(1.0 - p_value))


class _FallbackOptimizeResult:
    def __init__(self, x: list[float], fun: float):
        self.x = np.array(x, dtype=np.float64)
        self.fun = float(fun)
        self.success = True


def _fallback_minimize(
    objective: Callable[[list[float]], float],
    x0: list[float],
    bounds: list[tuple[float | None, float | None]],
) -> _FallbackOptimizeResult:
    """Bounded coordinate search used when scipy is unavailable."""
    current = list(x0)
    best = objective(current)

    for _ in range(12):
        improved = False
        for index, (lower, upper) in enumerate(bounds):
            lower = current[index] if lower is None else lower
            upper = current[index] if upper is None else upper
            if upper <= lower:
                continue
            span = upper - lower
            step = max(span / 8.0, 1e-6)
            candidates = []
            for delta in (-step, -0.5 * step, 0.5 * step, step):
                value = min(upper, max(lower, current[index] + delta))
                candidate = list(current)
                candidate[index] = value
                candidates.append(candidate)
            for candidate in candidates:
                score = objective(candidate)
                if score < best:
                    current = candidate
                    best = score
                    improved = True
        if not improved:
            break

    return _FallbackOptimizeResult(current, best)



class PhysicsAnalyser:
    """
    Full physics analysis pipeline.

    Processes a batch of ReconstructedEvents and returns AnalysisResult objects
    for each analysis type requested.
    """

    def __init__(
        self,
        mass_range_gev: tuple[float, float] = (0.0, 500.0),
        n_mass_bins: int = 50,
        higgs_mass_gev: float = 125.1,
    ):
        self.mass_range = mass_range_gev
        self.n_mass_bins = n_mass_bins
        self.higgs_mass_gev = higgs_mass_gev
        self.engine = HistogramEngine()

        # Pre-book standard histograms
        self.h_dijet_mass = self.engine.book(
            "dijet_invariant_mass", n_mass_bins, mass_range_gev[0], mass_range_gev[1]
        )
        self.h_jet_pt  = self.engine.book("leading_jet_pt",  50, 0.0, 1000.0)
        self.h_n_jets  = self.engine.book("n_jets",          15, 0.0,   15.0)
        self.h_met     = self.engine.book("met",             50, 0.0,  500.0)
        self.h_n_tracks= self.engine.book("n_tracks",        30, 0.0,   30.0)

    def analyse_events(self, events: list[ReconstructedEvent]) -> list[AnalysisResult]:
        """
        Run all analysis modules on a batch of reconstructed events.

        Returns:
            List of AnalysisResult objects.
        """
        results = []

        # Fill standard histograms
        for event in events:
            self.h_n_jets.fill(float(event.n_jets))
            self.h_met.fill(event.met_gev)
            self.h_n_tracks.fill(float(event.n_tracks))
            if event.jets:
                self.h_jet_pt.fill(event.jets[0].pt_gev)

        # Invariant mass spectrum
        compute_invariant_mass_spectrum(events, self.h_dijet_mass, min_jets=2)
        results.append(self._result_from_histogram(self.h_dijet_mass, "invariant_mass"))

        # Fit the mass spectrum
        if self.h_dijet_mass.n_entries >= 10:
            fit_result = self._fit_mass_spectrum()
            if fit_result:
                results.append(fit_result)

        # Summary statistics
        results.append(self._summary_analysis(events))

        return results

    def _result_from_histogram(self, h: Histogram1D, analysis_type: str) -> AnalysisResult:
        return AnalysisResult(
            result_id=str(uuid.uuid4())[:8],
            analysis_type=analysis_type,
            value=h.mean(),
            uncertainty=h.rms() / math.sqrt(max(1, h.n_entries)),
            units="GeV",
            histogram_bins=h.bin_centers().tolist(),
            histogram_counts=h.counts.tolist(),
            significance_sigma=0.0,
            metadata=h.as_dict(),
        )

    def _fit_mass_spectrum(self) -> AnalysisResult | None:
        """Fit the di-jet mass histogram with signal + background model."""
        fitter = LikelihoodFitter(self.h_dijet_mass)
        mu_init = self.higgs_mass_gev
        sigma_init = 5.0
        fit = fitter.fit(mu_init, sigma_init)

        if not fit.get("success", False):
            return None

        n_sig = fit["n_signal"]
        n_bg  = fit["n_background"]
        sigma = profile_likelihood_significance(n_sig, n_bg)

        return AnalysisResult(
            result_id=str(uuid.uuid4())[:8],
            analysis_type="mass_spectrum_fit",
            value=fit["mu_gev"],
            uncertainty=fit["sigma_gev"],
            units="GeV",
            significance_sigma=sigma,
            metadata={
                **fit,
                "p_value": sigma_to_pvalue(sigma),
            },
        )

    def _summary_analysis(self, events: list[ReconstructedEvent]) -> AnalysisResult:
        """Compute summary statistics across all events."""
        n = len(events)
        mean_jets = sum(e.n_jets for e in events) / max(n, 1)
        mean_met  = sum(e.met_gev for e in events) / max(n, 1)

        return AnalysisResult(
            result_id=str(uuid.uuid4())[:8],
            analysis_type="event_summary",
            value=float(n),
            uncertainty=math.sqrt(float(n)),
            units="events",
            significance_sigma=0.0,
            metadata={
                "n_events": n,
                "mean_n_jets": mean_jets,
                "mean_met_gev": mean_met,
            },
        )
