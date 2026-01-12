"""Tests for EditableField component."""

from unittest.mock import MagicMock


import flet as ft

from soupawhisper.gui.components import EditableField, SettingsSection


class TestEditableField:
    """Tests for EditableField component."""

    def test_initial_state_button_disabled(self):
        """Test that confirm button is disabled initially."""
        field = ft.TextField(value="initial")
        editable = EditableField(
            field=field,
            initial_value="initial",
            on_save=MagicMock(),
        )

        assert editable.confirm_btn.disabled is True
        assert editable.confirm_btn.icon_color == ft.Colors.GREY_500

    def test_button_enabled_on_change(self):
        """Test that button becomes enabled when field changes."""
        field = ft.TextField(value="initial")
        editable = EditableField(
            field=field,
            initial_value="initial",
            on_save=MagicMock(),
        )

        # Simulate field change
        field.value = "changed"
        editable._on_field_change(MagicMock())

        assert editable.confirm_btn.disabled is False
        assert editable.confirm_btn.icon_color == ft.Colors.GREEN_500

    def test_button_disabled_when_value_reverted(self):
        """Test that button is disabled when value reverts to initial."""
        field = ft.TextField(value="initial")
        editable = EditableField(
            field=field,
            initial_value="initial",
            on_save=MagicMock(),
        )

        # Change value
        field.value = "changed"
        editable._on_field_change(MagicMock())

        # Revert value
        field.value = "initial"
        editable._on_field_change(MagicMock())

        assert editable.confirm_btn.disabled is True

    def test_on_save_called_on_confirm(self):
        """Test that on_save callback is called when confirmed."""
        field = ft.TextField(value="initial")
        on_save = MagicMock()
        editable = EditableField(
            field=field,
            initial_value="initial",
            on_save=on_save,
        )

        # Change and confirm
        field.value = "new_value"
        editable._on_confirm(MagicMock())

        on_save.assert_called_once_with("new_value")

    def test_button_disabled_after_confirm(self):
        """Test that button is disabled after confirming."""
        field = ft.TextField(value="initial")
        editable = EditableField(
            field=field,
            initial_value="initial",
            on_save=MagicMock(),
        )

        # Change and confirm
        field.value = "new_value"
        editable._on_confirm(MagicMock())

        assert editable.confirm_btn.disabled is True
        assert editable.confirm_btn.icon_color == ft.Colors.GREY_500

    def test_initial_value_updated_after_confirm(self):
        """Test that initial value is updated after confirm."""
        field = ft.TextField(value="initial")
        editable = EditableField(
            field=field,
            initial_value="initial",
            on_save=MagicMock(),
        )

        # Change and confirm
        field.value = "new_value"
        editable._on_confirm(MagicMock())

        # Now changing to "initial" should enable button (it's different from new initial)
        field.value = "initial"
        editable._on_field_change(MagicMock())

        assert editable.confirm_btn.disabled is False

    def test_reset_updates_field_and_initial(self):
        """Test that reset updates both field value and initial value."""
        field = ft.TextField(value="initial")
        editable = EditableField(
            field=field,
            initial_value="initial",
            on_save=MagicMock(),
        )

        editable.reset("new_initial")

        assert field.value == "new_initial"
        assert editable._initial_value == "new_initial"
        assert editable.confirm_btn.disabled is True

    def test_value_property(self):
        """Test value property getter and setter."""
        field = ft.TextField(value="initial")
        editable = EditableField(
            field=field,
            initial_value="initial",
            on_save=MagicMock(),
        )

        assert editable.value == "initial"

        editable.value = "new"
        assert editable.value == "new"
        assert editable._initial_value == "new"

    def test_works_with_dropdown(self):
        """Test EditableField works with Dropdown."""
        field = ft.Dropdown(
            value="option1",
            options=[
                ft.dropdown.Option("option1"),
                ft.dropdown.Option("option2"),
            ],
        )
        on_save = MagicMock()
        editable = EditableField(
            field=field,
            initial_value="option1",
            on_save=on_save,
        )

        # Change dropdown
        field.value = "option2"
        editable._on_field_change(MagicMock())

        assert editable.confirm_btn.disabled is False

        editable._on_confirm(MagicMock())
        on_save.assert_called_once_with("option2")

    def test_works_with_switch(self):
        """Test EditableField works with Switch."""
        field = ft.Switch(value=False)
        on_save = MagicMock()
        editable = EditableField(
            field=field,
            initial_value=False,
            on_save=on_save,
        )

        # Toggle switch
        field.value = True
        editable._on_field_change(MagicMock())

        assert editable.confirm_btn.disabled is False

        editable._on_confirm(MagicMock())
        on_save.assert_called_once_with(True)


class TestSettingsSection:
    """Tests for SettingsSection component."""

    def test_section_has_title(self):
        """Test that section has title text."""
        section = SettingsSection("Test Title", [ft.Text("content")])

        assert len(section.controls) == 2
        assert isinstance(section.controls[0], ft.Text)
        assert section.controls[0].value == "Test Title"

    def test_section_contains_controls(self):
        """Test that section contains provided controls."""
        control1 = ft.Text("control1")
        control2 = ft.Text("control2")
        section = SettingsSection("Title", [control1, control2])

        assert control1 in section.controls
        assert control2 in section.controls
