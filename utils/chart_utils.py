import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from config.settings import CHART_COLORS


class ChartGenerator:
    @staticmethod
    def create_budget_usage_chart(frame, budget_data, title="Budget Usage"):
        """Create a horizontal bar chart of budget usage"""
        # Sort data by percentage used
        sorted_data = sorted(budget_data, key=lambda x: x["percent"], reverse=True)

        # Limit to top 10 for readability
        if len(sorted_data) > 10:
            sorted_data = sorted_data[:10]

        budget_names = [item["name"] for item in sorted_data]
        percentages = [item["percent"] for item in sorted_data]

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(8, 6))

        # Create horizontal bar chart
        bars = ax.barh(range(len(budget_names)), percentages)

        # Color bars based on percentage
        for i, bar in enumerate(bars):
            percent = percentages[i]
            if percent > 90:
                bar.set_color('#e15759')  # Red for high usage
            elif percent > 70:
                bar.set_color('#f28e2c')  # Orange for moderate usage
            else:
                bar.set_color('#4e79a7')  # Blue for low usage

        # Set labels and title
        ax.set_yticks(range(len(budget_names)))
        ax.set_yticklabels(budget_names)
        ax.set_xlabel('Percentage Used')
        ax.set_title(title)
        ax.set_xlim(0, 100)  # Percentage from 0 to 100

        # Add percentage labels
        for i, percent in enumerate(percentages):
            ax.text(percent + 2, i, f"{percent:.1f}%", va='center')

        fig.tight_layout()

        # Create canvas widget
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()

        return canvas

    @staticmethod
    def create_monthly_spending_chart(frame, monthly_data, title="Monthly Spending"):
        """Create a bar chart of monthly spending"""
        months = [item["month"] for item in monthly_data]
        amounts = [item["amount"] for item in monthly_data]

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(8, 6))

        # Create bar chart
        bars = ax.bar(months, amounts, color=CHART_COLORS[0])

        # Set labels and title
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount ($)')
        ax.set_title(title)

        # Add data labels on bars
        for i, v in enumerate(amounts):
            ax.text(i, v + 100, f"${v:,.0f}", ha='center')

        # Rotate x labels for better readability
        plt.xticks(rotation=45, ha='right')

        fig.tight_layout()

        # Create canvas widget
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()

        return canvas

    @staticmethod
    def create_pie_chart(frame, data, label_field, value_field, title="Distribution"):
        """Create a pie chart"""
        # Sort data by value
        sorted_data = sorted(data, key=lambda x: x[value_field], reverse=True)

        # Limit to top 8 slices for readability
        other_total = 0
        if len(sorted_data) > 8:
            other_total = sum(item[value_field] for item in sorted_data[8:])
            sorted_data = sorted_data[:8]

        labels = [item[label_field] for item in sorted_data]
        values = [item[value_field] for item in sorted_data]

        # Add "Other" category if needed
        if other_total > 0:
            labels.append("Other")
            values.append(other_total)

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(8, 6))

        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=CHART_COLORS,
            wedgeprops=dict(width=0.5)  # Make it a donut chart
        )

        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        ax.set_title(title)

        # Make text more readable
        for text in texts:
            text.set_fontsize(9)

        plt.setp(autotexts, fontsize=9, fontweight='bold')

        fig.tight_layout()

        # Create canvas widget
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()

        return canvas