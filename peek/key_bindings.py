import logging
import os

from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import ValidationState
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Condition, completion_is_selected, is_searching
from prompt_toolkit.key_binding import KeyBindings

from peek.errors import PeekSyntaxError

_logger = logging.getLogger(__name__)

SPECIAL_LEADING_CHAR = '%'


def key_bindings(repl):
    kb = KeyBindings()

    @kb.add('enter', filter=~(completion_is_selected | is_searching) & buffer_should_be_handled(repl))
    def _(event):
        event.current_buffer.validate_and_handle()

    @kb.add('escape', 'enter', filter=~(completion_is_selected | is_searching))
    def _(event):
        event.app.current_buffer.newline()

    @kb.add('c-d')
    def _(event):
        repl.signal_exit()
        # Short circuit the validation
        event.current_buffer.validation_state = ValidationState.VALID
        event.current_buffer.validate_and_handle()

    @kb.add('f3')
    def _(event):
        _logger.debug('Reformatting')
        try:
            texts = []
            for stmt in repl.parser.parse(event.current_buffer.text):
                texts.append(stmt.format_pretty() if not repl.is_pretty else stmt.format_compact())
            event.current_buffer.text = ''.join(texts)
            repl.is_pretty = not repl.is_pretty
        except PeekSyntaxError as e:
            _logger.debug(f'Cannot reformat for invalid/incomplete input: {e}')

    return kb


def buffer_should_be_handled(repl):
    @Condition
    def cond():
        doc = get_app().layout.get_buffer_by_name(DEFAULT_BUFFER).document
        _logger.debug(f'current doc: {doc}')
        if doc.text.strip() == '':
            return True
        elif doc.text.lstrip().startswith(SPECIAL_LEADING_CHAR):
            return True

        # Handle ES API call when an empty line is entered
        last_linesep_position = doc.text.rfind(os.linesep)
        if last_linesep_position != -1 and doc.text[last_linesep_position:].strip() == '':
            return True

        return False

    return cond
