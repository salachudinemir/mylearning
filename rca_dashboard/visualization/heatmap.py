import streamlit as st
import plotly.express as px

def show_heatmap_rca_vs_severity(pivot):
    st.subheader("🔥 Interactive Heatmap RCA vs Severity")

    severity_order = ['Emergency', 'Critical', 'Major']
    available_severity = [s for s in severity_order if s in pivot.columns]
    pivot_sorted = pivot.reindex(columns=available_severity)

    fig = px.imshow(
        pivot_sorted.values,
        x=available_severity,
        y=pivot_sorted.index,
        color_continuous_scale='Viridis',
        text_auto=True,
        aspect='auto',
        labels=dict(x="Severity", y="RCA", color="Count"),
        title="Heatmap RCA vs Severity"
    )

    fig.update_layout(
        title_font_size=22,
        title_font_color='darkblue',
        font=dict(size=18, color='black'),
        xaxis=dict(title_font_size=20, tickfont_size=18),
        yaxis=dict(title_font_size=20, tickfont_size=18),
        coloraxis_colorbar=dict(
            title=dict(text='Jumlah', font=dict(size=20)),
            tickfont=dict(size=18)
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def show_heatmap_circle_vs_severity(pivot_circle):
    st.subheader("🔥 Interactive Heatmap Circle vs Severity")

    severity_order = ['Emergency', 'Critical', 'Major']
    available_severity = [s for s in severity_order if s in pivot_circle.columns]
    pivot_sorted = pivot_circle.reindex(columns=available_severity)

    fig = px.imshow(
        pivot_sorted.values,
        x=available_severity,
        y=pivot_sorted.index,
        color_continuous_scale='Viridis',
        text_auto=True,
        aspect='auto',
        labels=dict(x="Severity", y="Circle", color="Count"),
        title="Heatmap Circle vs Severity"
    )

    fig.update_layout(
        title_font_size=22,
        title_font_color='darkblue',
        font=dict(size=18, color='black'),
        xaxis=dict(title_font_size=20, tickfont_size=18),
        yaxis=dict(title_font_size=20, tickfont_size=18),
        coloraxis_colorbar=dict(
            title=dict(text='Jumlah', font=dict(size=20)),
            tickfont=dict(size=18)
        )
    )

    st.plotly_chart(fig, use_container_width=True)
