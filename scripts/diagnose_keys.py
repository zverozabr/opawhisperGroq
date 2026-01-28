#!/usr/bin/env python3
"""Diagnostic script to capture actual Flet key names."""

import flet as ft


def main(page: ft.Page):
    page.title = "Key Name Diagnostic"
    page.window.width = 600
    page.window.height = 400

    key_log = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    last_key = ft.Text("Press any key...", size=24, weight=ft.FontWeight.BOLD)

    def on_keyboard(e: ft.KeyboardEvent):
        key_info = (
            f"key='{e.key}' | "
            f"ctrl={e.ctrl} | alt={e.alt} | shift={e.shift} | meta={e.meta}"
        )
        last_key.value = f"Key: {e.key}"
        key_log.controls.insert(0, ft.Text(key_info, size=12))
        if len(key_log.controls) > 30:
            key_log.controls.pop()
        page.update()

    page.on_keyboard_event = on_keyboard

    page.add(
        ft.Text("Press keys to see their Flet names:", size=16),
        last_key,
        ft.Divider(),
        ft.Text("Key Log:", size=14),
        key_log,
    )


if __name__ == "__main__":
    ft.app(main)
