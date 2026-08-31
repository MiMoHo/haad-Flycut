#!/usr/bin/env python3
"""Regression tests for layout-independent synthetic paste."""

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


class KeyboardLayoutPasteRegressionTests(unittest.TestCase):
    def test_missing_layout_lookup_becomes_command_a_while_physical_v_is_nine(self) -> None:
        fixture = r'''
#import <Foundation/Foundation.h>
#import <Carbon/Carbon.h>

int main(void) {
    @autoreleasepool {
        NSNumber *missingLayoutLookup = nil;
        CGKeyCode missingCode = (CGKeyCode)[missingLayoutLookup intValue];
        if (missingCode != kVK_ANSI_A) return 1;
        if (kVK_ANSI_A != 0) return 2;
        if (kVK_ANSI_V != 9) return 3;
    }
    return 0;
}
'''
        with tempfile.TemporaryDirectory(prefix="flycut-key-layout-") as directory:
            source = pathlib.Path(directory) / "key_layout.m"
            binary = pathlib.Path(directory) / "key_layout"
            source.write_text(fixture)
            build = subprocess.run(
                [
                    "/usr/bin/xcrun",
                    "clang",
                    "-fobjc-arc",
                    "-fmodules",
                    "-framework",
                    "Foundation",
                    "-framework",
                    "Carbon",
                    str(source),
                    "-o",
                    str(binary),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            run = subprocess.run([str(binary)], cwd=ROOT, timeout=30)
            self.assertEqual(run.returncode, 0)

    def test_fake_command_v_uses_the_layout_independent_physical_key(self) -> None:
        source = APP_CONTROLLER.read_text()
        method = method_body(source, "-(void)fakeCommandV")
        self.assertIn("#import <Carbon/Carbon.h>", source)
        self.assertIn("@(kVK_ANSI_V)", method)
        self.assertNotIn("reverseTransformedValue", method)

    def test_fake_key_rejects_a_missing_keycode_before_posting_events(self) -> None:
        source = APP_CONTROLLER.read_text()
        method = method_body(source, "-(void)fakeKey:")
        nil_guard = "if (keyCode == nil)"
        event_source = "CGEventSourceCreate"
        self.assertIn(nil_guard, method)
        self.assertIn(event_source, method)
        self.assertLess(method.index(nil_guard), method.index(event_source))


if __name__ == "__main__":
    unittest.main()
