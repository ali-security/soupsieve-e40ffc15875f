"""Test attribute selectors."""
import os
import signal
import subprocess
import sys
import soupsieve as sv
from .. import util


class TestAttribute(util.TestCase):
    """Test attribute selectors."""

    MARKUP = """
    <div id="div">
    <p id="0">Some text <span id="1"> in a paragraph</span>.</p>
    <a id="2" href="http://google.com">Link</a>
    <span id="3">Direct child</span>
    <pre id="pre">
    <span id="4">Child 1</span>
    <span id="5">Child 2</span>
    <span id="6">Child 3</span>
    </pre>
    </div>
    """

    def test_attribute_not_equal_no_quotes(self):
        """Test attribute with value that does not equal specified value (no quotes)."""

        # No quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!=\\35]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_quotes(self):
        """Test attribute with value that does not equal specified value (quotes)."""

        # Quotes
        self.assert_selector(
            self.MARKUP,
            "body [id!='5']",
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_double_quotes(self):
        """Test attribute with value that does not equal specified value (double quotes)."""

        # Double quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!="5"]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def assert_syntax_error_no_timeout(self, selector, timeout=3):
        """Assert that compiling the selector fails for syntax error, not timeout error."""

        if hasattr(signal, 'SIGALRM'):

            def timeout_handler(signum, frame):
                raise TimeoutError

            handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)

            passed = False
            try:
                with self.assertRaises(sv.SelectorSyntaxError):
                    sv.compile(selector)
                passed = True
            except TimeoutError:
                pass
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, handler)
            self.assertTrue(passed)
        else:
            # `SIGALRM` is not available on all platforms (e.g. Windows), so compile
            # the selector in a separate process that is killed if it times out.
            script = (
                'import sys\n'
                'sys.path.insert(0, sys.argv[1])\n'
                'import soupsieve as sv\n'
                'try:\n'
                '    sv.compile(sys.stdin.read())\n'
                'except sv.SelectorSyntaxError:\n'
                '    sys.exit(0)\n'
                'sys.exit(1)\n'
            )
            path = os.path.dirname(os.path.dirname(os.path.abspath(sv.__file__)))
            try:
                result = subprocess.run(
                    [sys.executable, '-c', script, path],
                    input=selector,
                    universal_newlines=True,
                    timeout=timeout * 10
                )
            except subprocess.TimeoutExpired:
                result = None
            self.assertIsNotNone(result, 'Compiling the selector timed out')
            self.assertEqual(result.returncode, 0)

    def test_bad_attribute_unclused(self):
        """Test bad attribute fails for syntax error, not timeout error."""

        self.assert_syntax_error_no_timeout('[a="' + ('x' * 300))

    def test_bad_attribute_unclosed_single_quote(self):
        """Test bad attribute with unclosed single quote fails for syntax error, not timeout error."""

        self.assert_syntax_error_no_timeout("[a='" + ('x' * 300))

    def test_bad_lang_value_unclosed(self):
        """Test `:lang()` with unclosed quoted value fails for syntax error, not timeout error."""

        self.assert_syntax_error_no_timeout(':lang("' + ('x' * 300))

    def test_bad_contains_value_unclosed(self):
        """Test `:-soup-contains()` with unclosed quoted value fails for syntax error, not timeout error."""

        self.assert_syntax_error_no_timeout(":-soup-contains('" + ('x' * 300))
