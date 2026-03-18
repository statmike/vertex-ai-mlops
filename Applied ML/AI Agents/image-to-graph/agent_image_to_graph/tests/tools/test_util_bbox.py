"""Tests for util_bbox: IoU, label similarity, centroid proximity, and CV-to-graph matching."""

import pytest

from agent_image_to_graph.tools.util_bbox import (
    compute_centroid_proximity,
    compute_iou,
    compute_label_similarity,
    detect_schematic_mode,
    fix_oversized_bboxes,
    fix_schematic_bboxes,
    match_cv_to_graph_elements,
)


class TestComputeIoU:
    """Tests for compute_iou."""

    def test_full_overlap(self):
        bbox = [100, 200, 300, 400]
        assert compute_iou(bbox, bbox) == pytest.approx(1.0)

    def test_no_overlap(self):
        a = [0, 0, 100, 100]
        b = [200, 200, 300, 300]
        assert compute_iou(a, b) == pytest.approx(0.0)

    def test_partial_overlap(self):
        a = [0, 0, 200, 200]
        b = [100, 100, 300, 300]
        # Intersection: [100,100,200,200] = 100*100 = 10000
        # Union: 40000 + 40000 - 10000 = 70000
        assert compute_iou(a, b) == pytest.approx(10000 / 70000)

    def test_zero_area(self):
        a = [100, 100, 100, 200]  # zero height
        b = [50, 50, 150, 250]
        assert compute_iou(a, b) == pytest.approx(0.0)


class TestComputeLabelSimilarity:
    """Tests for compute_label_similarity."""

    def test_exact_match(self):
        assert compute_label_similarity("Process", "Process") == pytest.approx(1.0)

    def test_case_insensitive(self):
        assert compute_label_similarity("Foo", "foo") == pytest.approx(1.0)

    def test_partial_match(self):
        score = compute_label_similarity("Process Data", "Process")
        assert 0.3 < score < 1.0

    def test_empty_strings(self):
        assert compute_label_similarity("", "") == pytest.approx(0.0)


class TestComputeCentroidProximity:
    """Tests for compute_centroid_proximity."""

    def test_identical_bboxes(self):
        bbox = [100, 200, 300, 400]
        assert compute_centroid_proximity(bbox, bbox) == pytest.approx(1.0)

    def test_nearby_bboxes(self):
        a = [100, 100, 200, 200]  # center (150, 150)
        b = [110, 110, 210, 210]  # center (160, 160) — distance ~14
        score = compute_centroid_proximity(a, b)
        assert score > 0.95  # very close → near 1.0

    def test_distant_bboxes(self):
        a = [0, 0, 100, 100]      # center (50, 50)
        b = [800, 800, 900, 900]  # center (850, 850) — distance ~1131
        score = compute_centroid_proximity(a, b)
        assert score < 0.01  # very far → near 0.0


