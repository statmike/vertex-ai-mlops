"""Assess whether a source image is suitable for deterministic CV preprocessing."""

import base64
import logging

import cv2
import numpy as np
from google.adk import tools

from .util_common import log_tool_error

logger = logging.getLogger(__name__)


async def assess_image(tool_context: tools.ToolContext) -> str:
    """
    Assess whether the source image is suitable for deterministic CV preprocessing.

    Computes quick heuristics — contrast ratio, edge density, noise level, and
    color distribution — to decide if OpenCV contour detection is likely to
    produce meaningful results.

    Args:
        tool_context: The ADK tool context containing the source image in state.

    Returns:
        A summary of the assessment including suitability level ("high", "medium",
        or "low"), reasoning, and recommended detection parameters.
    """
    try:
        source_image_b64 = tool_context.state.get("source_image")
        if not source_image_b64:
            return "Error: No source image loaded. Use load_image first."

        image_bytes = base64.b64decode(source_image_b64)
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            return "Error: Could not decode image for CV assessment."

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # --- Contrast ratio (std of intensity) ---
        intensity_std = float(np.std(gray))

        # --- Edge density (fraction of edge pixels via Canny) ---
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.count_nonzero(edges)) / (h * w)

        # --- Noise level (Laplacian variance — high = sharp, low = blurry/noisy) ---
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # --- Color distribution (number of dominant colors via k-means on a sample) ---
        sample_pixels = img.reshape(-1, 3)
        # Subsample for speed
        if len(sample_pixels) > 10000:
            indices = np.random.default_rng(42).choice(len(sample_pixels), 10000, replace=False)
            sample_pixels = sample_pixels[indices]
        sample_pixels = np.float32(sample_pixels)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(sample_pixels, 8, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
        # Count clusters with >5% representation
        unique, counts = np.unique(labels, return_counts=True)
        significant_colors = int(np.sum(counts > len(labels) * 0.05))

        # --- Suitability decision ---
        reasons = []
        score = 0

        # High contrast = good for thresholding
        if intensity_std > 60:
            score += 2
            reasons.append(f"high contrast (std={intensity_std:.0f})")
        elif intensity_std > 35:
            score += 1
            reasons.append(f"moderate contrast (std={intensity_std:.0f})")
        else:
            reasons.append(f"low contrast (std={intensity_std:.0f})")

        # Moderate edge density = structured diagram
        if 0.02 < edge_density < 0.25:
            score += 2
            reasons.append(f"structured edges (density={edge_density:.3f})")
        elif edge_density <= 0.02:
            score += 1
            reasons.append(f"sparse edges (density={edge_density:.3f})")
        else:
            reasons.append(f"very dense edges (density={edge_density:.3f}) — may be photographic")

        # Sharp edges = clean line art
        if laplacian_var > 500:
            score += 2
            reasons.append(f"sharp edges (laplacian_var={laplacian_var:.0f})")
        elif laplacian_var > 100:
            score += 1
            reasons.append(f"moderate sharpness (laplacian_var={laplacian_var:.0f})")
        else:
            reasons.append(f"blurry/noisy (laplacian_var={laplacian_var:.0f})")

        # Few dominant colors = diagram-like
        if significant_colors <= 4:
            score += 2
            reasons.append(f"few colors ({significant_colors} dominant)")
        elif significant_colors <= 6:
            score += 1
            reasons.append(f"moderate colors ({significant_colors} dominant)")
        else:
            reasons.append(f"many colors ({significant_colors} dominant) — may be photographic")

        # Map score to suitability
        if score >= 6:
            suitability = "high"
        elif score >= 4:
            suitability = "medium"
        else:
            suitability = "low"

        # Recommend parameters based on assessment
        recommended_params = {
            "binary_threshold": "adaptive",
            "min_contour_area": 500,
            "approx_epsilon": 0.02,
            "morphology_kernel": 3,
        }
        if edge_density > 0.15:
            recommended_params["min_contour_area"] = 800
            recommended_params["morphology_kernel"] = 5
        elif edge_density < 0.03:
            recommended_params["min_contour_area"] = 300

        # Store assessment in state
        assessment = {
            "suitability": suitability,
            "score": score,
            "metrics": {
                "intensity_std": round(intensity_std, 1),
                "edge_density": round(edge_density, 4),
                "laplacian_var": round(laplacian_var, 1),
                "significant_colors": significant_colors,
            },
            "recommended_params": recommended_params,
        }
        tool_context.state["cv_assessment"] = assessment

        reason_str = "; ".join(reasons)

        return (
            f"Image assessment complete.\n"
            f"  Suitability: {suitability} (score {score}/8)\n"
            f"  Reasons: {reason_str}\n"
            f"  Recommended params: {recommended_params}\n\n"
            f"{'Proceed with detect_elements using recommended params.'if suitability != 'low' else 'Suitability is low — call report_results with status \"skipped\" to return to the main agent.'}"
        )

    except Exception as e:
        return log_tool_error("assess_image", e)
