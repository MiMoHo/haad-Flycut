#!/usr/bin/env python3
"""Source integration regressions for Flycut's Accessibility UI flow."""

from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_CONTROLLER_M = REPO_ROOT / "AppController.m"


def objective_c_method(source: str, signature: str) -> str:
    """Return one Objective-C method, ending at the next method declaration."""
    start = source.index(signature)
    remainder = source[start + len(signature) :]
    next_method = re.search(r"\n[+-]\s*\([^\n]+\)", remainder)
    end = start + len(signature) + next_method.start() if next_method else len(source)
    return source[start:end]


class AccessibilityPromptSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.implementation = APP_CONTROLLER_M.read_text(encoding="utf-8")

    def test_launch_does_not_show_accessibility_explanation(self) -> None:
        awake_from_nib = objective_c_method(self.implementation, "- (void)awakeFromNib")
        self.assertNotIn("[self showAccessibilityAlert]", awake_from_nib)

    def test_launch_does_not_activate_flycut(self) -> None:
        awake_from_nib = objective_c_method(self.implementation, "- (void)awakeFromNib")
        self.assertNotIn("activateIgnoringOtherApps", awake_from_nib)

    def test_system_prompt_request_does_not_force_open_settings(self) -> None:
        request_prompt = objective_c_method(
            self.implementation, "- (void)requestAccessibilityWithPrompt"
        )
        self.assertNotIn("[self openAccessibilitySettings]", request_prompt)

    def test_failed_paste_routes_through_session_policy(self) -> None:
        fake_command_v = objective_c_method(self.implementation, "-(void)fakeCommandV")
        policy_call = "FlycutShouldShowAccessibilityExplanation("
        mark_statement = "hasShownAccessibilityExplanationThisSession = YES;"
        show_statement = "[self showAccessibilityAlert];"
        for statement in (policy_call, mark_statement, show_statement):
            self.assertIn(statement, fake_command_v)
        policy = fake_command_v.index(policy_call)
        mark_shown = fake_command_v.index(mark_statement)
        show = fake_command_v.index(show_statement)
        self.assertLess(policy, mark_shown)
        self.assertLess(mark_shown, show)
        self.assertNotIn("dispatch_async", fake_command_v)

    def test_failed_paste_dialog_explains_permission_scope(self) -> None:
        show_alert = objective_c_method(
            self.implementation, "- (void)showAccessibilityAlert"
        )
        self.assertIn('@"Paste Needs Accessibility Access"', show_alert)
        self.assertIn("this copy of Flycut", show_alert)
        self.assertIn("only to send Command-V", show_alert)
        self.assertNotIn("kAXTrustedCheckOptionPrompt: @YES", show_alert)

    def test_failed_paste_dialog_uses_user_controlled_choices(self) -> None:
        show_alert = objective_c_method(
            self.implementation, "- (void)showAccessibilityAlert"
        )
        self.assertIn('[alert addButtonWithTitle:@"Open Settings"]', show_alert)
        self.assertIn('[alert addButtonWithTitle:@"Not Now"]', show_alert)
        self.assertNotIn("Request System Prompt", show_alert)
        self.assertNotIn("suppressAccessibilityAlert", show_alert)
        self.assertRegex(
            show_alert,
            r"if\s*\(response == NSAlertFirstButtonReturn\)\s*\{\s*"
            r"\[self openAccessibilitySettings\];",
        )

    def test_explanation_activates_only_after_trust_recheck(self) -> None:
        show_alert = objective_c_method(
            self.implementation, "- (void)showAccessibilityAlert"
        )
        trust_guard = "if (&AXIsProcessTrustedWithOptions != NULL && !trusted)"
        activation = "[NSApp activateIgnoringOtherApps:YES];"
        run_modal = "[alert runModal]"
        for statement in (trust_guard, activation, run_modal):
            self.assertIn(statement, show_alert)
        self.assertLess(show_alert.index(trust_guard), show_alert.index(activation))
        self.assertLess(show_alert.index(activation), show_alert.index(run_modal))

    def test_explanation_hides_flycut_before_opening_settings(self) -> None:
        show_alert = objective_c_method(
            self.implementation, "- (void)showAccessibilityAlert"
        )
        run_modal = "[alert runModal]"
        hide = "[self hideApp];"
        open_settings = "[self openAccessibilitySettings];"
        for statement in (run_modal, hide, open_settings):
            self.assertIn(statement, show_alert)
        self.assertLess(show_alert.index(run_modal), show_alert.index(hide))
        self.assertLess(show_alert.index(hide), show_alert.index(open_settings))


if __name__ == "__main__":
    unittest.main(verbosity=2)