class TestMatchCvToGraphElements:
    """Tests for match_cv_to_graph_elements."""

    def test_nudge_high_overlap_same_label(self):
        """High IoU + matching text → nudge."""
        cv_elements = [
            {"text": "Start", "bounding_box": [50, 400, 125, 605]},
        ]
        graph_nodes = [
            {"id": "n1", "label": "Start", "shape": "oval", "bounding_box": [55, 410, 120, 600]},
        ]
        matches = match_cv_to_graph_elements(cv_elements, graph_nodes)
        assert len(matches) == 1
        assert matches[0]["action"] == "nudge"
        assert matches[0]["node_id"] == "n1"

    def test_nudge_reads_text_field(self):
        """CV elements use 'text' not 'label' — matching must read 'text'."""
        cv_elements = [
            {"text": "Holiday Adjustment", "bounding_box": [86, 346, 168, 459]},
        ]
        graph_nodes = [
            {"id": "n1", "label": "Holiday Adjustment", "shape": "rectangle",
             "bounding_box": [90, 350, 170, 460]},
        ]
        matches = match_cv_to_graph_elements(cv_elements, graph_nodes)
        assert len(matches) == 1
        assert matches[0]["label_score"] > 0.9
        assert matches[0]["action"] == "nudge"

    def test_flag_low_overlap_different_label(self):
        """Low IoU + different label + far apart → flag."""
        cv_elements = [
            {"text": "XYZ", "bounding_box": [800, 800, 900, 900]},
        ]
        graph_nodes = [
            {"id": "n1", "label": "Start", "shape": "oval", "bounding_box": [50, 50, 150, 150]},
        ]
        matches = match_cv_to_graph_elements(cv_elements, graph_nodes)
        assert len(matches) == 1
        assert matches[0]["action"] == "flag"

    def test_skip_groups(self):
        """Group nodes (shape=group_rectangle) are excluded from matching."""
        cv_elements = [
            {"text": "Group", "bounding_box": [0, 0, 500, 500]},
        ]
        graph_nodes = [
            {"id": "g1", "label": "Group", "shape": "group_rectangle", "bounding_box": [0, 0, 500, 500]},
        ]
        matches = match_cv_to_graph_elements(cv_elements, graph_nodes)
        assert len(matches) == 0

    def test_one_to_one_matching(self):
        """Each CV element is matched to at most one node (and vice versa)."""
        cv_elements = [
            {"text": "A", "bounding_box": [0, 0, 100, 100]},
            {"text": "B", "bounding_box": [200, 200, 300, 300]},
        ]
        graph_nodes = [
            {"id": "n1", "label": "A", "shape": "rectangle", "bounding_box": [5, 5, 95, 95]},
            {"id": "n2", "label": "B", "shape": "rectangle", "bounding_box": [205, 205, 295, 295]},
        ]
        matches = match_cv_to_graph_elements(cv_elements, graph_nodes)
        matched_node_ids = [m["node_id"] for m in matches]
        matched_cv_indices = [m["cv_index"] for m in matches]
        assert len(set(matched_node_ids)) == len(matched_node_ids)
        assert len(set(matched_cv_indices)) == len(matched_cv_indices)

    def test_fallback_to_label_field(self):
        """Falls back to 'label' field when 'text' is absent (backwards compat)."""
        cv_elements = [
            {"label": "Start", "bounding_box": [50, 400, 125, 605]},
        ]
        graph_nodes = [
            {"id": "n1", "label": "Start", "shape": "oval", "bounding_box": [55, 410, 120, 600]},
        ]
        matches = match_cv_to_graph_elements(cv_elements, graph_nodes)
        assert len(matches) == 1
        assert matches[0]["label_score"] > 0.9

    def test_skip_partial_contour(self):
        """CV bbox much smaller than graph bbox → skip (partial contour)."""
        cv_elements = [
            # Partial contour: only 18 units tall vs node's 81
            {"text": "Trend Component", "bounding_box": [811, 619, 829, 700]},
        ]
        graph_nodes = [
            {"id": "n1", "label": "Trend Component", "shape": "cylinder",
             "bounding_box": [790, 619, 900, 700]},
        ]
        matches = match_cv_to_graph_elements(cv_elements, graph_nodes)
        assert len(matches) == 1
        assert matches[0]["action"] == "skip"
        assert matches[0]["area_ratio"] < 0.3

    def test_skip_oversized_contour(self):
        """CV bbox much larger than graph bbox → skip (merged contour)."""
        cv_elements = [
            # Merged contour: 4x the area
            {"text": "Start", "bounding_box": [0, 0, 400, 400]},
        ]
        graph_nodes = [
            {"id": "n1", "label": "Start", "shape": "oval",
             "bounding_box": [50, 50, 150, 150]},
        ]
        matches = match_cv_to_graph_elements(cv_elements, graph_nodes)
        assert len(matches) == 1
        assert matches[0]["action"] != "nudge"


