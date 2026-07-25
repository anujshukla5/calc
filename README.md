# Seed Blend Optimizer Pro

[![Build Android APK](https://github.com/anujshukla5/calc/actions/workflows/build-android.yml/badge.svg)](https://github.com/anujshukla5/calc/actions/workflows/build-android.yml)

A focused Python + CustomTkinter desktop application for optimizing seed-lot blends against maximum quality specifications.

## Run

Python 3.10+ and Tkinter are required. From this folder:

```powershell
python -m pip install -r requirements.txt
python main.py
```

On Windows, double-click `app.pyw` or `main.pyw` to launch without a console window. The application remembers the last entered values, parameter rows, solver mode, FM option, and manual slider position in `%APPDATA%\SeedBlendOptimizerPro\last_values.json`.

CustomTkinter is already available in the current development environment.

## Workflow

1. Enter the fixed good-quality lot quantity and optional desired FM target.
2. Add, remove, or rename quality parameters.
3. Enter percentages for the low lot, good lot, and maximum specification.
4. Use **Optimization** mode to calculate the maximum low seed that can be added, or **Manual** mode to inspect a fixed low-lot quantity with the slider.
5. Save/open projects as JSON and export calculated status rows as CSV.

Blank values are treated as zero. All specifications are maximum limits. Results are rounded to the nearest kilogram. Impossible parameters are reported in the results panel instead of stopping the calculation.

For the original low-lot dilution direction, the optimizer uses:

`Good Seed = L * (LP - S) / (S - GP)`

where `L` is low-lot weight, `LP` is low-lot percentage, `GP` is good-lot percentage, and `S` is the maximum specification. The largest per-parameter requirement is the controlling parameter. When enabled, foreign material is included as a third fixed blending component.

The current reverse workflow fixes the good-lot weight and calculates the maximum low-lot quantity for each parameter. If the calculated blend FM is below the desired FM target, outside FM is reported as a pure FM addition.

## Kivy mobile version

A mobile-friendly Kivy version has been added in `kivy_app.py` with a simplified, single-column screen layout for smaller displays. Run it on desktop with:

```powershell
python kivy_app.py
```

For Android, package the app using Buildozer. A starter `buildozer.spec` file is included in the project root.

This repository also includes a GitHub Actions workflow that builds the Android APK automatically on every push and pull request.

### Buildozer Android packaging

Buildozer is best used from Linux or WSL on Windows. The general steps are:

1. Open a Linux shell, WSL terminal, or Linux VM.
2. Install the required tools:

```bash
sudo apt update
sudo apt install -y python3-pip python3-setuptools git zip unzip openjdk-17-jdk
python3 -m pip install --user buildozer cython
```

3. Change to your project folder:

```bash
cd /mnt/c/Users/anujs/Desktop/Anuj/software/vs
```

4. Build the APK:

```bash
~/.local/bin/buildozer android debug
```

5. Install and run the APK on a connected Android device:

```bash
~/.local/bin/buildozer android debug deploy run
```

### Notes

- The included `buildozer.spec` is configured for `kivy_app.py` as the entry point.
- If you want a custom icon, add `icon.png` and update `icon.filename` in `buildozer.spec`.
- For production, use `buildozer android release` after testing.

Alternatively, you can use the Kivy Launcher app on Android for quick testing without packaging, but Buildozer is the recommended path for a proper APK install.
