from __future__ import annotations

from pathlib import Path
from typing import Any

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager

from seed_blend_optimizer.solver import CompositionAlternative, ParameterResult, ReverseBlendResult, solve_reverse_blend

KV = """
<ParameterRow>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '46dp'
    spacing: '4dp'
    padding: ['8dp', '4dp', '8dp', '4dp']
    canvas.before:
        Color:
            rgba: 0.10, 0.13, 0.12, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]

    TextInput:
        id: name_input
        text: root.name
        hint_text: 'Parameter'
        multiline: False
        size_hint_x: 0.35
        background_color: 0.10, 0.15, 0.14, 1
        foreground_color: 1, 1, 1, 1
        halign: 'left'

    TextInput:
        id: low_input
        text: root.low
        hint_text: 'Low %'
        multiline: False
        input_filter: 'float'
        size_hint_x: 0.2
        background_color: 0.10, 0.15, 0.14, 1
        foreground_color: 1, 1, 1, 1

    TextInput:
        id: good_input
        text: root.good
        hint_text: 'Good %'
        multiline: False
        input_filter: 'float'
        size_hint_x: 0.2
        background_color: 0.10, 0.15, 0.14, 1
        foreground_color: 1, 1, 1, 1

    TextInput:
        id: spec_input
        text: root.spec
        hint_text: 'Max %'
        multiline: False
        input_filter: 'float'
        size_hint_x: 0.2
        background_color: 0.10, 0.15, 0.14, 1
        foreground_color: 1, 1, 1, 1

    Button:
        text: '×'
        size_hint_x: None
        width: '40dp'
        on_release: root.remove_row()
        background_color: 0.71, 0.58, 0.39, 1
        color: 0, 0, 0, 1

<SeedBlendMobileRoot>:
    orientation: 'vertical'
    spacing: '4dp'
    canvas.before:
        Color:
            rgba: 0.06, 0.09, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: '56dp'
        padding: ['12dp', '10dp']
        spacing: '10dp'
        canvas.before:
            Color:
                rgba: 0.10, 0.14, 0.12, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'Seed Blend Optimizer'
            bold: True
            color: 0.72, 0.92, 0.68, 1
            halign: 'left'
            valign: 'middle'
            text_size: self.size

    ScreenManager:
        id: screen_manager
        transition: NoTransition()

        Screen:
            name: 'input'
            BoxLayout:
                orientation: 'vertical'
                padding: ['12dp', '12dp', '12dp', '0dp']
                spacing: '10dp'

                ScrollView:
                    BoxLayout:
                        id: input_panel
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: '10dp'

                        Label:
                            text: 'Blend inputs'
                            size_hint_y: None
                            height: '32dp'
                            bold: True
                            color: 0.92, 0.96, 0.88, 1
                            halign: 'left'
                            valign: 'middle'
                            text_size: self.size

                        BoxLayout:
                            size_hint_y: None
                            height: '44dp'
                            spacing: '8dp'
                            Label:
                                text: 'Good lot (kg)'
                                size_hint_x: 0.5
                                color: 0.86, 0.92, 0.85, 1
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                            TextInput:
                                id: good_quantity_input
                                text: '1000'
                                multiline: False
                                input_filter: 'float'
                                halign: 'center'

                        BoxLayout:
                            size_hint_y: None
                            height: '44dp'
                            spacing: '8dp'
                            Label:
                                text: 'FM target (%)'
                                size_hint_x: 0.5
                                color: 0.86, 0.92, 0.85, 1
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                            TextInput:
                                id: fm_target_input
                                text: '0'
                                multiline: False
                                input_filter: 'float'
                                halign: 'center'

                        BoxLayout:
                            size_hint_y: None
                            height: '44dp'
                            spacing: '8dp'
                            Label:
                                text: 'Add outside FM if needed'
                                color: 0.86, 0.92, 0.85, 1
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                            ToggleButton:
                                id: fm_switch
                                text: 'No'
                                group: 'fm'
                                state: 'normal'
                                on_state:
                                    self.text = 'Yes' if self.state == 'down' else 'No'
                                on_press: root.update_fm_enabled(self.state == 'down')
                                size_hint_x: 0.3
                        BoxLayout:
                            size_hint_y: None
                            height: '44dp'
                            spacing: '8dp'
                            Label:
                                text: 'Mode'
                                size_hint_x: 0.5
                                color: 0.86, 0.92, 0.85, 1
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                            Spinner:
                                id: mode_spinner
                                text: 'Optimization'
                                values: ['Optimization', 'Manual']
                                size_hint_x: 0.5
                                on_text: root.update_mode(self.text)

                        BoxLayout:
                            size_hint_y: None
                            height: '44dp'
                            spacing: '8dp'
                            Label:
                                text: 'Low quantity fixed:'
                                size_hint_x: 0.55
                                color: 0.86, 0.92, 0.85, 1
                                halign: 'left'
                                valign: 'middle'
                                text_size: self.size
                            Label:
                                id: low_label
                                text: '0 kg'
                                size_hint_x: 0.45
                                color: 0.90, 0.97, 0.76, 1
                                halign: 'right'
                                valign: 'middle'
                                text_size: self.size

                        Slider:
                            id: low_slider
                            min: 0
                            max: 10000
                            value: 0
                            disabled: True
                            on_value: root.update_low_label(self.value)

                        Button:
                            text: 'Calculate blend'
                            size_hint_y: None
                            height: '48dp'
                            background_color: 0.35, 0.59, 0.36, 1
                            on_release: root.calculate_blend()

                        Label:
                            text: 'Use the Parameters screen to edit seed quality percentages and max specs.'
                            color: 0.76, 0.83, 0.78, 1
                            size_hint_y: None
                            height: '52dp'
                            text_size: self.width, None
                            halign: 'left'
                            valign: 'top'

        Screen:
            name: 'parameters'
            BoxLayout:
                orientation: 'vertical'
                padding: ['12dp', '12dp', '12dp', '12dp']
                spacing: '8dp'
                BoxLayout:
                    size_hint_y: None
                    height: '42dp'
                    spacing: '8dp'
                    Label:
                        text: 'Quality parameters'
                        bold: True
                        color: 0.92, 0.96, 0.88, 1
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    Button:
                        text: '+ Add'
                        size_hint_x: None
                        width: '88dp'
                        on_release: root.add_parameter()
                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True
                    GridLayout:
                        id: parameter_list
                        cols: 1
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: '6dp'
                Label:
                    id: parameter_hint
                    text: 'Tap parameter names and percentages to edit. Remove rows with the × button.'
                    color: 0.75, 0.82, 0.76, 1
                    size_hint_y: None
                    height: '48dp'
                    text_size: self.width, None
                    halign: 'left'
                    valign: 'middle'

        Screen:
            name: 'results'
            BoxLayout:
                orientation: 'vertical'
                padding: ['12dp', '12dp', '12dp', '12dp']
                spacing: '8dp'
                Label:
                    text: 'Blend Results'
                    size_hint_y: None
                    height: '32dp'
                    bold: True
                    color: 0.92, 0.96, 0.88, 1
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size
                Label:
                    id: results_summary
                    text: 'No calculation yet.'
                    size_hint_y: None
                    height: '42dp'
                    color: 0.82, 0.90, 0.83, 1
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size
                ScrollView:
                    do_scroll_x: False
                    BoxLayout:
                        id: results_container
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: '6dp'
                Label:
                    id: review_hint
                    text: 'Review parameter status, pass/fail badges, and composition alternatives if shown.'
                    color: 0.75, 0.82, 0.76, 1
                    size_hint_y: None
                    height: '48dp'
                    text_size: self.width, None
                    halign: 'left'
                    valign: 'middle'

        Screen:
            name: 'profit'
            BoxLayout:
                orientation: 'vertical'
                padding: ['12dp', '12dp', '12dp', '12dp']
                spacing: '10dp'
                Label:
                    text: 'Profit analysis'
                    size_hint_y: None
                    height: '32dp'
                    bold: True
                    color: 0.92, 0.96, 0.88, 1
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size
                GridLayout:
                    cols: 2
                    size_hint_y: None
                    height: self.minimum_height
                    row_default_height: '44dp'
                    row_force_default: True
                    spacing: '8dp'
                    Label:
                        text: 'Low lot price / kg'
                        color: 0.86, 0.92, 0.85, 1
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: low_price_input
                        text: '0'
                        multiline: False
                        input_filter: 'float'
                    Label:
                        text: 'Good lot price / kg'
                        color: 0.86, 0.92, 0.85, 1
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: good_price_input
                        text: '0'
                        multiline: False
                        input_filter: 'float'
                    Label:
                        text: 'Outside FM price / kg'
                        color: 0.86, 0.92, 0.85, 1
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: fm_price_input
                        text: '0'
                        multiline: False
                        input_filter: 'float'
                    Label:
                        text: 'Selling price / kg'
                        color: 0.86, 0.92, 0.85, 1
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    TextInput:
                        id: selling_price_input
                        text: '0'
                        multiline: False
                        input_filter: 'float'
                Button:
                    text: 'Calculate profit'
                    size_hint_y: None
                    height: '48dp'
                    background_color: 0.35, 0.59, 0.36, 1
                    on_release: root.calculate_profit()
                ScrollView:
                    do_scroll_x: False
                    BoxLayout:
                        id: profit_container
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: '6dp'
                        padding: ['0dp', '4dp', '0dp', '4dp']

    BoxLayout:
        size_hint_y: None
        height: '52dp'
        spacing: '2dp'
        padding: ['4dp', '4dp']
        canvas.before:
            Color:
                rgba: 0.09, 0.14, 0.11, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Button:
            text: 'Inputs'
            on_release: root.switch_screen('input')
        Button:
            text: 'Params'
            on_release: root.switch_screen('parameters')
        Button:
            text: 'Results'
            on_release: root.switch_screen('results')
        Button:
            text: 'Profit'
            on_release: root.switch_screen('profit')
"""


