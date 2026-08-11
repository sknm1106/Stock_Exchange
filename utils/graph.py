import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_price_chart(history_data, dept_name="학과"):
    """
    학과 가격 기록을 시간순으로 표시하는 주가 차트
    """
    if not history_data:
        fig = go.Figure()

        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            annotations=[
                dict(
                    text="가격 데이터가 없습니다",
                    showarrow=False,
                    font=dict(size=16, color="#6B7280")
                )
            ]
        )

        return fig

    df = pd.DataFrame(history_data)

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # timestamp가 같은 경우 id까지 사용해서 순서 보장
    sort_columns = ['timestamp']

    if 'id' in df.columns:
        sort_columns.append('id')

    df = df.sort_values(sort_columns)

    first_price = float(df['price'].iloc[0])
    last_price = float(df['price'].iloc[-1])

    is_positive = last_price >= first_price

    line_color = "#059669" if is_positive else "#DC2626"

    fill_color = (
        "rgba(5, 150, 105, 0.12)"
        if is_positive
        else "rgba(220, 38, 38, 0.12)"
    )

    fig = go.Figure()

    # 주가 선
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['price'],
        mode='lines',
        name=dept_name,
        line=dict(
            color=line_color,
            width=3,
            shape='spline'
        ),
        fill='tozeroy',
        fillcolor=fill_color,
        hovertemplate=(
            "<b>시간:</b> %{x|%m/%d %H:%M}"
            "<br><b>가격:</b> %{y:,.1f} Coin"
            "<extra></extra>"
        )
    ))

    # 최고가
    max_row = df.loc[df['price'].idxmax()]

    fig.add_trace(go.Scatter(
        x=[max_row['timestamp']],
        y=[max_row['price']],
        mode='markers+text',
        name='최고가',
        marker=dict(
            color='#2563EB',
            size=9,
            symbol='circle'
        ),
        text=[f"최고: {max_row['price']:,.1f}"],
        textposition="top center",
        hoverinfo='none'
    ))

    # 최저가
    min_row = df.loc[df['price'].idxmin()]

    fig.add_trace(go.Scatter(
        x=[min_row['timestamp']],
        y=[min_row['price']],
        mode='markers+text',
        name='최저가',
        marker=dict(
            color='#D97706',
            size=9,
            symbol='circle'
        ),
        text=[f"최저: {min_row['price']:,.1f}"],
        textposition="bottom center",
        hoverinfo='none'
    ))

    # 현재가 = price_history의 가장 마지막 값
    last_row = df.iloc[-1]

    fig.add_trace(go.Scatter(
        x=[last_row['timestamp']],
        y=[last_row['price']],
        mode='markers+text',
        name='현재가',
        marker=dict(
            color='#00703E',
            size=11,
            symbol='circle'
        ),
        text=[f"현재: {last_row['price']:,.1f}"],
        textposition="top right",
        hovertemplate=(
            "<b>현재가</b>"
            "<br>시간: %{x|%m/%d %H:%M}"
            "<br>가격: %{y:,.1f} Coin"
            "<extra></extra>"
        )
    ))

    fig.update_layout(
        template="plotly_white",

        title=dict(
            text=f"<b>{dept_name} 주가 추이</b>",
            font=dict(
                size=18,
                color="#1F2937"
            )
        ),

        margin=dict(
            l=20,
            r=20,
            t=50,
            b=30
        ),

        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F9FAFB",

        xaxis=dict(
            showgrid=True,
            gridcolor="#E5E7EB",
            tickformat="%H:%M\n%m/%d",
            showline=False,
            tickfont=dict(color="#6B7280")
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor="#E5E7EB",
            showline=False,
            zeroline=False,
            side="right",
            tickfont=dict(color="#6B7280")
        ),

        showlegend=False,
        hovermode="x unified",
        height=380
    )

    return fig

def create_portfolio_pie_chart(holdings, coin):
    """
    Creates a modern Donut chart of user portfolio breakdown (Bright theme).
    """
    labels = ["보유 코인 (Cash)"]
    values = [coin]
    colors = ["#00703E"]  # Konkuk Green for Cash

    dept_colors = [
        "#059669", "#2563EB", "#D97706", "#DB2777", "#7C3AED", 
        "#0891B2", "#EA580C", "#0D9488", "#475569", "#9333EA"
    ]

    for idx, h in enumerate(holdings):
        labels.append(h['dept_name'])
        values.append(h['eval_value'])
        colors.append(dept_colors[idx % len(dept_colors)])

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>평가금액: %{value:,.1f} Coin (%{percent})<extra></extra>"
    )])

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=20),
        showlegend=False,
        height=300
    )

    return fig

def create_comparison_chart(dept_histories):
    """
    Multi-line chart comparing price histories of multiple departments (Bright theme).
    """
    fig = go.Figure()
    
    colors = ["#2563EB", "#059669", "#D97706", "#DB2777", "#7C3AED", "#0891B2"]
    
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
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F9FAFB",
        margin=dict(l=20, r=20, t=30, b=30),
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(showgrid=True, gridcolor="#E5E7EB", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=320
    )
    return fig
