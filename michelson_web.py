# =====================================================================
# Michelson Interferometer Simulation — Streamlit Web Version
# Physics: I = cos^2( (2π/λ) · d · cosθ )
# Deploy free at streamlit.io/cloud
# =====================================================================

import streamlit as st          # streamlit: turns this script into a web page
import numpy as np              # numpy: fast math on arrays/grids
import matplotlib.pyplot as plt # matplotlib: draw the fringe image and profile
import time                     # time: used to throttle the auto play loop

# =====================================================================
# PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title="Michelson Interferometer Simulation",
    layout="wide",
)

# =====================================================================
# SESSION STATE — persists values across reruns
# Streamlit reruns the whole script on every interaction.
# session_state is how we remember things between reruns.
# =====================================================================
if "dd_um" not in st.session_state:
    st.session_state.dd_um = 0.0        # mirror shift Δd (µm)
if "playing" not in st.session_state:
    st.session_state.playing = False    # auto play on/off flag
if "play_step" not in st.session_state:
    st.session_state.play_step = 0.05  # how much Δd advances per auto step (µm)
if "play_wrap" not in st.session_state:
    st.session_state.play_wrap = 5.0   # Δd loops back to 0 after this value (µm)

# =====================================================================
# LASER PRESETS (DATA)
# =====================================================================
LASERS = {
    "He-Ne (632.8 nm)":    632.8,
    "Green DPSS (532 nm)": 532.0,
    "Blue diode (450 nm)": 450.0,
    "Red diode (650 nm)":  650.0,
    "Violet (405 nm)":     405.0,
}

# =====================================================================
# SIDEBAR — STATIC INPUTS (laser, start arm, screen, resolution)
# =====================================================================
st.sidebar.header("Parameters")

laser_name = st.sidebar.selectbox(
    "Laser",
    list(LASERS.keys()),
    index=0,
)
lam_nm = LASERS[laser_name]

st.sidebar.markdown("---")

d0_um = st.sidebar.number_input(
    "Start arm difference (µm)",
    min_value=0.1,
    max_value=100000.0,
    value=20.0,
    step=1.0,
    format="%.2f",
    help="Initial optical path difference between the two arms.",
)

screen_half_mm = st.sidebar.number_input(
    "Screen half-width (mm)",
    min_value=0.5,
    max_value=100.0,
    value=12.0,
    step=0.5,
    format="%.1f",
    help="Half the width of the simulated screen. Smaller = zoom in on rings.",
)

N = st.sidebar.select_slider(
    "Resolution (grid points)",
    options=[200, 300, 400, 500],
    value=300,
    help="Higher = sharper image but slower to render.",
)

st.sidebar.markdown("---")

# =====================================================================
# SIDEBAR — MIRROR SHIFT Δd  (manual number input, stays in sync)
# =====================================================================
st.sidebar.markdown("**Mirror shift Δd**")

# Number input reads FROM session state so auto play keeps it synced
dd_input = st.sidebar.number_input(
    "Δd (µm) — type or use arrows",
    min_value=0.0,
    max_value=1000.0,
    value=float(st.session_state.dd_um),   # always reflects current state
    step=0.01,
    format="%.4f",
    key="dd_input_box",
)
# If the user manually changed it, write back to session state
if dd_input != st.session_state.dd_um:
    st.session_state.dd_um = dd_input

st.sidebar.markdown("---")

# =====================================================================
# SIDEBAR — AUTO PLAY CONTROLS
# =====================================================================
st.sidebar.markdown("**Auto Play**")

col_s1, col_s2 = st.sidebar.columns(2)

# Toggle button: shows Play or Stop depending on state
with col_s1:
    if st.session_state.playing:
        if st.button("⏹ Stop", use_container_width=True):
            st.session_state.playing = False
            st.rerun()
    else:
        if st.button("▶ Play", use_container_width=True):
            st.session_state.playing = True
            st.rerun()

# Reset Δd back to zero
with col_s2:
    if st.button("↺ Reset Δd", use_container_width=True):
        st.session_state.dd_um = 0.0
        st.session_state.playing = False
        st.rerun()

# Step size and wrap point controls
st.session_state.play_step = st.sidebar.number_input(
    "Step size (µm per frame)",
    min_value=0.001,
    max_value=1.0,
    value=st.session_state.play_step,
    step=0.01,
    format="%.3f",
)
st.session_state.play_wrap = st.sidebar.number_input(
    "Wrap Δd back to 0 at (µm)",
    min_value=0.1,
    max_value=1000.0,
    value=st.session_state.play_wrap,
    step=0.1,
    format="%.1f",
)

# =====================================================================
# TITLE
# =====================================================================
st.title("🔬 Michelson Interferometer Simulation")
status_label = "▶ Auto playing..." if st.session_state.playing else "Paused"
st.markdown(
    f"**{status_label}** &nbsp;|&nbsp; "
    f"Physics: **I = cos²((2π/λ) · d · cosθ)**"
)

# =====================================================================
# PHYSICS — build grid and compute intensity
# =====================================================================
L = 300.0                                               # interferometer→screen (mm)
dd_um = st.session_state.dd_um                          # use the session-state value

x = np.linspace(-screen_half_mm, screen_half_mm, N)
X, Y = np.meshgrid(x, x)
R = np.sqrt(X**2 + Y**2)
theta = np.arctan(R / L)
cos_theta = np.cos(theta)

d_total_nm = (d0_um + 2.0 * dd_um) * 1000.0            # total path diff (nm)
phase = (2.0 * np.pi / lam_nm) * d_total_nm * cos_theta
I = np.cos(phase) ** 2                                  # intensity 0..1

# Readout numbers
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
        I, cmap="inferno", origin="lower",
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
    st.subheader("Horizontal intensity profile (through center)")
    fig2, ax2 = plt.subplots(figsize=(5, 2.8))
    center_idx = N // 2
    ax2.plot(x, I[center_idx, :], color="crimson")
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
# AUTO PLAY LOOP
# If playing=True, advance Δd, wait a moment, then trigger a rerun.
# This is Streamlit's way of doing animation: rerun the whole script
# with an updated value each frame.
# =====================================================================
if st.session_state.playing:
    # Advance Δd
    st.session_state.dd_um += st.session_state.play_step
    # Loop back to 0 when it exceeds the wrap point
    if st.session_state.dd_um > st.session_state.play_wrap:
        st.session_state.dd_um = 0.0
    # Wait a short moment so the browser can render before the next frame
    time.sleep(0.08)                                    # ~12 frames per second
    # Trigger next frame
    st.rerun()