class TestDetectSchematicMode:
    """Tests for detect_schematic_mode."""

    def test_detect_schematic_mode_by_type(self):
        """diagram_type containing 'schematic' triggers detection."""
        graph = {"diagram_type": "Schematic"}
        nodes = [{"id": "n1", "bounding_box": [100, 100, 200, 200]}]
        assert detect_schematic_mode(graph, nodes) is True

    def test_detect_schematic_mode_circuit_type(self):
        """diagram_type containing 'circuit' triggers detection."""
        graph = {"diagram_type": "Circuit Diagram"}
        nodes = [{"id": "n1", "bounding_box": [100, 100, 200, 200]}]
        assert detect_schematic_mode(graph, nodes) is True

    def test_detect_schematic_mode_by_pattern(self):
        """Many extreme aspect-ratio bboxes trigger detection even with non-schematic type."""
        graph = {"diagram_type": "other"}
        # 4 of 5 nodes have extreme aspect ratios (>80%)
        nodes = [
            {"id": "n1", "bounding_box": [100, 490, 600, 510]},   # 500:20 = 25:1
            {"id": "n2", "bounding_box": [200, 390, 700, 410]},   # 500:20 = 25:1
            {"id": "n3", "bounding_box": [50, 495, 950, 505]},    # 900:10 = 90:1
            {"id": "n4", "bounding_box": [300, 100, 310, 900]},   # 10:800 = 80:1
            {"id": "n5", "bounding_box": [100, 100, 200, 200]},   # 100:100 = 1:1 (normal)
        ]
        assert detect_schematic_mode(graph, nodes) is True

    def test_detect_schematic_mode_flowchart(self):
        """Normal bboxes with flowchart type returns False."""
        graph = {"diagram_type": "flowchart"}
        nodes = [
            {"id": "n1", "bounding_box": [50, 400, 120, 600]},    # 70:200 ≈ 2.9:1
            {"id": "n2", "bounding_box": [200, 350, 300, 650]},   # 100:300 = 3:1
            {"id": "n3", "bounding_box": [400, 350, 500, 650]},   # 100:300 = 3:1
            {"id": "n4", "bounding_box": [600, 400, 700, 600]},   # 100:200 = 2:1
        ]
        assert detect_schematic_mode(graph, nodes) is False

    def test_detect_schematic_mode_skips_groups(self):
        """Group nodes are excluded from aspect ratio calculation."""
        graph = {"diagram_type": "other"}
        # Only group nodes have extreme ratios; real nodes are normal
        nodes = [
            {"id": "g1", "shape": "group_rectangle", "bounding_box": [0, 490, 1000, 510]},
            {"id": "n1", "bounding_box": [100, 100, 200, 200]},
            {"id": "n2", "bounding_box": [300, 300, 400, 400]},
            {"id": "n3", "bounding_box": [500, 500, 600, 600]},
        ]
        assert detect_schematic_mode(graph, nodes) is False

    def test_detect_schematic_mode_oversized_alone_not_sufficient(self):
        """Oversized bboxes alone do NOT trigger schematic mode (handled by general guard)."""
        graph = {"diagram_type": "other"}
        # 2 of 5 nodes are oversized, but none have extreme aspect ratios
        nodes = [
            {"id": "n1", "bounding_box": [65, 77, 598, 588]},    # 533×511 = 272k (oversized)
            {"id": "n2", "bounding_box": [218, 230, 612, 602]},  # 394×372 = 147k (oversized)
            {"id": "n3", "bounding_box": [100, 100, 130, 130]},  # 30×30 (normal)
            {"id": "n4", "bounding_box": [200, 200, 230, 230]},  # 30×30 (normal)
            {"id": "n5", "bounding_box": [300, 300, 330, 330]},  # 30×30 (normal)
        ]
        assert detect_schematic_mode(graph, nodes) is False


