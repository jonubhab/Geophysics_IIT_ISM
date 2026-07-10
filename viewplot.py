import argparse
import os
import pickle
import matplotlib.pyplot as plt


def load_and_show_plot():
    # 1. Setup the CLI argument parser
    parser = argparse.ArgumentParser(description="Load and view an interactive pickled Matplotlib figure.")
    parser.add_argument(
        "filepath",
        type=str,
        help="Path to the .pickle file containing the figure data"
    )

    # 2. Parse the arguments
    args = parser.parse_args()

    # 3. Validate file existence
    if not os.path.exists(args.filepath):
        print(f"Error: The file '{args.filepath}' does not exist.")
        return

    # 4. Load the figure object back into memory
    print(f"Loading figure from {args.filepath}...")
    with open(args.filepath, "rb") as f:
        fig = pickle.load(f)

    # 5. Show the plot with all pan/zoom features intact
    print("Opening interactive viewer window...")
    plt.show()

if __name__ == "__main__":
    load_and_show_plot()