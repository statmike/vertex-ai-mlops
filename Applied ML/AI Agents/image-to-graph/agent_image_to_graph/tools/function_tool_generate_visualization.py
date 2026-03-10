import json
import logging
import os

from google import genai
from google.adk import tools

from .util_common import log_tool_error
from .util_output import get_results_dir

logger = logging.getLogger(__name__)


async def generate_visualization(tool_context: tools.ToolContext) -> str:
    """
    Generate an interactive HTML visualization of the image-to-graph result.

    Creates a two-panel HTML page:
    - Left panel: the source image with SVG bounding box overlays, plus schema
      (split into node/edge definition blocks with linked highlighting)
    - Right panel: generated description, graph nodes and edges

    Interactive behavior:
    - Hover a node/edge/bbox to temporarily highlight (blue) across all panels
      including the corresponding schema section.
    - Click to "pin" the highlight (amber) — it stays until the next click.
    - Click background to clear the pinned selection.

    The HTML is saved as a 'visualization.html' artifact. After embedding the image,
    the source image bytes are cleared from state to prevent context overflow.

    Args:
        tool_context: The ADK tool context containing image and graph in state.

    Returns:
        A message confirming the visualization was saved, or an error message.
    """
    try:
        source_image_b64 = tool_context.state.get("source_image")
        if not source_image_b64:
            return "Error: No source image loaded. Use load_image first."

        graph = tool_context.state.get("graph")
        if graph is None:
            return "Error: No graph state found. Use load_image first."

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        if not nodes:
            return "Error: Graph has no nodes. Build the graph before generating visualization."

        mime_type = tool_context.state.get("source_image_mime_type", "image/png")
        dimensions = tool_context.state.get("image_dimensions", {})
        img_width = dimensions.get("width", 1000)
        img_height = dimensions.get("height", 1000)

        schema = tool_context.state.get("input_schema") or tool_context.state.get("schema")
        description = tool_context.state.get("diagram_description", "")

        # Count nodes that have bounding boxes
        nodes_with_bbox = sum(1 for n in nodes if n.get("bounding_box"))

        html = _build_html(
            image_b64=source_image_b64,
            mime_type=mime_type,
            img_width=img_width,
            img_height=img_height,
            graph=graph,
            schema=schema,
            description=description,
        )

        html_blob = genai.types.Part.from_bytes(
            data=html.encode("utf-8"),
            mime_type="text/html",
        )
        await tool_context.save_artifact(filename="visualization.html", artifact=html_blob)

        # Write visualization to disk alongside the source image
        results_dir = get_results_dir(tool_context)
        if results_dir:
            with open(os.path.join(results_dir, "visualization.html"), "w") as f:
                f.write(html)

        # Clear source image from state — it's now embedded in the HTML artifact.
        # This prevents context/state overflow on subsequent agent turns.
        tool_context.state["source_image"] = None

        disk_line = f"\n  Files also written to: {results_dir}" if results_dir else ""

        return (
            f"Interactive visualization saved as 'visualization.html' artifact.\n"
            f"  Nodes with bounding boxes: {nodes_with_bbox}/{len(nodes)}\n"
            f"  Edges: {len(edges)}\n"
            f"  Description included: {'yes' if description else 'no'}\n"
            f"  Schema included: {'yes' if schema else 'no'}\n"
            f"  Source image cleared from state to free memory."
            f"{disk_line}"
        )

    except Exception as e:
        return log_tool_error("generate_visualization", e)


