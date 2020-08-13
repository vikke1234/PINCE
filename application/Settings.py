#
#  Copyright (c) 2020 Viktor Horsmanheimo <viktor.horsmanheimo@gmail.com>
#  Copyright (C) 2016-2017 Korcan Karaokçu <korcankaraokcu@gmail.com>

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from enum import Enum
from libPINCE import type_defs



# represents the index of columns in address table

# settings
current_settings_version = "master-17"  # Increase version by one if you change settings. Format: branch_name-version
update_table: bool = True
table_update_interval: float = 0.2
show_messagebox_on_exception: bool = True
show_messagebox_on_toggle_attach: bool = True
gdb_output_mode: tuple = type_defs.gdb_output_mode(True, True, True)
auto_attach_list: str = ""
auto_attach_regex: bool = False
logo_path: str = "ozgurozbek/pince_small_transparent.png"
code_injection_method: int = type_defs.INJECTION_METHOD.SIMPLE_DLOPEN_CALL
bring_disassemble_to_front: bool = False
instructions_per_scroll: int = 2
gdb_path: str = type_defs.PATHS.GDB_PATH
gdb_logging: bool = False

# represents the index of columns in breakpoint table
class Break(Enum):
    BREAK_NUM_COL = 0
    BREAK_TYPE_COL = 1
    BREAK_DISP_COL = 2
    BREAK_ENABLED_COL = 3
    BREAK_ADDR_COL = 4
    BREAK_SIZE_COL = 5
    BREAK_ON_HIT_COL = 6
    BREAK_HIT_COUNT_COL = 7
    BREAK_COND_COL = 8


# row colours for disassemble qtablewidget


# represents the index of columns in disassemble table
DISAS_ADDR_COL = 0
DISAS_BYTES_COL = 1
DISAS_OPCODES_COL = 2
DISAS_COMMENT_COL = 3

# represents the index of columns in floating point table
FLOAT_REGISTERS_NAME_COL = 0
FLOAT_REGISTERS_VALUE_COL = 1

# represents the index of columns in stacktrace table
STACKTRACE_RETURN_ADDRESS_COL = 0
STACKTRACE_FRAME_ADDRESS_COL = 1
STACK_POINTER_ADDRESS_COL = 0

# represents the index of columns in stack table
STACK_VALUE_COL = 1
STACK_POINTS_TO_COL = 2

# represents row and column counts of Hex table
HEX_VIEW_COL_COUNT = 16
HEX_VIEW_ROW_COUNT = 42  # J-JUST A COINCIDENCE, I SWEAR!
# represents the index of columns in track watchpoint table(what accesses this address thingy)
TRACK_WATCHPOINT_COUNT_COL = 0
TRACK_WATCHPOINT_ADDR_COL = 1

# represents the index of columns in track breakpoint table(which addresses this instruction accesses thingy)
TRACK_BREAKPOINT_COUNT_COL = 0
TRACK_BREAKPOINT_ADDR_COL = 1
TRACK_BREAKPOINT_VALUE_COL = 2
TRACK_BREAKPOINT_SOURCE_COL = 3

# represents the index of columns in function info table
FUNCTIONS_INFO_ADDR_COL = 0
FUNCTIONS_INFO_SYMBOL_COL = 1

# represents the index of columns in libPINCE reference resources table
LIBPINCE_REFERENCE_ITEM_COL = 0
LIBPINCE_REFERENCE_VALUE_COL = 1

# represents the index of columns in search opcode table
SEARCH_OPCODE_ADDR_COL = 0
SEARCH_OPCODE_OPCODES_COL = 1

# represents the index of columns in memory regions table
MEMORY_REGIONS_ADDR_COL = 0
MEMORY_REGIONS_PERM_COL = 1
MEMORY_REGIONS_SIZE_COL = 2
MEMORY_REGIONS_PATH_COL = 3
MEMORY_REGIONS_RSS_COL = 4
MEMORY_REGIONS_PSS_COL = 5
MEMORY_REGIONS_SHRCLN_COL = 6
MEMORY_REGIONS_SHRDRTY_COL = 7
MEMORY_REGIONS_PRIVCLN_COL = 8
MEMORY_REGIONS_PRIVDRTY_COL = 9
MEMORY_REGIONS_REF_COL = 10
MEMORY_REGIONS_ANON_COL = 11
MEMORY_REGIONS_SWAP_COL = 12

# represents the index of columns in dissect code table

# represents the index of columns in referenced calls table
REF_STR_ADDR_COL = 0
REF_STR_COUNT_COL = 1
REF_STR_VAL_COL = 2
REF_CALL_ADDR_COL = 0
REF_CALL_COUNT_COL = 1