class TestFixSchematicBboxes:
    """Tests for fix_schematic_bboxes."""

    def test_fix_extreme_ratio(self):
        """A 14×500 bbox is normalized to ~84×84."""
        nodes = [{"id": "n1", "bounding_box": [100, 493, 600, 507]}]  # h=500, w=14
        corrections = fix_schematic_bboxes(nodes)
        assert len(corrections) == 1
        assert corrections[0]["node_id"] == "n1"
        new = nodes[0]["bounding_box"]
        new_h = new[2] - new[0]
        new_w = new[3] - new[1]
        # sqrt(500*14) ≈ 83.7 → side = 83
        assert 70 <= new_h <= 100
        assert 70 <= new_w <= 100

    def test_skips_normal_bbox(self):
        """A 100×100 bbox is unchanged."""
        original = [100, 100, 200, 200]
        nodes = [{"id": "n1", "bounding_box": original[:]}]
        corrections = fix_schematic_bboxes(nodes)
        assert len(corrections) == 0
        assert nodes[0]["bounding_box"] == original

    def test_skips_groups(self):
        """Group nodes are never modified."""
        nodes = [{"id": "g1", "shape": "group_rectangle", "bounding_box": [0, 490, 1000, 510]}]
        corrections = fix_schematic_bboxes(nodes)
        assert len(corrections) == 0
        assert nodes[0]["bounding_box"] == [0, 490, 1000, 510]

    def test_preserves_centroid(self):
        """The centroid of the new bbox should be near the centroid of the old bbox."""
        nodes = [{"id": "n1", "bounding_box": [165, 139, 601, 165]}]  # h=436, w=26
        fix_schematic_bboxes(nodes)
        new = nodes[0]["bounding_box"]
        new_cy = (new[0] + new[2]) / 2
        new_cx = (new[1] + new[3]) / 2
        # Original centroid: y=383, x=152
        assert abs(new_cy - 383) <= 1
        assert abs(new_cx - 152) <= 1

    def test_clamps_to_bounds(self):
        """A bbox near the edge is clamped to 0-1000."""
        nodes = [{"id": "n1", "bounding_box": [0, 495, 500, 505]}]  # centroid near y=250
        corrections = fix_schematic_bboxes(nodes)
        assert len(corrections) == 1
        new = nodes[0]["bounding_box"]
        assert all(0 <= v <= 1000 for v in new)

    def test_minimum_side_30(self):
        """Very tiny bboxes get a minimum side of 30."""
        # h=100, w=1 → sqrt(100) = 10 → clamped to 30
        nodes = [{"id": "n1", "bounding_box": [450, 500, 550, 501]}]
        fix_schematic_bboxes(nodes)
        new = nodes[0]["bounding_box"]
        new_h = new[2] - new[0]
        new_w = new[3] - new[1]
        assert new_h >= 30
        assert new_w >= 30

    def test_does_not_fix_oversized_area(self):
        """Oversized-area bboxes are NOT fixed by fix_schematic_bboxes (handled by general guard)."""
        nodes = [
            # Normal component for reference
            {"id": "n1", "bounding_box": [139, 600, 169, 625]},
            # Oversized but NOT extreme ratio (533×511 ≈ 1.04:1)
            {"id": "rail", "bounding_box": [65, 77, 598, 588]},
        ]
        corrections = fix_schematic_bboxes(nodes)
        assert len(corrections) == 0  # no extreme ratios → nothing to fix
        assert nodes[1]["bounding_box"] == [65, 77, 598, 588]  # unchanged