def _build_html(
    image_b64: str,
    mime_type: str,
    img_width: int,
    img_height: int,
    graph: dict,
    schema: dict | None,
    description: str = "",
) -> str:
    """Build the self-contained interactive HTML page."""

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    diagram_type = graph.get("diagram_type", "unknown")

    # Build SVG rects for nodes with bounding boxes
    # Render group bounding boxes first (behind regular nodes)
    svg_rects = []
    for node in nodes:
        if node.get("shape") != "group_rectangle":
            continue
        bbox = node.get("bounding_box")
        if not bbox or len(bbox) != 4:
            continue
        node_id = node.get("id", "")
        label = node.get("label", "")
        y_min, x_min, y_max, x_max = bbox
        svg_rects.append(
            f'<rect class="bbox-group" data-node-id="{_esc(node_id)}" '
            f'x="{x_min}" y="{y_min}" '
            f'width="{x_max - x_min}" height="{y_max - y_min}">'
            f"<title>{_esc(label)}</title></rect>"
        )
    # Then render regular node bounding boxes
    for node in nodes:
        if node.get("shape") == "group_rectangle":
            continue
        bbox = node.get("bounding_box")
        if not bbox or len(bbox) != 4:
            continue
        node_id = node.get("id", "")
        label = node.get("label", "")
        y_min, x_min, y_max, x_max = bbox
        svg_rects.append(
            f'<rect class="bbox" data-node-id="{_esc(node_id)}" '
            f'x="{x_min}" y="{y_min}" '
            f'width="{x_max - x_min}" height="{y_max - y_min}">'
            f"<title>{_esc(label)}</title></rect>"
        )

    # Build node list HTML
    node_items = []
    for node in nodes:
        node_id = node.get("id", "")
        label = node.get("label", "")
        etype = node.get("element_type", "")
        shape = node.get("shape", "")
        has_bbox = bool(node.get("bounding_box"))

        conf = node.get("confidence", "high")
        attrs = {
            k: v
            for k, v in node.items()
            if k not in ("id", "label", "element_type", "shape", "bounding_box", "confidence")
        }
        attr_html = ""
        if attrs:
            pills = "".join(
                f'<span class="attr-pill">{_esc(str(k))}: {_esc(str(v))}</span>'
                for k, v in attrs.items()
            )
            attr_html = f'<div class="attrs">{pills}</div>'

        bbox_indicator = (
            f'<span class="confidence-dot confidence-{_esc(conf)}" title="Confidence: {_esc(conf)}"></span>'
            if has_bbox
            else ""
        )
        etype_html = f'<span class="meta-tag">{_esc(etype)}</span>' if etype else ""
        shape_html = f'<span class="meta-tag">{_esc(shape)}</span>' if shape else ""

        node_items.append(
            f'<div class="graph-node" data-node-id="{_esc(node_id)}">'
            f'  <div class="node-header">'
            f"    {bbox_indicator}"
            f'    <span class="node-id">{_esc(node_id)}</span>'
            f'    <span class="node-label">{_esc(label)}</span>'
            f"  </div>"
            f'  <div class="node-meta">'
            f"    {etype_html}"
            f"    {shape_html}"
            f"  </div>"
            f"  {attr_html}"
            f"</div>"
        )

    # Build edge list HTML
    edge_items = []
    for edge in edges:
        edge_id = edge.get("id", "")
        source = edge.get("source", "")
        target = edge.get("target", "")
        label = edge.get("label", "")
        edge_conf = edge.get("confidence", "high")

        attrs = {
            k: v
            for k, v in edge.items()
            if k not in ("id", "source", "target", "label", "confidence")
        }
        attr_html = ""
        if attrs:
            pills = "".join(
                f'<span class="attr-pill">{_esc(str(k))}: {_esc(str(v))}</span>'
                for k, v in attrs.items()
            )
            attr_html = f'<div class="attrs">{pills}</div>'

        label_html = f' <span class="edge-label">"{_esc(label)}"</span>' if label else ""
        conf_tag = f' <span class="confidence-dot confidence-{_esc(edge_conf)}" title="Confidence: {_esc(edge_conf)}"></span>'
        low_conf_class = " low-confidence" if edge_conf == "low" else ""

        edge_items.append(
            f'<div class="graph-edge{low_conf_class}" data-edge-id="{_esc(edge_id)}" '
            f'data-source="{_esc(source)}" data-target="{_esc(target)}">'
            f'  <div class="edge-header">'
            f'    <span class="edge-id">{_esc(edge_id)}</span>'
            f'    <span class="edge-arrow">{_esc(source)} &rarr; {_esc(target)}</span>'
            f"    {label_html}"
            f"    {conf_tag}"
            f"  </div>"
            f"  {attr_html}"
            f"</div>"
        )

    # Description section (first on the right panel)
    description_html = ""
    if description:
        desc_paragraphs = description.split("\n\n")
        desc_body = "".join(f"<p>{_esc(p.strip())}</p>" for p in desc_paragraphs if p.strip())
        description_html = (
            f'<div class="description-section">'
            f"  <h3>Generated Description</h3>"
            f'  <div class="description-content">{desc_body}</div>'
            f"</div>"
        )

    # Schema section (rendered for left panel, split into node/edge blocks)
    schema_html = _build_schema_html(schema) if schema else ""

    # Graph JSON section (left panel, searchable)
    graph_json_html = _build_graph_json_html(graph)

    # Recreated Graph section (Mermaid diagram)
    mermaid_def = _build_mermaid_definition(graph)
    recreation_html = (
        f'<div class="recreation-section">'
        f"<h3>Recreated Graph</h3>"
        f'<pre class="mermaid">\n{mermaid_def}\n</pre>'
        f"</div>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Image to Graph — {_esc(diagram_type)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8f9fa; color: #202124; }}

/* Header */
.header {{ background: #1a73e8; color: white; padding: 12px 24px; display: flex; align-items: center; gap: 16px; }}
.header h1 {{ font-size: 18px; font-weight: 500; }}
.header .badge {{ background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 12px; font-size: 13px; }}
.header .stats {{ margin-left: auto; font-size: 13px; opacity: 0.9; }}

/* Layout */
.container {{ display: flex; height: calc(100vh - 48px); }}

/* Left Panel (image + schema) */
.left-panel {{
    flex: 1; overflow-y: auto; background: #e8eaed; padding: 16px;
}}
.image-section {{
    display: flex; justify-content: center;
}}
.image-wrapper {{ position: relative; display: inline-block; box-shadow: 0 2px 8px rgba(0,0,0,0.15); background: white; }}
.image-wrapper img {{ display: block; max-width: 100%; }}
.image-wrapper svg {{
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none;
}}

/* Bounding boxes — base */
.bbox {{
    fill: transparent; stroke: transparent; stroke-width: 2;
    cursor: pointer; pointer-events: all;
    transition: fill 0.15s, stroke 0.15s;
}}
/* Hover highlight (blue) */
.bbox:hover, .bbox.hover-hl {{
    fill: rgba(26, 115, 232, 0.15); stroke: #1a73e8; stroke-width: 3;
}}
/* Pinned highlight (amber) — overrides hover */
.bbox.pinned {{
    fill: rgba(243, 156, 18, 0.22); stroke: #f39c12; stroke-width: 3;
    animation: pulse-pin 0.8s ease-in-out;
}}
@keyframes pulse-pin {{
    0% {{ stroke-width: 3; }}
    50% {{ stroke-width: 5; }}
    100% {{ stroke-width: 3; }}
}}

/* Resize handle */
.divider {{
    width: 6px; background: #dadce0; cursor: col-resize; flex-shrink: 0;
    transition: background 0.15s;
}}
.divider:hover {{ background: #1a73e8; }}

/* Right Panel (description + nodes + edges) */
.right-panel {{
    flex: 1; overflow-y: auto; padding: 20px; background: white;
    border-left: 1px solid #dadce0;
}}
.right-panel h3 {{
    font-size: 14px; font-weight: 600; color: #5f6368; text-transform: uppercase;
    letter-spacing: 0.5px; margin: 20px 0 8px 0; padding-bottom: 4px; border-bottom: 2px solid #e8eaed;
}}
.right-panel h3:first-child {{ margin-top: 0; }}

/* Description */
.description-section {{ margin-bottom: 16px; }}
.description-content {{
    font-size: 14px; line-height: 1.7; color: #3c4043;
    background: #f8f9fa; border: 1px solid #e8eaed; border-radius: 8px; padding: 16px;
    max-height: 400px; overflow-y: auto;
}}
.description-content p {{ margin-bottom: 12px; }}
.description-content p:last-child {{ margin-bottom: 0; }}

/* Node cards — base */
.graph-node {{
    padding: 10px 12px; margin: 4px 0; border-radius: 8px; border: 1px solid #e8eaed;
    cursor: pointer; transition: all 0.15s; background: white;
}}
/* Hover (blue) */
.graph-node.hover-hl {{ border-color: #1a73e8; background: #f0f6ff; }}
/* Pinned (amber) — overrides hover */
.graph-node.pinned {{ border-color: #f39c12; background: #fef9e7; box-shadow: 0 0 0 2px rgba(243,156,18,0.2); }}
.node-header {{ display: flex; align-items: center; gap: 8px; }}
.node-id {{ font-family: "Roboto Mono", monospace; font-size: 12px; color: #5f6368; background: #f1f3f4; padding: 2px 6px; border-radius: 4px; }}
.node-label {{ font-weight: 500; font-size: 14px; }}
.node-meta {{ display: flex; gap: 6px; margin-top: 4px; }}
.meta-tag {{ font-size: 11px; color: #1a73e8; background: #e8f0fe; padding: 2px 8px; border-radius: 10px; }}
.bbox-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #34a853; flex-shrink: 0; }}
.confidence-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
.confidence-high {{ background: #34a853; }}
.confidence-medium {{ background: #f9ab00; }}
.confidence-low {{ background: #ea4335; }}
.graph-edge.low-confidence {{ border-left-style: dashed; }}

/* Edge cards — base */
.graph-edge {{
    padding: 8px 12px; margin: 4px 0; border-radius: 8px;
    border-left: 4px solid #dadce0; background: #fafafa; cursor: pointer;
    transition: all 0.15s;
}}
/* Hover (blue) */
.graph-edge.hover-hl {{ border-left-color: #1a73e8; background: #f0f6ff; }}
/* Pinned (amber) */
.graph-edge.pinned {{ border-left-color: #f39c12; background: #fef9e7; }}
.edge-header {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
.edge-id {{ font-family: "Roboto Mono", monospace; font-size: 12px; color: #5f6368; background: #f1f3f4; padding: 2px 6px; border-radius: 4px; }}
.edge-arrow {{ font-size: 13px; font-weight: 500; }}
.edge-label {{ font-size: 12px; color: #e37400; font-style: italic; }}

/* Attributes */
.attrs {{ margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }}
.attr-pill {{ font-size: 11px; background: #f1f3f4; color: #3c4043; padding: 2px 8px; border-radius: 10px; }}

/* Schema section (left panel, below image) — collapsible */
.schema-section {{
    margin-top: 16px; background: white; border-radius: 8px; padding: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}}
.schema-section > summary {{
    cursor: pointer; list-style: revert; display: list-item;
}}
.schema-section > summary > h3 {{
    display: inline; font-size: 14px; font-weight: 600; color: #5f6368;
    text-transform: uppercase; letter-spacing: 0.5px; border-bottom: none;
    margin: 0; padding: 0;
}}
.schema-section[open] > summary {{ margin-bottom: 12px; }}
.schema-section[open] > summary > h3 {{
    padding-bottom: 4px; border-bottom: 2px solid #e8eaed;
}}
.schema-block {{
    margin: 8px 0; border-left: 4px solid #e8eaed; padding: 8px 12px;
    border-radius: 0 8px 8px 0; transition: all 0.2s;
}}
.schema-block h4 {{
    font-size: 12px; font-weight: 600; color: #5f6368; margin-bottom: 6px;
    text-transform: uppercase; letter-spacing: 0.3px;
}}
/* Hover (blue) */
.schema-block.hover-hl {{
    border-left-color: #1a73e8; background: #f0f6ff;
}}
/* Pinned (amber) — overrides hover */
.schema-block.pinned {{
    border-left-color: #f39c12; background: #fffbf2;
}}
.schema-pre {{
    font-family: "Roboto Mono", monospace; font-size: 12px; background: #f8f9fa;
    border: 1px solid #e8eaed; border-radius: 8px; padding: 12px; overflow-x: auto;
    max-height: 300px; overflow-y: auto; line-height: 1.5;
}}
.schema-details {{
    margin-top: 12px;
}}
.schema-details summary {{
    font-size: 12px; color: #5f6368; cursor: pointer; padding: 4px 0;
    font-weight: 500;
}}
.schema-details summary:hover {{ color: #1a73e8; }}

/* Graph JSON section (left panel, searchable) */
.graph-json-section {{
    margin-top: 16px; background: white; border-radius: 8px; padding: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}}
.graph-json-section > summary {{
    cursor: pointer; list-style: revert; display: list-item;
}}
.graph-json-section > summary > h3 {{
    display: inline; font-size: 14px; font-weight: 600; color: #5f6368;
    text-transform: uppercase; letter-spacing: 0.5px; border-bottom: none;
    margin: 0; padding: 0;
}}
.graph-json-section[open] > summary {{ margin-bottom: 12px; }}
.graph-json-section[open] > summary > h3 {{
    padding-bottom: 4px; border-bottom: 2px solid #e8eaed;
}}
.graph-json-search {{
    display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}}
.graph-json-search input {{
    flex: 1; padding: 6px 10px; border: 1px solid #e8eaed; border-radius: 4px;
    font-size: 13px; font-family: inherit;
}}
.graph-json-search input:focus {{ outline: none; border-color: #1a73e8; }}
#graphJsonMatchCount {{ font-size: 12px; color: #5f6368; white-space: nowrap; }}
.graph-json-pre {{
    font-family: "Roboto Mono", monospace; font-size: 12px; background: #f8f9fa;
    border: 1px solid #e8eaed; border-radius: 8px; padding: 12px; overflow-x: auto;
    max-height: 500px; overflow-y: auto; line-height: 1.5;
}}
mark.search-hit {{ background: #fde68a; border-radius: 2px; }}
mark.search-hit.current {{ background: #f59e0b; }}

/* Group bounding boxes */
.bbox-group {{
    fill: rgba(128, 90, 213, 0.06);
    stroke: #8b5cf6;
    stroke-width: 2;
    stroke-dasharray: 8 4;
    cursor: pointer;
    pointer-events: all;
    transition: fill 0.15s, stroke 0.15s;
}}
.bbox-group:hover, .bbox-group.hover-hl {{
    fill: rgba(139, 92, 246, 0.15); stroke: #7c3aed; stroke-width: 3;
}}
.bbox-group.pinned {{
    fill: rgba(243, 156, 18, 0.15); stroke: #f39c12; stroke-width: 3;
    animation: pulse-pin 0.8s ease-in-out;
}}

/* Recreated Graph section (left panel, below schema) */
.recreation-section {{
    margin-top: 16px; background: white; border-radius: 8px; padding: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}}
.recreation-section h3 {{
    font-size: 14px; font-weight: 600; color: #5f6368; text-transform: uppercase;
    letter-spacing: 0.5px; margin: 0 0 12px 0; padding-bottom: 4px; border-bottom: 2px solid #e8eaed;
}}
.recreation-section .mermaid {{ overflow-x: auto; }}

/* No bbox note */
.no-bbox-note {{ font-size: 12px; color: #9aa0a6; font-style: italic; margin: 4px 0 12px 0; }}
</style>
</head>
<body>

<div class="header">
    <h1>Image to Graph</h1>
    <span class="badge">{_esc(diagram_type)}</span>
    <span class="stats">{len(nodes)} nodes &middot; {len(edges)} edges</span>
</div>

<div class="container">
    <div class="left-panel" id="leftPanel">
        <div class="image-section">
            <div class="image-wrapper">
                <img src="data:{mime_type};base64,{image_b64}" alt="Source diagram" />
                <svg viewBox="0 0 1000 1000" preserveAspectRatio="none">
                    {"".join(svg_rects)}
                </svg>
            </div>
        </div>
        {schema_html}
        {graph_json_html}
        {recreation_html}
    </div>

    <div class="divider" id="divider"></div>

    <div class="right-panel" id="rightPanel">
        {description_html}

        <h3>Nodes ({len(nodes)})</h3>
        {"".join(node_items)}

        <h3>Edges ({len(edges)})</h3>
        {'<p class="no-bbox-note">Hover or click an edge to highlight its source and target nodes.</p>' if edges else ""}
        {"".join(edge_items)}
    </div>
</div>

<script>
(function() {{
    // --- State ---
    let pinnedType = null;   // 'node' | 'edge' | null
    let pinnedId = null;     // node id string or edge DOM element

    // --- Helpers ---
    function clearHover() {{
        document.querySelectorAll('.hover-hl').forEach(el => el.classList.remove('hover-hl'));
    }}

    function clearPinned() {{
        document.querySelectorAll('.pinned').forEach(el => el.classList.remove('pinned'));
        pinnedType = null;
        pinnedId = null;
    }}

    function applyNodeHL(nodeId, cls) {{
        const bbox = document.querySelector('.bbox[data-node-id="' + nodeId + '"]')
                  || document.querySelector('.bbox-group[data-node-id="' + nodeId + '"]');
        const card = document.querySelector('.graph-node[data-node-id="' + nodeId + '"]');
        if (bbox) bbox.classList.add(cls);
        if (card) {{
            card.classList.add(cls);
            if (cls === 'pinned') card.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
        }}
        const sb = document.querySelector('.schema-block[data-schema-section="node"]');
        if (sb) sb.classList.add(cls);
    }}

    function applyEdgeHL(edgeEl, cls) {{
        edgeEl.classList.add(cls);
        const src = edgeEl.dataset.source;
        const tgt = edgeEl.dataset.target;
        [src, tgt].forEach(function(nid) {{
            const bbox = document.querySelector('.bbox[data-node-id="' + nid + '"]');
            const card = document.querySelector('.graph-node[data-node-id="' + nid + '"]');
            if (bbox) bbox.classList.add(cls);
            if (card) card.classList.add(cls);
        }});
        const sb = document.querySelector('.schema-block[data-schema-section="edge"]');
        if (sb) sb.classList.add(cls);
    }}

    // --- Hover handlers ---
    function hoverNode(nodeId) {{
        clearHover();
        applyNodeHL(nodeId, 'hover-hl');
    }}

    function hoverEdge(edgeEl) {{
        clearHover();
        applyEdgeHL(edgeEl, 'hover-hl');
    }}

    // --- Pin handlers ---
    function pinNode(nodeId) {{
        clearPinned();
        clearHover();
        pinnedType = 'node';
        pinnedId = nodeId;
        applyNodeHL(nodeId, 'pinned');
    }}

    function pinEdge(edgeEl) {{
        clearPinned();
        clearHover();
        pinnedType = 'edge';
        pinnedId = edgeEl;
        applyEdgeHL(edgeEl, 'pinned');
    }}

    // --- Event listeners: bounding boxes on image (regular + group) ---
    document.querySelectorAll('.bbox, .bbox-group').forEach(function(rect) {{
        rect.addEventListener('mouseenter', function() {{ hoverNode(rect.dataset.nodeId); }});
        rect.addEventListener('mouseleave', clearHover);
        rect.addEventListener('click', function(e) {{
            e.stopPropagation();
            pinNode(rect.dataset.nodeId);
        }});
    }});

    // --- Event listeners: node cards ---
    document.querySelectorAll('.graph-node').forEach(function(card) {{
        card.addEventListener('mouseenter', function() {{ hoverNode(card.dataset.nodeId); }});
        card.addEventListener('mouseleave', clearHover);
        card.addEventListener('click', function(e) {{
            e.stopPropagation();
            pinNode(card.dataset.nodeId);
        }});
    }});

    // --- Event listeners: edge cards ---
    document.querySelectorAll('.graph-edge').forEach(function(card) {{
        card.addEventListener('mouseenter', function() {{ hoverEdge(card); }});
        card.addEventListener('mouseleave', clearHover);
        card.addEventListener('click', function(e) {{
            e.stopPropagation();
            pinEdge(card);
        }});
    }});

    // Click background to clear pinned
    document.addEventListener('click', function() {{ clearPinned(); clearHover(); }});

    // --- Graph JSON search ---
    var graphJsonPre = document.getElementById('graphJsonPre');
    var graphJsonSearch = document.getElementById('graphJsonSearch');
    var graphJsonMatchCount = document.getElementById('graphJsonMatchCount');
    var graphJsonOriginal = graphJsonPre ? graphJsonPre.textContent : '';
    var currentMatchIndex = -1;

    function doGraphJsonSearch() {{
        if (!graphJsonPre || !graphJsonSearch) return;
        var term = graphJsonSearch.value.trim();
        currentMatchIndex = -1;
        if (!term) {{
            graphJsonPre.innerHTML = graphJsonOriginal.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
            if (graphJsonMatchCount) graphJsonMatchCount.textContent = '';
            return;
        }}
        // Escape HTML in the original text
        var escaped = graphJsonOriginal.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        // Escape regex special chars in search term, then search case-insensitively
        var escapedTerm = term.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
        var regex = new RegExp('(' + escapedTerm + ')', 'gi');
        var matchCount = 0;
        var highlighted = escaped.replace(regex, function(m) {{
            matchCount++;
            return '<mark class="search-hit">' + m + '</mark>';
        }});
        graphJsonPre.innerHTML = highlighted;
        if (graphJsonMatchCount) {{
            graphJsonMatchCount.textContent = matchCount > 0 ? matchCount + ' match' + (matchCount !== 1 ? 'es' : '') : 'No matches';
        }}
        // Scroll first match into view
        if (matchCount > 0) {{
            currentMatchIndex = 0;
            highlightCurrentMatch();
        }}
    }}

    function highlightCurrentMatch() {{
        var marks = graphJsonPre.querySelectorAll('mark.search-hit');
        marks.forEach(function(m) {{ m.classList.remove('current'); }});
        if (marks.length > 0 && currentMatchIndex >= 0) {{
            marks[currentMatchIndex].classList.add('current');
            marks[currentMatchIndex].scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
        }}
    }}

    if (graphJsonSearch) {{
        graphJsonSearch.addEventListener('input', doGraphJsonSearch);
        graphJsonSearch.addEventListener('keydown', function(e) {{
            if (e.key === 'Enter') {{
                var marks = graphJsonPre.querySelectorAll('mark.search-hit');
                if (marks.length === 0) return;
                if (e.shiftKey) {{
                    currentMatchIndex = (currentMatchIndex - 1 + marks.length) % marks.length;
                }} else {{
                    currentMatchIndex = (currentMatchIndex + 1) % marks.length;
                }}
                highlightCurrentMatch();
                e.preventDefault();
            }}
        }});
    }}

    // --- Resizable divider ---
    var divider = document.getElementById('divider');
    var leftPanel = document.getElementById('leftPanel');
    var rightPanel = document.getElementById('rightPanel');
    var isResizing = false;

    divider.addEventListener('mousedown', function(e) {{
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    }});

    document.addEventListener('mousemove', function(e) {{
        if (!isResizing) return;
        var containerRect = document.querySelector('.container').getBoundingClientRect();
        var pct = ((e.clientX - containerRect.left) / containerRect.width) * 100;
        var clamped = Math.max(20, Math.min(80, pct));
        leftPanel.style.flex = 'none';
        leftPanel.style.width = clamped + '%';
        rightPanel.style.flex = 'none';
        rightPanel.style.width = (100 - clamped) + '%';
    }});

    document.addEventListener('mouseup', function() {{
        isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    }});
}})();
</script>
<script>
(function() {{
  var s = document.createElement('script');
  s.src = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js';
  s.onload = function() {{
    mermaid.initialize({{ startOnLoad: false, theme: 'default', flowchart: {{ curve: 'basis' }} }});
    mermaid.run();
  }};
  document.head.appendChild(s);
}})();
</script>
</body>
</html>"""


def _build_schema_html(schema: dict) -> str:
    """Build schema HTML for the left panel, split into node/edge definition blocks."""
    node_def, edge_def = _extract_schema_sections(schema)

    parts = ['<details class="schema-section"><summary><h3>Schema</h3></summary>']

    if node_def:
        parts.append(
            f'<div class="schema-block" data-schema-section="node">'
            f"<h4>Node Definition</h4>"
            f'<pre class="schema-pre">{_esc(json.dumps(node_def, indent=2))}</pre>'
            f"</div>"
        )

    if edge_def:
        parts.append(
            f'<div class="schema-block" data-schema-section="edge">'
            f"<h4>Edge Definition</h4>"
            f'<pre class="schema-pre">{_esc(json.dumps(edge_def, indent=2))}</pre>'
            f"</div>"
        )

    if not node_def and not edge_def:
        # Couldn't extract sections — show full schema as a single block
        parts.append(f'<pre class="schema-pre">{_esc(json.dumps(schema, indent=2))}</pre>')
    else:
        # Full schema in a collapsible section
        parts.append(
            f'<details class="schema-details">'
            f"<summary>Full Schema</summary>"
            f'<pre class="schema-pre">{_esc(json.dumps(schema, indent=2))}</pre>'
            f"</details>"
        )

    parts.append("</details>")
    return "\n".join(parts)


def _extract_schema_sections(schema: dict) -> tuple[dict | None, dict | None]:
    """Extract resolved node and edge definitions from a JSON Schema."""
    node_def = None
    edge_def = None

    props = schema.get("properties", {})

    # Get node items — may be a $ref or inline
    node_items = props.get("nodes", {}).get("items", {})
    if "$ref" in node_items:
        node_def = _resolve_ref(schema, node_items["$ref"])
    elif node_items:
        node_def = node_items

    # Get edge items — may be a $ref or inline
    edge_items = props.get("edges", {}).get("items", {})
    if "$ref" in edge_items:
        edge_def = _resolve_ref(schema, edge_items["$ref"])
    elif edge_items:
        edge_def = edge_items

    return node_def, edge_def


def _resolve_ref(schema: dict, ref: str) -> dict | None:
    """Resolve a JSON Schema $ref (e.g., '#/$defs/FlowchartNode') within the same document."""
    if not ref or not ref.startswith("#/"):
        return None
    parts = ref[2:].split("/")
    current = schema
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current if isinstance(current, dict) else None


def _build_graph_json_html(graph: dict) -> str:
    """Build a collapsible, searchable graph JSON section for the left panel."""
    # Create a clean copy without bounding boxes for readability
    graph_json = json.dumps(graph, indent=2)
    escaped_json = _esc(graph_json)

    return (
        '<details class="graph-json-section">'
        "<summary><h3>Graph Data</h3></summary>"
        '<div class="graph-json-search">'
        '<input type="text" id="graphJsonSearch" placeholder="Search graph data..." />'
        '<span id="graphJsonMatchCount"></span>'
        "</div>"
        f'<pre class="graph-json-pre" id="graphJsonPre">{escaped_json}</pre>'
        "</details>"
    )


def _build_mermaid_definition(graph: dict) -> str:
    """Build a Mermaid flowchart definition string from the graph dict."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    lines = ["flowchart TD"]

    def _sanitize_label(label: str) -> str:
        """Wrap label in double quotes, replacing internal double quotes."""
        return '"' + label.replace('"', "'") + '"'

    # Shape syntax mapping
    def _node_syntax(node_id: str, label: str, shape: str) -> str:
        sanitized = _sanitize_label(label)
        match shape:
            case "rectangle":
                return f"{node_id}[{sanitized}]"
            case "cylinder":
                return f"{node_id}[({sanitized})]"
            case "diamond":
                return f"{node_id}{{{sanitized}}}"
            case "circle":
                return f"{node_id}(({sanitized}))"
            case "oval" | "stadium":
                return f"{node_id}([{sanitized}])"
            case "hexagon":
                return f"{node_id}{{{{{sanitized}}}}}"
            case "circle_with_x":
                return f"{node_id}(({sanitized}))"
            case _:
                return f"{node_id}[{sanitized}]"

    # Separate group nodes from regular nodes
    group_nodes = {n["id"]: n for n in nodes if n.get("shape") == "group_rectangle"}
    regular_nodes = [n for n in nodes if n.get("shape") != "group_rectangle"]

    # Build parent_id -> children mapping
    children_by_parent: dict[str, list[dict]] = {}
    top_level_nodes: list[dict] = []
    for node in regular_nodes:
        parent = node.get("parent_id")
        if parent and parent in group_nodes:
            children_by_parent.setdefault(parent, []).append(node)
        else:
            top_level_nodes.append(node)

    # Emit subgraphs
    for group_id, group_node in group_nodes.items():
        label = group_node.get("label", group_id)
        lines.append(f"    subgraph {group_id} [{_sanitize_label(label)}]")
        for child in children_by_parent.get(group_id, []):
            child_id = child.get("id", "")
            child_label = child.get("label", child_id)
            child_shape = child.get("shape", "rectangle")
            lines.append(f"        {_node_syntax(child_id, child_label, child_shape)}")
        lines.append("    end")

    # Emit top-level nodes
    for node in top_level_nodes:
        node_id = node.get("id", "")
        label = node.get("label", node_id)
        shape = node.get("shape", "rectangle")
        lines.append(f"    {_node_syntax(node_id, label, shape)}")

    # Emit edges
    for edge in edges:
        source = edge.get("source", "")
        target = edge.get("target", "")
        label = edge.get("label", "")
        edge_type = edge.get("edge_type", "flow")

        # Arrow style
        if edge_type and ("feedback" in edge_type or "dashed" in edge_type):
            arrow = "-.->"
        else:
            arrow = "-->"

        # Label on edge
        if label:
            sanitized_label = _sanitize_label(label)
            lines.append(f"    {source} {arrow}|{sanitized_label}| {target}")
        else:
            lines.append(f"    {source} {arrow} {target}")

    return "\n".join(lines)


def _esc(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
