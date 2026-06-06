# =====================================================================
# Michelson Interferometer Simulation — Streamlit Web Version
# Physics: I = cos^2( (2π/λ) · d · cosθ )
# Deploy free at streamlit.io/cloud
# =====================================================================

import streamlit as st          # streamlit: turns this script into a web page
import numpy as np              # numpy: fast math on arrays/grids
import matplotlib.pyplot as plt # matplotlib: draw the fringe image and profile
import matplotlib.colors as mc  # matplotlib colors: for the inferno colormap

# =====================================================================
# PAGE CONFIG
# Sets the browser tab title and uses the full screen width.
# =====================================================================
st.set_page_config(
    page_title="Michelson Interferometer Simulation",
    layout="wide",
)

# =====================================================================
# TITLE & DESCRIPTION
# =====================================================================
st.title("🔬 Michelson Interferometer Simulation")
st.markdown(
    "Adjust the parameters on the left. The fringe pattern and intensity "
    "profile update instantly. Physics: **I = cos²((2π/λ) · d · cosθ)**"
)

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
# SIDEBAR — ALL INPUTS GO HERE
# Streamlit reruns the whole script on every input change,
# so no callbacks needed — just read the widget values directly.
# =====================================================================
st.sidebar.header("Parameters")

laser_name = st.sidebar.selectbox(
    "Laser",
    list(LASERS.keys()),
    index=0,
)
lam_nm = LASERS[laser_name]         # wavelength in nm

st.sidebar.markdown("---")

d0_um = st.sidebar.number_input(
    "Start arm difference (µm)",
    min_value=0.1,
    max_value=100000.0,
    value=20.0,
    step=1.0,
    format="%.2f",
    help="Initial optical path difference between the two arms, in micrometres.",
)

dd_um = st.sidebar.number_input(
    "Mirror shift Δd (µm)",
    min_value=0.0,
    max_value=1000.0,
    value=0.0,
    step=0.01,
    format="%.4f",
    help="How far the moving mirror has shifted. Path difference changes by 2Δd.",
)

st.sidebar.markdown("---")

screen_half_mm = st.sidebar.number_input(
    "Screen half-width (mm)",
    min_value=0.5,
    max_value=100.0,
    value=12.0,
    step=0.5,
    format="%.1f",
    help="Half the width of the simulated screen. Smaller = zoom in on central rings.",
)

st.sidebar.markdown("---")

N = st.sidebar.select_slider(
    "Resolution (grid points)",
    options=[200, 300, 400, 500],
    value=300,
    help="Higher = sharper image but slower to render.",
)

# =====================================================================
# PHYSICS — build grid and compute intensity
# =====================================================================
L = 300.0                               # interferometer→screen distance (mm)

x = np.linspace(-screen_half_mm, screen_half_mm, N)   # x positions
X, Y = np.meshgrid(x, x)                               # 2D coordinate grid
R = np.sqrt(X**2 + Y**2)                               # radial distance
theta = np.arctan(R / L)                               # incidence angle θ
cos_theta = np.cos(theta)                              # cos(θ)

d_total_nm = (d0_um + 2.0 * dd_um) * 1000.0           # total path diff (nm)
phase = (2.0 * np.pi / lam_nm) * d_total_nm * cos_theta  # phase at each point
I = np.cos(phase) ** 2                                 # intensity 0..1

# =====================================================================
# READOUT NUMBERS
# =====================================================================
delta_m = 2.0 * (dd_um * 1000.0) / lam_nm             # fringes shifted Δm = 2Δd/λ

m_center = 2.0 * d_total_nm / lam_nm
m_edge   = 2.0 * d_total_nm * cos_theta.min() / lam_nm
n_rings  = int(abs(m_center - m_edge))                 # visible ring count

# =====================================================================
# LAYOUT — two columns: fringe image | profile + readout
# =====================================================================
col1, col2 = st.columns([1, 1])                        # equal-width columns

# ---- LEFT: fringe image ----
with col1:
    st.subheader(f"Fringe pattern — {laser_name}")

    fig1, ax1 = plt.subplots(figsize=(5, 5))           # square figure
    ax1.imshow(
        I,
        cmap="inferno",
        origin="lower",
        extent=[-screen_half_mm, screen_half_mm,
                -screen_half_mm, screen_half_mm],
        vmin=0, vmax=1,
    )
    ax1.set_xlabel("Screen x (mm)")
    ax1.set_ylabel("Screen y (mm)")
    fig1.tight_layout()
    st.pyplot(fig1)                                    # render in Streamlit
    plt.close(fig1)                                    # free memory

# ---- RIGHT: intensity profile + readout ----
with col2:
    st.subheader("Horizontal intensity profile (through center)")

    fig2, ax2 = plt.subplots(figsize=(5, 2.8))        # wider, shorter
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

    # Readout table
    st.markdown("---")
    st.markdown("**Live readout**")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Wavelength λ",       f"{lam_nm:.1f} nm")
        st.metric("Start arm diff",     f"{d0_um:.2f} µm")
        st.metric("Mirror shift Δd",    f"{dd_um:.4f} µm")
        st.metric("Path diff (total)",  f"{d_total_nm/1000:.3f} µm")
    with col_b:
        st.metric("Fringes shifted Δm", f"{delta_m:.2f}")
        st.metric("Visible rings",      f"~ {n_rings}")
        st.metric("Screen half-width",  f"{screen_half_mm:.1f} mm")
        st.metric("Check λ = 2Δd/Δm",
                  f"{(2*dd_um*1000/delta_m):.1f} nm" if delta_m > 0 else "—")
