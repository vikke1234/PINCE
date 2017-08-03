# -*- coding: utf-8 -*-
"""
Copyright (C) 2016-2017 Jakob Kreuze <jakob@memeware.net>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os.path

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection


#:tag:Injection
def get_dynamic_symbols(binary_path):
    """Collects all of the dynamic symbols in an ELF binary.

    Args:
        binary_path (str): Path to the binary file to analyze.

    Returns:
        tuple: (symbol name, offset)

    Notes:
        The output of this function is only really meaningful for shared objects.
    """
    with open(binary_path, "rb") as elf_file:
        elf = ELFFile(elf_file)
        syms = elf.get_section_by_name(".dynsym")

        if not isinstance(syms, SymbolTableSection):
            # TODO: Specialized exception?
            raise Exception("No dynamic symbols section")

        return [(sym.name, sym["st_value"]) for sym in syms.iter_symbols()]