class ParameterRow(BoxLayout):
    name = StringProperty("Parameter")
    low = StringProperty("")
    good = StringProperty("")
    spec = StringProperty("")
    app = ObjectProperty(None)

    def remove_row(self) -> None:
        if self.app:
            self.app.remove_parameter(self)


class SeedBlendMobileRoot(BoxLayout):
    fm_enabled = BooleanProperty(False)
    mode = StringProperty("Optimization")
    low_quantity = NumericProperty(0)
    current_result: ReverseBlendResult | None = None
    store: JsonStore | None = None
    parameter_rows: ListProperty[Any] = ListProperty([])

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.persistence_path = Path.home() / '.seed_blend_optimizer_mobile.json'
        self.store = JsonStore(str(self.persistence_path))
        self.add_parameter('Dal')
        self.add_parameter('Damaged Seed')
        self.add_parameter('Foreign Material')
        self.load_state()
        self.update_low_label(self.ids.low_slider.value)

    def add_parameter(self, name: str = 'New parameter') -> None:
        row = ParameterRow(name=name, low='', good='', spec='', app=self)
        self.ids.parameter_list.add_widget(row)
        self.parameter_rows.append(row)

    def remove_parameter(self, row: ParameterRow) -> None:
        if len(self.parameter_rows) <= 1:
            self.show_message('Keep at least one quality parameter.')
            return
        self.ids.parameter_list.remove_widget(row)
        self.parameter_rows.remove(row)

    def update_fm_enabled(self, active: bool) -> None:
        self.fm_enabled = active

    def update_mode(self, mode_text: str) -> None:
        self.mode = mode_text
        self.ids.low_slider.disabled = mode_text != 'Manual'
        if mode_text == 'Optimization':
            self.ids.low_label.text = '0 kg'
            self.ids.low_slider.value = 0

    def update_low_label(self, value: float) -> None:
        self.low_quantity = int(value)
        self.ids.low_label.text = f'{int(value):,} kg'

    def switch_screen(self, name: str) -> None:
        self.ids.screen_manager.current = name

    def gather_inputs(self) -> tuple[dict[str, str], dict[str, str], dict[str, str], float, float]:
        low_values = {}
        good_values = {}
        specs = {}
        for row in self.parameter_rows:
            name = row.ids.name_input.text.strip() or 'Parameter'
            low_values[name] = row.ids.low_input.text
            good_values[name] = row.ids.good_input.text
            specs[name] = row.ids.spec_input.text
        good_quantity = self._to_float(self.ids.good_quantity_input.text)
        fm_target = self._to_float(self.ids.fm_target_input.text)
        return low_values, good_values, specs, good_quantity, fm_target

    def calculate_blend(self) -> None:
        try:
            low_values, good_values, specs, good_quantity, fm_target = self.gather_inputs()
            result = solve_reverse_blend(
                good_quantity,
                low_values,
                good_values,
                specs,
                fm_target if self.fm_enabled else 0,
            )
            if self.mode == 'Manual':
                result = self.evaluate_manual(result, self.low_quantity)
            self.current_result = result
            self.render_results(result)
            self.ids.results_summary.text = f'Max low seed {result.allowed_low_kg:,} kg — {"PASS" if result.overall_pass else "REVIEW"}'
            self.save_state()
            self.show_message('Blend calculation completed.', title='Success')
            self.switch_screen('results')
        except ValueError as exc:
            self.show_message(str(exc), title='Input error')

    def evaluate_manual(self, result: ReverseBlendResult, low_quantity: int) -> ReverseBlendResult:
        low_values, good_values, specs, good_quantity, fm_target = self.gather_inputs()
        rows = []
        total = good_quantity + low_quantity
        for item in result.parameters:
            if item.specification is None:
                rows.append(item)
                continue
            low_mass = low_quantity * item.low_value + good_quantity * item.good_value
            final_value = low_mass / total if total else 0.0
            meets = final_value <= item.specification + 1e-9
            rows.append(
                ParameterResult(
                    item.name,
                    item.specification,
                    item.low_value,
                    item.good_value,
                    item.foreign_value,
                    final_value,
                    item.required_good_kg,
                    meets,
                    item.impossible,
                    'Pass' if meets else f'Fail: use less low seed',
                )
            )
        outside_fm = 0
        fm_item = next((item for item in rows if item.name == 'Foreign Material'), None)
        if self.fm_enabled and fm_target > 0 and fm_item and 0 < fm_target < 100:
            current_fm_mass = good_quantity * fm_item.good_value + low_quantity * fm_item.low_value
            target_mass = fm_target * (good_quantity + low_quantity)
            if current_fm_mass < target_mass:
                outside_fm = round((target_mass - current_fm_mass) / (100 - fm_target))
        overall = bool(rows) and all(item.meets_specification and not item.impossible for item in rows if item.specification is not None)
        return ReverseBlendResult(low_quantity, result.controlling_parameter, tuple(rows), overall, good_quantity, outside_fm, fm_target, result.alternatives)

    def render_results(self, result: ReverseBlendResult) -> None:
        container = self.ids.results_container
        container.clear_widgets()
        summary_text = '\n'.join([
            f'Controlling: {result.controlling_parameter}',
            'Overall pass' if result.overall_pass else 'Review specs',
        ])
        summary = self._result_card(
            f'Max low seed: {result.allowed_low_kg:,} kg',
            f'Outside FM: {result.outside_fm_kg:,} kg',
            summary_text,
        )
        container.add_widget(summary)
        for item in result.parameters:
            container.add_widget(self._parameter_status(item))
        if result.alternatives:
            alt_header = self._info_card('Composition alternatives', 'Each option fixes one parameter at its max and shows low-seed compensation values.')
            container.add_widget(alt_header)
            for alternative in result.alternatives:
                container.add_widget(self._alternative_card(alternative))

    def calculate_profit(self) -> None:
        if not self.current_result:
            self.show_message('Calculate a blend first before profit.', title='Info')
            self.switch_screen('input')
            return
        try:
            low_price = self._to_float(self.ids.low_price_input.text)
            good_price = self._to_float(self.ids.good_price_input.text)
            fm_price = self._to_float(self.ids.fm_price_input.text)
            selling_price = self._to_float(self.ids.selling_price_input.text)
            if min(low_price, good_price, fm_price, selling_price) < 0:
                raise ValueError('Prices must be non-negative.')
        except ValueError as exc:
            self.show_message(str(exc), title='Input error')
            return

        low_kg = self.current_result.allowed_low_kg
        good_kg = self.current_result.good_quantity_kg
        fm_kg = self.current_result.outside_fm_kg if self.fm_enabled else 0
        total_kg = low_kg + good_kg + fm_kg
        total_cost = low_kg * low_price + good_kg * good_price + fm_kg * fm_price
        average_rate = total_cost / total_kg if total_kg else 0
        profit_per_kg = selling_price - average_rate
        total_profit = profit_per_kg * total_kg
        self.ids.profit_container.clear_widgets()
        for label, value, color in [
            ('Low seed quantity', f'{low_kg:,} kg', [1, 1, 1, 1]),
            ('Good seed quantity', f'{good_kg:,} kg', [1, 1, 1, 1]),
            ('Outside FM quantity', f'{fm_kg:,} kg', [1, 1, 1, 1]),
            ('Total blend weight', f'{total_kg:,} kg', [1, 1, 1, 1]),
            ('Total blend cost', f'{total_cost:,.2f}', [1, 1, 1, 1]),
            ('Average cost rate', f'{average_rate:,.2f} / kg', [1, 1, 1, 1]),
            ('Selling rate', f'{selling_price:,.2f} / kg', [1, 1, 1, 1]),
            ('Profit per kg', f'{profit_per_kg:,.2f}', [0.36, 0.74, 0.36, 1] if profit_per_kg >= 0 else [0.86, 0.36, 0.36, 1]),
            ('Total profit', f'{total_profit:,.2f}', [0.36, 0.74, 0.36, 1] if total_profit >= 0 else [0.86, 0.36, 0.36, 1]),
        ]:
            card = self._result_card(label, value)
            card.children[0].color = color
            self.ids.profit_container.add_widget(card)
        self.save_state()
        self.show_message('Profit analysis updated.', title='Success')

    def _to_float(self, raw: str) -> float:
        try:
            return float(raw.strip() or 0)
        except ValueError:
            raise ValueError('Enter valid numeric values.')

    def _result_card(self, title: str, value: str, details: str | None = None) -> BoxLayout:
        card = BoxLayout(orientation='vertical', size_hint_y=None, height='80dp', padding=['10dp', '10dp'], spacing='4dp')
        card.canvas.before.clear()
        with card.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.12, 0.18, 0.15, 1)
            RoundedRectangle(pos=card.pos, size=card.size, radius=[12])
        card.bind(pos=self._update_rect, size=self._update_rect)
        card.add_widget(Label(text=title, color=(0.93, 0.98, 0.90, 1), bold=True, halign='left', valign='middle', text_size=(card.width, None)))
        card.add_widget(Label(text=value, color=(0.87, 0.97, 0.77, 1), halign='left', valign='middle', text_size=(card.width, None)))
        if details:
            card.add_widget(Label(text=details, color=(0.74, 0.81, 0.76, 1), font_size='12sp', halign='left', valign='middle', text_size=(card.width, None)))
        return card

    def _info_card(self, title: str, details: str) -> BoxLayout:
        card = self._result_card(title, '', details)
        return card

    def _parameter_status(self, item: ParameterResult) -> BoxLayout:
        status = 'PASS' if item.meets_specification else 'FAIL'
        color = [0.36, 0.74, 0.36, 1] if item.meets_specification else [0.94, 0.62, 0.45, 1]
        caption = f'{item.name}: {item.final_value:.2f}% / max {item.specification:.2f}%'
        detail = item.detail or ''
        return self._result_card(caption, status, detail)

    def _alternative_card(self, alternative: CompositionAlternative) -> BoxLayout:
        content = f'{alternative.controlling_parameter}: {alternative.low_quantity_kg:,} kg low seed'
        card = self._result_card('Alternative composition', content)
        for value in alternative.values:
            if value.final_percentage is None:
                continue
            line = f'{value.name}: {value.final_percentage:.2f}% ({value.final_kg:,.1f} kg)'
            card.add_widget(Label(text=line, color=(0.82, 0.88, 0.84, 1), font_size='12sp', halign='left', valign='middle', text_size=(card.width, None)))
        return card

    def _update_rect(self, instance: Any, value: Any) -> None:
        for instr in instance.canvas.before.children:
            if hasattr(instr, 'size'):
                instr.size = instance.size
                instr.pos = instance.pos

    def show_message(self, text: str, title: str = 'Notice') -> None:
        popup = Popup(title=title, size_hint=(0.85, 0.35), auto_dismiss=True)
        popup.content = Label(text=text, color=(1, 1, 1, 1), halign='center', valign='middle', text_size=(popup.width - 20, None))
        popup.open()

    def save_state(self) -> None:
        try:
            data = {
                'good_quantity': self.ids.good_quantity_input.text,
                'fm_target': self.ids.fm_target_input.text,
                'fm_enabled': self.fm_enabled,
                'mode': self.mode,
                'low_quantity': self.low_quantity,
                'parameters': [
                    {
                        'name': row.ids.name_input.text,
                        'low': row.ids.low_input.text,
                        'good': row.ids.good_input.text,
                        'spec': row.ids.spec_input.text,
                    }
                    for row in self.parameter_rows
                ],
                'prices': {
                    'low': self.ids.low_price_input.text,
                    'good': self.ids.good_price_input.text,
                    'fm': self.ids.fm_price_input.text,
                    'selling': self.ids.selling_price_input.text,
                },
            }
            self.store.put('state', **data)
        except Exception:
            pass

    def load_state(self) -> None:
        if not self.store.exists('state'):
            return
        state = self.store.get('state')
        self.ids.good_quantity_input.text = state.get('good_quantity', '1000')
        self.ids.fm_target_input.text = state.get('fm_target', '0')
        self.fm_enabled = state.get('fm_enabled', False)
        self.ids.fm_switch.state = 'down' if self.fm_enabled else 'normal'
        self.ids.fm_switch.text = 'Yes' if self.fm_enabled else 'No'
        self.mode = state.get('mode', 'Optimization')
        self.ids.mode_spinner.text = self.mode
        self.ids.low_slider.disabled = self.mode != 'Manual'
        self.ids.low_slider.value = int(state.get('low_quantity', 0))
        self.ids.low_label.text = f'{int(self.ids.low_slider.value):,} kg'
        saved_parameters = state.get('parameters', [])
        if saved_parameters:
            for row in list(self.parameter_rows):
                self.remove_parameter(row)
            for parameter in saved_parameters:
                self.add_parameter(parameter.get('name', 'Parameter'))
                row = self.parameter_rows[-1]
                row.ids.low_input.text = parameter.get('low', '')
                row.ids.good_input.text = parameter.get('good', '')
                row.ids.spec_input.text = parameter.get('spec', '')
        self.ids.low_price_input.text = state.get('prices', {}).get('low', '0')
        self.ids.good_price_input.text = state.get('prices', {}).get('good', '0')
        self.ids.fm_price_input.text = state.get('prices', {}).get('fm', '0')
        self.ids.selling_price_input.text = state.get('prices', {}).get('selling', '0')


class SeedBlendMobileApp(App):
    def build(self) -> SeedBlendMobileRoot:
        Builder.load_string(KV)
        return SeedBlendMobileRoot()


if __name__ == '__main__':
    SeedBlendMobileApp().run()
