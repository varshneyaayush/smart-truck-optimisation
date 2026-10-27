"""
visualization/loading_3d.py
Renders interactive 3D loading arrangements using Plotly.
Accurately plots vehicle container boundaries, rear door frame, floor, and cargo items
with physical dimensions, coordinates, hover diagnostics, and theme styling.
"""

from typing import List, Optional
import plotly.graph_objects as go
from core.models import Vehicle, PlacedCargoInstance, ValidationResult

# Curated enterprise color palette aligned with brand theme
PALETTE = [
    "#8B263E",  # Deep Wine
    "#2E6F7E",  # Teal Slate
    "#D97724",  # Amber Ochre
    "#3E784E",  # Forest Sage
    "#5A4E8C",  # Muted Indigo
    "#C05C46",  # Terracotta
    "#347B98",  # Steel Blue
    "#7D5A44",  # Warm Bronze
    "#43695B",  # Deep Sage
    "#A84659",  # Raspberry
]

FRAGILE_COLOR = "#D32F2F"     # Distinct Crimson Red for fragile
LATE_ORDER_COLOR = "#FF9800"  # Vibrant Amber for late-arriving orders


def _get_box_mesh(
    x: float, y: float, z: float,
    dx: float, dy: float, dz: float,
    color: str,
    opacity: float = 0.88,
    hover_text: str = "",
    name: str = ""
) -> go.Mesh3d:
    """
    Creates a 3D rectangular cuboid mesh for Plotly.
    Vertices:
    0: (x, y, z)
    1: (x+dx, y, z)
    2: (x+dx, y+dy, z)
    3: (x, y+dy, z)
    4: (x, y, z+dz)
    5: (x+dx, y, z+dz)
    6: (x+dx, y+dy, z+dz)
    7: (x, y+dy, z+dz)
    """
    vx = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
    vy = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
    vz = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]

    # Triangles defining the 12 triangular facets of the box
    i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
    j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
    k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]

    return go.Mesh3d(
        x=vx, y=vy, z=vz,
        i=i, j=j, k=k,
        color=color,
        opacity=opacity,
        name=name,
        text=hover_text,
        hoverinfo="text",
        flatshading=True,
        lighting=dict(ambient=0.75, diffuse=0.8, specular=0.15, roughness=0.5),
        showlegend=True,
    )


def _get_box_wireframe(
    x: float, y: float, z: float,
    dx: float, dy: float, dz: float,
    line_color: str = "#1A1A1A",
    line_width: int = 2
) -> go.Scatter3d:
    """
    Draws neat dark edge lines around a box for high-contrast visual definition.
    """
    path_x = [x, x+dx, x+dx, x, x,  x, x+dx, x+dx, x, x,  None, x, x, None, x+dx, x+dx, None, x+dx, x+dx]
    path_y = [y, y, y+dy, y+dy, y,  y, y, y+dy, y+dy, y,  None, y+dy, y+dy, None, y, y, None, y+dy, y+dy]
    path_z = [z, z, z, z, z,        z+dz, z+dz, z+dz, z+dz, z+dz, None, z, z+dz, None, z, z+dz, None, z, z+dz]

    return go.Scatter3d(
        x=path_x, y=path_y, z=path_z,
        mode="lines",
        line=dict(color=line_color, width=line_width),
        hoverinfo="none",
        showlegend=False
    )


