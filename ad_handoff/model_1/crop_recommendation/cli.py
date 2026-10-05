"""Command Line Interface for Crop Recommendation System."""

import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from crop_recommendation.api import recommend_crops
from crop_recommendation.config import DEFAULT_SCORING_WEIGHTS


def main():
    parser = argparse.ArgumentParser(
        description="Crop Recommendation Engine with Independent History/Rotation Scoring Layer."
    )
    # Soil test arguments
    parser.add_argument("--n", type=float, required=True, help="Soil Nitrogen test value (kg/ha).")
    parser.add_argument("--p", type=float, required=True, help="Soil Phosphorus test value (kg/ha).")
    parser.add_argument("--k", type=float, required=True, help="Soil Potassium test value (kg/ha).")
    parser.add_argument("--ph", type=float, default=6.5, help="Soil pH (default: 6.5).")
    parser.add_argument("--temp", type=float, default=25.0, help="Temperature in Celsius (default: 25.0).")
    parser.add_argument("--humidity", type=float, default=70.0, help="Humidity percentage (default: 70.0).")
    parser.add_argument("--rainfall", type=float, default=100.0, help="Rainfall in mm (default: 100.0).")
    parser.add_argument("--state", type=str, default="Maharashtra", help="State / Region (e.g. Maharashtra, Punjab).")

    # History arguments
    parser.add_argument("--current-crop", type=str, default=None, help="Current standing crop or most recently harvested (T).")
    parser.add_argument("--prev-crop-1", type=str, default=None, help="Crop grown 1 season ago (T-1).")
    parser.add_argument("--prev-crop-2", type=str, default=None, help="Crop grown 2 seasons ago (T-2).")
    parser.add_argument("--prev-crop-3", type=str, default=None, help="Crop grown 3 seasons ago (T-3).")

    # Configurable weights arguments
    parser.add_argument("--w-soil", type=float, default=0.50, help="Weight for SoilClimateScore (default: 0.50).")
    parser.add_argument("--w-reg", type=float, default=0.30, help="Weight for RegionalScore (default: 0.30).")
    parser.add_argument("--w-hist", type=float, default=0.20, help="Weight for HistoryRotationScore (default: 0.20).")
    parser.add_argument("--top-k", type=int, default=5, help="Number of recommendations to display (default: 5).")

    args = parser.parse_args()

    console = Console()

    console.print(Panel(
        f"[bold green]Crop Recommendation System[/bold green]\n"
        f"[dim]Soil Test Primary Indicator | Rule-Based History/Rotation Layer[/dim]\n"
        f"Weights: Soil/Climate: {args.w_soil:.2f} | Regional: {args.w_reg:.2f} | History/Rotation: {args.w_hist:.2f}\n"
        f"Input History: Current: '{args.current_crop or 'None'}', Prev 1: '{args.prev_crop_1 or 'None'}', Prev 2: '{args.prev_crop_2 or 'None'}', Prev 3: '{args.prev_crop_3 or 'None'}'",
        title="Execution Config",
        expand=False
    ))

    weights_dict = {
        "soil_climate": args.w_soil,
        "regional": args.w_reg,
        "history_rotation": args.w_hist
    }

    response = recommend_crops(
        n=args.n,
        p=args.p,
        k=args.k,
        ph=args.ph,
        temperature=args.temp,
        humidity=args.humidity,
        rainfall=args.rainfall,
        state=args.state,
        current_crop=args.current_crop,
        prev_crop_1=args.prev_crop_1,
        prev_crop_2=args.prev_crop_2,
        prev_crop_3=args.prev_crop_3,
        top_k=args.top_k,
        weights=weights_dict,
    )

    table = Table(title="Top Crop Recommendations", show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Rank", style="dim", width=5, justify="center")
    table.add_column("Crop", style="bold cyan", width=12)
    table.add_column("Soil/Climate\nScore", justify="right", style="green", width=12)
    table.add_column("Regional\nScore", justify="right", style="yellow", width=10)
    table.add_column("History/Rotation\nScore", justify="right", style="blue", width=16)
    table.add_column("Final\nScore", justify="right", style="bold green", width=10)
    table.add_column("Reason", style="white", min_width=30)

    for idx, rec in enumerate(response.recommendations, 1):
        table.add_row(
            str(idx),
            rec.crop.capitalize(),
            f"{rec.soil_climate_score:.4f}",
            f"{rec.regional_score:.4f}",
            f"{rec.history_rotation_score:.4f}",
            f"{rec.final_score:.4f}",
            rec.reason
        )

    console.print(table)
    console.print()

    console.print("[bold yellow]Individual Crop Breakdowns:[/bold yellow]")
    for idx, rec in enumerate(response.recommendations, 1):
        console.print(f"[bold cyan]Crop:[/bold cyan] {rec.crop.capitalize()}")
        console.print(f"  [bold]Soil/Climate Score:[/bold]     {rec.soil_climate_score:.4f}")
        console.print(f"  [bold]Regional Score:[/bold]         {rec.regional_score:.4f}")
        console.print(f"  [bold]History/Rotation Score:[/bold] {rec.history_rotation_score:.4f}")
        console.print(f"  [bold green]Final Score:[/bold green]            {rec.final_score:.4f}")
        console.print(f"  [bold]Reason:[/bold]                 {rec.reason}")
        console.print("-" * 75)

    console.print(f"[dim italic]* Note: {response.note}[/dim italic]\n")


if __name__ == "__main__":
    main()
