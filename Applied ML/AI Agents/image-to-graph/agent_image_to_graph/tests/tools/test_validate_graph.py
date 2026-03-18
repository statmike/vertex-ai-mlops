"""Tests for function_tool_validate_graph."""

import pytest

from agent_image_to_graph.tools.function_tool_validate_graph import validate_graph


class TestValidateGraphStructural:
    """Structural validation tests."""

    @pytest.mark.asyncio
    async def test_valid_graph(self, mock_tool_context, sample_graph):
        mock_tool_context.state["graph"] = sample_graph
        result = await validate_graph(mock_tool_context)
        assert "PASSED" in result

    @pytest.mark.asyncio
    async def test_empty_graph(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        result = await validate_graph(mock_tool_context)
        assert "empty" in result.lower()

    @pytest.mark.asyncio
    async def test_no_graph_state(self, mock_tool_context):
        result = await validate_graph(mock_tool_context)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_missing_node_id(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [{"label": "no id"}],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "missing" in result.lower() and "id" in result.lower()

    @pytest.mark.asyncio
    async def test_duplicate_node_ids(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "A"},
                {"id": "n1", "label": "B"},
            ],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "Duplicate" in result

    @pytest.mark.asyncio
    async def test_orphaned_edge(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [{"id": "n1", "label": "A"}],
            "edges": [{"id": "e1", "source": "n1", "target": "n_nonexistent"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "non-existent" in result.lower()

    @pytest.mark.asyncio
    async def test_disconnected_nodes_warning(self, mock_tool_context):
        """With 3 nodes and 1 edge, n3 is disconnected — reported as disconnected."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "A"},
                {"id": "n2", "label": "B"},
                {"id": "n3", "label": "C"},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        result = await validate_graph(mock_tool_context)
        # Small disconnected component (<3) is merged, so standard check fires
        assert "Disconnected" in result

    @pytest.mark.asyncio
    async def test_self_loop_warning(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [{"id": "n1", "label": "A"}],
            "edges": [{"id": "e1", "source": "n1", "target": "n1"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "self-loop" in result.lower()

    @pytest.mark.asyncio
    async def test_low_confidence_warning(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [{"id": "n1", "label": "A", "confidence": "low"}],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "LOW confidence" in result


class TestValidateGraphContentSwap:
    """Integration test: content-based swap detection via validate_graph."""

    @staticmethod
    def _make_landscape_image(marks: list[tuple[int, int]]) -> str:
        """Create a 2000x1000 white PNG with black marks, return base64."""
        import base64
        import io

        from PIL import Image, ImageDraw

        img = Image.new("L", (2000, 1000), 255)
        draw = ImageDraw.Draw(img)
        for mx, my in marks:
            draw.rectangle([mx - 5, my - 5, mx + 5, my + 5], fill=0)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    @pytest.mark.asyncio
    async def test_content_swap_corrects_schematic_bboxes(self, mock_tool_context):
        """Schematic-like nodes with swapped bboxes are corrected when source image exists."""
        # Nodes with x/y swapped bboxes (stored as [x, y, x, y] instead of [y, x, y, x])
        nodes = [
            {"id": f"n{i}", "label": f"C{i}",
             "bounding_box": [100 + i * 80, 300, 120 + i * 80, 320]}
            for i in range(8)
        ]
        # Marks at the SWAPPED (correct) positions
        marks = []
        for n in nodes:
            bb = n["bounding_box"]
            # Swapped center: y_center = (bb[1]+bb[3])/2, x_center = (bb[0]+bb[2])/2
            s_px = int((bb[0] + bb[2]) / 2 / 1000 * 2000)
            s_py = int((bb[1] + bb[3]) / 2 / 1000 * 1000)
            marks.append((s_px, s_py))

        mock_tool_context.state["graph"] = {
            "diagram_type": "schematic",
            "nodes": nodes,
            "edges": [{"id": "e1", "source": "n0", "target": "n1"}],
        }
        mock_tool_context.state["image_dimensions"] = {"width": 2000, "height": 1000}
        mock_tool_context.state["source_image"] = self._make_landscape_image(marks)

        result = await validate_graph(mock_tool_context)
        assert "swap detected" in result.lower()

        # Verify bboxes were swapped
        corrected = mock_tool_context.state["graph"]["nodes"][0]["bounding_box"]
        assert corrected == [300, 100, 320, 120]  # y,x,y,x after swap


class TestValidateGraphGroups:
    """Group (parent_id) validation tests."""

    @pytest.mark.asyncio
    async def test_valid_parent_id(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "g1", "label": "Group", "shape": "group_rectangle"},
                {
                    "id": "n1",
                    "label": "Child",
                    "parent_id": "g1",
                    "bounding_box": [100, 100, 200, 200],
                },
            ],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        # Should pass (no error about invalid parent_id)
        assert "PASSED" in result

    @pytest.mark.asyncio
    async def test_invalid_parent_id(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "Child", "parent_id": "nonexistent"},
            ],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "does not exist" in result

    @pytest.mark.asyncio
    async def test_group_no_children_warning(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "g1", "label": "Empty Group", "shape": "group_rectangle"},
            ],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "no children" in result.lower()

    @pytest.mark.asyncio
    async def test_group_bbox_auto_computed(self, mock_tool_context):
        """Group bbox should be auto-computed from children."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {
                    "id": "g1",
                    "label": "Group",
                    "shape": "group_rectangle",
                    "bounding_box": [0, 0, 500, 500],
                },
                {"id": "n1", "label": "A", "parent_id": "g1", "bounding_box": [100, 100, 200, 200]},
                {"id": "n2", "label": "B", "parent_id": "g1", "bounding_box": [300, 300, 400, 400]},
            ],
            "edges": [],
        }
        await validate_graph(mock_tool_context)
        # Group bbox should be recomputed from children + padding
        group = mock_tool_context.state["graph"]["nodes"][0]
        assert group["bounding_box"] == [80, 80, 420, 420]


class TestValidateGraphCvRefinement:
    """CV bounding box refinement tests."""

    @pytest.mark.asyncio
    async def test_cv_refinement_nudges_bbox(self, mock_tool_context):
        """When cv_preprocessing is present with matching elements, bboxes are nudged."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "flowchart",
            "nodes": [
                {"id": "n1", "label": "Start", "shape": "oval", "bounding_box": [55, 410, 120, 600]},
                {"id": "n2", "label": "Process", "shape": "rectangle", "bounding_box": [210, 360, 310, 660]},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        mock_tool_context.state["cv_preprocessing"] = {
            "status": "complete",
            "elements": [
                {"text": "Start", "bounding_box": [50, 400, 125, 605]},
                {"text": "Process", "bounding_box": [200, 350, 300, 650]},
            ],
        }
        await validate_graph(mock_tool_context)
        nodes = mock_tool_context.state["graph"]["nodes"]
        # n1 should be nudged to CV bbox
        assert nodes[0]["bounding_box"] == [50, 400, 125, 605]
        # n2 should be nudged to CV bbox
        assert nodes[1]["bounding_box"] == [200, 350, 300, 650]

    @pytest.mark.asyncio
    async def test_cv_refinement_no_cv_data(self, mock_tool_context, sample_graph):
        """Without cv_preprocessing in state, no changes to bboxes."""
        mock_tool_context.state["graph"] = sample_graph
        original_bboxes = [n["bounding_box"][:] for n in sample_graph["nodes"]]
        await validate_graph(mock_tool_context)
        for i, node in enumerate(mock_tool_context.state["graph"]["nodes"]):
            assert node["bounding_box"] == original_bboxes[i]

    @pytest.mark.asyncio
    async def test_cv_refinement_tracks_corrections(self, mock_tool_context):
        """Nudge count is tracked in bbox_corrections state."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "flowchart",
            "nodes": [
                {"id": "n1", "label": "Start", "shape": "oval", "bounding_box": [55, 410, 120, 600]},
            ],
            "edges": [],
        }
        mock_tool_context.state["cv_preprocessing"] = {
            "status": "complete",
            "elements": [
                {"text": "Start", "bounding_box": [50, 400, 125, 605]},
            ],
        }
        await validate_graph(mock_tool_context)
        corrections = mock_tool_context.state.get("bbox_corrections", [])
        cv_entries = [c for c in corrections if c.get("op") == "cv_refinement"]
        assert len(cv_entries) == 1
        assert cv_entries[0]["nudge_count"] >= 1


