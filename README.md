# cpytraceafl-regex

This is a thinly modified version of Matthew Barnett's
[mrab-regex](https://bitbucket.org/mrabarnett/mrab-regex) regular expression library with
added instrumentation for use when fuzzing python code with
[cpytraceafl](https://github.com/risicle/cpytraceafl).

The intention is for fuzzing harnesses to be able to substitute the builtin `re` module
library with this, highly compatible, module and thereby allow AFL to generate examples
which pass regular expressions used in the target or explore their limits in interesting
ways.

See the original [README.mrab-regex.rst](./README.mrab-regex.rst) for more general
information in this library's extended regex features.

## Recommended usage

Early in the startup of the fuzzing harness, (though after the call to `install_rewriter()`):

```python
import regex
from sys import modules
modules["re"] = regex
```

code later importing/referencing the `re` module should instead be using this instrumented
`regex` code. Note that before evaluating any regexes, `cpytraceafl.tracehook.set_map_start()`
will need to have been initialized with a memory region to write its intrumentation data
into. Otherwise you'll get segfaults.

This works unless the code under test attempts to use the `typing` module, at which point its
trick involving the `Pattern` type will trip up over itself. Some further hackery will need
to be devised to get past this.
