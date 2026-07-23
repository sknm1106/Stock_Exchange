import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_price_chart(history_data, dept_name="학과"):
    """
    Creates an interactive, beautiful dark-themed Plotly line/area chart for department price history.
    """
    if not history_data:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text="가격 데이터가 없습니다", showarrow=False, font=dict(size=16))]
        )
        return fig

    df = pd.DataFrame(history_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    first_price = df['price'].iloc[0]
    last_price = df['price'].iloc[-1]
    is_positive = last_price >= first_price

    line_color = "#00C076" if is_positive else "#FF4D4D"  # Emerald Green vs Crimson Red
    fill_color = "rgba(0, 192, 118, 0.15)" if is_positive else "rgba(255, 77, 77, 0.15)"

    fig = go.Figure()

    # Price Area Plot
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['price'],
        mode='lines',
        name=dept_name,
        line=dict(color=line_color, width=3, shape='spline'),
        fill='tozeroy',
        fillcolor=fill_color,
        hovertemplate="<b>시간:</b> %{x|%m/%d %H:%M}<br><b>가격:</b> %{y:,.1f} Coin<extra></extra>"
    ))

    # Min/Max Points
    max_row = df.loc[df['price'].idxmax()]
    min_row = df.loc[df['price'].idxmin()]

    fig.add_trace(go.Scatter(
        x=[max_row['timestamp']],
        y=[max_row['price']],
        mode='markers+text',
        name='최고가',
        marker=dict(color='#3B82F6', size=9, symbol='circle'),
        text=[f"최고: {max_row['price']:,.0f}"],
        textposition="top center",
        hoverinfo='none'
    ))

    fig.add_trace(go.Scatter(
        x=[min_row['timestamp']],
        y=[min_row['price']],
        mode='markers+text',
        name='최저가',
        marker=dict(color='#F59E0B', size=9, symbol='circle'),
        text=[f"최저: {min_row['price']:,.0f}"],
        textposition="bottom center",
        hoverinfo='none'
    ))

    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text=f"<b>{dept_name} 주가 추이</b>",
            font=dict(size=18, color="#FFFFFF")
        ),
        margin=dict(l=20, r=20, t=50, b=30),
        paper_bgcolor="rgba(15, 23, 42, 0.6)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.05)",
            tickformat="%H:%M\n%m/%d",
            showline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.05)",
            showline=False,
            zeroline=False,
            side="right"
        ),
        showlegend=False,
        hovermode="x unified",
        height=380
    )

    return fig

def create_portfolio_pie_chart(holdings, coin):
    """
    Creates a modern Donut chart of user portfolio breakdown (Coin vs. Stock Holdings).
    """
    labels = ["보유 코인 (Cash)"]
    values = [coin]
    colors = ["#6366F1"]  # Indigo for Cash

    dept_colors = [
        "#10B981", "#3B82F6", "#F59E0B", "#EC4899", "#8B5CF6", 
        "#06B6D4", "#F97316", "#14B8A6", "#64748B", "#A855F7"
    ]

    for idx, h in enumerate(holdings):
        labels.append(h['dept_name'])
        values.append(h['eval_value'])
        colors.append(dept_colors[idx % len(dept_colors)])

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color='#0F172A', width=2)),
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>평가금액: %{value:,.1f} Coin (%{percent})<extra></extra>"
    )])

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=20),
        showlegend=False,
        height=300
    )

    return fig

def create_comparison_chart(dept_histories):
    """
    Multi-line chart comparing price histories of multiple departments.
    """
    fig = go.Figure()
    
    colors = ["#3B82F6", "#10B981", "#F59E0B", "#EC4899", "#8B5CF6", "#06B6D4"]
    
    for idx, (dept_name, history) in enumerate(dept_histories.items()):
        if not history:
            continue
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            mode='lines',
            name=dept_name,
            line=dict(color=colors[idx % len(colors)], width=2.5)
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.6)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        margin=dict(l=20, r=20, t=30, b=30),
        xaxis=dict(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255, 255, 255, 0.05)", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=320
    )
    return fig
