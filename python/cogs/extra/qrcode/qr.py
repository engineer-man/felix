# ┌────────────────────────────────────────────────────────────────────────────┐
# │                           QR CODE GENERATOR                                │
# │                                                                            │
# │  Based on https://www.thonky.com/qr-code-tutorial                          │
# │                                                                            │
# │  by https://github.com/brtwrst                                    05/2022  │
# └────────────────────────────────────────────────────────────────────────────┘

from functools import reduce
from operator import add
from itertools import zip_longest
from itertools import product
from .qr_tools import GF2_create_tables, Polynomial_GF256_exp as polynomial_exp
from .qr_tools import Polynomial_GF256_int as polynomial_int
from .qr_tools import get_matrix_str_full_size, get_matrix_str_half_size
from .qr_tables import CHAR_CAPACITY_TABLE, CHARCOUNT_INDICATOR_LENGTHS_TABLE
from .qr_tables import ALPHANUM_ENCODING_TABLE, ECC_INFO_TABLE, ALIGNMENT_PATTERN_LOCATIONS_TABLE
from .qr_tables import FORMAT_INFORMATION_STRINGS_TABLE, VERSION_INFORMATION_STRINGS_TABLE

# Enter data
data = 'https://emkc.org'

# Chose Error Correction (0: L, 1: M, 2:Q, 3:H)
ecl = 1


