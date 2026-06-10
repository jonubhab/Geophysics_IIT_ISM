import ast
import math

import dash_daq as daq
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from scipy.spatial import cKDTree

DATA_FILE = "data.txt"


def load_data(path):
    with open(path, "r") as f:
        txt = f.read().strip()

    txt = txt.replace("nan", "None").replace("NaN", "None")
    data = ast.literal_eval(txt)

    coords = np.array([row[:3] for row in data], dtype=float)
    vals = np.array([
        np.nan if row[3] is None else float(row[3])
        for row in data
    ], dtype=float)
    return coords, vals


coords, vals = load_data(DATA_FILE)
xs, ys, zs = coords[:, 0], coords[:, 1], coords[:, 2]

finite = np.isfinite(vals)
finite_points = coords[finite]
finite_vals = vals[finite]

if len(finite_points) == 0:
    raise ValueError("No finite scalar values found in the input file.")

xmin, xmax = xs.min(), xs.max()
ymin, ymax = ys.min(), ys.max()
zmin, zmax = zs.min(), zs.max()

box_center = np.array([(xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2], dtype=float)
box_size = np.array([xmax - xmin, ymax - ymin, zmax - zmin], dtype=float)
max_dim = float(np.max(box_size))

kdtree = cKDTree(finite_points)


def norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def orthonormal_basis(n):
    n = norm(np.asarray(n, dtype=float))
    ref = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = norm(np.cross(n, ref))
    v = norm(np.cross(n, u))
    return u, v


def plane_square(origin, normal, size):
    u, v = orthonormal_basis(normal)
    c = np.asarray(origin, dtype=float)
    s = size / 2.0
    pts = np.array([
        c + (-s) * u + (-s) * v,
        c + (s) * u + (-s) * v,
        c + (s) * u + (s) * v,
        c + (-s) * u + (s) * v,
        c + (-s) * u + (-s) * v,
    ])
    return pts


def smooth_scalar_at(points, k=8, eps=1e-9):
    dists, idx = kdtree.query(points, k=min(k, len(finite_points)))
    if dists.ndim == 1:
        dists = dists[:, None]
        idx = idx[:, None]
    w = 1.0 / (dists + eps)
    w = w / np.sum(w, axis=1, keepdims=True)
    return np.sum(w * finite_vals[idx], axis=1)


def slice_geometry(origin, normal, thickness):
    n = norm(np.array(normal, dtype=float))
    origin = np.array(origin, dtype=float)
    u, v = orthonormal_basis(n)

    size = max_dim * 1.15
    grid_n = 80
    a = np.linspace(-size / 2, size / 2, grid_n)
    b = np.linspace(-size / 2, size / 2, grid_n)
    A, B = np.meshgrid(a, b)

    pts = origin[None, None, :] + A[..., None] * u + B[..., None] * v
    flat = pts.reshape(-1, 3)
    bg = smooth_scalar_at(flat, k=10).reshape(grid_n, grid_n)

    dist = np.abs((coords - origin) @ n)
    band = dist <= thickness / 2.0
    band_points = coords[band]
    band_vals = vals[band]
    band_finite = np.isfinite(band_vals)
    band_points = band_points[band_finite]
    band_vals = band_vals[band_finite]

    rel = band_points - origin
    cu = rel @ u
    cv = rel @ v

    return u, v, a, b, bg, cu, cv, band_vals, n


def make_figures(pos_frac, thickness_frac, yaw, pitch):
    thickness = max(1e-6, thickness_frac * max_dim)

    n = np.array([
        math.cos(pitch) * math.sin(yaw),
        math.sin(pitch),
        math.cos(pitch) * math.cos(yaw),
    ], dtype=float)
    n = norm(n)

    origin = np.array([
        xmin + pos_frac * (xmax - xmin),
        ymin + pos_frac * (ymax - ymin),
        zmin + pos_frac * (zmax - zmin),
    ], dtype=float)

    u, v, a, b, bg, cu, cv, band_vals, n = slice_geometry(origin, n, thickness)
    vmin = float(np.nanmin(finite_vals))
    vmax = float(np.nanmax(finite_vals))

    # 2D panel
    fig2d = go.Figure()
    fig2d.add_trace(go.Heatmap(
        x=a,
        y=b,
        z=bg,
        colorscale="Inferno",
        zmin=vmin,
        zmax=vmax,
        colorbar=dict(title="Scalar", len=0.85, x=1.02),
        hoverinfo="skip",
        showscale=True,
    ))
    if len(cu) > 0:
        fig2d.add_trace(go.Scattergl(
            x=cu,
            y=cv,
            mode="markers",
            marker=dict(
                size=6,
                color=band_vals,
                colorscale="Inferno",
                cmin=vmin,
                cmax=vmax,
                line=dict(color="rgba(0,0,0,0.45)", width=0.5),
            ),
            hovertemplate="u=%{x:.3f}<br>v=%{y:.3f}<br>val=%{marker.color:.4f}<extra></extra>",
        ))
    fig2d.update_layout(
        title="2D Cross Section",
        margin=dict(l=10, r=10, t=35, b=10),
        template="plotly_dark",
        dragmode=False,
        xaxis_title="Slice U",
        yaxis_title="Slice V",
    )
    fig2d.update_yaxes(scaleanchor="x", scaleratio=1)

    # 3D panel
    plane = plane_square(origin, n, max_dim * 1.1)

    box_x = [xmin, xmax, xmax, xmin, xmin, xmin, xmax, xmax, xmin, xmin, xmin, xmin, xmax, xmax, xmax, xmax, None]
    box_y = [ymin, ymin, ymax, ymax, ymin, ymin, ymin, ymax, ymax, ymax, ymax, ymin, ymin, ymin, ymax, ymax, None]
    box_z = [zmin, zmin, zmin, zmin, zmin, zmax, zmax, zmax, zmax, zmin, zmax, zmax, zmax, zmin, zmin, zmax, None]

    fig3d = go.Figure()
    fig3d.add_trace(go.Scatter3d(
        x=box_x,
        y=box_y,
        z=box_z,
        mode="lines",
        line=dict(color="rgba(200,200,200,0.55)", width=4),
        showlegend=False,
        hoverinfo="skip",
    ))
    fig3d.add_trace(go.Scatter3d(
        x=finite_points[:, 0],
        y=finite_points[:, 1],
        z=finite_points[:, 2],
        mode="markers",
        marker=dict(
            size=4,
            color=finite_vals,
            colorscale="Inferno",
            cmin=vmin,
            cmax=vmax,
            opacity=0.95,
            colorbar=dict(title="Scalar", x=1.07, len=0.7),
        ),
        showlegend=False,
        hovertemplate="x=%{x}<br>y=%{y}<br>z=%{z}<br>val=%{marker.color:.4f}<extra></extra>",
    ))
    fig3d.add_trace(go.Mesh3d(
        x=plane[:, 0],
        y=plane[:, 1],
        z=plane[:, 2],
        color="rgba(120,180,255,0.18)",
        opacity=0.18,
        showscale=False,
        hoverinfo="skip",
    ))
    fig3d.add_trace(go.Scatter3d(
        x=plane[:, 0],
        y=plane[:, 1],
        z=plane[:, 2],
        mode="lines",
        line=dict(color="rgba(120,180,255,0.9)", width=6),
        hoverinfo="skip",
        showlegend=False,
    ))
    fig3d.add_trace(go.Scatter3d(
        x=[xmin, xmax],
        y=[ymin, ymin],
        z=[zmin, zmin],
        mode="lines",
        line=dict(color="red", width=6),
        showlegend=False,
        hoverinfo="skip",
    ))
    fig3d.add_trace(go.Scatter3d(
        x=[xmin, xmin],
        y=[ymin, ymax],
        z=[zmin, zmin],
        mode="lines",
        line=dict(color="green", width=6),
        showlegend=False,
        hoverinfo="skip",
    ))
    fig3d.add_trace(go.Scatter3d(
        x=[xmin, xmin],
        y=[ymin, ymin],
        z=[zmin, zmax],
        mode="lines",
        line=dict(color="blue", width=6),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig3d.update_layout(
        title="3D Orientation View",
        template="plotly_dark",
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        scene=dict(
            xaxis=dict(title="X", showbackground=True, zeroline=True),
            yaxis=dict(title="Y", showbackground=True, zeroline=True),
            zaxis=dict(title="Z", showbackground=True, zeroline=True),
            aspectmode="data",
        ),
    )

    return fig2d, fig3d


app = Dash(__name__)
app.layout = html.Div([
    html.Div([
        dcc.Graph(id="slice-2d", style={"height": "96vh"}),
    ], style={"width": "68%", "display": "inline-block", "verticalAlign": "top"}),

    html.Div([
        dcc.Graph(id="view-3d", style={"height": "58vh"}),

        html.Div([
            html.Div("Controller", style={"fontWeight": "bold", "marginBottom": "8px"}),

            html.Div("Slice position"),
            dcc.Slider(
                id="pos-slider",
                min=0, max=1, step=0.001, value=0.5,
                tooltip={"placement": "bottom", "always_visible": False},
            ),

            html.Div("Slice thickness", style={"marginTop": "18px"}),
            dcc.Slider(
                id="thick-slider",
                min=0.01, max=0.5, step=0.001, value=0.08,
                tooltip={"placement": "bottom", "always_visible": False},
            ),

            html.Div("Joystick", style={"marginTop": "18px"}),
            daq.Joystick(
                id="joy",
                label="Joystick",
                labelPosition="top",
                size=140,
                style={"marginTop": "8px"},
            ),

            html.Div(id="joy-readout", style={"marginTop": "10px"}),
        ], style={"height": "37vh", "padding": "10px", "borderTop": "1px solid #333"}),
    ], style={"width": "32%", "display": "inline-block", "verticalAlign": "top"}),
], style={"fontFamily": "sans-serif", "height": "100vh", "backgroundColor": "#111"})


@app.callback(
    Output("slice-2d", "figure"),
    Output("view-3d", "figure"),
    Output("joy-readout", "children"),
    Input("pos-slider", "value"),
    Input("thick-slider", "value"),
    Input("joy", "angle"),
    Input("joy", "force"),
)
def update(pos, thick, angle, force):
    yaw = 0.0
    pitch = 0.0
    if angle is not None and force is not None:
        theta = math.radians(angle)
        r = float(force)
        yaw = r * math.cos(theta) * math.pi
        pitch = r * math.sin(theta) * (math.pi / 3)

    fig2d, fig3d = make_figures(pos, thick, yaw, pitch)
    return fig2d, fig3d, f"Angle: {angle} | Force: {force}"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
