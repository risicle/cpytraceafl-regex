import ctypes
import mmap

import pytest

from cpytraceafl import tracehook

import regex


def _reset_prev_loc():
    # perform just enough matching to empty prev_loc up to the maximum
    # ngram size we're likely to be using
    regex.match("aaaaa", "aaaaa")


def _reset_mem(mem, map_size_bits):
    mem.seek(0)
    mem.write(b"\0" * (1<<map_size_bits))
    mem.seek(0)


@pytest.mark.parametrize("map_size_bits", (16, 11,))
@pytest.mark.parametrize("ngram_size", (0, 2,))
@pytest.mark.parametrize("pattern,teststr0,maxvisits0,teststr1,visits1", (
    (regex.compile(r"q{4,17}r"), ("q"*10)+"r", 10, "qqqfr", 3),
    (regex.compile(r"\d+t?"), ("678"*3), 9, "287t", 3),
    (regex.compile(r"[1-3a-c]*c", flags=regex.A), "12bbbb3c", 8, "ccc1JJJ", 4),
    (regex.compile(r"z?[1-3a-c]*c", flags=regex.I), "12bBbB3c", 8, "ccA1JJJ", 4),
))
def test_single_repeated(
    map_size_bits,
    ngram_size,
    pattern,
    teststr0,
    maxvisits0,
    teststr1,
    visits1,
):
    """
    After matching `teststr0` against `pattern`, the most-visited map address
    should be extected to have `maxvisits0` visits. after clearing the map and
    matching for `teststr1`, that same address should now have `visits1` visits.
    """

    # the only map addresses that get reliably repeatedly incremented will be ones
    # where prev_loc == this_loc, i.e. excluding the first visit at a loc. with
    # ngrams enabled, this uncounted region is increased proportionally to the
    # ngram_size
    if ngram_size:
        maxvisits0 -= ngram_size - 1
        visits1 -= ngram_size - 1

    with mmap.mmap(-1, 1<<map_size_bits, flags=mmap.MAP_PRIVATE) as mem:
        first_byte = ctypes.c_byte.from_buffer(mem)
        try:
            tracehook.set_map_start(ctypes.addressof(first_byte))
            tracehook.set_map_size_bits(map_size_bits)
            tracehook.set_ngram_size(ngram_size)

            _reset_prev_loc()
            _reset_mem(mem, map_size_bits)
            pattern.match(teststr0)

            max_i, max_val = max(enumerate(mem.read()), key=lambda i_v: i_v[1])
            mem.seek(0)

            assert max_val == maxvisits0

            _reset_prev_loc()
            _reset_mem(mem, map_size_bits)
            pattern.match(teststr1)

            assert mem.read()[max_i] == visits1

        finally:
            del first_byte


@pytest.mark.parametrize("map_size_bits", (16, 9,))
@pytest.mark.parametrize("ngram_size", (0, 2,))
@pytest.mark.parametrize("pattern,teststr_fewer,teststr_greater", (
    (regex.compile(r"foobarbaz"), "xxxxxrbaz", "xoobarbaz",),
    (regex.compile(r"abcdefghi", regex.I), "321321ghi", "abcDefGHI",),
    (regex.compile(r"a+[56s].(bc?)+"), "asd0bcbb", "aas0bcbb",),
    (regex.compile(r"12|\d{8}"), "12", "87654321",),
    (regex.compile(r"(p[pP]?)\1"), "ppP", "ppp",),
))
def test_more_visits(
    map_size_bits,
    ngram_size,
    pattern,
    teststr_fewer,
    teststr_greater,
):
    """
    After matching `teststr_fewer` and `teststr_greater` against `pattern`,
    `teststr_greater` should have more overall visits in its map. results
    could be sensitive to small upstream changes.
    """
    with mmap.mmap(-1, 1<<map_size_bits, flags=mmap.MAP_PRIVATE) as mem:
        first_byte = ctypes.c_byte.from_buffer(mem)
        try:
            tracehook.set_map_start(ctypes.addressof(first_byte))
            tracehook.set_map_size_bits(map_size_bits)
            tracehook.set_ngram_size(ngram_size)

            _reset_prev_loc()
            _reset_mem(mem, map_size_bits)
            pattern.match(teststr_fewer)

            visits_fewer = sum(mem.read())
            mem.seek(0)

            _reset_prev_loc()
            _reset_mem(mem, map_size_bits)
            pattern.match(teststr_greater)

            visits_greater = sum(mem.read())

            assert visits_fewer < visits_greater

        finally:
            del first_byte