def generate_qr_code(data, ecl, output='string', verbose=False):
    assert len(data) > 0
    if verbose:
        print('DATA:   ', data, '\nLENGTH: ', len(data))
    assert 0 <= ecl <= 3
    if verbose:
        print('ECC:    ', ['L', 'M', 'Q', 'H'][ecl], f'({ecl})')

    # ============================================================================================
    # Data Analysis - https://www.thonky.com/qr-code-tutorial/data-analysis
    # ============================================================================================

    # Automatically pick best mode (0: Numeric, 1:Alphanumeric, 2:Byte)
    if all(x in '0123456789' for x in data):
        mode = 0
    elif all(x in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:' for x in data):
        mode = 1
    else:
        mode = 2
    MODE_IND = ['0001', '0010', '0100', '1000']
    assert 0 <= mode <= 3
    if verbose:
        print('MODE:   ', mode, '-',  ['Numeric', 'Alphanumeric', 'Byte', 'Kanji'][mode])

    # --------------------------------------------------------------------------------------------
    # Automatically pick best (smallest) Version (Size) from 1-40
    version = 1
    while CHAR_CAPACITY_TABLE[version][ecl][mode] < len(data):
        version += 1
    assert 1 <= version <= 40
    if verbose:
        print('VERSION:', version)

    # --------------------------------------------------------------------------------------------
    # Find length of character count indicator based on version and mode
    for max_version, counts in CHARCOUNT_INDICATOR_LENGTHS_TABLE.items():
        if version <= max_version:
            charcount_ind_len = counts[mode]
            break
    assert charcount_ind_len > 0

    # ============================================================================================
    # Encode data - https://www.thonky.com/qr-code-tutorial/data-encoding
    # ============================================================================================

    encoded_data = ''
    if mode == 0:
        # Numeric encoding
        # https://www.thonky.com/qr-code-tutorial/numeric-mode-encoding
        # Split number into 3 digit numbers (the last number can be 1, 2 or 3 digits long)
        # Convert each 3 digit number into a bit binary number and pad with zeroes to len 10
        # Convert each 2 digit number into a bit binary number and pad with zeroes to len 7
        # Convert each 1 digit number into a bit binary number and pad with zeroes to len 4

        for i in range(0, len(data), 3):
            num = data[i:i+3]
            if len(num) == 1:
                fill = 4
            elif len(num) == 2:
                fill = 7
            else:
                fill = 10
            encoded_data += bin(int(num))[2:].zfill(fill)
    elif mode == 1:
        # Alphanumeric encoding
        # https://www.thonky.com/qr-code-tutorial/alphanumeric-mode-encoding
        # Split the string into pairs of characters. The last "pair" might only have 1
        # character if the number of characters in the string is odd.
        # For each pair: Look up the corresponding number of each character in the pair
        #   Multiply the number of the first character in the pair with 45 and add it to the
        #   number of the second character in the pair.
        #   convert the product into an 11 bit binary number (pad with zeroes if required)

        for i in range(0, len(data), 2):
            pair = data[i:i+2]
            if len(pair) == 2:
                n = 45 * ALPHANUM_ENCODING_TABLE[pair[0]] + ALPHANUM_ENCODING_TABLE[pair[1]]
                encoded_data += bin(n)[2:].zfill(11)
            else:
                n = ALPHANUM_ENCODING_TABLE[pair[0]]
                encoded_data += bin(n)[2:].zfill(6)
    elif mode == 2:
        # Byte encoding
        # https://www.thonky.com/qr-code-tutorial/byte-mode-encoding
        # Convert each character into a UTF-8 encoded byte (ISO 8859-1 if UTF8 is unsupported)
        # Pad on the left with zeroes if required

        for c in data:
            encoded_data += bin(ord(c))[2:].zfill(8)
    elif mode == 3:
        raise NotImplementedError
    else:
        raise ValueError('ENCODING: Invalid mode ecountered')

    # --------------------------------------------------------------------------------------------
    # Add Mode Indicator and Charcount at the beginning of the encoded data
    encoded_data = MODE_IND[mode] + bin(len(data))[2:].zfill(charcount_ind_len) + encoded_data

    # --------------------------------------------------------------------------------------------
    # Calculate required data bits
    (
        num_error_correction_codewords,
        num_blocks_in_group_1,
        codewords_per_block_in_group_1,
        num_blocks_in_group_2,
        codewords_per_block_in_group_2
    ) = ECC_INFO_TABLE[version][ecl]
    num_required_data_cw = (
        num_blocks_in_group_1 * codewords_per_block_in_group_1 +
        num_blocks_in_group_2 * codewords_per_block_in_group_2
    )
    required_data_bits = num_required_data_cw * 8

    # --------------------------------------------------------------------------------------------
    # Add Terminator
    # If the encoded data has less than the required length, add a maximum of 4 zeroes
    terminator = '0'*(min(4, required_data_bits - len(encoded_data)))
    encoded_data += terminator

    # --------------------------------------------------------------------------------------------
    # Make multiple of 8
    # If the encoded data is not a multiple of 8, add up to seven zeroes to make it one
    remainder = len(encoded_data) % 8
    makemultipleof8 = '0' * ((8-remainder) if remainder else 0)
    encoded_data += makemultipleof8

    # --------------------------------------------------------------------------------------------
    # Add Padding
    # If the length of the encoded data is less than the required length, add alternating
    # padding bytes (236, 17) until its is exactly at the required length
    pad = ['11101100', '00010001']
    i = 0
    while len(encoded_data) < required_data_bits:
        encoded_data += pad[i]
        i ^= 1

    assert len(encoded_data) == required_data_bits

    # ============================================================================================
    # Encode Correction Coding - https://www.thonky.com/qr-code-tutorial/error-correction-coding
    # This implements Reed-Solomon Error correction which is too complicated to explain here
    # ============================================================================================

    # Split encoded data into codewords
    codewords = [int(encoded_data[x:x+8], 2) for x in range(0, len(encoded_data), 8)]
    assert len(codewords) == num_required_data_cw

    # --------------------------------------------------------------------------------------------
    # Put codewords into blocks, blocks into groups according to table at
    # https://www.thonky.com/qr-code-tutorial/error-correction-table
    num_blocks_in_group = (num_blocks_in_group_1, num_blocks_in_group_2)
    codewords_per_block_in_grp = (codewords_per_block_in_group_1, codewords_per_block_in_group_2)
    groups = [[], []]
    current_group = 0
    current_block = []
    for codeword in codewords:
        current_block.append(codeword)
        if len(current_block) == codewords_per_block_in_grp[current_group]:
            groups[current_group].append(current_block)
            current_block = []
            if len(groups[current_group]) == num_blocks_in_group[current_group]:
                current_group += 1

    group1, group2 = groups
    assert len(group1) == num_blocks_in_group_1
    assert len(group2) == num_blocks_in_group_2
    assert all(len(block) == codewords_per_block_in_group_1 for block in group1)
    assert all(len(block) == codewords_per_block_in_group_2 for block in group2)

    # --------------------------------------------------------------------------------------------
    # Log & Antilog Table for Galios Field 256 (GF256) with irreducible polynomial 285
    # See comments in GF2_create_tables definition (F12) for more info
    # See also Step3 ff here: https://www.thonky.com/qr-code-tutorial/error-correction-coding
    ALOG, LOG = GF2_create_tables(256, 285)

    assert num_error_correction_codewords > 0

    # --------------------------------------------------------------------------------------------
    # Generate generator polynomial
    # See also Step7 here: https://www.thonky.com/qr-code-tutorial/error-correction-coding

    # The generator Polynomial is created by multiplying (x - 2**0) ... (x - 2**n-1)
    # Example: the Generator Polynomial for 2 ECC is: (x-2**0)*(x-2**1) = 2**0x² + 2**25x + 2**1
    # To get the generator Polynomial for 3 ECC we just multiply the previous generator polynomial
    # by the next element: (2**0x² + 2**25x + 2**1)*(x-2**2) = 2**0x³ + 2**198x² + 2**199x + 2**3
    # Our generator polynomial needs to be size n=num of error correction codewords needed for our
    # case (see table: https://www.thonky.com/qr-code-tutorial/error-correction-table)
    generator_poly = polynomial_exp([0, 0])
    for i in range(1, num_error_correction_codewords):
        generator_poly = generator_poly * polynomial_exp([0, i])

    # The same generator Polynomial will be reused for every ECC calculation of the next step

    # --------------------------------------------------------------------------------------------
    # Calculate Error Correction Codewords (ECC)
    ecc_polys = [polynomial_int(), polynomial_int()]
    # Calculate the error correction polynomial for each block in each group and store them for
    # the next step. To get the error correction polynomial we divide the message polynomial by
    # the generator polynomial. See Step 9 for more information
    # https://www.thonky.com/qr-code-tutorial/error-correction-coding
    for g, group in enumerate(groups):
        for b, block in enumerate(group):
            # The message polynomial is just the codewords of the current block
            message_poly = polynomial_int(block)
            # To make sure that the exponent of the lead term doesn't become too small during the
            # division, multiply the message polynomial by x**n where n is the number of
            # error correction codewords that are needed.
            # We can do this quickly by just adding n zeroes to the end of the polynomial, which
            # was implemented as polynomial.copy_with_increased_degree()
            message_poly = message_poly.copy_with_increased_degree(num_error_correction_codewords)
            # The following steps must be repeated until the message polynomial has degree
            # num_error_correction_codewords - 1. The resulting num_error_correction_codewords
            # terms Will be the error correction codewords that we are after.
            while len(message_poly) > num_error_correction_codewords:
                # For each iteration we first "resize" the generator polynomial to be the same
                # degree as the message polynomial by getting a copy with increased degree
                degree_difference = len(message_poly) - len(generator_poly)
                resized_gen = generator_poly.copy_with_increased_degree(degree_difference)
                # Now we multiply the resized generator polynomial by the lead term of the message
                # polynomial. This can be done quickly by converting the lead term to exponent
                # notation with the LOG lookup table and then adding the term to each coefficient
                # exponent then reducing mod 255.
                # This is implemented with polynomial.multiply_by()
                factor = LOG[message_poly[0]]
                resized_gen = resized_gen.multiply_by(factor)
                # Now we convert this polynomial to integer notation and XOR (add) it to our
                # message polynomial
                resized_gen_int = resized_gen.to_int()
                message_poly = message_poly ^ resized_gen_int
                # finally we discard all leading terms with a zero coefficient
                message_poly = message_poly.discard_leading_zeroes()
            # When we have iterated enough times the message_poly we are left with is the
            # error polynomial which can be stored for later use.
            ecc_polys[g].append(message_poly)
            # Then we move on to the rest of the Blocks

    # ============================================================================================
    # Structure final message - https://www.thonky.com/qr-code-tutorial/structure-final-message
    # ============================================================================================
    # We have all the data blocks (codewords) in the groups object :
    # [[G1B1, G1B2...], [G2B1, G2B2 ...]]
    # and all the corresponding error correction blocks (codewords) in the ecc_polys object :
    # [[G1E1, G1E2...], [G2E1, G2E2 ...]]

    # The data blocks and error correction codewords must now be interleaved
    # If there is only 1 block of data codewords, no interleaving is neccessary but because the
    # algorithm used works in both cases, no separation was made.

    # --------------------------------------------------------------------------------------------
    # First we unpack all blocks from the 2 groups into a flat list
    # [G1B1, G1B2... , G2B1, G2B2 ...]
    blocks = [b for g in groups for b in g]
    # Then we interleave the blocks according to the following rules:
    # take the first data codeword from the first block
    # followed by the first data codeword from the second block
    # followed by the first data codeword from the third block
    # followed by the first data codeword from the fourth block
    # followed by the second data codeword from the first block
    # and so on
    # This can be done quickly with a reduce and the zip_longest function
    inter_data = reduce(
        add, [[x for x in a if x is not None] for a in zip_longest(*blocks, fillvalue=None)]
    )

    # Now we do the same for the error correction blocks
    # Unpack
    ecb = [b for g in ecc_polys for b in g]
    # Interleave Rules:
    # take the first error correction codeword from the first block
    # followed by the first error correction codeword from the second block
    # followed by the first error correction codeword from the third block
    # followed by the first error correction codeword from the fourth block
    # followed by the second error correction codeword from the first block
    # and so on
    eccinter_data = reduce(
        add, [[x for x in a if x is not None] for a in zip_longest(*ecb, fillvalue=None)]
    )

    # --------------------------------------------------------------------------------------------
    # The final message consists of the interleaved data codewords
    # followed by the interleaved error correction codewords.
    final_message = inter_data + eccinter_data

    # --------------------------------------------------------------------------------------------
    # Convert to binary and combine in 1 unbroken string
    final_message_bin = ''.join([bin(x)[2:].zfill(8) for x in final_message])

    # --------------------------------------------------------------------------------------------
    # For some QR versions, the final binary message is not long enough to fill the required
    # number of bits. In this case, it is necessary to add a certain number of 0s to the end of
    # the final message to make it have the correct length. Use the version to index into the
    # following list to get the number of required bits for your version
    r_bits = [-1, 0, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3,
              3, 3, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0]
    # add remainder bits if necessary
    final_message_bin += '0'*r_bits[version]

    # ============================================================================================
    # Module placement in Matrix - https://www.thonky.com/qr-code-tutorial/module-placement-matrix
    # ============================================================================================
    # Module vs Pixel: I refer to the black and white squares of the QR code as modules rather
    # than pixels. This is to differentiate between on-screen pixels and the black and white
    # squares of the QR code.

    # The size of the qr code in modules per side
    # The total numer of modules = size * size because QR Codes are squares
    # The size of a QR code can be calculated with the formula (((V-1)*4)+21)
    # where V is the QR code version.
    size = ((version-1)*4)+21

    # Our QR code is a dict of points to value dict(x,y) -> int
    # with:
    #   0 being a white module
    #   1 being a black module
    #   2 being a reserved module
    matrix = dict()
    # We initialize a set in which we will store the positions of the modules that have been
    # filled with our "final message" as we go along. We will need that list of positions later
    # to apply masks to the "data area".
    matrix_data_area = set()

    # --------------------------------------------------------------------------------------------
    # The finder pattern and separators
    ################## ################## ##################
    #              ██# #██              # #████████████████#
    #  ██████████  ██# #██  ██████████  # #              ██#
    #  ██      ██  ██# #██  ██      ██  # #  ██████████  ██#
    #  ██      ██  ██# #██  ██      ██  # #  ██      ██  ██#
    #  ██      ██  ██# #██  ██      ██  # #  ██      ██  ██#
    #  ██████████  ██# #██  ██████████  # #  ██      ██  ██#
    #              ██# #██              # #  ██████████  ██#
    #████████████████# #████████████████# #              ██#
    ################## ################## ##################
    # have to be added to the top left, top right and bottom left corners respectively
    # The top-left finder pattern's top left corner is always at (0,0).
    # The top-right finder pattern's top LEFT corner is always at ([(((V-1)*4)+21) - 7], 0)
    # The bottom-left finder pattern's top LEFT corner is always at (0,[(((V-1)*4)+21) - 7])
    # With V being the selected version

    # At each finder pattern position we do the following:
    for start_x, start_y in ((0, 0), ((((version-1)*4)+21) - 7, 0), (0, (((version-1)*4)+21) - 7)):
        # first we create a 9x9 white square where some of the edges will be outside the QR Code
        # area and will be removed later
        for y in range(start_y-1, start_y+8):
            for x in range(start_x-1, start_x+8):
                matrix[x, y] = 0
        # then we create a 7x7 black square inside the white square
        for y in range(start_y, start_y+7):
            for x in range(start_x, start_x+7):
                matrix[x, y] = 1
        # then we create the horizontal lines of the "white ring"
        for y in range(start_y+1, start_y+6):
            matrix[start_x + 1, y] = 0
            matrix[start_x + 5, y] = 0
        # and the vertical lines of the "white ring"
        for x in range(start_x+2, start_x+5):
            matrix[x, start_y+1] = 0
            matrix[x, start_y+5] = 0
    # finally we remove all modules that have been added outside the QR code area
    for x, y in [*(matrix.keys())]:
        if not 0 <= x < size or not 0 <= y < size:
            del matrix[x, y]

    # --------------------------------------------------------------------------------------------
    # QR codes that are version 2 and larger are required to have alignment patterns.
    ############
    #          #
    #  ██████  #
    #  ██  ██  #
    #  ██████  #
    #          #
    ############
    # The Position can be taken from
    # https://www.thonky.com/qr-code-tutorial/alignment-pattern-locations
    # The numbers are to be used as BOTH row and column coordinates.
    # For example, Version 2 has the numbers 6 and 18. This means that the CENTER MODULES of the
    # alignment patterns are to be placed at (6, 6), (6, 18), (18, 6) and (18, 18)
    # This can be generated with itertools.product((6,18),(6,18))
    # HOWEVER: The alignment Pattern MUST NOT overlap the finder patterns or separators.
    # If a pattern would overlap it is instead omitted from the matrix
    required_alignment_pattern_locations = [
        *product(
            ALIGNMENT_PATTERN_LOCATIONS_TABLE[version],
            ALIGNMENT_PATTERN_LOCATIONS_TABLE[version]
        )
    ]
    for start_x, start_y in required_alignment_pattern_locations:
        # Fpr each middle position of the required alignment patterns
        # Check for overlap with existing modules
        overlap = False
        for y in range(start_y-1, start_y+8):
            for x in range(start_x-1, start_x+8):
                if (x, y) in matrix:
                    overlap = True
                    break
        # If it overlaps, omit the current pattern
        if overlap:
            continue
        # To draw a pattern we draw
        for y in range(start_y-2, start_y+3):
            # a black 5x5 square
            for x in range(start_x-2, start_x+3):
                matrix[x, y] = 1
            # then we create the horizontal lines of the "white ring"
            for y in range(start_y-1, start_y+2):
                matrix[start_x + 1, y] = 0
                matrix[start_x - 1, y] = 0
            # and the vertical lines of the "white ring"
            matrix[start_x, start_y+1] = 0
            matrix[start_x, start_y-1] = 0

    # --------------------------------------------------------------------------------------------
    # Add Timing Patterns
    # The timing patterns are two lines, one horizontal and one vertical, of alternating
    # dark and light modules. The horizontal timing pattern is placed on the 6th row of the
    # QR code between the separators. The vertical timing pattern is placed on the 6th column
    # of the QR code between the separators
    pxl = 1
    for x in range(size):
        if (x, 6) not in matrix:
            matrix[x, 6] = pxl
        pxl ^= 1
    pxl = 1
    for y in range(size):
        if (6, y) not in matrix:
            matrix[6, y] = pxl
        pxl ^= 1

    # --------------------------------------------------------------------------------------------
    # Add Dark Module
    # All QR codes have a dark module beside the bottom left finder pattern.
    # More specifically, the dark module is always located at the coordinate
    # ([(4 * V) + 9], 8) where V is the version of the QR code.
    matrix[8, (4 * version) + 9] = 1

    # --------------------------------------------------------------------------------------------
    # Add reserved areas

    # Format Information Area
    # A strip of modules beside the separators must be reserved for the format information area:
    # Near the top-left finder pattern, a one-module strip must be reserved below and to the right
    #   of the separator.
    # Near the top-right finder pattern, a one-module strip must be reserved below the separator.
    # Near the bottom-left finder pattern, a one-module strip must be reserved to the right
    #   of the separator.
    for x in range(9):
        if (x, 8) not in matrix:
            matrix[x, 8] = 2
    for y in range(8):
        if (8, y) not in matrix:
            matrix[8, y] = 2

    for x in range(size-8, size):
        if (x, 8) not in matrix:
            matrix[x, 8] = 2

    for y in range(size-7, size):
        if (8, y) not in matrix:
            matrix[8, y] = 2

    # Reserve Version Information Area if version >= 7
    # QR codes versions 7 and up must contain two areas where version information bits are placed.
    # The areas are a 6x3 block above the bottom-left finder pattern and a 3x6 block to the left
    # of the top-right finder pattern
    if version >= 7:
        for x in range(6):
            for y in range(size-11, size-8):
                matrix[x, y] = 2
        for y in range(6):
            for x in range(size-11, size-8):
                matrix[x, y] = 2

    # --------------------------------------------------------------------------------------------
    # Fill data area with data modules

    # The data modules have to be placed in a very specific pattern
    # The data bits are placed starting at the bottom-right of the matrix and proceeding upward
    # in a column that is 2 modules wide. Use white pixels for 0, and black pixels for 1.
    # When the column reaches the top, the next 2-module column starts immediately to the left
    # of the previous column and continues downward. Whenever the current column reaches the
    # edge of the matrix, move on to the next 2-module column and change direction.
    # If a function pattern or reserved area is encountered, the data bit is placed in the
    # next unused module. When the vertical timing pattern is reached, the next column starts to
    # the left of it
    # Module order when going upward  | Module order when going downward
    #              ┌───┬───┐                        ┌───┬───┐
    #              │ 8 │ 7 │                        │ 2 │ 1 │
    #              ├───┼───┤                        ├───┼───┤
    #              │ 6 │ 5 │                        │ 4 │ 3 │
    #              ├───┼───┤                        ├───┼───┤
    #              │ 4 │ 3 │                        │ 6 │ 5 │
    #              ├───┼───┤                        ├───┼───┤
    #              │ 2 │ 1 │                        │ 8 │ 7 │
    #              └───┴───┘                        └───┴───┘

    # The following generator generates this path over the whole of the QR code
    def walk_path():
        x, y = size-1, size-1
        upwards = ((-1, 0), (1, -1))
        downwards = ((-1, 0), (1, 1))
        while x >= 0:
            step = 0
            while 0 <= y:
                yield x, y
                dx, dy = upwards[step]
                step = (step+1) % 2
                x += dx
                y += dy
            y = 0
            x -= 2 if x != 8 else 3
            step = 0
            while y < size:
                yield x, y
                dx, dy = downwards[step]
                step = (step+1) % 2
                x += dx
                y += dy

            y = size-1
            x -= 2 if x != 8 else 3

    # The following expression returns a generator that gives the final message bits in order
    # If everything was set up correctly up until here, the number of message bits should be
    # exactly the same as the number of free (not taken / not reserved) modules in the matrix
    bits = map(int, final_message_bin)

    # use the walk_path generator and the bits generator to fill the data area
    # store the position of each encountered module in the data_area set
    for x, y in walk_path():
        if (x, y) not in matrix:
            matrix[x, y] = next(bits)
            matrix_data_area.add((x, y))

    # ============================================================================================
    # Data Masking - https://www.thonky.com/qr-code-tutorial/data-masking
    # ============================================================================================
    # Now that the modules have been placed in the matrix, the best mask pattern must be
    # determined. A mask pattern changes which modules are dark and which are light according
    # to a particular rule. The purpose of this step is to modify the QR code to make it as
    # easy for a QR code reader to scan as possible.

    # The mask patterns from https://www.thonky.com/qr-code-tutorial/mask-patterns
    masks = [
        lambda x, y:(x+y) % 2 == 0,
        lambda x, y:(y) % 2 == 0,
        lambda x, y:(x) % 3 == 0,
        lambda x, y:(x+y) % 3 == 0,
        lambda x, y:(x//3+y//2) % 2 == 0,
        lambda x, y:((x*y) % 2)+((x*y) % 3) == 0,
        lambda x, y:(((x*y) % 2)+((x*y) % 3)) % 2 == 0,
        lambda x, y:(((x+y) % 2)+((x*y) % 3)) % 2 == 0,
    ]

    # --------------------------------------------------------------------------------------------
    # Determining the Best Mask
    # After a mask pattern has been applied to the QR matrix, it is given a penalty score based
    # on four evaluation conditions that are defined in the QR code specification.
    # A QR code encoder must apply all eight mask patterns and evaluate each one.
    # Whichever mask pattern results in the lowest penalty score is the mask pattern that
    # must be used for the final output.

    # Keeping track of the best mask
    best_matrix_score = 10**99
    best_matrix = None

    # Generate all 8 QR codes (1 for each mask) and use the best one
    for mask in range(8):
        # Create a fresh copy of the matrix to not mess with the unmasked one
        matrix_candidate = matrix.copy()

        # ----------------------------------------------------------------------------------------
        # Add Format Information String
        # The format information string encodes which error correction level and which mask
        # pattern is in use in the current QR code. Since there are four possible error correction
        # levels (L, M, Q, and H) and eight possible mask patterns, there are 32 (4 times 8)
        # possible format information strings. The next section explains how to generate these
        # format strings. For a complete list of the 32 format strings, please refer to the table
        format_information_string = FORMAT_INFORMATION_STRINGS_TABLE[ecl][mask]

        # The format information string is placed below the topmost finder patterns and to the
        # right of the leftmost finder patterns
        # The number 0 in the image refers to the most significant bit of the format string,
        # and the number 14 refers to the least significant bit.
        ####################
        #              ██14#
        #  ██████████  ██13#
        #  ██      ██  ██12#
        #  ██      ██  ██11#
        #  ██      ██  ██10#
        #  ██████████  ██ 9#
        #              ██  #
        #████████████████ 8#
        # 0 1 2 3 4 5   6 7#
        ####################
        to_write = map(int, format_information_string)
        for x in range(9):
            if matrix_candidate[x, 8] == 2:
                matrix_candidate[x, 8] = next(to_write)
        for y in range(9, -1, -1):
            if matrix_candidate[8, y] == 2:
                matrix_candidate[8, y] = next(to_write)

        ####################         ##################
        #████████████████  #         #██              #
        #              ██ 6#         #██  ██████████  #
        #  ██████████  ██ 5#         #██  ██      ██  #
        #  ██      ██  ██ 4#         #██  ██      ██  #
        #  ██      ██  ██ 3#         #██  ██      ██  #
        #  ██      ██  ██ 2#         #██  ██████████  #
        #  ██████████  ██ 1#         #██              #
        #              ██ 0#         #████████████████#
        ####################         #7 8 9 1011121314#
                ##################
        to_write = map(int, format_information_string)
        for y in range(size-1, size-8, -1):
            if matrix_candidate[8, y] == 2:
                matrix_candidate[8, y] = next(to_write)
        for x in range(size-8, size):
            if matrix_candidate[x, 8] == 2:
                matrix_candidate[x, 8] = next(to_write)

        # ----------------------------------------------------------------------------------------
        # Add Version Information String if version >= 7
        # If the QR Code is version 7 or larger, you must include an 18-bit version information
        # string in the bottom left and top right corners of the QR code. For a full list of
        # all possible version information strings, refer to the table
        if version >= 7:
            version_information_string = VERSION_INFORMATION_STRINGS_TABLE[version]

            # The version information is placed beside the finder patterns
            # no matter how large the QR code is.

            # Bottom Left
            # The bottom left version information block is 3 pixels tall and 6 pixels wide.
            # The following table explains how to arrange the bits of the version information
            # string in the bottom-left version information area.
            # The 0 represents the RIGHTmost (least significant) bit of the version
            # information string, and the 17 represents the LEFTmost (most significant)
            # bit of the version information string.
            # ┌───┬───┬───┬───┬───┬───┐
            # │ 0 │ 3 │ 6 │ 9 │ 12│ 15│
            # ├───┼───┼───┼───┼───┼───┤
            # │ 1 │ 4 │ 7 │ 10│ 13│ 16│
            # ├───┼───┼───┼───┼───┼───┤
            # │ 2 │ 5 │ 8 │ 11│ 14│ 17│
            # └───┴───┴───┴───┴───┴───┘
            to_write = map(int, reversed(version_information_string))
            for x in range(6):
                for y in range(size-11, size-8):
                    if matrix_candidate[x, y] == 2:
                        matrix_candidate[x, y] = next(to_write)

            # Top Right
            # The top right version information block is 3 pixels wide and 6 pixels tall.
            # The following table explains how to arrange the bits of the version information
            # string in the top-right version information area. The 0 represents the RIGHTmost
            # (least significant) bit of the version information string, and the 17 represents
            # the LEFTmost (most significant) bit of the version information string.
            # ┌───┬───┬───┐
            # │ 0 │ 1 │ 2 │
            # ├───┼───┼───┤
            # │ 3 │ 4 │ 5 │
            # ├───┼───┼───┤
            # │ 6 │ 7 │ 8 │
            # ├───┼───┼───┤
            # │ 9 │ 10│ 11│
            # ├───┼───┼───┤
            # │ 12│ 13│ 14│
            # ├───┼───┼───┤
            # │ 15│ 16│ 17│
            # └───┴───┴───┘
            to_write = map(int, reversed(version_information_string))
            for y in range(6):
                for x in range(size-11, size-8):
                    if matrix_candidate[x, y] == 2:
                        matrix_candidate[x, y] = next(to_write)

        # ----------------------------------------------------------------------------------------
        # Apply Mask to data
        # Mask patterns must ONLY be applied to data modules and error correction modules.
        # In other words: Do not mask function patterns (finder & alignment patterns,
        # timing patterns, separators)
        # Do not mask reserved areas (format information area, version information area)
        # Here we use the matrix_data_area set from before to check if the mask should be applied
        masked_matrix = dict()
        mask_f = masks[mask]
        for k, v in matrix_candidate.items():
            if k in matrix_data_area:
                masked_matrix[k] = v ^ 1 if mask_f(*k) else v
            else:
                masked_matrix[k] = v

        # ----------------------------------------------------------------------------------------
        # Calculating the penalties

        # Penalty 1
        # For the first evaluation condition, check each row one-by-one.
        # If there are five consecutive modules of the same color, add 3 to the penalty.
        # If there are more modules of the same color after the first five, add 1 for each
        # additional module of the same color. Afterward, check each column one-by-one, checking
        # for the same condition. Add the horizontal and vertical total to obtain penalty score 1.
        penalty1 = 0

        # Rows
        for y in range(size):
            current_bit = None
            current_run = 1
            for x in range(size):
                if masked_matrix[x, y] == current_bit:
                    current_run += 1
                    if current_run == 5:
                        penalty1 += 3
                    elif current_run > 5:
                        penalty1 += 1
                else:
                    current_run = 1
                    current_bit = masked_matrix[x, y]
        # Columns
        for x in range(size):
            current_bit = None
            current_run = 1
            for y in range(size):
                if masked_matrix[x, y] == current_bit:
                    current_run += 1
                    if current_run == 5:
                        penalty1 += 3
                    elif current_run > 5:
                        penalty1 += 1
                else:
                    current_run = 1
                    current_bit = masked_matrix[x, y]

        # Penalty 2
        # For second evaluation condition, look for areas of the same color that are at least
        # 2x2 modules or larger. The QR code specification says that for a solid-color block
        # of size m × n, the penalty score is 3 × (m - 1) × (n - 1). However, the QR code
        # specification does not specify how to calculate the penalty when there are multiple
        # ways of dividing up the solid-color blocks. Therefore, rather than looking for
        # solid-color blocks larger than 2x2, simply add 3 to the penalty score for every
        # 2x2 block of the same color in the QR code, making sure to count overlapping 2x2 blocks.
        # For example, a 3x2 block of the same color should be counted as two 2x2 blocks,
        # one overlapping the other.
        penalty2 = 0
        for x in range(size-1):
            for y in range(size-1):
                if masked_matrix[x, y] == masked_matrix[x+1, y] == masked_matrix[x, y+1] == masked_matrix[x+1, y+1]:
                    penalty2 += 3

        # Penalty 3
        # The third penalty rule looks for patterns of dark-light-dark-dark-dark-light-dark that
        # have four light modules on either side.
        # In other words, it looks for any of the following two patterns:
        ########################      ########################
        #████████  ██      ██  #      #  ██      ██  ████████#
        ########################      ########################
        penalty3 = 0
        # Horizonal
        for y in range(size):
            for x in range(size-10):
                horiz = (
                    masked_matrix[x, y],
                    masked_matrix[x+1, y],
                    masked_matrix[x+2, y],
                    masked_matrix[x+3, y],
                    masked_matrix[x+4, y],
                    masked_matrix[x+5, y],
                    masked_matrix[x+6, y],
                    masked_matrix[x+7, y],
                    masked_matrix[x+8, y],
                    masked_matrix[x+9, y],
                    masked_matrix[x+10, y],
                )
                if horiz in ((1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0), (0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1)):
                    penalty3 += 40

        # Vertical
        for x in range(size):
            for y in range(size-10):
                vert = (
                    masked_matrix[x, y],
                    masked_matrix[x, y+1],
                    masked_matrix[x, y+2],
                    masked_matrix[x, y+3],
                    masked_matrix[x, y+4],
                    masked_matrix[x, y+5],
                    masked_matrix[x, y+6],
                    masked_matrix[x, y+7],
                    masked_matrix[x, y+8],
                    masked_matrix[x, y+9],
                    masked_matrix[x, y+10],
                )
                if vert in ((1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0), (0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1)):
                    penalty3 += 40

        # Penalty 4
        # The final evaluation condition is based on the ratio of light modules to dark modules. To calculate this penalty rule, do the following steps:
        # Count the total number of modules in the matrix.
        # Count how many dark modules there are in the matrix.
        # Calculate the percent of modules in the matrix that are dark: (dark / total) * 100
        # Determine the previous and next multiple of five of this percent.
        #   For 43 percent, the previous multiple is 40, and the next multiple is 45.
        # Subtract 50 from each of these multiples and take the absolute value of the result.
        #   For example, |40 - 50| = |-10| = 10 and |45 - 50| = |-5| = 5.
        # Divide each of these by five. For example, 10/5 = 2 and 5/5 = 1.
        # Finally, take the smallest of the two numbers and multiply it by 10.
        # In this example, the lower number is 1, so the result is 10. This is penalty score #4.
        num_modules = size * size
        dark_modules = [*masked_matrix.values()].count(1)
        percentage = (dark_modules / num_modules) * 100
        lower = 100 * dark_modules // num_modules
        while lower % 5:
            lower -= 1
        higher = 100 * dark_modules // num_modules + 1
        while higher % 5:
            higher += 1
        lower = abs(lower-50)
        higher = abs(higher-50)
        lower //= 5
        higher //= 5
        penalty4 = 10 * min(lower, higher)

        total = sum((penalty1, penalty2, penalty3, penalty4))

        # Check if current masked matrix is best we have seen so far and if yes -> store it
        if total < best_matrix_score:
            best_matrix_score = total
            best_matrix = masked_matrix

    # Output the best matrix as a string (or other format)
    if output == 'full_str':
        return get_matrix_str_full_size(best_matrix)
    elif output == 'half_str':
        return get_matrix_str_half_size(best_matrix)
    elif output == 'all':
        return (
            get_matrix_str_full_size(best_matrix),
            get_matrix_str_half_size(best_matrix)
        )
    # Implement PNG output here :)

if __name__ == '__main__':
    for res in generate_qr_code(data, ecl, output='all', verbose=True):
        print(res)
