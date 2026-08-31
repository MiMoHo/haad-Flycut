#!/usr/bin/env python3
"""Regression tests for Escape handling in the clipping bezel."""

from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_CONTROLLER = ROOT / "AppController.m"


def method_body(source: str, signature: str) -> str:
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"Unclosed method: {signature}")


class BezelEscapeRegressionTests(unittest.TestCase):
    def test_appkit_can_deliver_escape_keycode_without_characters(self) -> None:
        harness = r'''
#import <AppKit/AppKit.h>

int main(void) {
    @autoreleasepool {
        NSEvent *event = [NSEvent keyEventWithType:NSEventTypeKeyDown
                                         location:NSZeroPoint
                                    modifierFlags:0
                                        timestamp:0
                                     windowNumber:0
                                          context:nil
                                       characters:@""
                      charactersIgnoringModifiers:@""
                                         isARepeat:NO
                                           keyCode:53];
        if ([event keyCode] != 53) return 1;
        if ([[event charactersIgnoringModifiers] length] != 0) return 2;
    }
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "escape_event.m"
            binary = pathlib.Path(directory) / "escape_event"
            source.write_text(harness)
            subprocess.run(
                [
                    "/usr/bin/xcrun",
                    "clang",
                    "-fobjc-arc",
                    "-framework",
                    "AppKit",
                    str(source),
                    "-o",
                    str(binary),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run([str(binary)], check=True)

    def test_production_handles_escape_keycode_before_reading_characters(self) -> None:
        source = APP_CONTROLLER.read_text()
        method = method_body(source, "- (void)processBezelKeyDown:")

        keycode_check = "[theEvent keyCode] == 53"
        character_read = "characterAtIndex:0"
        self.assertIn(keycode_check, method)
        self.assertIn(character_read, method)
        self.assertLess(method.index(keycode_check), method.index(character_read))

    def test_production_guards_empty_character_events(self) -> None:
        source = APP_CONTROLLER.read_text()
        method = method_body(source, "- (void)processBezelKeyDown:")

        empty_guard = "[characters length] == 0"
        character_read = "characterAtIndex:0"
        self.assertIn(empty_guard, method)
        self.assertIn(character_read, method)
        self.assertLess(method.index(empty_guard), method.index(character_read))


if __name__ == "__main__":
    unittest.main()
