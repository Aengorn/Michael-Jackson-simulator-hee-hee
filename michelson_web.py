# =====================================================================
# Michelson Interferometer Simulation — Streamlit Web Version
# Physics: I = cos^2( (2π/λ) · d · cosθ )
# =====================================================================

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# =====================================================================
# PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title="Michelson Interferometer Simulation",
    layout="wide",
)

# =====================================================================
# SESSION STATE — persists values across reruns
# =====================================================================
defaults = {
    "dd_um":      0.0,      # mirror shift Δd (µm)
    "playing":    False,    # auto play flag
    "play_step":  0.05,     # Δd step per frame (µm)
    "play_wrap":  5.0,      # Δd wraps back to 0 at this value
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =====================================================================
# LASER PRESETS
# =====================================================================
LASERS = {
    "He-Ne (632.8 nm)":    632.8,
    "Green DPSS (532 nm)": 532.0,
    "Blue diode (450 nm)": 450.0,
    "Red diode (650 nm)":  650.0,
    "Violet (405 nm)":     405.0,
}

# =====================================================================
# AUTO PLAY: ADVANCE Δd FIRST, BEFORE ANYTHING IS DRAWN
# This is the key fix — if playing, update the value NOW so the image
# drawn below reflects the NEW value, not the old one.
# =====================================================================
if st.session_state.playing:
    st.session_state.dd_um += st.session_state.play_step
    if st.session_state.dd_um > st.session_state.play_wrap:
        st.session_state.dd_um = 0.0

# =====================================================================
# SIDEBAR — INPUTS
# =====================================================================
st.sidebar.header("Parameters")

laser_name = st.sidebar.selectbox("Laser", list(LASERS.keys()), index=0)
lam_nm = LASERS[laser_name]

st.sidebar.markdown("---")

d0_um = st.sidebar.number_input(
    "Start arm difference (µm)",
    min_value=0.1, max_value=100000.0,
    value=20.0, step=1.0, format="%.2f",
)

screen_half_mm = st.sidebar.number_input(
    "Screen half-width (mm)",
    min_value=0.5, max_value=100.0,
    value=12.0, step=0.5, format="%.1f",
)

N = st.sidebar.select_slider(
    "Resolution (grid points)",
    options=[150, 200, 300, 400],
    value=200,                              # lower default = faster rerender
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Mirror shift Δd**")

# Manual Δd input — synced to session state
dd_manual = st.sidebar.number_input(
    "Δd (µm)",
    min_value=0.0, max_value=1000.0,
    value=float(st.session_state.dd_um),
    step=0.01, format="%.4f",
    key="dd_box",
)
# Only update from the box if NOT playing (avoid fighting the auto loop)
if not st.session_state.playing:
    st.session_state.dd_um = dd_manual

st.sidebar.markdown("---")
st.sidebar.markdown("**Auto Play**")

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    if st.session_state.playing:
        if st.button("⏹ Stop", use_container_width=True):
            st.session_state.playing = False
            st.rerun()
    else:
        if st.button("▶ Play", use_container_width=True):
            st.session_state.playing = True
            st.rerun()
with col_s2:
    if st.button("↺ Reset", use_container_width=True):
        st.session_state.dd_um = 0.0
        st.session_state.playing = False
        st.rerun()

st.session_state.play_step = st.sidebar.number_input(
    "Step per frame (µm)",
    min_value=0.001, max_value=2.0,
    value=st.session_state.play_step,
    step=0.01, format="%.3f",
)
st.session_state.play_wrap = st.sidebar.number_input(
    "Wrap back to 0 at (µm)",
    min_value=0.1, max_value=1000.0,
    value=st.session_state.play_wrap,
    step=0.1, format="%.1f",
)

# =====================================================================
# TITLE
# =====================================================================
st.title("🔬 Michelson Interferometer Simulation")
st.markdown(
    f"{'▶ **Auto playing...**' if st.session_state.playing else '⏸ Paused'}"
    f" &nbsp;|&nbsp; **Δd = {st.session_state.dd_um:.4f} µm**"
    f" &nbsp;|&nbsp; I = cos²((2π/λ) · d · cosθ)"
)

# =====================================================================
# PHYSICS — uses the ALREADY-ADVANCED dd_um from session state
# =====================================================================
L = 300.0
dd_um = st.session_state.dd_um                         # read the updated value

x = np.linspace(-screen_half_mm, screen_half_mm, N)
X, Y = np.meshgrid(x, x)
R = np.sqrt(X**2 + Y**2)
theta = np.arctan(R / L)
cos_theta = np.cos(theta)

d_total_nm = (d0_um + 2.0 * dd_um) * 1000.0
phase = (2.0 * np.pi / lam_nm) * d_total_nm * cos_theta
I_grid = np.cos(phase) ** 2

delta_m = 2.0 * (dd_um * 1000.0) / lam_nm
m_center = 2.0 * d_total_nm / lam_nm
m_edge   = 2.0 * d_total_nm * cos_theta.min() / lam_nm
n_rings  = int(abs(m_center - m_edge))

# =====================================================================
# LAYOUT — fringe image | profile + readout
# =====================================================================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"Fringe pattern — {laser_name}")
    fig1, ax1 = plt.subplots(figsize=(5, 5))
    ax1.imshow(
        I_grid, cmap="inferno", origin="lower",
        extent=[-screen_half_mm, screen_half_mm,
                -screen_half_mm, screen_half_mm],
        vmin=0, vmax=1,
    )
    ax1.set_xlabel("Screen x (mm)")
    ax1.set_ylabel("Screen y (mm)")
    fig1.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)

with col2:
    st.subheader("Horizontal intensity profile")
    fig2, ax2 = plt.subplots(figsize=(5, 2.8))
    center_idx = N // 2
    ax2.plot(x, I_grid[center_idx, :], color="crimson")
    ax2.set_xlabel("Screen x (mm)")
    ax2.set_ylabel("Intensity")
    ax2.set_ylim(-0.05, 1.05)
    ax2.set_xlim(-screen_half_mm, screen_half_mm)
    ax2.grid(alpha=0.3)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    st.markdown("---")
    st.markdown("**Live readout**")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Wavelength λ",      f"{lam_nm:.1f} nm")
        st.metric("Start arm diff",    f"{d0_um:.2f} µm")
        st.metric("Mirror shift Δd",   f"{dd_um:.4f} µm")
        st.metric("Path diff (total)", f"{d_total_nm/1000:.3f} µm")
    with col_b:
        st.metric("Fringes shifted Δm", f"{delta_m:.2f}")
        st.metric("Visible rings",      f"~ {n_rings}")
        st.metric("Screen half-width",  f"{screen_half_mm:.1f} mm")
        st.metric("Check λ = 2Δd/Δm",
                  f"{(2*dd_um*1000/delta_m):.1f} nm" if delta_m > 0 else "—")

# =====================================================================
# TRIGGER NEXT FRAME — only fires when playing
# Sleep briefly so the browser has time to render before the next hit.
# =====================================================================
if st.session_state.playing:
    time.sleep(0.12)                                    # ~8 frames per second
    st.rerun()                                          # loop back to top
