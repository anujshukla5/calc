"""Seed Blend Optimizer Pro desktop application."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from seed_blend_optimizer.solver import BlendResult, ReverseBlendResult, solve_reverse_blend


APP_TITLE = "SEED BLEND OPTIMIZER PRO"
DEFAULT_PARAMETERS = ["Dal", "Damaged Seed", "Foreign Material"]
BG = "#101614"
PANEL = "#17221e"
PANEL_ALT = "#1d2b25"
BORDER = "#30483c"
TEXT = "#edf4ef"
MUTED = "#9caf9f"
GREEN = "#63d391"
GREEN_DARK = "#2d8b58"
RED = "#ee847b"
AMBER = "#e7ba65"


class ParameterRow:
    def __init__(self, parent: ctk.CTkFrame, name: str, remove_callback):
        self.name = name
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.name_entry = ctk.CTkEntry(self.frame, width=168, height=34, fg_color=PANEL_ALT, border_color=BORDER)
        self.name_entry.insert(0, name)
        self.name_entry.grid(row=0, column=0, padx=(0, 8))
        self.low_entry = self._entry(1)
        self.good_entry = self._entry(2)
        self.spec_entry = self._entry(3)
        self.remove_button = ctk.CTkButton(self.frame, text="×", width=34, height=34, fg_color="#26332d", hover_color="#693f3d", command=remove_callback)
        self.remove_button.grid(row=0, column=4, padx=(8, 0))

    def _entry(self, column: int) -> ctk.CTkEntry:
        entry = ctk.CTkEntry(self.frame, width=104, height=34, fg_color=PANEL_ALT, border_color=BORDER, placeholder_text="0.00")
        entry.grid(row=0, column=column, padx=4)
        return entry

    def values(self) -> dict[str, str]:
        return {"name": self.name_entry.get().strip(), "low": self.low_entry.get(), "good": self.good_entry.get(), "spec": self.spec_entry.get()}

    def destroy(self) -> None:
        self.frame.destroy()


class SeedBlendApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1240x790")
        self.minsize(1040, 700)
        self.configure(fg_color=BG)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.rows: list[ParameterRow] = []
        self.current_result: ReverseBlendResult | None = None
        self.project_path: Path | None = None
        self.mode = ctk.StringVar(value="Optimization")
        self.low_quantity = ctk.DoubleVar(value=0)
        self.foreign_enabled = ctk.BooleanVar(value=False)
        self.persistence_path = Path.home() / "AppData" / "Roaming" / "SeedBlendOptimizerPro" / "last_values.json"
        self._build()
        for parameter in DEFAULT_PARAMETERS:
            self.add_parameter(parameter)
        self._load_last_values()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._set_status("Ready. Previous inputs are restored automatically.", "info")

    def _build(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_sidebar()
        self._build_main()
        self._build_statusbar()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, height=68, fg_color="#14201b", corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text="SB", text_color=GREEN, font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=(24, 12), pady=16)
        ctk.CTkLabel(header, text=APP_TITLE, text_color=TEXT, font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=1, sticky="w")
        tools = ctk.CTkFrame(header, fg_color="transparent")
        tools.grid(row=0, column=2, padx=20)
        self._tool_button(tools, "New", self.new_project).pack(side="left", padx=3)
        self._tool_button(tools, "Open", self.open_project).pack(side="left", padx=3)
        self._tool_button(tools, "Save", self.save_project).pack(side="left", padx=3)
        self._tool_button(tools, "Export CSV", self.export_csv).pack(side="left", padx=3)
        ctk.CTkButton(tools, text="About", width=68, height=30, fg_color=GREEN_DARK, hover_color="#3ba96b", command=self.show_about).pack(side="left", padx=(12, 0))

    def _tool_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, width=68, height=30, fg_color="#263b31", hover_color="#355743", command=command)

    def _build_sidebar(self) -> None:
        side = ctk.CTkFrame(self, width=266, fg_color=PANEL, corner_radius=0)
        side.grid(row=1, column=0, sticky="nsew")
        side.grid_propagate(False)
        ctk.CTkLabel(side, text="BLEND INPUT", text_color=GREEN, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=22, pady=(24, 16))
        self._field(side, "Good quality lot (kg)", "1000", "good_quantity_entry")
        self._field(side, "Desired FM target (%)", "0", "fm_target_entry")
        ctk.CTkCheckBox(side, text="Add outside FM if needed", variable=self.foreign_enabled, text_color=MUTED, fg_color=GREEN_DARK, hover_color="#3ba96b", command=self._foreign_toggled).pack(anchor="w", padx=22, pady=(0, 8))
        ctk.CTkLabel(side, text="SOLVER MODE", text_color=GREEN, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=22, pady=(28, 10))
        ctk.CTkSegmentedButton(side, values=["Optimization", "Manual"], variable=self.mode, command=self._mode_changed).pack(fill="x", padx=22)
        self.manual_label = ctk.CTkLabel(side, text="Low seed quantity: 0 kg", text_color=MUTED)
        self.manual_label.pack(anchor="w", padx=22, pady=(22, 7))
        self.manual_slider = ctk.CTkSlider(side, from_=0, to=10000, variable=self.low_quantity, command=self._manual_changed, progress_color=GREEN_DARK, button_color=GREEN, button_hover_color="#93e7b2")
        self.manual_slider.pack(fill="x", padx=22)
        self.manual_slider.configure(state="disabled")
        ctk.CTkLabel(side, text="Set a fixed low-lot quantity in Manual mode.", text_color="#708278", wraplength=210, justify="left").pack(anchor="w", padx=22, pady=(8, 22))
        self.calculate_button = ctk.CTkButton(side, text="Calculate blend", height=42, fg_color=GREEN_DARK, hover_color="#3ba96b", font=ctk.CTkFont(size=14, weight="bold"), command=self.calculate)
        self.calculate_button.pack(fill="x", padx=22, pady=(16, 8))
        ctk.CTkLabel(side, text="Maximum specifications only\nBlank values are treated as zero\nGood lot availability is ignored", text_color="#708278", justify="left", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=22, pady=18)

    def _field(self, parent, label: str, value: str, attribute: str) -> None:
        ctk.CTkLabel(parent, text=label, text_color=MUTED).pack(anchor="w", padx=22, pady=(0, 5))
        entry = ctk.CTkEntry(parent, height=36, fg_color=PANEL_ALT, border_color=BORDER)
        entry.insert(0, value)
        entry.pack(fill="x", padx=22, pady=(0, 14))
        setattr(self, attribute, entry)

    def _build_main(self) -> None:
        tabs = ctk.CTkTabview(self, fg_color=BG, segmented_button_fg_color=PANEL, segmented_button_selected_color=GREEN_DARK, segmented_button_selected_hover_color="#3ba96b")
        tabs.grid(row=1, column=1, sticky="nsew", padx=24, pady=16)
        tabs.add("Blend Calculator")
        tabs.add("Profit")
        self.main_tabs = tabs
        main = tabs.tab("Blend Calculator")
        main.configure(fg_color=BG)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)
        heading = ctk.CTkFrame(main, fg_color="transparent")
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        ctk.CTkLabel(heading, text="Quality parameters", text_color=TEXT, font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkButton(heading, text="＋ Add parameter", width=130, height=32, fg_color="#263b31", hover_color="#355743", command=lambda: self.add_parameter("New parameter")).pack(side="right")
        self._build_parameter_panel(main)
        self._build_results_panel(main)
        self._build_profit_tab(tabs.tab("Profit"))

    def _build_profit_tab(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(parent, text="Profit analysis", text_color=TEXT, font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(8, 18))
        inputs = ctk.CTkFrame(parent, fg_color=PANEL, border_color=BORDER, border_width=1, corner_radius=8)
        inputs.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        inputs.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(inputs, text="Enter prices per kilogram", text_color=GREEN, font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(16, 12))
        self._profit_field(inputs, "Low lot price / kg", "low_price")
        self._profit_field(inputs, "Good lot price / kg", "good_price")
        self._profit_field(inputs, "Outside FM price / kg", "fm_price")
        self._profit_field(inputs, "Selling price / kg", "selling_price")
        ctk.CTkButton(inputs, text="Calculate profit", height=38, fg_color=GREEN_DARK, hover_color="#3ba96b", command=self.calculate_profit).grid(row=5, column=0, columnspan=2, sticky="ew", padx=18, pady=(10, 18))
        self.profit_results = ctk.CTkScrollableFrame(parent, fg_color=PANEL, border_color=BORDER, border_width=1, corner_radius=8)
        self.profit_results.grid(row=2, column=0, sticky="nsew")
        ctk.CTkLabel(self.profit_results, text="Calculate a blend first, then enter prices to see the average rate and profit.", text_color=MUTED, wraplength=650, justify="left").pack(anchor="w", padx=18, pady=24)

    def _profit_field(self, parent, label: str, attribute: str) -> None:
        row = parent.grid_size()[1]
        ctk.CTkLabel(parent, text=label, text_color=MUTED).grid(row=row, column=0, sticky="w", padx=18, pady=6)
        entry = ctk.CTkEntry(parent, width=180, height=34, fg_color=PANEL_ALT, border_color=BORDER, placeholder_text="0.00")
        entry.grid(row=row, column=1, sticky="e", padx=18, pady=6)
        setattr(self, attribute, entry)

    def calculate_profit(self) -> None:
        if not self.current_result:
            self._set_status("Calculate the blend before calculating profit.", "warning")
            self.main_tabs.set("Blend Calculator")
            return
        try:
            low_price = float(self.low_price.get() or 0)
            good_price = float(self.good_price.get() or 0)
            fm_price = float(self.fm_price.get() or 0)
            selling_price = float(self.selling_price.get() or 0)
            if min(low_price, good_price, fm_price, selling_price) < 0:
                raise ValueError
        except ValueError:
            self._set_status("Enter valid non-negative prices in the Profit tab.", "error")
            return

        low_kg = self.current_result.allowed_low_kg
        good_kg = self.current_result.good_quantity_kg
        fm_kg = self.current_result.outside_fm_kg if self.foreign_enabled.get() else 0
        total_kg = low_kg + good_kg + fm_kg
        total_cost = low_kg * low_price + good_kg * good_price + fm_kg * fm_price
        average_rate = total_cost / total_kg if total_kg else 0
        profit_per_kg = selling_price - average_rate
        total_profit = profit_per_kg * total_kg
        self._save_last_values()
        for widget in self.profit_results.winfo_children():
            widget.destroy()
        self._profit_result("Low seed quantity", f"{low_kg:,} kg")
        self._profit_result("Good seed quantity", f"{good_kg:,} kg")
        self._profit_result("Outside FM quantity", f"{fm_kg:,} kg")
        self._profit_result("Total blend weight", f"{total_kg:,} kg")
        self._profit_result("Total blend cost", f"{total_cost:,.2f}")
        self._profit_result("Average cost rate", f"{average_rate:,.2f} / kg")
        self._profit_result("Selling rate", f"{selling_price:,.2f} / kg")
        self._profit_result("Profit per kg", f"{profit_per_kg:,.2f}", GREEN if profit_per_kg >= 0 else RED)
        self._profit_result("Total profit", f"{total_profit:,.2f}", GREEN if total_profit >= 0 else RED)
        self._set_status("Profit analysis updated.", "success" if total_profit >= 0 else "warning")

    def _profit_result(self, label: str, value: str, color: str = TEXT) -> None:
        row = ctk.CTkFrame(self.profit_results, fg_color=PANEL_ALT, corner_radius=5)
        row.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(row, text=label, text_color=MUTED, anchor="w").pack(side="left", padx=12, pady=9)
        ctk.CTkLabel(row, text=value, text_color=color, anchor="e", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=12, pady=9)

    def _build_parameter_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, fg_color=PANEL, border_color=BORDER, border_width=1, corner_radius=8)
        panel.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        panel.grid_columnconfigure(0, weight=1)
        labels = ["Parameter", "Low lot %", "Good lot %", "Maximum spec %", ""]
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        widths = [168, 104, 104, 104, 34]
        for index, (label, width) in enumerate(zip(labels, widths)):
            ctk.CTkLabel(header, text=label, width=width, anchor="w", text_color=MUTED, font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=index, padx=4)
        self.parameter_container = ctk.CTkFrame(panel, fg_color="transparent")
        self.parameter_container.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

    def _build_results_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, fg_color=PANEL, border_color=BORDER, border_width=1, corner_radius=8)
        panel.grid(row=2, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        top = ctk.CTkFrame(panel, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=16)
        ctk.CTkLabel(top, text="Blend result", text_color=TEXT, font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        self.result_summary = ctk.CTkLabel(top, text="No calculation yet", text_color=MUTED)
        self.result_summary.pack(side="right")
        self.results_box = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.results_box.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 12))
        self._render_empty_results()

    def _build_statusbar(self) -> None:
        self.status = ctk.CTkLabel(self, text="", height=32, fg_color="#16231d", text_color=MUTED, anchor="w", padx=18)
        self.status.grid(row=2, column=0, columnspan=2, sticky="ew")

    def add_parameter(self, name: str) -> None:
        row = ParameterRow(self.parameter_container, name, lambda: self.remove_parameter(row))
        row.frame.pack(fill="x", pady=4)
        self.rows.append(row)

    def remove_parameter(self, row: ParameterRow) -> None:
        if len(self.rows) <= 1:
            self._set_status("Keep at least one quality parameter.", "warning")
            return
        row.destroy()
        self.rows.remove(row)

    def _mode_changed(self, value: str) -> None:
        enabled = "normal" if value == "Manual" else "disabled"
        self.manual_slider.configure(state=enabled)
        self.calculate_button.configure(text="Evaluate manual blend" if value == "Manual" else "Calculate blend")
        if value == "Manual":
            self._set_status("Manual mode active. Move the slider to inspect a fixed quantity.", "info")

    def _foreign_toggled(self) -> None:
        self._set_status("Foreign material is included in the blend." if self.foreign_enabled.get() else "Foreign material is excluded from the blend.", "info")

    def _manual_changed(self, value: float) -> None:
        self.manual_label.configure(text=f"Low seed quantity: {round(float(value)):,} kg")
        if self.mode.get() == "Manual":
            self.calculate()

    def _read_inputs(self) -> tuple[dict, dict, dict, float, float]:
        low_values, good_values, specifications = {}, {}, {}
        for row in self.rows:
            values = row.values()
            name = values["name"] or "Unnamed parameter"
            low_values[name] = values["low"]
            good_values[name] = values["good"]
            specifications[name] = values["spec"]
        return low_values, good_values, specifications, float(self.good_quantity_entry.get() or 0), float(self.fm_target_entry.get() or 0)

    def calculate(self) -> None:
        try:
            low_values, good_values, specifications, good_quantity, fm_target = self._read_inputs()
            result = solve_reverse_blend(good_quantity, low_values, good_values, specifications, fm_target if self.foreign_enabled.get() else 0)
            if self.mode.get() == "Manual":
                result = self._evaluate_manual(result, good_values, specifications, low_values, good_quantity)
            self.current_result = result
            self._save_last_values()
            self._render_results(result)
            tone = "success" if result.overall_pass else "warning"
            self._set_status("Blend meets all specifications." if result.overall_pass else "Review the highlighted parameters and any impossible specifications.", tone)
        except ValueError:
            self._set_status("Enter numeric values for lot quantities.", "error")

    def _save_last_values(self) -> None:
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            self.persistence_path.write_text(json.dumps({
                "good_quantity_kg": self.good_quantity_entry.get(),
                "fm_target": self.fm_target_entry.get(),
                "outside_fm_enabled": self.foreign_enabled.get(),
                "mode": self.mode.get(),
                "low_slider": self.low_quantity.get(),
                "prices": {
                    "low": self.low_price.get(),
                    "good": self.good_price.get(),
                    "fm": self.fm_price.get(),
                    "selling": self.selling_price.get(),
                },
                "parameters": [row.values() for row in self.rows],
            }, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _load_last_values(self) -> None:
        if not self.persistence_path.exists():
            return
        try:
            data = json.loads(self.persistence_path.read_text(encoding="utf-8"))
            self.good_quantity_entry.delete(0, "end")
            self.good_quantity_entry.insert(0, str(data.get("good_quantity_kg", "1000")))
            self.fm_target_entry.delete(0, "end")
            self.fm_target_entry.insert(0, str(data.get("fm_target", "0")))
            self.foreign_enabled.set(bool(data.get("outside_fm_enabled", False)))
            self.mode.set(data.get("mode", "Optimization"))
            self.low_quantity.set(float(data.get("low_slider", 0)))
            prices = data.get("prices", {})
            for entry, key in [(self.low_price, "low"), (self.good_price, "good"), (self.fm_price, "fm"), (self.selling_price, "selling")]:
                entry.delete(0, "end")
                entry.insert(0, str(prices.get(key, "")))
            saved_parameters = data.get("parameters", [])
            if saved_parameters:
                for row in self.rows:
                    row.destroy()
                self.rows.clear()
                for parameter in saved_parameters:
                    self.add_parameter(parameter.get("name", "Parameter"))
                    row = self.rows[-1]
                    for entry, key in [(row.low_entry, "low"), (row.good_entry, "good"), (row.spec_entry, "spec")]:
                        entry.insert(0, str(parameter.get(key, "")))
            self._mode_changed(self.mode.get())
            self._manual_changed(self.low_quantity.get())
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return

    def _close(self) -> None:
        self._save_last_values()
        self.destroy()

    def _evaluate_manual(self, optimized: ReverseBlendResult, good_values, specifications, low_values, good_quantity) -> ReverseBlendResult:
        quantity = round(self.low_quantity.get())
        rows = []
        total = good_quantity + quantity
        for item in optimized.parameters:
            if item.specification is None:
                rows.append(item)
                continue
            low_mass = quantity * item.low_value + good_quantity * item.good_value
            final = low_mass / total if total else 0
            meets = final <= item.specification + 1e-9
            rows.append(item.__class__(item.name, item.specification, item.low_value, item.good_value, item.foreign_value, final, item.required_good_kg, meets, item.impossible, "Pass" if meets else f"Maximum {item.required_good_kg:,} kg low seed"))
        outside_fm = 0
        fm_item = next((item for item in optimized.parameters if item.name == "Foreign Material"), None)
        if self.foreign_enabled.get() and fm_item and optimized.fm_target > 0 and optimized.fm_target < 100:
            current_fm_mass = good_quantity * fm_item.good_value + quantity * fm_item.low_value
            target_mass = optimized.fm_target * total
            if current_fm_mass < target_mass:
                outside_fm = round((target_mass - current_fm_mass) / (100 - optimized.fm_target))
        return ReverseBlendResult(quantity, optimized.controlling_parameter, tuple(rows), bool(rows) and all(item.meets_specification and not item.impossible for item in rows if item.specification is not None), good_quantity, outside_fm, optimized.fm_target)

    def _render_empty_results(self) -> None:
        ctk.CTkLabel(self.results_box, text="Your calculated quality status will appear here.", text_color=MUTED).pack(pady=42)

    def _render_results(self, result: ReverseBlendResult) -> None:
        for widget in self.results_box.winfo_children():
            widget.destroy()
        self.result_summary.configure(text=f"Controlling parameter: {result.controlling_parameter}  |  Outside FM: {result.outside_fm_kg:,} kg")
        summary = ctk.CTkFrame(self.results_box, fg_color="#20382b", corner_radius=8)
        summary.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(summary, text=f"{result.allowed_low_kg:,} kg", text_color=GREEN, font=ctk.CTkFont(size=28, weight="bold")).pack(side="left", padx=18, pady=12)
        ctk.CTkLabel(summary, text=f"maximum low seed to add  |  FM to add: {result.outside_fm_kg:,} kg", text_color=TEXT).pack(side="left")
        badge = "PASS" if result.overall_pass else "REVIEW"
        ctk.CTkLabel(summary, text=badge, text_color=BG if result.overall_pass else BG, fg_color=GREEN if result.overall_pass else AMBER, corner_radius=5, padx=10, pady=5, font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=18)
        for item in result.parameters:
            self._result_row(item)
        if result.alternatives:
            ctk.CTkLabel(self.results_box, text="Composition alternatives", text_color=GREEN, anchor="w", font=ctk.CTkFont(size=14, weight="bold")).pack(fill="x", pady=(18, 6))
            ctk.CTkLabel(self.results_box, text="Each option makes one parameter meet its maximum. Compensation shows low seed to remove when another parameter fails.", text_color=MUTED, anchor="w", wraplength=760, justify="left").pack(fill="x", pady=(0, 8))
            for alternative in result.alternatives:
                self._alternative_panel(alternative)

    def _alternative_panel(self, alternative) -> None:
        panel = ctk.CTkFrame(self.results_box, fg_color="#1b2a23", border_color=BORDER, border_width=1, corner_radius=6)
        panel.pack(fill="x", pady=4)
        ctk.CTkLabel(panel, text=f"{alternative.controlling_parameter}-controlled composition: {alternative.low_quantity_kg:,} kg low seed", text_color=TEXT, anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=12, pady=(9, 5))
        for value in alternative.values:
            if value.final_percentage is None:
                continue
            status = "PASS" if value.meets_specification else f"FAIL; remove {round(value.compensation_low_kg):,} kg low seed"
            color = GREEN if value.meets_specification else AMBER
            ctk.CTkLabel(panel, text=f"{value.name}: {value.final_percentage:.2f}% ({value.final_kg:,.1f} kg) | {status}", text_color=color, anchor="w").pack(fill="x", padx=22, pady=2)
        ctk.CTkFrame(panel, height=6, fg_color="transparent").pack()

    def _result_row(self, item) -> None:
        row = ctk.CTkFrame(self.results_box, fg_color=PANEL_ALT, corner_radius=6)
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(1, weight=1)
        color = RED if item.impossible else (GREEN if item.meets_specification else AMBER)
        mark = "!" if item.impossible else ("✓" if item.meets_specification else "·")
        ctk.CTkLabel(row, text=mark, width=30, text_color=color, font=ctk.CTkFont(size=17, weight="bold")).grid(row=0, column=0, padx=(10, 2), pady=9)
        ctk.CTkLabel(row, text=item.name, text_color=TEXT, width=150, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w")
        value = "—" if item.final_value is None else f"{item.final_value:.2f}%"
        ctk.CTkLabel(row, text=value, text_color=color, width=90, anchor="e").grid(row=0, column=2, padx=12)
        ctk.CTkLabel(row, text=f"max {item.specification:.2f}%" if item.specification is not None else "no spec", text_color=MUTED, width=100, anchor="e").grid(row=0, column=3, padx=8)
        difference = ""
        if item.difference_from_specification is not None:
            difference = f"  ({item.difference_from_specification:.2f}% below max)"
        ctk.CTkLabel(row, text=item.detail + difference, text_color=color, anchor="w").grid(row=0, column=4, sticky="ew", padx=(8, 14))

    def project_data(self) -> dict:
        low_values, good_values, specifications, good_quantity, fm_target = self._read_inputs()
        return {"good_quantity_kg": good_quantity, "fm_target": fm_target, "outside_fm_enabled": self.foreign_enabled.get(), "parameters": [{"name": name, "low": low_values[name], "good": good_values[name], "spec": specifications[name]} for name in specifications], "results": self._result_data()}

    def _result_data(self) -> dict | None:
        if not self.current_result:
            return None
        return {"allowed_low_kg": self.current_result.allowed_low_kg, "outside_fm_kg": self.current_result.outside_fm_kg, "controlling_parameter": self.current_result.controlling_parameter, "overall_pass": self.current_result.overall_pass}

    def new_project(self) -> None:
        for row in self.rows:
            row.destroy()
        self.rows.clear()
        self.good_quantity_entry.delete(0, "end")
        self.good_quantity_entry.insert(0, "1000")
        self.fm_target_entry.delete(0, "end")
        self.fm_target_entry.insert(0, "0")
        self.foreign_enabled.set(False)
        for parameter in DEFAULT_PARAMETERS:
            self.add_parameter(parameter)
        self.project_path = None
        self._set_status("New project created.", "success")

    def save_project(self) -> None:
        path = self.project_path or Path(filedialog.asksaveasfilename(title="Save project", defaultextension=".json", filetypes=[("JSON project", "*.json")]))
        if not path:
            return
        path.write_text(json.dumps(self.project_data(), indent=2), encoding="utf-8")
        self.project_path = Path(path)
        self._set_status(f"Saved project: {self.project_path.name}", "success")

    def open_project(self) -> None:
        selected = filedialog.askopenfilename(title="Open project", filetypes=[("JSON project", "*.json")])
        if not selected:
            return
        data = json.loads(Path(selected).read_text(encoding="utf-8"))
        self.new_project()
        self.good_quantity_entry.delete(0, "end")
        self.good_quantity_entry.insert(0, str(data.get("good_quantity_kg", 1000)))
        self.fm_target_entry.delete(0, "end")
        self.fm_target_entry.insert(0, str(data.get("fm_target", 0)))
        self.foreign_enabled.set(bool(data.get("outside_fm_enabled", False)))
        for row in self.rows:
            row.destroy()
        self.rows.clear()
        for parameter in data.get("parameters", []):
            self.add_parameter(parameter.get("name", "Parameter"))
            row = self.rows[-1]
            for entry, key in [(row.low_entry, "low"), (row.good_entry, "good"), (row.spec_entry, "spec")]:
                entry.insert(0, str(parameter.get(key, "")))
        self.project_path = Path(selected)
        self._set_status(f"Opened project: {self.project_path.name}", "success")

    def export_csv(self) -> None:
        if not self.current_result:
            self.calculate()
        if not self.current_result:
            return
        selected = filedialog.asksaveasfilename(title="Export results", defaultextension=".csv", filetypes=[("CSV file", "*.csv")])
        if not selected:
            return
        with open(selected, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Parameter", "Low lot %", "Good lot %", "Final %", "Maximum spec %", "Difference below max %", "Status", "Detail"])
            for item in self.current_result.parameters:
                writer.writerow([item.name, item.low_value, item.good_value, item.final_value, item.specification, item.difference_from_specification, "PASS" if item.meets_specification else "FAIL", item.detail])
        self._set_status(f"Exported results: {Path(selected).name}", "success")

    def show_about(self) -> None:
        messagebox.showinfo("About Seed Blend Optimizer Pro", "Seed Blend Optimizer Pro\n\nA focused quality blending calculator for seed lots.\nVersion 1.0.0")

    def _set_status(self, message: str, tone: str) -> None:
        colors = {"success": GREEN, "warning": AMBER, "error": RED, "info": MUTED}
        self.status.configure(text=message, text_color=colors.get(tone, MUTED))


if __name__ == "__main__":
    SeedBlendApp().mainloop()