class TestFixOversizedBboxes:
    """Tests for fix_oversized_bboxes."""

    def test_fix_oversized_bbox(self):
        """An oversized bbox (>10% of image area) is shrunk to reference size."""
        nodes = [
            # Normal component for reference: 30×25 = 750 area
            {"id": "n1", "bounding_box": [139, 600, 169, 625]},
            # Oversized: 533×511 = 272,363 area (27% of image)
            {"id": "rail", "bounding_box": [65, 77, 598, 588]},
        ]
        corrections = fix_oversized_bboxes(nodes)
        assert len(corrections) == 1
        assert corrections[0]["node_id"] == "rail"
        # n1 should be unchanged
        assert nodes[0]["bounding_box"] == [139, 600, 169, 625]
        # rail should be shrunk to component-sized
        new = nodes[1]["bounding_box"]
        new_h = new[2] - new[0]
        new_w = new[3] - new[1]
        assert new_h < 100  # was 533
        assert new_w < 100  # was 511
        # Centroid preserved: original centroid y=331.5, x=332.5
        new_cy = (new[0] + new[2]) / 2
        new_cx = (new[1] + new[3]) / 2
        assert abs(new_cy - 331.5) <= 1
        assert abs(new_cx - 332.5) <= 1

    def test_uses_median_reference(self):
        """Oversized bbox target side comes from median of normal components."""
        nodes = [
            # 3 normal components: areas 900, 2500, 10000
            {"id": "n1", "bounding_box": [100, 100, 130, 130]},   # 30×30 = 900
            {"id": "n2", "bounding_box": [200, 200, 250, 250]},   # 50×50 = 2500
            {"id": "n3", "bounding_box": [300, 300, 400, 400]},   # 100×100 = 10000
            # Oversized
            {"id": "rail", "bounding_box": [0, 0, 600, 600]},     # 600×600 = 360,000
        ]
        corrections = fix_oversized_bboxes(nodes)
        assert len(corrections) == 1
        new = nodes[3]["bounding_box"]
        new_side = new[2] - new[0]
        # Median area = 2500 (middle of [900, 2500, 10000]) → side = sqrt(2500) = 50
        assert 45 <= new_side <= 55

    def test_skips_normal_nodes(self):
        """Bboxes under 10% area are not modified at default threshold."""
        # 100×100 = 10,000 (1% of image) — should NOT be fixed
        original = [100, 100, 200, 200]
        nodes = [{"id": "n1", "bounding_box": original[:]}]
        corrections = fix_oversized_bboxes(nodes)
        assert len(corrections) == 0
        assert nodes[0]["bounding_box"] == original

    def test_skips_groups(self):
        """Group nodes are never modified."""
        nodes = [{"id": "g1", "shape": "group_rectangle", "bounding_box": [0, 0, 800, 800]}]
        corrections = fix_oversized_bboxes(nodes)
        assert len(corrections) == 0
        assert nodes[0]["bounding_box"] == [0, 0, 800, 800]

    def test_custom_threshold(self):
        """Lower threshold catches smaller oversized bboxes."""
        nodes = [
            {"id": "n1", "bounding_box": [100, 100, 130, 130]},   # 30×30 = 900 (normal)
            # 250×250 = 62,500 → 6.25% of image: below 10% but above 5%
            {"id": "n2", "bounding_box": [200, 200, 450, 450]},
        ]
        # Default threshold (10%) → no fix
        corrections_10 = fix_oversized_bboxes(
            [{"id": n["id"], "bounding_box": n["bounding_box"][:]} for n in nodes]
        )
        assert len(corrections_10) == 0
        # 5% threshold → catches n2
        corrections_5 = fix_oversized_bboxes(nodes, area_threshold=0.05)
        assert len(corrections_5) == 1
        assert corrections_5[0]["node_id"] == "n2"

    def test_preserves_centroid(self):
        """The centroid of the new bbox should be near the centroid of the old bbox."""
        nodes = [
            {"id": "n1", "bounding_box": [100, 100, 130, 130]},   # normal reference
            {"id": "n2", "bounding_box": [200, 300, 600, 700]},   # 400×400 = 160k (oversized)
        ]
        fix_oversized_bboxes(nodes)
        new = nodes[1]["bounding_box"]
        new_cy = (new[0] + new[2]) / 2
        new_cx = (new[1] + new[3]) / 2
        # Original centroid: y=400, x=500
        assert abs(new_cy - 400) <= 1
        assert abs(new_cx - 500) <= 1

    def test_default_reference_when_no_normals(self):
        """When all nodes are oversized, uses default reference_side=50."""
        nodes = [
            {"id": "n1", "bounding_box": [0, 0, 500, 500]},     # 250k (oversized)
            {"id": "n2", "bounding_box": [100, 100, 600, 600]},  # 250k (oversized)
        ]
        corrections = fix_oversized_bboxes(nodes)
        assert len(corrections) == 2
        # Both should use default side=50
        for node in nodes:
            h = node["bounding_box"][2] - node["bounding_box"][0]
            assert h == 50

    def test_extreme_ratio_triggers_fix(self):
        """Node with 40:1 ratio but small area gets fixed."""
        nodes = [
            # Normal references
            {"id": "n1", "bounding_box": [100, 100, 184, 192]},  # 84×92 = 7728
            {"id": "n2", "bounding_box": [300, 100, 384, 192]},  # 84×92 = 7728
            {"id": "n3", "bounding_box": [500, 100, 584, 192]},  # 84×92 = 7728
            # Extreme ratio: h=5, w=201, area=1005 (0.1% of image — under area threshold)
            {"id": "spike", "bounding_box": [341, 258, 346, 459]},
        ]
        corrections = fix_oversized_bboxes(nodes)
        assert len(corrections) == 1
        assert corrections[0]["node_id"] == "spike"
        new = nodes[3]["bounding_box"]
        new_h = new[2] - new[0]
        new_w = new[3] - new[1]
        # Should be shrunk to reference_side (~87)
        assert new_h < 100
        assert new_w < 100

    def test_outlier_dimension_triggers_fix(self):
        """Node with one large dimension (>4x median side) gets fixed."""
        nodes = [
            # Normal references: 84×92 each, median area ≈ 7728, reference_side ≈ 87
            # max_dim_limit = min(350, 4*87) = 348
            {"id": "n1", "bounding_box": [100, 100, 184, 192]},
            {"id": "n2", "bounding_box": [300, 100, 384, 192]},
            {"id": "n3", "bounding_box": [500, 100, 584, 192]},
            # Large y-span: h=401, w=174, area=69,774 (7% — under 10% threshold)
            # ratio = 401/174 ≈ 2.3 (under 8:1), but max dim 401 > 348
            {"id": "big", "bounding_box": [17, 113, 418, 287]},
        ]
        corrections = fix_oversized_bboxes(nodes)
        assert len(corrections) == 1
        assert corrections[0]["node_id"] == "big"
        new = nodes[3]["bounding_box"]
        new_h = new[2] - new[0]
        assert new_h < 100

    def test_moderate_ratio_not_fixed(self):
        """Node with 3:1 ratio is NOT fixed (under 8:1 threshold)."""
        nodes = [
            {"id": "n1", "bounding_box": [100, 100, 184, 192]},
            {"id": "n2", "bounding_box": [300, 100, 384, 192]},
            {"id": "n3", "bounding_box": [500, 100, 584, 192]},
            # 3:1 ratio: h=150, w=50, area=7500
            {"id": "mod", "bounding_box": [200, 300, 350, 350]},
        ]
        corrections = fix_oversized_bboxes(nodes)
        assert len(corrections) == 0

    def test_moderate_dimension_not_fixed(self):
        """Node with max dim slightly under limit is NOT fixed."""
        nodes = [
            # reference_side ≈ 87, max_dim_limit = min(350, 4*87) = 348
            {"id": "n1", "bounding_box": [100, 100, 184, 192]},
            {"id": "n2", "bounding_box": [300, 100, 384, 192]},
            {"id": "n3", "bounding_box": [500, 100, 584, 192]},
            # h=275 (< 348), w=82, area=22,550, ratio ≈ 3.4:1
            {"id": "tall", "bounding_box": [100, 400, 375, 482]},
        ]
        corrections = fix_oversized_bboxes(nodes)
        assert len(corrections) == 0
