import os
import sys
import matplotlib

# Force non-GUI backend before any plotting happens
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import pickle
from click.testing import CliRunner
from msnoise.scripts.msnoise import cli


def savepkl(cmd_string, save_path):
    """
    Runs an MSNoise command using CliRunner in the current process,
    then saves the resulting matplotlib figure to interactive HTML.
    """
    # 1. Clean the command string to remove the word "msnoise" if present
    # CliRunner just needs the subcommands (e.g., ['plot', 'distance', '-f', '1'])
    args = cmd_string.split()
    if args[0] == "msnoise":
        args = args[1:]

    # 2. Use CliRunner to execute the command with proper context initialization
    runner = CliRunner()
    result = runner.invoke(cli, args, obj={})  # obj={} fixes the NoneType error

    success = result.exit_code == 0
    if not success:
        print(f"Error running MSNoise command:\n{result.output}")
        if result.exception:
            print(f"Exception details: {result.exception}")

    # 3. Capture the figure and save to HTML
    if success:
        fig = plt.gcf()

        # Build your output paths
        dirname, file = os.path.split(save_path)
        output = os.path.join(dirname, "interactive", file.replace(".png", ".pickle"))
        os.makedirs(os.path.dirname(output), exist_ok=True)

        # Save to interactive HTML
        with open(output, "wb") as f:
            pickle.dump(fig, f)

        # Clear the figure canvas so the next loop starts completely fresh
        plt.close(fig)

    return success