class TestValidateGraphSchematicMode:
    """Schematic-specific bbox normalization tests."""

    @pytest.mark.asyncio
    async def test_schematic_mode_normalizes_extreme_ratio(self, mock_tool_context):
        """Schematic type + extreme-ratio bboxes → normalized."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "Schematic",
            "nodes": [
                {"id": "n1", "label": "R1", "shape": "rectangle",
                 "bounding_box": [100, 490, 600, 510]},  # h=500, w=20 → extreme
                {"id": "n2", "label": "C1", "shape": "rectangle",
                 "bounding_box": [200, 200, 300, 300]},  # 100×100 → normal
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "Schematic mode" in result
        assert "1 degenerate" in result
        # n1 should be normalized
        n1 = mock_tool_context.state["graph"]["nodes"][0]
        n1_h = n1["bounding_box"][2] - n1["bounding_box"][0]
        n1_w = n1["bounding_box"][3] - n1["bounding_box"][1]
        assert n1_h < 200  # was 500, now component-sized
        assert n1_w > 15   # was 20, now component-sized
        # n2 should be unchanged
        n2 = mock_tool_context.state["graph"]["nodes"][1]
        assert n2["bounding_box"] == [200, 200, 300, 300]
        # Corrections tracked in state
        corrections = mock_tool_context.state.get("bbox_corrections", [])
        schematic_entries = [c for c in corrections if c.get("op") == "schematic_bbox_normalization"]
        assert len(schematic_entries) == 1
        assert schematic_entries[0]["correction_count"] == 1

    @pytest.mark.asyncio
    async def test_schematic_mode_oversized_handled_by_general_guard(self, mock_tool_context):
        """Schematic type + oversized rail bboxes → caught by general oversized guard (5% threshold)."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "Electronic Schematic",
            "nodes": [
                {"id": "reg", "label": "NCP1117", "shape": "rectangle",
                 "bounding_box": [139, 600, 169, 625]},   # 30×25 → normal
                {"id": "rail_5v", "label": "+5V Rail", "shape": "rectangle",
                 "bounding_box": [65, 77, 598, 588]},      # 533×511 → 27% of image
                {"id": "gnd", "label": "GND", "shape": "rectangle",
                 "bounding_box": [131, 148, 517, 504]},    # 386×356 → 14% of image
            ],
            "edges": [
                {"id": "e1", "source": "reg", "target": "rail_5v"},
                {"id": "e2", "source": "reg", "target": "gnd"},
            ],
        }
        result = await validate_graph(mock_tool_context)
        assert "Oversized bbox guard" in result
        assert "2 node bounding" in result
        # reg should be unchanged
        reg = mock_tool_context.state["graph"]["nodes"][0]
        assert reg["bounding_box"] == [139, 600, 169, 625]
        # rail_5v should be shrunk
        rail = mock_tool_context.state["graph"]["nodes"][1]
        rail_h = rail["bounding_box"][2] - rail["bounding_box"][0]
        assert rail_h < 100  # was 533
        # gnd should be shrunk
        gnd = mock_tool_context.state["graph"]["nodes"][2]
        gnd_h = gnd["bounding_box"][2] - gnd["bounding_box"][0]
        assert gnd_h < 100  # was 386
        # Corrections tracked as oversized_bbox_guard
        corrections = mock_tool_context.state.get("bbox_corrections", [])
        guard_entries = [c for c in corrections if c.get("op") == "oversized_bbox_guard"]
        assert len(guard_entries) == 1
        assert guard_entries[0]["correction_count"] == 2

    @pytest.mark.asyncio
    async def test_schematic_mode_no_effect_on_flowchart(self, mock_tool_context):
        """Flowchart diagram_type with normal bboxes → no schematic normalization."""
        original_bboxes = [
            [50, 400, 120, 600],
            [200, 350, 300, 650],
        ]
        mock_tool_context.state["graph"] = {
            "diagram_type": "flowchart",
            "nodes": [
                {"id": "n1", "label": "Start", "shape": "oval",
                 "bounding_box": original_bboxes[0][:]},
                {"id": "n2", "label": "Process", "shape": "rectangle",
                 "bounding_box": original_bboxes[1][:]},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "Schematic mode" not in result
        # Bboxes unchanged
        nodes = mock_tool_context.state["graph"]["nodes"]
        assert nodes[0]["bounding_box"] == original_bboxes[0]
        assert nodes[1]["bounding_box"] == original_bboxes[1]


class TestValidateGraphOversizedGuard:
    """General oversized bbox guard tests (all diagram types)."""

    @pytest.mark.asyncio
    async def test_oversized_flowchart_nodes_shrunk(self, mock_tool_context):
        """Flowchart nodes exceeding 10% area are shrunk by general guard."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "flowchart",
            "nodes": [
                {"id": "n1", "label": "Start", "shape": "oval",
                 "bounding_box": [50, 400, 120, 600]},           # 70×200 = 14k (1.4%)
                {"id": "n2", "label": "Process", "shape": "rectangle",
                 "bounding_box": [200, 350, 300, 650]},          # 100×300 = 30k (3%)
                {"id": "big", "label": "Eval Metrics", "shape": "rectangle",
                 "bounding_box": [100, 50, 712, 560]},           # 612×510 = 312k (31%)
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "big"},
            ],
        }
        result = await validate_graph(mock_tool_context)
        assert "Oversized bbox guard" in result
        assert "1 node bounding" in result
        # big should be shrunk
        big = mock_tool_context.state["graph"]["nodes"][2]
        big_h = big["bounding_box"][2] - big["bounding_box"][0]
        assert big_h < 200  # was 612
        # Normal nodes unchanged
        n1 = mock_tool_context.state["graph"]["nodes"][0]
        assert n1["bounding_box"] == [50, 400, 120, 600]

    @pytest.mark.asyncio
    async def test_oversized_guard_before_group_computation(self, mock_tool_context):
        """Oversized child corrected BEFORE group auto-computation."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "flowchart",
            "nodes": [
                {"id": "group_modeling", "label": "Modeling", "shape": "group_rectangle",
                 "bounding_box": [0, 0, 1000, 1000]},
                {"id": "trend", "label": "Trend Modeling", "parent_id": "group_modeling",
                 "bounding_box": [100, 50, 555, 510]},           # 455×460 = 209k (21%)
                {"id": "normal_child", "label": "ARIMA", "parent_id": "group_modeling",
                 "bounding_box": [300, 300, 370, 450]},           # 70×150 = 10.5k (1%)
            ],
            "edges": [
                {"id": "e1", "source": "trend", "target": "normal_child"},
            ],
        }
        await validate_graph(mock_tool_context)
        # trend should be shrunk first
        trend = mock_tool_context.state["graph"]["nodes"][1]
        trend_h = trend["bounding_box"][2] - trend["bounding_box"][0]
        assert trend_h < 200  # was 455
        # Group bbox should be computed from corrected children, not the oversized one
        group = mock_tool_context.state["graph"]["nodes"][0]
        group_h = group["bounding_box"][2] - group["bounding_box"][0]
        assert group_h < 300  # much smaller than original 1000

    @pytest.mark.asyncio
    async def test_oversized_guard_no_effect_on_small_nodes(self, mock_tool_context):
        """Normal-sized flowchart nodes are unaffected by oversized guard."""
        original_bboxes = [
            [50, 400, 120, 600],
            [200, 350, 300, 650],
        ]
        mock_tool_context.state["graph"] = {
            "diagram_type": "flowchart",
            "nodes": [
                {"id": "n1", "label": "Start", "shape": "oval",
                 "bounding_box": original_bboxes[0][:]},
                {"id": "n2", "label": "Process", "shape": "rectangle",
                 "bounding_box": original_bboxes[1][:]},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "Oversized bbox guard" not in result
        nodes = mock_tool_context.state["graph"]["nodes"]
        assert nodes[0]["bounding_box"] == original_bboxes[0]
        assert nodes[1]["bounding_box"] == original_bboxes[1]

    @pytest.mark.asyncio
    async def test_schematic_uses_5pct_threshold(self, mock_tool_context):
        """Schematic diagrams use 5% threshold for oversized guard."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "Schematic",
            "nodes": [
                {"id": "n1", "label": "R1", "shape": "rectangle",
                 "bounding_box": [100, 100, 130, 130]},          # 30×30 = 900 (normal)
                # 250×250 = 62,500 → 6.25%: below 10% but above 5%
                {"id": "n2", "label": "IC1", "shape": "rectangle",
                 "bounding_box": [200, 200, 450, 450]},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "Oversized bbox guard" in result
        assert "5%" in result


class TestValidateGraphOverlapDetection:
    """Non-group bbox overlap detection tests (section 5d)."""

    @pytest.mark.asyncio
    async def test_overlap_detected(self, mock_tool_context):
        """Two non-group nodes where one is fully inside the other → warning."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "flowchart",
            "nodes": [
                {"id": "outer", "label": "Outer", "shape": "rectangle",
                 "bounding_box": [170, 262, 263, 553]},
                {"id": "inner", "label": "Inner", "shape": "rectangle",
                 "bounding_box": [190, 300, 250, 500]},
            ],
            "edges": [{"id": "e1", "source": "outer", "target": "inner"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "significantly overlap" in result
        assert "outer" in result
        assert "inner" in result

    @pytest.mark.asyncio
    async def test_no_overlap_no_warning(self, mock_tool_context):
        """Two non-group nodes with no spatial overlap → no overlap warning."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "flowchart",
            "nodes": [
                {"id": "n1", "label": "A", "shape": "rectangle",
                 "bounding_box": [100, 100, 200, 200]},
                {"id": "n2", "label": "B", "shape": "rectangle",
                 "bounding_box": [300, 300, 400, 400]},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "significantly overlap" not in result

    @pytest.mark.asyncio
    async def test_partial_overlap_below_threshold(self, mock_tool_context):
        """Two nodes overlapping ~50% → no warning (below 70% containment threshold)."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "flowchart",
            "nodes": [
                {"id": "n1", "label": "A", "shape": "rectangle",
                 "bounding_box": [100, 100, 200, 200]},
                # Overlaps right half of n1: intersection 100×50=5000, smaller area=10000 → 50%
                {"id": "n2", "label": "B", "shape": "rectangle",
                 "bounding_box": [100, 150, 200, 250]},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "significantly overlap" not in result

    @pytest.mark.asyncio
    async def test_group_nodes_excluded_from_overlap(self, mock_tool_context):
        """Group nodes are excluded from overlap detection."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "flowchart",
            "nodes": [
                {"id": "g1", "label": "Group", "shape": "group_rectangle",
                 "bounding_box": [50, 50, 500, 500]},
                {"id": "n1", "label": "Child", "parent_id": "g1",
                 "bounding_box": [100, 100, 200, 200]},
            ],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "significantly overlap" not in result


class TestValidateGraphSchema:
    """Schema conformance validation."""

    @pytest.mark.asyncio
    async def test_schema_conformance_check(self, mock_tool_context, sample_schema):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [{"id": "n1"}],  # missing label (required)
            "edges": [],
        }
        mock_tool_context.state["input_schema"] = sample_schema
        result = await validate_graph(mock_tool_context)
        assert "label" in result
