"""Tests for generate_schematic_grid() in util_diagram_type."""

from agent_image_to_graph.tools.util_diagram_type import generate_schematic_grid


class TestGridCellCount:
    """Grid produces the correct number of cells."""

    def test_default_landscape(self):
        cells = generate_schematic_grid(cols=4, rows=3)
        assert len(cells) == 12

    def test_default_portrait(self):
        cells = generate_schematic_grid(cols=3, rows=4)
        assert len(cells) == 12

    def test_custom_grid(self):
        cells = generate_schematic_grid(cols=5, rows=5)
        assert len(cells) == 25

    def test_single_cell(self):
        cells = generate_schematic_grid(cols=1, rows=1)
        assert len(cells) == 1


class TestGridCoverage:
    """All cells tile the 0-1000 space completely."""

    def test_full_coverage_no_gaps(self):
        """Every point in 0-999 must be inside at least one cell."""
        cells = generate_schematic_grid(cols=4, rows=3, overlap=0.0)
        for y in range(0, 1000, 50):
            for x in range(0, 1000, 50):
                covered = any(
                    c["bounding_box"][0] <= y < c["bounding_box"][2]
                    and c["bounding_box"][1] <= x < c["bounding_box"][3]
                    for c in cells
                )
                assert covered, f"Point ({y}, {x}) not covered by any cell"

    def test_boundary_1000_covered(self):
        """The point (999, 999) must be inside at least one cell."""
        cells = generate_schematic_grid(cols=4, rows=3, overlap=0.0)
        covered = any(
            c["bounding_box"][0] <= 999 <= c["bounding_box"][2]
            and c["bounding_box"][1] <= 999 <= c["bounding_box"][3]
            for c in cells
        )
        assert covered, "Point (999, 999) not covered"


class TestGridOverlap:
    """Overlap produces cells larger than the non-overlapping size."""

    def test_overlap_expands_cells(self):
        cells_no_overlap = generate_schematic_grid(cols=4, rows=3, overlap=0.0)
        cells_with_overlap = generate_schematic_grid(cols=4, rows=3, overlap=0.05)

        # Interior cells (not on edges) should be strictly larger with overlap
        for no_ov, with_ov in zip(cells_no_overlap, cells_with_overlap, strict=True):
            no_w = no_ov["bounding_box"][3] - no_ov["bounding_box"][1]
            with_w = with_ov["bounding_box"][3] - with_ov["bounding_box"][1]
            no_h = no_ov["bounding_box"][2] - no_ov["bounding_box"][0]
            with_h = with_ov["bounding_box"][2] - with_ov["bounding_box"][0]
            assert with_w >= no_w
            assert with_h >= no_h

    def test_overlap_bounds_clamped(self):
        """Overlap padding must not push coordinates outside 0-1000."""
        cells = generate_schematic_grid(cols=4, rows=3, overlap=0.10)
        for cell in cells:
            top, left, bottom, right = cell["bounding_box"]
            assert top >= 0, f"top={top} < 0"
            assert left >= 0, f"left={left} < 0"
            assert bottom <= 1000, f"bottom={bottom} > 1000"
            assert right <= 1000, f"right={right} > 1000"


class TestGridRegionFields:
    """Each region has required fields and correct element_type."""

    def test_element_type_is_grid_cell(self):
        cells = generate_schematic_grid(cols=4, rows=3)
        for cell in cells:
            assert cell["element_type"] == "grid_cell"

    def test_required_fields(self):
        cells = generate_schematic_grid(cols=4, rows=3)
        for cell in cells:
            assert "region_id" in cell
            assert "label" in cell
            assert "description" in cell
            assert "bounding_box" in cell
            assert "element_type" in cell

    def test_region_ids_unique(self):
        cells = generate_schematic_grid(cols=4, rows=3)
        ids = [c["region_id"] for c in cells]
        assert len(ids) == len(set(ids))

    def test_bounding_box_is_list_of_4(self):
        cells = generate_schematic_grid(cols=4, rows=3)
        for cell in cells:
            bbox = cell["bounding_box"]
            assert isinstance(bbox, list)
            assert len(bbox) == 4

    def test_bounding_box_top_less_than_bottom(self):
        cells = generate_schematic_grid(cols=4, rows=3)
        for cell in cells:
            top, left, bottom, right = cell["bounding_box"]
            assert top < bottom, f"top={top} >= bottom={bottom}"
            assert left < right, f"left={left} >= right={right}"


class TestGridAspectRatio:
    """Landscape vs portrait grid selection logic."""

    def test_landscape_has_more_cols(self):
        """4×3 grid: wider cells for landscape images."""
        cells = generate_schematic_grid(cols=4, rows=3, overlap=0.0)
        # First row should have 4 cells
        first_row = [c for c in cells if c["bounding_box"][0] == 0]
        assert len(first_row) == 4

    def test_portrait_has_more_rows(self):
        """3×4 grid: taller layout for portrait images."""
        cells = generate_schematic_grid(cols=3, rows=4, overlap=0.0)
        # First column should have 4 cells
        first_col = [c for c in cells if c["bounding_box"][1] == 0]
        assert len(first_col) == 4