@pytest.mark.parametrize("map_size_bits", (18, 11,))
@pytest.mark.parametrize("ngram_size", (0, 2,))
@pytest.mark.parametrize("pattern,teststr0,teststr1", (
    (regex.compile(r"abcdef|ghijkl"), "abcdef", "ghijkl",),
    (regex.compile(r"(ec+d$|ef*g.|h?i(j|k))"), "egd", "efgd",),
    (regex.compile(r"foobarbaz"), "foobrbaz", "foobxrbaz",),
    (
        regex.compile(r"((a\s+)+.?)(bc|d?a)\1"),
        "a  a a  !aa  a a     ",
        "a  a a  !daa  a a     ",
    ),
    (
        regex.compile(r".*\b(\w)\w.*\1\b"),
        "barn  burp test buns",
        "barn  burp  test buns",
    ),
    (
        regex.compile(r"sap([0-9]{3,9})foobarb.z?\1(buzbong|(\D\d?)+)o"),
        "sap1415foobarbo1415x",
        "sap1415foobarbo1415b",
    ),
))
def test_diff_visits(
    map_size_bits,
    ngram_size,
    pattern,
    teststr0,
    teststr1,
):
    """
    Matching `teststr0` and `teststr1` against `pattern` should produce
    different maps
    """
    with mmap.mmap(-1, 1<<map_size_bits, flags=mmap.MAP_PRIVATE) as mem:
        first_byte = ctypes.c_byte.from_buffer(mem)
        try:
            tracehook.set_map_start(ctypes.addressof(first_byte))
            tracehook.set_map_size_bits(map_size_bits)
            tracehook.set_ngram_size(ngram_size)

            _reset_prev_loc()
            _reset_mem(mem, map_size_bits)
            pattern.match(teststr0)

            visits0 = mem.read()
            mem.seek(0)

            _reset_prev_loc()
            _reset_mem(mem, map_size_bits)
            pattern.match(teststr1)

            visits1 = mem.read()
            mem.seek(0)

            assert visits0 != visits1

        finally:
            del first_byte


@pytest.mark.parametrize("map_size_bits", (17, 12,))
@pytest.mark.parametrize("ngram_size", (0, 2,))
@pytest.mark.parametrize("pattern,teststr0,teststr1", (
    (regex.compile(r"[ab][cd][^ef][gh]"), "acxg", "bd h",),
    (regex.compile(r"ab(?=cd)(ef|\D\d)"), "abef", "abg2",),
    (regex.compile(r".*abc"), "zzzzzabc", "zzbzzabc",),
    (regex.compile(r"foobarbaz"), "foobrbaz", "foobaz",),
))
def test_same_visits(
    map_size_bits,
    ngram_size,
    pattern,
    teststr0,
    teststr1,
):
    """
    Matching `teststr0` and `teststr1` against `pattern` should produce
    identical maps for one reason or another
    """
    with mmap.mmap(-1, 1<<map_size_bits, flags=mmap.MAP_PRIVATE) as mem:
        first_byte = ctypes.c_byte.from_buffer(mem)
        try:
            tracehook.set_map_start(ctypes.addressof(first_byte))
            tracehook.set_map_size_bits(map_size_bits)
            tracehook.set_ngram_size(ngram_size)

            _reset_prev_loc()
            _reset_mem(mem, map_size_bits)
            pattern.match(teststr0)

            visits0 = mem.read()
            mem.seek(0)

            _reset_prev_loc()
            _reset_mem(mem, map_size_bits)
            pattern.match(teststr1)

            visits1 = mem.read()
            mem.seek(0)

            assert visits0 == visits1

        finally:
            del first_byte