def create_truck_3d_figure(
    vehicle: Vehicle,
    placements: List[PlacedCargoInstance],
    highlight_instance_id: Optional[str] = None,
    validation: Optional[ValidationResult] = None,
    camera_view: str = "isometric"
) -> go.Figure:
    """
    Creates an interactive 3D Plotly figure representing the vehicle cargo bay container
    and all placed cargo boxes.
    """
    fig = go.Figure()

    vl = vehicle.internal_length_cm
    vw = vehicle.internal_width_cm
    vh = vehicle.internal_height_cm

    # 1. Vehicle Floor Bed (Light Sand / Warm Neutral)
    floor_mesh = go.Mesh3d(
        x=[0, vl, vl, 0],
        y=[0, 0, vw, vw],
        z=[0, 0, 0, 0],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color="#E4D5B7",
        opacity=0.65,
        hoverinfo="text",
        text=f"Vehicle Bed Floor: {vl:.0f}L × {vw:.0f}W cm",
        name="Truck Floor",
        showlegend=False
    )
    fig.add_trace(floor_mesh)

    # 2. Semi-transparent Cabin Front Bulkhead (X = 0)
    front_bulkhead = go.Mesh3d(
        x=[0, 0, 0, 0],
        y=[0, vw, vw, 0],
        z=[0, 0, vh, vh],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color="#7F011F",
        opacity=0.10,
        hoverinfo="text",
        text=f"Front Cabin Bulkhead (X = 0)",
        name="Front Bulkhead",
        showlegend=False
    )
    fig.add_trace(front_bulkhead)

    # 3. Semi-transparent Left Sidewall (Y = 0)
    left_wall = go.Mesh3d(
        x=[0, vl, vl, 0],
        y=[0, 0, 0, 0],
        z=[0, 0, vh, vh],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color="#D4C5A9",
        opacity=0.08,
        hoverinfo="text",
        text="Left Sidewall (Y = 0)",
        name="Left Sidewall",
        showlegend=False
    )
    fig.add_trace(left_wall)

    # 4. Vehicle Container Perimeter Wireframe (Wine Red #7F011F)
    border_x = [0, vl, vl, 0, 0, 0, vl, vl, 0, 0, None, vl, vl, None, vl, vl, None, 0, 0]
    border_y = [0, 0, vw, vw, 0, 0, 0, vw, vw, 0, None, 0, 0, None, vw, vw, None, vw, vw]
    border_z = [0, 0, 0, 0, 0, vh, vh, vh, vh, vh, None, 0, vh, None, 0, vh, None, 0, vh]

    fig.add_trace(
        go.Scatter3d(
            x=border_x, y=border_y, z=border_z,
            mode="lines",
            line=dict(color="#7F011F", width=3.5),
            hoverinfo="text",
            text=f"Cargo Bay Envelope ({vehicle.label}): {vl:.0f}L × {vw:.0f}W × {vh:.0f}H cm",
            name="Truck Container Frame"
        )
    )

    # 5. Rear Door Opening Outline at X = vl (Teal #008080)
    dw = vehicle.door_width_cm
    dh = vehicle.door_height_cm
    door_y_start = (vw - dw) / 2.0
    door_y_end = door_y_start + dw
    door_x = [vl, vl, vl, vl, vl]
    door_y = [door_y_start, door_y_end, door_y_end, door_y_start, door_y_start]
    door_z = [0, 0, dh, dh, 0]

    fig.add_trace(
        go.Scatter3d(
            x=door_x, y=door_y, z=door_z,
            mode="lines",
            line=dict(color="#008080", width=4),
            hoverinfo="text",
            text=f"Rear Doorway Clearance: {dw:.0f}W × {dh:.0f}H cm",
            name="Rear Door Clearance"
        )
    )

    # 6. Cabin Front & Rear Door Text Annotations
    fig.add_trace(
        go.Scatter3d(
            x=[0], y=[vw / 2], z=[vh + 12],
            mode="text",
            text=["CABIN (FRONT)"],
            textposition="top center",
            textfont=dict(size=11, color="#7F011F", family="Outfit, Inter"),
            hoverinfo="none",
            showlegend=False
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[vl], y=[vw / 2], z=[dh + 12],
            mode="text",
            text=["REAR CARGO ENTRY"],
            textposition="top center",
            textfont=dict(size=11, color="#008080", family="Outfit, Inter"),
            hoverinfo="none",
            showlegend=False
        )
    )

    # 7. Render Placed Cargo Items
    parent_ids = list(dict.fromkeys(p.parent_item_id for p in placements))
    color_map = {pid: PALETTE[i % len(PALETTE)] for i, pid in enumerate(parent_ids)}

    for idx, p in enumerate(placements):
        is_highlighted = (highlight_instance_id and p.instance_id == highlight_instance_id)

        if is_highlighted:
            box_color = "#E91E63"  # Highlight magenta
            wire_color = "#FFFFFF"
            wire_width = 4
        elif p.fragile:
            box_color = FRAGILE_COLOR
            wire_color = "#5A0000"
            wire_width = 3
        elif p.is_late_order:
            box_color = LATE_ORDER_COLOR
            wire_color = "#663300"
            wire_width = 3
        else:
            box_color = color_map.get(p.parent_item_id, "#4A90E2")
            wire_color = "#1A1A1A"
            wire_width = 2

        flags = []
        if p.fragile:
            flags.append("FRAGILE (Top Isolated)")
        if not p.stackable:
            flags.append("NON-STACKABLE")
        if p.is_late_order:
            flags.append("LATE ORDER")
        flags_str = f"<br><b>Handling:</b> {', '.join(flags)}" if flags else ""

        hover = (
            f"<b>Item:</b> {p.instance_id} ({p.name})<br>"
            f"<b>Coordinates (X, Y, Z):</b> ({p.x_cm:.1f}, {p.y_cm:.1f}, {p.z_cm:.1f}) cm<br>"
            f"<b>Placed Dims (L×W×H):</b> {p.placed_length_cm:.0f} × {p.placed_width_cm:.0f} × {p.placed_height_cm:.0f} cm<br>"
            f"<b>Weight:</b> {p.weight_kg:.1f} kg<br>"
            f"<b>Orientation:</b> {p.orientation_label}<br>"
            f"<b>Sequence #:</b> {p.loading_sequence_index or idx+1}"
            f"{flags_str}"
        )

        mesh = _get_box_mesh(
            x=p.x_cm, y=p.y_cm, z=p.z_cm,
            dx=p.placed_length_cm, dy=p.placed_width_cm, dz=p.placed_height_cm,
            color=box_color,
            opacity=0.90 if not is_highlighted else 0.98,
            hover_text=hover,
            name=f"{p.parent_item_id}"
        )
        fig.add_trace(mesh)

        wire = _get_box_wireframe(
            x=p.x_cm, y=p.y_cm, z=p.z_cm,
            dx=p.placed_length_cm, dy=p.placed_width_cm, dz=p.placed_height_cm,
            line_color=wire_color,
            line_width=wire_width
        )
        fig.add_trace(wire)

    # Camera Presets
    camera_eye = dict(x=1.75, y=-1.75, z=1.35)
    if camera_view == "top":
        camera_eye = dict(x=0.001, y=0.001, z=2.7)
    elif camera_view == "side":
        camera_eye = dict(x=0.001, y=-2.5, z=0.45)
    elif camera_view == "rear":
        camera_eye = dict(x=2.5, y=0.001, z=0.45)

    # Layout styling with Sand background and crisp grid
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="Length: X (cm) [Cabin → Door]", range=[-15, vl + 35], backgroundcolor="#FAF7F2", gridcolor="#E2D8C3"),
            yaxis=dict(title="Width: Y (cm) [Left → Right]", range=[-15, vw + 35], backgroundcolor="#FAF7F2", gridcolor="#E2D8C3"),
            zaxis=dict(title="Height: Z (cm) [Floor → Roof]", range=[-10, vh + 25], backgroundcolor="#FAF7F2", gridcolor="#E2D8C3"),
            aspectmode="data",
            camera=dict(
                eye=camera_eye,
                center=dict(x=0, y=0, z=-0.08)
            )
        ),
        paper_bgcolor="#FAF7F2",
        plot_bgcolor="#FAF7F2",
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#2C2C2C")
        ),
        height=560,
    )

    return fig
